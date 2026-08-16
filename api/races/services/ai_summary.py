"""대회 요약(ai_summary) 생성.

대회 603건 중 541건이 원본 사이트에서 긁어온 정보라, 상세 페이지에서 원본에 없는
콘텐츠는 이 요약뿐이다. 그런데 보유 건수가 47건(8%)에 그쳐 사실상 없는 것과 같았다.

프로바이더는 settings.LLM_PROVIDER 를 따른다('anthropic' | 'openai' 호환). 호출부 형태는
reg_status.py 와 겹치는데, 그쪽은 판정용 JSON 스키마와 토큰 한도가 묶여 있어 그대로는
재사용할 수 없다. 동작 중인 접수마감 판정 경로를 건드리지 않으려고 여기 별도로 둔다.

── 아직 일괄 실행하지 않았다 ──────────────────────────────────────────────────
gpt-5.4-nano / gpt-5.4-mini 로 표본을 dry-run 해 본 결과 품질이 기준에 못 미쳤다.
소개문이 가장 긴 대회들(1,200~3,900자)에서조차 출력의 절반가량이 상세 페이지의 표에
이미 있는 값(장소·주최·종목 거리·기념품)을 문장으로 옮긴 것이었다. 근본 원인은 모델이
아니라 원본 데이터다 — 소개문 길이 중앙값이 78자라 대부분의 대회는 표 밖에 쓸 재료가
없다. 이 상태로 556건을 채우면 색인이 거부된 페이지에 중복 문장을 더 얹는 셈이라,
줄이려던 문제를 키운다.

실제로 쓸 만한 출력이 나온 경우는 소개문에 표 밖의 사실이 있을 때였다
(예: '광안대교를 가로지르는 풀코스', '참가인원 400명', '셔틀버스 운행').
즉 선행 조건은 소개문 보강(crawler/enrich.py)이지 프롬프트 튜닝이 아니다.

따라서 이 모듈은 도구로만 커밋하고 배치 실행은 하지 않는다. 스케줄에도 걸지 않았다.
재평가할 때는 --limit N --dry-run 으로 표본부터 보고 판단할 것.
"""

import json
import logging

import httpx
from django.conf import settings

from ..constants import SPORT_LABELS

logger = logging.getLogger(__name__)

MAX_DESCRIPTION_CHARS = 1500
# 요약 재료가 이만큼도 안 되면 건너뛴다. 소개문 중앙값이 78자라 이 선에서 대략 절반이
# 걸러진다 — 남는 쪽이 실제로 쓸 말이 있는 대회다.
MIN_MATERIAL_CHARS = 60

