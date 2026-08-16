"""접수 마감상태 자동 갱신 — 마감 전 대회의 공식 페이지를 읽어 접수마감 여부를 판정하고 반영.

흐름:
  1. 마감 전(upcoming/registration_open) + official_url/source_url 있는 대회를 ORM으로 조회
  2. 페이지 텍스트 추출(httpx + BS4) → LLM 판정 (closed / reg_close / evidence)
  3. '마감' 판정 + 근거 인용문이 실제 페이지에 존재할 때만 status='registration_closed' 반영
     - auto_update_enabled=False 또는 locked_fields에 status가 있으면 건너뜀

신뢰도 설계 (nl_search와 동일 원칙 — LLM 출력은 신뢰하지 않는다):
  - closed=true 는 evidence(원문 인용)가 페이지 텍스트에 실제로 존재할 때만 인정.
    환각 인용은 기계적으로 기각된다.
  - 확신이 없으면 closed=false 로 답하도록 지시 — 못 잡은 마감(false negative)은
    다음 날 재시도 + registration_end 기반 computed_status 가 자연 복구하므로
    false positive 억제에만 집중한다.
"""
import json
import logging
import re
from datetime import date, datetime

import httpx
from bs4 import BeautifulSoup
from django.conf import settings
from django.db.models import Q
from django.utils import timezone

from races.models import Race

logger = logging.getLogger(__name__)

PAGE_TEXT_LIMIT = 6000   # LLM에 넘길 페이지 텍스트 최대 길이
MIN_PAGE_TEXT = 200      # 이보다 짧으면 에러/빈 페이지로 보고 판정하지 않는다
MIN_EVIDENCE = 5         # 근거 인용문 최소 길이 (이보다 짧으면 근거로 인정 안 함)

_SYSTEM_PROMPT = (
    '너는 대회 접수 페이지를 읽고 참가신청(접수)이 마감되었는지 판정하는 검수자다. '
    "페이지 원문에 '접수마감', '신청마감', '마감되었습니다', '접수 종료', '조기 마감', "
    "'closed', 'sold out' 등 명시적 근거가 있을 때만 closed=true 로 판정한다. "
    "선착순 마감 '예고', 마감 '임박', 접수 기간이 아직 남은 경우는 closed=false. "
    'JSON 객체로만 응답하고 다른 텍스트는 출력하지 마라.\n'
    '출력 형식: {"closed": true|false, "reg_close": "YYYY-MM-DD 또는 null", "evidence": "근거 문구"}\n'
    '- closed=true 라면 근거가 된 문구를 evidence에 페이지 원문 그대로(수정 없이) 인용한다.\n'
    '- 페이지에서 접수 마감일을 확인할 수 있으면 reg_close에 적는다 (불명확하면 null).\n'
    '- 확신이 없으면 반드시 closed=false 로 답한다.'
)

_VERDICT_SCHEMA = {
    'type': 'object',
    'properties': {
        'closed': {'type': 'boolean'},
        'reg_close': {'type': ['string', 'null']},
        'evidence': {'type': 'string'},
    },
    'required': ['closed', 'reg_close', 'evidence'],
    'additionalProperties': False,
}


def fetch_page_text(url):
    """페이지의 정제된 텍스트를 반환한다."""
    resp = httpx.get(url, timeout=10, follow_redirects=True,
                     headers={'User-Agent': 'Mozilla/5.0 (compatible; EnduroHubBot/1.0)'})
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')
    for t in soup(['script', 'style', 'noscript', 'svg']):
        t.decompose()
    return soup.get_text(' ', strip=True)[:PAGE_TEXT_LIMIT]


def _call_anthropic(system_prompt, user_message):
    try:
        import anthropic
    except ImportError:
        logger.warning('reg_status: anthropic SDK not installed')
        return None
    try:
        client = anthropic.Anthropic(api_key=settings.LLM_API_KEY).with_options(
            timeout=max(settings.LLM_TIMEOUT, 30)
        )
        resp = client.messages.create(
            model=settings.LLM_MODEL or 'claude-opus-4-8',
            max_tokens=400,
            system=system_prompt,
            messages=[{'role': 'user', 'content': user_message}],
        )
        for block in resp.content:
            if getattr(block, 'type', None) == 'text' and getattr(block, 'text', None):
                return block.text
        return None
    except Exception as exc:  # noqa: BLE001
        logger.warning('reg_status Anthropic call failed: %s', exc)
        return None


def _call_openai(system_prompt, user_message):
    url = f'{settings.LLM_BASE_URL}/chat/completions'
    # gpt-5 계열은 max_tokens/temperature 를 거부한다 — max_completion_tokens 사용,
    # temperature 미전송. reasoning 토큰이 완성 한도를 잠식하므로 여유 있게 잡는다.
    payload = {
        'model': settings.LLM_MODEL or 'gpt-4o-mini',
        'max_completion_tokens': 2048,
        'messages': [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_message},
        ],
    }
    if settings.LLM_JSON_MODE == 'json_schema':
        payload['response_format'] = {
            'type': 'json_schema',
            'json_schema': {'name': 'reg_close_verdict', 'strict': True, 'schema': _VERDICT_SCHEMA},
        }
    elif settings.LLM_JSON_MODE == 'json_object':
        payload['response_format'] = {'type': 'json_object'}
    headers = {
        'Authorization': f'Bearer {settings.LLM_API_KEY}',
        'Content-Type': 'application/json',
    }
    try:
        resp = httpx.post(url, json=payload, headers=headers,
                          timeout=max(settings.LLM_TIMEOUT, 20))
        resp.raise_for_status()
        return resp.json()['choices'][0]['message']['content']
    except (httpx.HTTPError, KeyError, IndexError, ValueError) as exc:
        body = getattr(getattr(exc, 'response', None), 'text', '')
        logger.warning('reg_status LLM call failed: %s %s', exc, body[:200])
        return None


