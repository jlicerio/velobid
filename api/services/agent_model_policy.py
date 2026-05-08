"""Cost-aware model routing policy for agent chat requests."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AgentModelPolicy:
    """Resolved model/tokens/tool settings for a single LLM call."""

    model: str
    max_tokens: int
    allow_tools: bool
    tier: str


_HEAVY_KEYWORDS = {
    "generate",
    "pdf",
    "blueprint",
    "takeoff",
    "line item",
    "cost code",
    "version",
    "scope",
    "update config",
    "pricing",
    "estimate",
    "validate",
    "schedule",
    "trade",
}


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name, "true" if default else "false").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int, minimum: int = 64, maximum: int = 16000) -> int:
    raw = os.getenv(name, str(default)).strip()
    try:
        value = int(raw)
    except ValueError:
        value = default
    return max(minimum, min(maximum, value))


def _last_user_text(messages: list[dict[str, Any]]) -> str:
    for message in reversed(messages):
        if message.get("role") == "user":
            return str(message.get("content", ""))
    return ""


def _complexity_score(messages: list[dict[str, Any]], project_id: str | None, iteration: int) -> int:
    score = 0
    user_text = _last_user_text(messages).lower()

    if project_id:
        score += 2
    if len(user_text) > 700:
        score += 2
    if len(messages) > 10:
        score += 1
    if iteration > 0:
        score += 1
    if any(keyword in user_text for keyword in _HEAVY_KEYWORDS):
        score += 2

    return score


def resolve_agent_model_policy(
    messages: list[dict[str, Any]],
    project_id: str | None,
    iteration: int,
) -> AgentModelPolicy:
    """Resolve model policy for one streaming iteration."""
    deep_model = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-pro").strip()
    fast_model = os.getenv("AGENT_MODEL_FAST", "deepseek-v4-flash").strip() or deep_model

    force_deep = _env_bool("AGENT_MODEL_FORCE_DEEP", False)
    routing_enabled = _env_bool("AGENT_MODEL_ROUTING_ENABLED", True)
    fast_max_tokens = _env_int("AGENT_MAX_TOKENS_FAST", 900)
    deep_max_tokens = _env_int("AGENT_MAX_TOKENS_DEEP", 2200)
    low_complexity_tools = _env_bool("AGENT_ALLOW_TOOLS_ON_LOW_COMPLEXITY", False)

    if force_deep or not routing_enabled:
        return AgentModelPolicy(
            model=deep_model,
            max_tokens=deep_max_tokens,
            allow_tools=True,
            tier="deep",
        )

    complexity = _complexity_score(messages, project_id, iteration)
    if complexity >= 3:
        return AgentModelPolicy(
            model=deep_model,
            max_tokens=deep_max_tokens,
            allow_tools=True,
            tier="deep",
        )

    return AgentModelPolicy(
        model=fast_model,
        max_tokens=fast_max_tokens,
        allow_tools=low_complexity_tools,
        tier="fast",
    )
