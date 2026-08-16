"""끝난 대회의 후기 요약(ai_summary) 생성 — 웹 검색 기반.

ai_summary.py 와 목적은 같지만(같은 필드를 채운다) 재료가 다르다. 그쪽은 DB 에 있는
소개문·주최·코스 정보만 쓰기 때문에, 그 값들이 비어 있는 대회는 MIN_MATERIAL_CHARS
문턱에서 걸러진다 — 요약이 없는 대회가 정확히 그 대회들이라 그 경로로는 영영 안 채워진다.

끝난 지 한 달이 넘었으면 웹에 참가 후기가 남아 있다. OpenAI Responses API 의 web_search
툴로 그 후기를 읽어 3줄로 요약한다. 대상은 ai_summary 가 비어 있는 대회뿐이고, 이미 있는
요약(관리자가 손댄 것 포함)은 건드리지 않는다.

신뢰도 설계 (reg_status.py 와 같은 원칙 — LLM 출력은 신뢰하지 않는다):
  후기는 원문을 우리가 들고 있지 않아 reg_status 의 _evidence_in_page 같은 문자열 대조를
  할 수 없다. 대신 응답의 구조로 검증한다.
  - web_search_call 이 없으면 = 검색을 안 하고 사전지식으로 지어낸 것 → 기각
  - url_citation 이 0건이면 → 기각
  - 쓸 후기가 없으면 NONE 만 출력하도록 지시하고, NONE 은 스킵으로 센다
  거짓 요약 한 건이 빈 칸 하나보다 나쁘므로 재현율보다 정확도에 몰아준다.
"""

import logging
import re
import time
from datetime import timedelta

import httpx
from django.conf import settings
from django.core.cache import cache
from django.db.models import Q
from django.utils import timezone

from races.models import Race

from ..constants import SPORT_LABELS
from .ai_summary import _clean

logger = logging.getLogger(__name__)

FINISHED_DAYS = 30       # 대회가 끝나고 이만큼 지나야 후기가 쌓인다
MIN_SUMMARY_CHARS = 20   # 이보다 짧으면 실패로 본다
NO_MATERIAL_TOKEN = 'NONE'

# 후기가 안 잡히는 대회는 매주 같은 자리를 다시 차지한다. 시도 기록을 남겨 한동안 제외한다.
# 필드를 늘리면 마이그레이션이 필요하고 이 값은 영구 보존할 이유도 없어서 캐시에 둔다.
TRIED_CACHE_PREFIX = 'ai_recap:tried:'
TRIED_TTL = 60 * 60 * 24 * 60  # 60일

# 우리 사이트를 읽고 되돌려주면 순환이다 — 채우려는 빈칸을 우리 페이지에서 다시 읽게 된다.
BLOCKED_DOMAINS = ['endurohub.kr', 'www.endurohub.kr']

