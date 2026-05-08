"""Async proxy to the containerized Hermes HTTP API.

No Docker dependency — communicates via Hermes' own API and admin server.
Compatible with both Docker Compose and K8s deployments.
"""
import copy
import json
import os
from typing import AsyncGenerator, Optional

import httpx

HERMES_INTERNAL_URL = os.getenv("HERMES_URL", "http://hermes:8642")
HERMES_ADMIN_URL = os.getenv("HERMES_ADMIN_URL", "http://hermes:8640")
HERMES_API_KEY = os.getenv("HERMES_API_KEY", "velobid-internal")


def _get_env_int(name: str, default: int, minimum: int = 1) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return max(minimum, value)


def _get_env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    normalized = raw.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return default


HERMES_CHAT_HISTORY_LIMIT = _get_env_int("HERMES_CHAT_HISTORY_LIMIT", 16)
HERMES_MAX_MESSAGE_CHARS = _get_env_int("HERMES_MAX_MESSAGE_CHARS", 4000)
HERMES_CONCISE_SYSTEM_PROMPT = _get_env_bool(
    "HERMES_CONCISE_SYSTEM_PROMPT", True
)
_CONCISE_PROMPT_MARKER = "[velobid-cost-note]"
_CONCISE_SYSTEM_PROMPT = (
    f"{_CONCISE_PROMPT_MARKER} Respond concisely and cost-effectively. "
    "Keep answers brief, avoid repetition, and ask only essential follow-ups."
)


def _truncate_message_content(content: str, max_chars: int) -> str:
    if len(content) <= max_chars:
        return content
    clipped_count = len(content) - max_chars
    clip_marker = f"\n...[clipped {clipped_count} chars for cost control]"
    head_len = max_chars - len(clip_marker)
    if head_len <= 0:
        return content[:max_chars]
    return f"{content[:head_len]}{clip_marker}"


def _sanitize_outgoing_message(message: dict) -> Optional[dict]:
    if not isinstance(message, dict):
        return None

    role = message.get("role")
    if not isinstance(role, str):
        return None

    sanitized = {"role": role}
    content = message.get("content")
    if isinstance(content, str):
        sanitized["content"] = _truncate_message_content(
            content, HERMES_MAX_MESSAGE_CHARS
        )
    elif content is not None:
        sanitized["content"] = copy.deepcopy(content)

    # Keep known message fields used by tool/function flows.
    for key in ("name", "tool_call_id", "refusal"):
        value = message.get(key)
        if isinstance(value, str):
            sanitized[key] = value
    for key in ("tool_calls", "function_call"):
        value = message.get(key)
        if isinstance(value, (list, dict)):
            sanitized[key] = copy.deepcopy(value)

    return sanitized


def _shape_outgoing_messages(messages: list) -> list:
    sanitized = []
    for message in messages:
        cleaned = _sanitize_outgoing_message(message)
        if cleaned is not None:
            sanitized.append(cleaned)

    if len(sanitized) > HERMES_CHAT_HISTORY_LIMIT:
        sanitized = sanitized[-HERMES_CHAT_HISTORY_LIMIT:]
    return sanitized


def _ensure_concise_system_prompt(messages: list) -> list:
    if not HERMES_CONCISE_SYSTEM_PROMPT:
        return messages

    for message in messages:
        if (
            message.get("role") == "system"
            and _CONCISE_PROMPT_MARKER in message.get("content", "")
        ):
            return messages

    insert_at = 0
    while insert_at < len(messages) and messages[insert_at].get("role") == "system":
        insert_at += 1

    concise_message = {"role": "system", "content": _CONCISE_SYSTEM_PROMPT}
    return messages[:insert_at] + [concise_message] + messages[insert_at:]


async def _fetch_soul_via_http(bidder_id: str) -> Optional[str]:
    """Read SOUL.md from the Hermes admin server via HTTP (no Docker needed)."""
    profile_name = f"bidder-{bidder_id}"
    url = f"{HERMES_ADMIN_URL}/admin/profiles/{profile_name}/soul"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("content")
    except Exception:
        pass
    return None


async def proxy_chat_to_hermes(
    messages: list,
    bidder_id: Optional[str] = None,
    project_id: Optional[str] = None,
    stream: bool = True,
) -> AsyncGenerator[str, None]:
    """Forward a chat conversation to the Hermes API and yield SSE chunks.

    If bidder_id is provided, injects the bidder's SOUL.md as a system prompt
    so Hermes has the company context automatically.
    """
    messages = _shape_outgoing_messages(messages)
    profile_name = f"bidder-{bidder_id}" if bidder_id else "default"

    # Inject bidder context as a system message if available
    if bidder_id:
        soul_content = await _fetch_soul_via_http(bidder_id)
        if soul_content:
            has_context = any(
                m.get("role") == "system" and "You are the AI estimating assistant"
                in m.get("content", "")
                for m in messages
            )
            if not has_context:
                messages = [
                    {"role": "system", "content": soul_content}
                ] + messages
    messages = _ensure_concise_system_prompt(messages)

    payload = {
        "model": profile_name,
        "messages": messages,
        "stream": stream,
    }
    headers = {"Authorization": f"Bearer {HERMES_API_KEY}"}
    url = f"{HERMES_INTERNAL_URL}/v1/chat/completions"

    async with httpx.AsyncClient(timeout=300) as client:
        async with client.stream("POST", url, json=payload, headers=headers) as resp:
            async for line in resp.aiter_lines():
                if not line.startswith("data: "):
                    continue
                raw = line[len("data: "):].strip()
                if raw == "[DONE]":
                    yield "data: [DONE]\n\n"
                    return
                try:
                    chunk = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                choices = chunk.get("choices", [])
                if not choices:
                    continue
                delta = choices[0].get("delta", {})
                finish = choices[0].get("finish_reason")

                # Reasoning / thinking content (e.g. DeepSeek R1, Claude)
                reasoning = delta.get("reasoning_content")
                if reasoning:
                    yield f"data: {json.dumps({'type': 'thought', 'delta': reasoning})}\n\n"

                # Regular content delta
                content = delta.get("content")
                if content:
                    yield f"data: {json.dumps({'type': 'content', 'delta': content})}\n\n"

                # Tool calls from the assistant
                tool_calls = delta.get("tool_calls")
                if tool_calls:
                    for tc in tool_calls:
                        fn = tc.get("function", {})
                        yield f"data: {json.dumps({'type': 'tool_call', 'name': fn.get('name', 'unknown')})}\n\n"

                if finish:
                    yield "data: [DONE]\n\n"
                    return
