"""LLM 레이어 — LangChain ChatOpenAI (tool 루프 / structured output / vision).

import 시점에 키를 요구하지 않도록 ChatOpenAI 는 요청마다 lazy 생성한다.
"""
import base64
import json
import logging
from typing import TypeVar

from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage, BaseMessage
from langchain_core.tools import BaseTool

from . import config

logger = logging.getLogger("marathon_crawler")


def _get_llm(effort: str, max_tokens: int) -> ChatOpenAI:
    return ChatOpenAI(model=config.MODEL, reasoning_effort=effort, max_tokens=max_tokens, timeout=60)


def _text_of(msg: BaseMessage) -> str:
    c = msg.content
    if isinstance(c, str):
        return c
    if isinstance(c, list):                 # content block 리스트일 수 있음
        return "".join(b.get("text", "") if isinstance(b, dict) else str(b) for b in c)
    return str(c)


def _log_usage(label: str, msg: BaseMessage) -> None:
    um = getattr(msg, "usage_metadata", None)
    if not um:
        return
    reasoning = (um.get("output_token_details") or {}).get("reasoning")
    logger.info("[tokens:%s] in=%s out=%s total=%s%s", label,
                um.get("input_tokens"), um.get("output_tokens"), um.get("total_tokens"),
                f" reasoning={reasoning}" if reasoning else "")


def run_agent(system_prmpt: str, user_prmpt: str, tools: list[BaseTool], tool_impls: dict[str, BaseTool], *,
              terminal_tool: str | None = None, effort: str = config.EFFORT_FAST,
              max_steps: int = 8) -> dict:
    """모델은 도구 호출만, 실행은 코드. 정지조건 2개(모델 최종답 / max_steps)."""
    llm = _get_llm(effort, 4096).bind_tools(tools)
    messages: list[BaseMessage] = [SystemMessage(content=system_prmpt), HumanMessage(content=user_prmpt)]
    for step in range(max_steps):                      # 정지조건②: 코드 안전장치
        logger.info("agent step %d/%d", step + 1, max_steps)
        ai_msg = llm.invoke(messages)
        _log_usage(f"agent#{step + 1}", ai_msg)
        messages.append(ai_msg)                            # assistant 메시지(도구호출 포함) 회신

        if not ai_msg.tool_calls:                          # 정지조건①: 모델이 최종 답
            logger.info("agent done (%d steps, no more tool calls)", step + 1)
            return {"text": _text_of(ai_msg), "messages": messages}

        for tool_call in ai_msg.tool_calls:
            name, args, tid = tool_call["name"], tool_call["args"], tool_call["id"]
            logger.info("  tool call: %s(%s)", name, json.dumps(args, ensure_ascii=False)[:120])
            if name == terminal_tool:                  # 구조화된 최종 결과 제출
                logger.info("  → terminal tool '%s' → 탐색 종료", terminal_tool)
                return {"result": args, "messages": messages}
            impl = tool_impls.get(name)                # 모델이 없는 도구를 부르면 크래시 대신 에러 회신
            if impl is None:
                logger.warning("  알 수 없는 도구 호출: %s", name)
                out = f"error: unknown tool {name}"
            else:
                out = impl.invoke(args)                # ← @tool 실행 (args dict)
            messages.append(ToolMessage(content=str(out), tool_call_id=tid))

    raise RuntimeError(f"max_steps({max_steps}) 초과 — 탐색 실패로 처리")


T = TypeVar("T", bound=BaseModel)

def structured_call(system: str, user: str, model_cls: type[T], *, effort: str = config.EFFORT_FAST) -> T:
    """단발 구조화 출력 (LangChain with_structured_output)."""
    llm = _get_llm(effort, 2048).with_structured_output(model_cls)
    parsed = llm.invoke([SystemMessage(content=system), HumanMessage(content=user)])
    if parsed is None:
        raise RuntimeError("structured output 실패 (parsed=None)")
    return parsed


def vision_extract(img_bytes: bytes, field: str) -> str | None:
    """이미지 바이트를 data URL로 실어 단발 멀티모달 호출."""
    b64 = base64.standard_b64encode(img_bytes).decode()
    msg = HumanMessage(content=[
        {"type": "text", "text": f"이 이미지에서 '{field}' 값만 한 줄로 출력. 없으면 정확히 null 이라고만 출력."},
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
    ])
    resp = _get_llm(config.EFFORT_FAST, 1024).invoke([msg])
    _log_usage(f"vision:{field}", resp)
    out = _text_of(resp).strip()
    return None if _is_null_answer(out) else out


# vision 모델이 지시를 무시하고 장황하게 답할 때(예: "...null 입니다", "확인할 수 없습니다")
# 값으로 오인하지 않도록 걸러낸다. 정확히 'null'만 통과시키지 않고 부정/거부 표현도 null 취급.
_REFUSAL_MARKERS: tuple[str, ...] = (
    "null", "확인할 수 없", "확인이 어렵", "찾을 수 없", "알 수 없", "식별할 수 없",
    "not found", "cannot", "can't", "unable", "n/a", "없음",
)

def _is_null_answer(out: str) -> bool:
    if not out:
        return True
    low = out.lower()
    return any(m in low for m in _REFUSAL_MARKERS)
