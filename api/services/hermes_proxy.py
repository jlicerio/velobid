"""Async proxy to the containerized Hermes HTTP API.

No Docker dependency — communicates via Hermes' own API and admin server.
Compatible with both Docker Compose and K8s deployments.
"""
import json
import os
from typing import AsyncGenerator, Optional

import httpx

HERMES_INTERNAL_URL = os.getenv("HERMES_URL", "http://hermes:8642")
HERMES_ADMIN_URL = os.getenv("HERMES_ADMIN_URL", "http://hermes:8640")
HERMES_API_KEY = os.getenv("HERMES_API_KEY", "velobid-internal")


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
