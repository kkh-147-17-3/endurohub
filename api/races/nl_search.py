"""자연어 대회 검색 — LLM으로 질의를 구조화 필터로 파싱.

엔드포인트(`RaceNlSearchView`)에서 호출한다. LLM이 자연어 검색 문장을
종목·지역·상태·거리 카테고리·월 범위·참가비 상한 + 사람이 읽을 요약/칩으로 분해한다.

provider 두 가지를 지원한다 (settings.LLM_PROVIDER):
- 'anthropic': 공식 anthropic SDK로 Claude 호출 (structured outputs로 JSON 보장).
- 'openai'   : OpenAI 호환 HTTP(/chat/completions). 로컬 LM Studio 등.

설계 원칙:
- LLM 출력은 신뢰하지 않는다. 반환값을 알려진 enum과 교집합만 남기는 화이트리스트 검증을 거친다.
- 키 미설정/타임아웃/HTTP 오류/JSON 깨짐 → None 반환. 호출자가 키워드 폴백으로 처리한다.
"""
from __future__ import annotations

import json
import logging
import re
from datetime import date

import httpx
from django.conf import settings

from .constants import DISTANCE_CATEGORIES, REGIONS, SPORT_LABELS

logger = logging.getLogger(__name__)

VALID_SPORTS = set(SPORT_LABELS.keys())
VALID_REGIONS = set(REGIONS)
VALID_STATUSES = {'registration_open', 'registration_closed', 'upcoming'}
# 종목별 허용 거리 카테고리 value 집합
VALID_DISTANCE_CATEGORIES = {
    sport: {c['value'] for c in cats} for sport, cats in DISTANCE_CATEGORIES.items()
}
# 모든 종목의 거리 카테고리 value (종목 미상일 때도 일단 받아두고 뷰에서 종목과 교차 검증)
ALL_DISTANCE_VALUES = {v for vs in VALID_DISTANCE_CATEGORIES.values() for v in vs}

_MONTH_RE = re.compile(r'^\d{4}-\d{2}$')


def _build_system_prompt(today: date) -> str:
    sports_desc = ', '.join(f'{k}({v})' for k, v in SPORT_LABELS.items())
    regions_desc = ', '.join(REGIONS)
    cat_lines = []
    for sport, cats in DISTANCE_CATEGORIES.items():
        labels = ', '.join(f"{c['value']}={c['label']}" for c in cats)
        cat_lines.append(f'  - {sport}: {labels}')
    cats_desc = '\n'.join(cat_lines)

    return f"""당신은 한국 지구력 스포츠 대회 검색 파서입니다. 오늘 날짜는 {today.isoformat()} 입니다.
사용자의 자연어 검색 문장을 분석해 아래 JSON 객체로만 응답하세요. JSON 외 텍스트는 절대 출력하지 마세요.

출력 형식:
{{"summary": "검색 조건을 설명하는 건조하고 사실적인 한 문장 (~합니다/~입니다체, 대회 번호·개수·이모지·과장 금지)",
  "chips": ["해석한 조건 2~4개, 예: 지역 서울", "거리 10km", "접수 중"],
  "sports": ["{', '.join(VALID_SPORTS)} 중 해당하는 값들, 없으면 빈 배열"],
  "regions": ["지역 이름들, 없으면 빈 배열"],
  "statuses": ["registration_open|registration_closed|upcoming 중 해당값, 없으면 빈 배열"],
  "distance_categories": ["거리 카테고리 value들, 없으면 빈 배열"],
  "month_from": "YYYY-MM 또는 빈 문자열",
  "month_to": "YYYY-MM 또는 빈 문자열",
  "fee_max": 참가비 상한 정수(원) 또는 null,
  "q": "종목·지역·상태·거리·날짜·참가비로 해석되지 않은 나머지 키워드, 없으면 빈 문자열"}}

종목 값: {sports_desc}
지역 값: {regions_desc}
종목별 거리 카테고리 value:
{cats_desc}

해석 규칙:
- 종목: 러닝/마라톤→running, 트레일/트레일런→trail_running, 사이클/자전거→cycling, 수영→swimming, 철인3종→triathlon
- "접수 가능한/마감 안 된/신청 가능/접수 중"→statuses:["registration_open"], "마감"→registration_closed, "예정/다가오는"→upcoming
- "서울 근처/수도권"→regions:["서울","경기","인천"]. 여러 지역이면 모두 배열에 넣습니다.
- 거리: 10K/10km→running short, 하프→half, 풀/풀코스→full, 울트라/100K→ultra 처럼 종목별 카테고리 value로 매핑.
  종목을 특정할 수 없으면 distance_categories는 비웁니다.
- 날짜: "이번 달"→오늘({today.isoformat()}) 기준 month_from=month_to=이번 달, "다음 달"→다음 달,
  "올해"→month_from=올해 1월·month_to=올해 12월, "내년"→내년 1~12월, "6월"→가장 가까운 미래의 해당 월.
- 참가비: "5만원 이하"→fee_max:50000, "3만원 미만"→fee_max:30000 (원 단위 정수).
- summary는 해석한 조건만 사실 그대로 서술합니다(구체적 결과 개수는 모르므로 언급 금지)."""