# 문체 규약은 ai_summary.SYSTEM_PROMPT 와 맞춘다. 같은 필드에 들어가 상세 페이지의 같은
# 자리에 렌더링되므로 두 경로의 결과가 따로 놀면 안 된다.
SYSTEM_PROMPT = f"""너는 이미 끝난 국내 지구력 스포츠 대회의 참가 후기를 찾아 정리하는 편집자다.
웹을 검색해 실제 참가자가 쓴 후기를 읽고, 그 대회를 한국어 3문장으로 요약한다.

작업 순서:
1. 주어진 대회명과 연도로 참가 후기를 검색한다. 블로그·카페 후기가 1차 자료다.
2. 검색 결과에서 실제로 그 대회, 그 연도(또는 인접 회차)를 다녀온 사람의 글을 고른다.
3. 그 글들에 실제로 적힌 내용만으로 3문장을 쓴다.

무엇을 쓰나 — 참가자가 직접 겪어야 알 수 있는 것:
- 코스 체감 (오르막 구간, 노면 상태, 반환점, 코스 풍경, 실제 난이도)
- 대회 운영 (보급 상태, 주차·셔틀, 화장실, 기록 측정, 출발 혼잡도)
- 기념품·완주 메달의 실물 평
- 다음에 참가할 사람이 미리 알면 좋은 것 (날씨, 도착 시간, 짐 보관)

무엇을 쓰지 않나:
- 대회명, 회차, 접수 기간, 참가비 금액, 종목 거리 나열, 대회 날짜, 주소.
  이 값들은 요약 바로 위·아래에 그대로 표시되므로 문장으로 반복하면 안 된다.
  '제30회 OO마라톤(2026) 코스는~' 처럼 시작하지 말고 바로 '코스는~' 으로 시작해라.
- 검색 결과에 없는 사실. 추측하거나 일반적인 마라톤 상식으로 메우지 마라.
- 다른 대회 후기에서 가져온 내용. 대회명이 일치하는지 확인해라.
- '다양한 거리를 선택할 수 있어 입문자에게 좋음' 같은 어느 대회에나 해당하는 문장.
- '최고', '최대', '환상적인', '아름다운' 같은 홍보성 수식어.
- 특정 개인의 완주 기록이나 개인 사정.

형식:
- 정확히 3문장. 각 문장은 '~였음.', '~해야 함.', '~구성.' 같은 음슴체로 끝낸다.
- 날짜를 꼭 언급해야 한다면 '11월 16일'처럼 한국어로 쓴다. ISO 형식(2026-11-16) 금지.
- 문장 사이는 줄바꿈 하나로 구분한다. 머리말, 목록 기호, 따옴표 없이 본문만 출력한다.
- 출처 링크나 각주를 본문에 쓰지 마라. URL, 마크다운 링크, 괄호 안 도메인 표기 모두 금지다.

쓸 만한 후기를 못 찾았을 때:
- 억지로 만들지 말고 {NO_MATERIAL_TOKEN} 한 단어만 출력한다.
- 검색 결과가 대회 공지·접수 페이지뿐이고 참가 후기가 없으면 {NO_MATERIAL_TOKEN} 이다.
- 3문장을 채울 만큼 없으면 {NO_MATERIAL_TOKEN} 이다. 두 문장으로 줄이지 마라."""


# 출처 표기를 하지 말라고 지시해도 모델이 문장 끝에 마크다운 인용을 붙인다
# (예: '...했음. ([gorunning.kr](https://...))'). 화면에 그대로 나가면 안 되므로 걷어낸다.
_MD_LINK = re.compile(r'\(?\[[^\]]*\]\(https?://[^)]*\)\)?')
_BARE_URL = re.compile(r'\(?\s*https?://\S+\s*\)?')

# 후기를 못 찾았을 때 NONE 대신 이유를 풀어 쓰는 경우가 있다. 그 문장이 요약으로 저장되면
# 대회 설명 자리에 '못 찾았음'이 박힌다 — NONE 토큰만 믿지 않고 내용으로도 거른다.
_META_PHRASES = (
    '확인할 수 없', '확인되지 않', '찾을 수 없', '찾지 못', '검색 결과',
    '후기를 특정', '자료가 없', '정보가 없', '구성할 수 없',
)


def _tried_key(slug):
    return f'{TRIED_CACHE_PREFIX}{slug}'


def _strip_citations(text):
    """본문에 섞여 들어온 마크다운 인용·맨 URL 을 제거한다."""
    text = _MD_LINK.sub('', text)
    text = _BARE_URL.sub('', text)
    # 인용을 걷어내면 ' .' 이나 줄 끝 공백이 남는다.
    text = re.sub(r'[ \t]+([.,])', r'\1', text)
    return '\n'.join(line.rstrip() for line in text.split('\n'))


def _looks_like_meta(text):
    """'후기를 못 찾았다'는 설명문인지."""
    return any(p in text for p in _META_PHRASES)


def _target_races(days=FINISHED_DAYS):
    """끝난 지 days 일 넘은 + 요약이 비어 있는 + 자동갱신이 켜진 대회들.

    race_end_date 가 있으면 그걸, 없으면 race_date 를 기준으로 삼는다 —
    reg_status._target_races() 와 같은 폴백이다(부호만 반대).
    """
    cutoff = timezone.localdate() - timedelta(days=days)
    finished = (
        Q(race_end_date__lt=cutoff) |
        Q(race_end_date__isnull=True, race_date__lt=cutoff)
    )
    empty = Q(ai_summary__isnull=True) | Q(ai_summary='')
    return (
        Race.objects
        .filter(finished)
        .filter(empty)
        .filter(auto_update_enabled=True)
        .order_by('-race_date')
    )


