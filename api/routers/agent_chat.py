import asyncio
import json
import os
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional

import openai
from openai import (
    AuthenticationError,
    RateLimitError,
    APITimeoutError,
    APIStatusError,
    APIConnectionError,
)
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from api.schemas.bids import GenerateBidRequest
from api.services.agent import TOOLS, client, handle_tool_call
from api.services.agent_access import AgentAccessError, enforce_agent_access
from api.services.auth_guard import AuthContext, get_auth_context
from api.services.agent_model_policy import resolve_agent_model_policy
from api.services.bids import OUTPUT_DIR, preview_bid, read_json, resolve_project_path

router = APIRouter(prefix="/api/v1/agent", tags=["agent"])


class ChatMessage(BaseModel):
    role: str
    content: str
    reasoning_content: Optional[str] = None


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    project_id: Optional[str] = None
    trade: Optional[str] = "hvac"


def _build_rich_context(project_id: str, trade: str, bidder_id: str) -> str:
    """Build a comprehensive project context string for LLM injection."""
    parts = []
    project_authorized = False

    try:
        path = resolve_project_path(project_id, bidder_id=bidder_id)
        project_authorized = True
        config = read_json(path)
        parts.append(f"**Project**: {config.get('name', project_id)}")
        parts.append(f"**Location**: {config.get('city', 'N/A')}, {config.get('state', 'N/A')}")
        parts.append(f"**Area**: {config.get('total_area_sf', 'N/A')} SF")
        parts.append(f"**Type**: {config.get('construction_type', 'N/A')} / {config.get('occupancy_group', 'N/A')}")
        parts.append(f"**Trade**: {trade}")
    except Exception:
        parts.append(f"**Project ID**: {project_id}")
        parts.append(f"**Trade**: {trade}")

    try:
        bid_request = GenerateBidRequest(project_id=project_id, trade=trade)
        preview = preview_bid(bid_request, bidder_id=bidder_id)
        parts.append("")
        parts.append("**Current Bid Snapshot:**")
        parts.append(f"  - Bidder: {preview.bidder_name}")
        parts.append(f"  - Region: {preview.region}")
        parts.append(f"  - Status: {preview.status}")
        parts.append(f"  - Total Material: ${preview.totals.total_material:,.2f}")
        parts.append(f"  - Total Labor: ${preview.totals.total_labor:,.2f}")
        parts.append(f"  - Direct Cost: ${preview.totals.total_direct_cost:,.2f}")
        parts.append(f"  - Contingency: ${preview.totals.contingency:,.2f} ({preview.totals.contingency_pct}%)")
        parts.append(f"  - Overhead & Profit: ${preview.totals.overhead_profit:,.2f} ({preview.totals.overhead_profit_pct}%)")
        parts.append(f"  - **Total Bid: ${preview.totals.total_bid_amount:,.2f}**")
        parts.append(f"  - Labor Hours: {preview.totals.total_labor_hours} hrs")
        parts.append("")
        parts.append("**Line Items:**")
        for item in preview.line_items:
            parts.append(f"  - [{item.cost_code}] {item.description}: {item.quantity} {item.unit} @ ${item.unit_cost_material:.2f}/mat + ${item.unit_cost_labor:.2f}/lab = ${item.total_phase:,.2f}")
        parts.append("")
        if preview.exclusions:
            parts.append("**Exclusions:**")
            for ex in preview.exclusions:
                parts.append(f"  - {ex}")
    except Exception:
        parts.append("\n(Bid preview unavailable)")

    if project_authorized:
        try:
            versions_dir = OUTPUT_DIR / project_id / trade / "versions"
            index_path = versions_dir / "index.json"
            if index_path.exists():
                with index_path.open(encoding="utf-8-sig") as f:
                    index = json.load(f)
                parts.append("")
                parts.append("**Version History:**")
                for entry in index[-5:]:
                    ts = entry.get("timestamp", "")[:19]
                    parts.append(f"  - {entry['version_id']} [{ts}] {entry.get('commit_message', '')}")
        except Exception:
            pass

    return "\n".join(parts)


def _error_event(code: str, message: str) -> str:
    """Build an SSE error event with a user-actionable message and no secret details."""
    return f"data: {json.dumps({'type': 'error', 'message': message, 'code': code})}\n\n"


def _mask_api_key(raw: str | None) -> str | None:
    """Mask all but the last 4 characters of an API key for safe logging."""
    if not raw or len(raw) < 8:
        return "***" if raw else None
    return raw[:4] + "..." + raw[-4:]