def _json_schema_format() -> dict:
    """OpenAI/LM Studio structured-output 스키마. enum 으로 값까지 제약한다."""
    str_array = {'type': 'array', 'items': {'type': 'string'}}
    enum_array = lambda values: {'type': 'array', 'items': {'type': 'string', 'enum': sorted(values)}}
    schema = {
        'type': 'object',
        'properties': {
            'summary': {'type': 'string'},
            'chips': str_array,
            'sports': enum_array(VALID_SPORTS),
            'regions': enum_array(VALID_REGIONS),
            'statuses': enum_array(VALID_STATUSES),
            'distance_categories': enum_array(ALL_DISTANCE_VALUES),
            'month_from': {'type': 'string'},
            'month_to': {'type': 'string'},
            'fee_max': {'type': ['integer', 'null']},
            'q': {'type': 'string'},
        },
        'required': [
            'summary', 'chips', 'sports', 'regions', 'statuses',
            'distance_categories', 'month_from', 'month_to', 'fee_max', 'q',
        ],
        'additionalProperties': False,
    }
    return {
        'type': 'json_schema',
        'json_schema': {'name': 'race_query', 'strict': True, 'schema': schema},
    }


def _anthropic_schema() -> dict:
    """Anthropic structured-output(output_config.format) 스키마. enum 으로 값까지 제약한다.

    Anthropic 지원 부분집합만 사용: 기본 타입·enum·anyOf, 모든 object는 additionalProperties=false +
    전 필드 required (숫자/문자열 길이 제약은 미사용).
    """
    str_array = {'type': 'array', 'items': {'type': 'string'}}

    def enum_array(values):
        return {'type': 'array', 'items': {'type': 'string', 'enum': sorted(values)}}

    schema = {
        'type': 'object',
        'properties': {
            'summary': {'type': 'string'},
            'chips': str_array,
            'sports': enum_array(VALID_SPORTS),
            'regions': enum_array(VALID_REGIONS),
            'statuses': enum_array(VALID_STATUSES),
            'distance_categories': enum_array(ALL_DISTANCE_VALUES),
            'month_from': {'type': 'string'},
            'month_to': {'type': 'string'},
            'fee_max': {'anyOf': [{'type': 'integer'}, {'type': 'null'}]},
            'q': {'type': 'string'},
        },
        'required': [
            'summary', 'chips', 'sports', 'regions', 'statuses',
            'distance_categories', 'month_from', 'month_to', 'fee_max', 'q',
        ],
        'additionalProperties': False,
    }
    return {'type': 'json_schema', 'schema': schema}