def _build_query(race):
    """모델에 넘길 지시문. 검색어를 직접 주지 않고 대회를 특정할 정보를 준다."""
    year = race.race_date.year if race.race_date else None
    lines = [f'대회명: {race.title}']
    if year:
        lines.append(f'개최 연도: {year}년')
    if race.race_date:
        lines.append(f'개최일: {race.race_date.year}년 {race.race_date.month}월 {race.race_date.day}일')
    if race.sport:
        lines.append(f'종목: {SPORT_LABELS.get(race.sport, race.sport)}')
    if race.location:
        lines.append(f'장소: {race.location}')
    if race.region:
        lines.append(f'지역: {race.region}')
    if race.organizer:
        lines.append(f'주최: {race.organizer}')
    # 후기 링크를 이미 알고 있으면 검색을 그쪽으로 유도한다.
    if race.recap_url:
        lines.append(f'참고 후기 링크: {race.recap_url}')

    return (
        '아래 대회의 참가 후기를 검색해 3문장으로 요약해라.\n'
        '동명의 다른 지역·다른 연도 대회와 헷갈리지 않도록 장소와 연도를 함께 확인해라.\n\n'
        + '\n'.join(lines)
    )


def _call_responses(user_message):
    """Responses API 를 web_search 툴과 함께 호출한다. 실패하면 None.

    reg_status._call_openai 와 달리 /chat/completions 가 아니라 /responses 다 —
    내장 web_search 툴이 Responses API 에만 있다. openai SDK 를 새로 넣지 않고
    저장소 관행대로 httpx 로 직접 친다.
    """
    payload = {
        'model': settings.AI_RECAP_MODEL,
        'instructions': SYSTEM_PROMPT,
        'input': user_message,
        'tools': [{
            'type': 'web_search',
            # 국내 대회 후기는 검색 엔진 색인이 얕아 medium 으로는 잘 안 걸린다.
            'search_context_size': 'high',
            'filters': {'blocked_domains': BLOCKED_DOMAINS},
            'user_location': {'type': 'approximate', 'country': 'KR'},
        }],
        'max_output_tokens': 2048,
    }
    headers = {
        'Authorization': f'Bearer {settings.LLM_API_KEY}',
        'Content-Type': 'application/json',
    }
    try:
        # 검색 + 페이지 읽기가 붙어 순수 생성보다 오래 걸린다.
        resp = httpx.post(
            f'{settings.LLM_BASE_URL}/responses',
            json=payload,
            headers=headers,
            timeout=max(settings.LLM_TIMEOUT, 90),
        )
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPStatusError as exc:
        logger.warning(
            'ai_recap: Responses API returned %s: %s',
            exc.response.status_code, exc.response.text[:300],
        )
        return None
    except (httpx.HTTPError, ValueError) as exc:
        logger.warning('ai_recap: Responses API call failed: %s', exc)
        return None


def _extract(data):
    """(text, citations, searched) 를 돌려준다.

    searched 는 모델이 실제로 web_search 를 호출했는지다 — 검색 없이 나온 답은
    사전지식으로 지어낸 것이므로 호출부에서 기각한다.
    """
    text_parts = []
    citations = []
    searched = False

    for item in (data.get('output') or []):
        item_type = item.get('type')
        if item_type == 'web_search_call':
            searched = True
            continue
        if item_type != 'message':
            continue
        for block in (item.get('content') or []):
            if block.get('text'):
                text_parts.append(block['text'])
            for ann in (block.get('annotations') or []):
                if ann.get('type') == 'url_citation' and ann.get('url'):
                    citations.append(ann['url'])

    return '\n'.join(text_parts).strip(), citations, searched