# 이 요약의 존재 이유는 상세 페이지의 표가 못 담는 것을 담는 것이다. 날짜·참가비·종목
# 목록은 바로 아래 표에 그대로 나오므로, 요약이 그걸 반복하면 페이지 안에서도 중복이고
# 대회끼리도 똑같은 문장이 된다(첫 시안이 정확히 그렇게 나왔다). 그래서 표에 있는 값은
# '맥락'으로만 주고 되풀이를 금지한다.
SYSTEM_PROMPT = """너는 국내 지구력 스포츠 대회 정보를 정리하는 편집자다.
이 대회를 다른 대회와 구별해 주는 내용을 한국어 2~3문장으로 쓴다.

무엇을 쓰나:
- 코스와 장소의 성격 (해안/도심/산악/강변, 순환인지 왕복인지, 출발지의 특징)
- 대회의 성격과 규모 (회차, 주최 성격, 정원, 기부·축제 등 목적)
- 참가자가 미리 알아야 할 것 (컷오프, 정원 마감, 필수 장비, 셔틀, 코스 난이도)
- 기념품 구성이 특징적일 때만 기념품

가장 중요한 규칙 — 모든 표현은 입력에 적힌 문구로 되짚을 수 있어야 한다:
- 대회명이나 장소 이름에서 코스 성격을 추측하지 마라. '한강런'이라고 강변 코스라고 쓰거나
  '아라타워'라고 해안 도로라고 쓰면 안 된다. 소개문에 그렇게 적혀 있을 때만 쓴다.
- 릴레이·팀·순환·왕복·고도·난이도는 입력에 그 단어가 있을 때만 쓴다.
- 한 문장이라도 근거를 못 찾겠으면 그 문장을 빼라. 짧은 요약이 틀린 요약보다 낫다.

쓰지 말아야 할 것:
- 접수 기간, 참가비 금액, 종목 거리 나열, 대회 날짜, 주소.
  이 값들은 요약 바로 아래 표에 그대로 표시되므로 문장으로 반복하면 안 된다.
- 어느 대회에나 해당하는 말. 아래는 전부 금지다:
  '사전에 확인해야 함', '안내에 따라 집결·이동해야 함', '동선을 확인해야 함',
  '정원 마감이 있을 수 있으니 서둘러야 함', '개인 준비물을 갖춰야 함',
  '다양한 거리를 선택할 수 있어 입문자에게 좋음'.
  이런 말밖에 쓸 게 없으면 그 문장을 아예 빼라.
- '최고', '최대', '환상적인', '아름다운' 같은 홍보성 수식어.

형식:
- 최대 2문장. 한 문장이면 한 문장만 쓴다. 분량을 채우려고 늘리지 마라.
- 한 문장은 60자 안팎으로 짧게.
- 문장은 '~임.', '~함.', '~됨.', '~구성.' 처럼 음슴체 종결어미로 끝낸다.
  '대회'라는 낱말을 종결어미처럼 붙이지 마라 ('코스 구성대회.', '축제의 장대회.' 는 비문이다).
- 날짜를 꼭 언급해야 한다면 '11월 16일'처럼 한국어로 쓴다. ISO 형식(2026-11-16) 금지.
- 문장 사이는 줄바꿈 하나로 구분한다. 머리말, 목록 기호, 따옴표 없이 본문만 출력한다."""


def build_user_message(race):
    """모델 입력을 만든다.

    입력을 두 덩이로 나눈다. '표에 이미 있는 값'은 상세 페이지가 그대로 보여주는
    것이라 요약이 되풀이하면 안 되고, 그럼에도 문장을 자연스럽게 쓰려면 알고는 있어야
    해서 맥락으로만 넘긴다. 두 번째 덩이가 실제 요약 재료다.

    (context, material) 을 돌려준다 — material 이 비면 쓸 말이 없다는 뜻이다.
    """
    context = []
    material = []

    def add(bucket, key, value):
        if value:
            bucket.append(f'{key}: {value}')

    add(context, '대회명', race.title)
    # sport 는 choices 없는 CharField 라 get_sport_display() 가 없다.
    add(context, '종목', SPORT_LABELS.get(race.sport, race.sport))
    add(context, '대회일', _format_date(race.race_date))
    add(context, '장소', race.location)
    add(context, '지역', race.region)

    if race.distances:
        courses = []
        for d in race.distances:
            if not isinstance(d, dict):
                continue
            name = d.get('name')
            if not name:
                continue
            cutoff = d.get('cutoff')
            courses.append(f'{name}(컷오프 {cutoff})' if cutoff else name)
        add(context, '코스', ', '.join(courses))

    if race.registration_start or race.registration_end:
        start = _format_date(race.registration_start) or '미정'
        end = _format_date(race.registration_end) or '미정'
        add(context, '접수 기간', f'{start} ~ {end}')

    # ── 요약 재료 ──────────────────────────────────────────────────────────
    add(material, '주최', race.organizer)
    if race.giveaways:
        add(material, '기념품', ', '.join(str(g) for g in race.giveaways if g))
    add(material, '노면', race.course_surface)
    add(material, '난이도', race.course_difficulty)
    add(material, '보급', race.aid_stations)
    add(material, '기록 측정', race.timing_method)
    add(material, '주차', race.parking)

    if race.description:
        desc = ' '.join(race.description.split())[:MAX_DESCRIPTION_CHARS]
        add(material, '주최측 소개문', desc)

    message = (
        '[표에 이미 표시되는 값 — 맥락 참고용, 문장에 반복하지 말 것]\n'
        + '\n'.join(context)
        + '\n\n[요약 재료]\n'
        + '\n'.join(material)
    )
    return message, material