def _call_anthropic(system_prompt: str, user_message: str) -> str | None:
    """공식 anthropic SDK로 Claude 호출. 응답 text 반환, 실패 시 None.

    1차: structured outputs(output_config)로 JSON 보장. 어떤 이유로든 실패하면
    2차: output_config 없이 프롬프트-온리로 재시도(Claude는 JSON-only 지시를 잘 따른다).
    """
    try:
        import anthropic
    except ImportError:
        logger.warning('NL search: anthropic SDK not installed')
        return None
    model = settings.LLM_MODEL or 'claude-opus-4-8'
    try:
        client = anthropic.Anthropic(api_key=settings.LLM_API_KEY).with_options(
            timeout=max(settings.LLM_TIMEOUT, 30)
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning('NL search Anthropic client init failed: %s', exc)
        return None

    base = {
        'model': model,
        'max_tokens': 600,
        'system': system_prompt,
        'messages': [{'role': 'user', 'content': user_message}],
    }
    for extra in ({'output_config': {'format': _anthropic_schema()}}, {}):
        try:
            resp = client.messages.create(**base, **extra)
            for block in resp.content:
                if getattr(block, 'type', None) == 'text' and getattr(block, 'text', None):
                    return block.text
            return None
        except Exception as exc:  # noqa: BLE001 — structured 실패 시 프롬프트-온리로 폴백
            logger.warning('NL search Anthropic call failed (structured=%s): %s', bool(extra), exc)
            continue
    return None


def _call_llm(system_prompt: str, user_message: str) -> str | None:
    """OpenAI 호환 /chat/completions 호출. 응답 본문 text 반환, 실패 시 None."""
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
    # JSON 강제 모드 (provider별 지원 상이):
    #  - 'json_schema': 제약 디코딩으로 스키마 준수 JSON 보장 (LM Studio·최신 OpenAI). 소형 로컬 모델 권장.
    #  - 'json_object': OpenAI 등. LM Studio는 거부.
    #  - '' (기본): 미전송. 프롬프트의 JSON-only 지시 + 견고한 파서에 의존.
    if settings.LLM_JSON_MODE == 'json_schema':
        payload['response_format'] = _json_schema_format()
    elif settings.LLM_JSON_MODE == 'json_object':
        payload['response_format'] = {'type': 'json_object'}
    headers = {
        'Authorization': f'Bearer {settings.LLM_API_KEY}',
        'Content-Type': 'application/json',
    }
    try:
        resp = httpx.post(url, json=payload, headers=headers, timeout=settings.LLM_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        return data['choices'][0]['message']['content']
    except (httpx.HTTPError, KeyError, IndexError, ValueError) as exc:
        logger.warning('NL search LLM call failed: %s', exc)
        return None


def _parse_json(raw: str) -> dict | None:
    """LLM 응답에서 JSON 객체 추출. 코드펜스/잡텍스트 방어."""
    try:
        t = raw.strip()
        t = re.sub(r'^```(?:json)?', '', t, flags=re.IGNORECASE).strip()
        t = re.sub(r'```$', '', t).strip()
        a, b = t.find('{'), t.rfind('}')
        if a == -1 or b == -1:
            return None
        obj = json.loads(t[a:b + 1])
        return obj if isinstance(obj, dict) else None
    except (ValueError, TypeError):
        return None


def _as_str_list(value) -> list[str]:
    if isinstance(value, list):
        return [str(x) for x in value if isinstance(x, (str, int, float))]
    if isinstance(value, str) and value:
        return [value]
    return []


def _validate(obj: dict) -> dict:
    """LLM 출력을 알려진 enum과 교집합만 남기는 화이트리스트 검증."""
    sports = [s for s in _as_str_list(obj.get('sports')) if s in VALID_SPORTS]
    regions = [r for r in _as_str_list(obj.get('regions')) if r in VALID_REGIONS]
    statuses = [s for s in _as_str_list(obj.get('statuses')) if s in VALID_STATUSES]
    # 거리 카테고리는 전체 value 집합으로 1차 필터. 종목 교차검증은 뷰에서.
    distance_categories = [
        c for c in _as_str_list(obj.get('distance_categories')) if c in ALL_DISTANCE_VALUES
    ]

    month_from = obj.get('month_from') or ''
    month_to = obj.get('month_to') or ''
    month_from = month_from if isinstance(month_from, str) and _MONTH_RE.match(month_from) else ''
    month_to = month_to if isinstance(month_to, str) and _MONTH_RE.match(month_to) else ''

    fee_max = obj.get('fee_max')
    try:
        fee_max = int(fee_max) if fee_max is not None else None
        if fee_max is not None and fee_max <= 0:
            fee_max = None
    except (ValueError, TypeError):
        fee_max = None

    q = obj.get('q')
    q = q.strip() if isinstance(q, str) else ''

    chips = _as_str_list(obj.get('chips'))[:5]
    summary = obj.get('summary')
    summary = summary.strip() if isinstance(summary, str) else ''

    return {
        'sports': sports,
        'regions': regions,
        'statuses': statuses,
        'distance_categories': distance_categories,
        'month_from': month_from,
        'month_to': month_to,
        'fee_max': fee_max,
        'q': q,
        'summary': summary,
        'chips': chips,
    }


def interpret_query(raw_query: str, today: date) -> dict | None:
    """자연어 질의를 구조화 필터로 파싱. 실패 시 None(호출자가 키워드 폴백)."""
    if not settings.LLM_API_KEY:
        return None
    raw_query = (raw_query or '').strip()
    if not raw_query:
        return None

    system_prompt = _build_system_prompt(today)
    if settings.LLM_PROVIDER == 'anthropic':
        raw = _call_anthropic(system_prompt, raw_query)
    else:
        raw = _call_llm(system_prompt, raw_query)
    if raw is None:
        return None
    obj = _parse_json(raw)
    if obj is None:
        logger.warning('NL search: failed to parse LLM JSON for query=%r', raw_query)
        return None
    return _validate(obj)