def generate_recap(race):
    """대회 하나의 후기 요약을 생성한다.

    (summary, reason) 을 돌려준다. summary 가 None 이면 reason 이 이유다 —
    호출부가 카운트하고 '후기 없음'과 '호출 실패'를 구분하기 위해 나눠준다.
    """
    if not settings.LLM_API_KEY:
        logger.warning('ai_recap: LLM_API_KEY 미설정')
        return None, 'no_api_key'

    # 이 경로는 OpenAI Responses API 의 내장 web_search 툴에 묶여 있다. anthropic provider
    # 에는 대응 엔드포인트가 없어서(서버사이드 검색은 messages API 의 tools 로 들어간다)
    # 조용히 엉뚱한 URL 을 치는 대신 여기서 멈춘다.
    if settings.LLM_PROVIDER != 'openai':
        logger.warning('ai_recap: openai provider 전용인데 LLM_PROVIDER=%s', settings.LLM_PROVIDER)
        return None, 'unsupported_provider'

    data = _call_responses(_build_query(race))
    if data is None:
        return None, 'api_error'

    text, citations, searched = _extract(data)

    if not searched:
        # 검색 없이 답했다 = 근거가 없다. 그럴듯해 보여도 기각한다.
        logger.warning('ai_recap: no web_search call, rejected', extra={'slug': race.slug})
        return None, 'rejected_no_search'

    if not text or text.strip().upper().startswith(NO_MATERIAL_TOKEN):
        return None, 'no_material'

    if _looks_like_meta(text):
        # NONE 대신 이유를 풀어 쓴 경우. 인용이 붙어 있어도 요약이 아니므로 여기서 막는다.
        return None, 'no_material'

    if not citations:
        logger.warning('ai_recap: no citations, rejected', extra={
            'slug': race.slug, 'text': text[:120],
        })
        return None, 'rejected_no_citation'

    summary = _clean(_strip_citations(text))
    if not summary or len(summary) < MIN_SUMMARY_CHARS:
        return None, 'too_short'

    logger.info('ai_recap: generated', extra={
        'slug': race.slug, 'citations': citations[:5], 'length': len(summary),
    })
    return summary, 'ok'


def generate_race_recaps(dry_run=False, limit=None, days=FINISHED_DAYS, slug=None,
                         sleep=0.0, on_result=None):
    """잡 1회 실행. 요약 카운트를 반환한다.

    on_result(race, text, reason) 가 주어지면 대회마다 호출한다 — 관리 명령이
    dry-run 으로 프롬프트를 다듬을 때 생성된 문장을 봐야 하기 때문이다.
    """
    summary_counts = {
        'total': 0, 'generated': 0, 'no_material': 0,
        'rejected': 0, 'errors': 0, 'skipped_tried': 0, 'skipped_existing': 0,
    }

    if slug:
        races = Race.objects.filter(slug=slug)
    else:
        races = _target_races(days=days)

    targets = []
    for race in races.iterator():
        # 직접 지정한 slug 는 시도 기록을 무시한다 — 수동 재시도가 막히면 안 된다.
        if not slug and cache.get(_tried_key(race.slug)):
            summary_counts['skipped_tried'] += 1
            continue
        targets.append(race)
        if limit and len(targets) >= limit:
            break

    for i, race in enumerate(targets):
        summary_counts['total'] += 1
        text, reason = generate_recap(race)

        if text is None:
            if reason == 'no_material':
                summary_counts['no_material'] += 1
            elif reason.startswith('rejected'):
                summary_counts['rejected'] += 1
            else:
                summary_counts['errors'] += 1
            # 호출 자체가 실패한 건은 다음 회차에 다시 시도할 값어치가 있다.
            # 후기가 없거나 기각된 건만 한동안 제외한다.
            if reason in ('no_material', 'rejected_no_citation', 'rejected_no_search', 'too_short'):
                if not dry_run:
                    cache.set(_tried_key(race.slug), reason, TRIED_TTL)
        else:
            summary_counts['generated'] += 1
            # --slug 는 대상 필터를 우회하므로 여기서 한 번 더 막는다. 기존 요약(관리자가
            # 손댄 것 포함)을 덮어쓰지 않는 게 이 잡의 유일한 불변식이라 쓰기 직전에 본다.
            if race.ai_summary and race.ai_summary.strip():
                summary_counts['generated'] -= 1
                summary_counts['skipped_existing'] += 1
                reason = 'has_summary'
                text = None
            elif not dry_run:
                race.ai_summary = text
                race.save(update_fields=['ai_summary', 'updated_at'])

        if on_result:
            on_result(race, text, reason)

        if sleep and i < len(targets) - 1:
            time.sleep(sleep)

    logger.info('ai_recap: run completed', extra=summary_counts)
    return summary_counts