def _parse_verdict(raw):
    """LLM 응답에서 판정 JSON 추출. 코드펜스/잡텍스트 방어. 실패 시 None."""
    try:
        t = re.sub(r'^```(?:json)?|```$', '', raw.strip(), flags=re.IGNORECASE).strip()
        a, b = t.find('{'), t.rfind('}')
        if a == -1 or b == -1:
            return None
        obj = json.loads(t[a:b + 1])
    except (ValueError, TypeError):
        return None
    if not isinstance(obj, dict) or not isinstance(obj.get('closed'), bool):
        return None
    evidence = obj.get('evidence')
    reg_close = obj.get('reg_close')
    return {
        'closed': obj['closed'],
        'evidence': evidence.strip() if isinstance(evidence, str) else '',
        'reg_close': _parse_close_date(reg_close) if isinstance(reg_close, str) else None,
    }


def _parse_close_date(value):
    """YYYY-MM-DD 검증 + 상식 범위(오늘 기준 ±2년) 밖이면 버린다."""
    try:
        d = datetime.strptime(value.strip(), '%Y-%m-%d').date()
    except (ValueError, AttributeError):
        return None
    today = date.today()
    if abs((d - today).days) > 730:
        return None
    return d


_WS = re.compile(r'\s+')


def _evidence_in_page(evidence, page_text):
    """근거 인용문이 페이지에 실제로 존재하는지 검증 — LLM 환각 인용을 기각하는 안전망."""
    ev = _WS.sub(' ', evidence).strip()
    if len(ev) < MIN_EVIDENCE:
        return False
    return ev in _WS.sub(' ', page_text)


def _judge(race, page_text):
    """페이지 텍스트를 근거로 접수마감 여부를 LLM 판정. 실패 시 None."""
    user = (
        f'오늘 날짜: {timezone.localdate().isoformat()}\n'
        f'대회명: {race.title}\n'
        f'대회일: {race.race_date}\n'
        f'DB상 접수 마감일: {race.registration_end or "미상"}\n\n'
        f'--- 페이지 원문 ---\n{page_text}'
    )
    if settings.LLM_PROVIDER == 'anthropic':
        raw = _call_anthropic(_SYSTEM_PROMPT, user)
    else:
        raw = _call_openai(_SYSTEM_PROMPT, user)
    return _parse_verdict(raw) if raw else None


def _target_races():
    """마감 전 + 아직 안 끝난 + 확인할 URL이 있는 대회들."""
    today = timezone.localdate()
    not_finished = Q(race_end_date__gte=today) | Q(race_end_date__isnull=True, race_date__gte=today)
    has_url = (
        (Q(official_url__isnull=False) & ~Q(official_url='')) |
        (Q(source_url__isnull=False) & ~Q(source_url=''))
    )
    return (
        Race.objects.by_status(['upcoming', 'registration_open'])
        .filter(not_finished)
        .filter(has_url)
        .order_by('race_date')
    )


def _apply(race, verdict, dry_run):
    """마감 반영. 잠금/자동갱신 설정을 존중한다. 반영(또는 dry-run 반영 예정)이면 True."""
    locked = set(race.locked_fields or [])
    if not race.auto_update_enabled:
        logger.info('reg_status: auto_update disabled, skipped', extra={'slug': race.slug})
        return False
    if 'status' in locked:
        logger.info('reg_status: status locked, skipped', extra={'slug': race.slug})
        return False

    update_fields = ['status', 'updated_at']
    race.status = 'registration_closed'
    if verdict['reg_close'] and 'registration_end' not in locked:
        race.registration_end = verdict['reg_close']
        update_fields.insert(1, 'registration_end')

    if dry_run:
        logger.info('reg_status: [dry-run] would close', extra={
            'slug': race.slug, 'evidence': verdict['evidence'][:100],
        })
        return True

    race.save(update_fields=update_fields)
    logger.info('reg_status: closed', extra={
        'slug': race.slug, 'evidence': verdict['evidence'][:100],
        'registration_end': str(race.registration_end),
    })
    return True


def update_registration_status(dry_run=False, limit=None):
    """잡 1회 실행. 요약 카운트를 반환한다."""
    summary = {'total': 0, 'checked': 0, 'closed': 0,
               'rejected_evidence': 0, 'skipped_locked': 0, 'errors': 0}
    races = _target_races()
    if limit:
        races = races[:limit]
    for race in races:
        summary['total'] += 1
        url = race.official_url or race.source_url
        try:
            page_text = fetch_page_text(url)
        except httpx.HTTPError as exc:
            logger.info('reg_status: page fetch failed', extra={'slug': race.slug, 'url': url, 'error': str(exc)})
            summary['errors'] += 1
            continue
        if len(page_text) < MIN_PAGE_TEXT:
            logger.info('reg_status: page text too short', extra={'slug': race.slug, 'length': len(page_text)})
            summary['errors'] += 1
            continue

        summary['checked'] += 1
        verdict = _judge(race, page_text)
        if verdict is None:
            summary['errors'] += 1
            continue
        if not verdict['closed']:
            continue
        if not _evidence_in_page(verdict['evidence'], page_text):   # 환각 인용 → 기각
            logger.warning('reg_status: evidence not found in page, rejected', extra={
                'slug': race.slug, 'evidence': verdict['evidence'][:100],
            })
            summary['rejected_evidence'] += 1
            continue
        if _apply(race, verdict, dry_run):
            summary['closed'] += 1
        else:
            summary['skipped_locked'] += 1

    logger.info('reg_status: run completed', extra=summary)
    return summary