def _format_date(value):
    """ISO 대신 한국어 표기 — 모델이 날짜를 인용할 때 그대로 쓰게 한다."""
    if not value:
        return None
    return f'{value.year}년 {value.month}월 {value.day}일'


def _call_anthropic(system_prompt, user_message):
    try:
        import anthropic
    except ImportError:
        logger.warning('ai_summary: anthropic SDK not installed')
        return None
    try:
        client = anthropic.Anthropic(api_key=settings.LLM_API_KEY).with_options(
            timeout=max(settings.LLM_TIMEOUT, 30)
        )
        resp = client.messages.create(
            model=settings.LLM_MODEL or 'claude-opus-5',
            max_tokens=1000,
            system=system_prompt,
            messages=[{'role': 'user', 'content': user_message}],
        )
        for block in resp.content:
            if getattr(block, 'type', None) == 'text' and getattr(block, 'text', None):
                return block.text
        return None
    except Exception as exc:  # noqa: BLE001
        logger.warning('ai_summary Anthropic call failed: %s', exc)
        return None


def _call_openai(system_prompt, user_message):
    # reg_status 와 같은 이유로 max_completion_tokens 를 쓴다 — gpt-5 계열은 max_tokens 를
    # 거부하고, reasoning 토큰이 완성 한도를 잠식하므로 여유 있게 잡는다.
    payload = {
        'model': settings.LLM_MODEL or 'gpt-4o-mini',
        'max_completion_tokens': 2048,
        'messages': [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_message},
        ],
    }
    headers = {
        'Authorization': f'Bearer {settings.LLM_API_KEY}',
        'Content-Type': 'application/json',
    }
    try:
        resp = httpx.post(
            f'{settings.LLM_BASE_URL}/chat/completions',
            json=payload,
            headers=headers,
            timeout=max(settings.LLM_TIMEOUT, 60),
        )
        resp.raise_for_status()
        data = resp.json()
        return data['choices'][0]['message']['content']
    except (httpx.HTTPError, KeyError, IndexError, json.JSONDecodeError) as exc:
        logger.warning('ai_summary OpenAI call failed: %s', exc)
        return None


def _clean(text):
    """모델 출력에서 머리말·목록 기호·빈 줄을 걷어낸다."""
    if not text:
        return None
    lines = []
    for raw in text.replace('\r\n', '\n').split('\n'):
        line = raw.strip().lstrip('-•*').strip()
        if not line:
            continue
        lines.append(line)
    if not lines:
        return None
    return '\n'.join(lines)


def generate_summary(race):
    """대회 하나의 요약을 생성한다. 실패하면 None."""
    if not settings.LLM_API_KEY:
        logger.warning('ai_summary: LLM_API_KEY 미설정')
        return None

    user_message, material = build_user_message(race)
    # 표에 있는 값 말고 쓸 재료가 없으면 생성하지 않는다. 억지로 만들면 대회마다 똑같은
    # 상투구가 붙어서, 줄이려던 중복을 오히려 늘린다.
    if not material or sum(len(m) for m in material) < MIN_MATERIAL_CHARS:
        return None

    if settings.LLM_PROVIDER == 'anthropic':
        raw = _call_anthropic(SYSTEM_PROMPT, user_message)
    else:
        raw = _call_openai(SYSTEM_PROMPT, user_message)

    return _clean(raw)