async def agent_stream_generator(
    messages: List[Dict[str, Any]], project_id: Optional[str], trade: str, bidder_id: str
):
    """Generator for streaming agent reasoning and tool calls via SSE."""

    if project_id and not any("PROJECT CONTEXT" in m.get("content", "") for m in messages):
        context = _build_rich_context(project_id, trade, bidder_id=bidder_id)
        system_prompt = f"""You are an AI Estimator for VeloBid, a construction bid generation platform.

PROJECT CONTEXT:
{context}

You have tools to research blueprints, update configs, and generate PDFs. Use them when appropriate.
"""
        messages.insert(0, {"role": "system", "content": system_prompt})

    max_iterations = 5

    # Pre-flight: check required upstream configuration early
    # so the user sees a clear error instead of an opaque OpenAI SDK exception.
    api_key = os.getenv("OPENCODE_API_KEY")
    base_url = os.getenv("OPENCODE_BASE_URL")
    if not api_key or not api_key.strip():
        print(f"CONFIG ERROR: OPENCODE_API_KEY is not set or is empty (masked={_mask_api_key(api_key)!r})")
        yield _error_event("config_error", "AI chat is unavailable because the upstream AI service credentials are not configured. Please contact your system administrator.")
        yield "data: [DONE]\n\n"
        return
    if not base_url or not base_url.strip():
        print(f"CONFIG ERROR: OPENCODE_BASE_URL is not set or is empty")
        yield _error_event("config_error", "AI chat is unavailable because the upstream AI service endpoint is not configured. Please contact your system administrator.")
        yield "data: [DONE]\n\n"
        return

    try:
        for i in range(max_iterations):
            policy = resolve_agent_model_policy(messages, project_id, i)

            # Sanitize messages before sending to the API:
            # Strip reasoning_content (DeepSeek only valid in streaming output, rejected as input)
            sanitized_messages = []
            for m in messages:
                sanitized = {"role": m["role"], "content": m.get("content", "")}
                if m.get("tool_calls"):
                    sanitized["tool_calls"] = m["tool_calls"]
                if m.get("tool_call_id"):
                    sanitized["tool_call_id"] = m["tool_call_id"]
                if m.get("name"):
                    sanitized["name"] = m["name"]
                # reasoning_content intentionally omitted
                sanitized_messages.append(sanitized)

            request_kwargs: dict[str, Any] = {
                "model": policy.model,
                "messages": sanitized_messages,
                "stream": True,
                "max_tokens": policy.max_tokens,
            }
            if policy.allow_tools:
                request_kwargs["tools"] = TOOLS
                request_kwargs["tool_choice"] = "auto"

            response = client.chat.completions.create(**request_kwargs)

            full_content = ""
            full_reasoning = ""
            tool_calls = []

            for chunk in response:
                delta = chunk.choices[0].delta

                reasoning = getattr(delta, "reasoning_content", None)
                if reasoning:
                    full_reasoning += reasoning
                    yield f"data: {json.dumps({'type': 'thought', 'delta': reasoning})}\n\n"

                if delta.content:
                    full_content += delta.content
                    yield f"data: {json.dumps({'type': 'content', 'delta': delta.content})}\n\n"

                if delta.tool_calls:
                    for tc in delta.tool_calls:
                        if len(tool_calls) <= tc.index:
                            tool_calls.append({
                                "id": tc.id,
                                "type": "function",
                                "function": {"name": "", "arguments": ""},
                            })
                        if tc.id:
                            tool_calls[tc.index]["id"] = tc.id
                        if tc.function.name:
                            tool_calls[tc.index]["function"]["name"] += tc.function.name
                        if tc.function.arguments:
                            tool_calls[tc.index]["function"]["arguments"] += tc.function.arguments

            if tool_calls:
                formatted_tool_calls = []
                for tc in tool_calls:
                    formatted_tool_calls.append({
                        "id": tc["id"],
                        "type": "function",
                        "function": {
                            "name": tc["function"]["name"],
                            "arguments": tc["function"]["arguments"],
                        },
                    })

                # Do NOT include reasoning_content in the stored message
                # as it will be re-sent to the API on the next iteration
                assistant_msg = {
                    "role": "assistant",
                    "content": full_content or None,
                    "tool_calls": formatted_tool_calls,
                }
                messages.append(assistant_msg)

                for tc in formatted_tool_calls:
                    tool_name = tc["function"]["name"]
                    yield f"data: {json.dumps({'type': 'tool_call', 'name': tool_name})}\n\n"
                    await asyncio.sleep(0.1)

                    class ToolCallMock:
                        def __init__(self, id, name, args):
                            self.id = id
                            self.function = type("obj", (object,), {"name": name, "arguments": args})

                    mock_tc = ToolCallMock(tc["id"], tool_name, tc["function"]["arguments"])
                    result = handle_tool_call(mock_tc)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "name": tool_name,
                        "content": result,
                    })
                    yield f"data: {json.dumps({'type': 'tool_result', 'name': tool_name, 'result': result})}\n\n"

                continue
            else:
                # No reasoning_content on final message — it's only for streaming deltas
                final_msg = {"role": "assistant", "content": full_content}
                messages.append(final_msg)
                break

        yield "data: [DONE]\n\n"

    except AuthenticationError as e:
        masked = _mask_api_key(os.getenv("OPENCODE_API_KEY"))
        print(f"AUTH ERROR: API key rejected (masked={masked!r})")
        traceback.print_exc()
        yield _error_event("auth_error", "AI chat is unavailable because the API key was rejected. Please contact your system administrator.")
        yield "data: [DONE]\n\n"

    except RateLimitError:
        print("RATE LIMIT: upstream AI service rate-limited the request")
        traceback.print_exc()
        yield _error_event("rate_limit", "AI chat is temporarily unavailable due to rate limiting. Please wait a moment and try again.")
        yield "data: [DONE]\n\n"

    except APITimeoutError:
        print("TIMEOUT: upstream AI service timed out")
        traceback.print_exc()
        yield _error_event("timeout", "AI chat timed out. Please try again.")
        yield "data: [DONE]\n\n"

    except APIConnectionError as e:
        print(f"CONNECTION ERROR: could not reach upstream AI service: {e}")
        traceback.print_exc()
        yield _error_event("connection_error", "AI chat is unavailable because the upstream AI service could not be reached. Please try again later.")
        yield "data: [DONE]\n\n"

    except APIStatusError as e:
        # Catch other HTTP-level API errors (e.g. 400, 429, 500)
        status = e.status_code
        body = str(e.response.text) if hasattr(e, "response") and hasattr(e.response, "text") else ""
        masked = _mask_api_key(os.getenv("OPENCODE_API_KEY"))
        print(f"API ERROR (HTTP {status}): masked_key={masked!r} body={body!r}")
        traceback.print_exc()
        yield _error_event("api_error", f"AI chat returned an unexpected error (HTTP {status}). Please try again or contact support.")
        yield "data: [DONE]\n\n"

    except Exception as e:
        # Catch-all: redact anything that looks like a secret before exposing to user
        error_text = str(e)
        # Patterns that might leak secrets, file paths, or internal config
        redact_patterns = [
            os.getenv("OPENCODE_API_KEY") or "",
            os.getenv("OPENAI_API_KEY") or "",
            os.getenv("ANTHROPIC_API_KEY") or "",
            "/home/",
            "/root/",
            "/var/",
            "/etc/",
            "/tmp/",
        ]
        for pattern in redact_patterns:
            if pattern and pattern in error_text:
                error_text = error_text.replace(pattern, "[REDACTED]")

        # Log the full error (with redacted secrets) to stdout for devs
        masked = _mask_api_key(os.getenv("OPENCODE_API_KEY"))
        print(f"UNEXPECTED ERROR in agent_stream_generator: masked_key={masked!r} error={error_text}")
        traceback.print_exc()

        yield _error_event("internal_error", "AI chat encountered an unexpected error. Please try again or contact support.")
        yield "data: [DONE]\n\n"


@router.post("/chat")
async def agent_chat_stream(
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
):
    """Stream AI agent chat using SSE, with rich project context injection."""
    try:
        enforce_agent_access(auth.bidder_id, auth.user_id)
    except AgentAccessError as error:
        raise HTTPException(
            status_code=error.status_code,
            detail=error.detail,
            headers=error.headers,
        ) from None

    body = await request.json()

    project_id = body.get("project_id")
    trade = body.get("trade", "hvac")
    incoming_messages = body.get("messages", [])

    messages = []
    for m in incoming_messages:
        msg = {"role": m.get("role"), "content": m.get("content")}
        if m.get("reasoning_content"):
            msg["reasoning_content"] = m.get("reasoning_content")
        if m.get("tool_calls"):
            msg["tool_calls"] = m.get("tool_calls")
        messages.append(msg)

    return StreamingResponse(
        agent_stream_generator(messages, project_id, trade, auth.bidder_id),
        media_type="text/event-stream",
    )
