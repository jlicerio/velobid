"""Agent access control: trial enforcement and request rate limiting."""

from __future__ import annotations

import json
import os
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from api.services.bidders import BIDDERS_DIR

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.getenv("VELOBID_DATA_DIR", PROJECT_ROOT / "data"))
RATE_LIMITS_DIR = DATA_DIR / "agent_rate_limits"

_ACTIVE_SUBSCRIPTION_STATUSES = {"active", "trialing", "past_due"}
_rate_limit_lock = threading.Lock()


@dataclass(frozen=True)
class AgentAccessState:
    """Result of an agent access check."""

    access_mode: str
    trial_ends_at: str | None
    subscription_status: str | None
    rate_limits: dict[str, Any]


@dataclass(frozen=True)
class AgentAccessError(Exception):
    """Raised when agent access must be denied."""

    status_code: int
    detail: dict[str, Any]
    headers: dict[str, str] | None = None


def _env_int(name: str, default: int, minimum: int = 0, maximum: int = 1_000_000) -> int:
    raw = os.getenv(name, str(default)).strip()
    try:
        value = int(raw)
    except ValueError:
        value = default
    return max(minimum, min(maximum, value))


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _to_iso(ts: datetime) -> str:
    return ts.strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_iso(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    clean = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(clean)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _read_bidder_record(bidder_id: str) -> dict[str, Any]:
    path = BIDDERS_DIR / bidder_id / "bidder.json"
    if not path.exists():
        raise FileNotFoundError(f"Bidder '{bidder_id}' not found")
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _write_bidder_record(bidder_id: str, record: dict[str, Any]) -> None:
    path = BIDDERS_DIR / bidder_id / "bidder.json"
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")


def _billing_data(record: dict[str, Any]) -> dict[str, Any]:
    raw = record.get("billing")
    if isinstance(raw, dict):
        return dict(raw)
    return {}


def _save_billing_data(bidder_id: str, updates: dict[str, Any]) -> dict[str, Any]:
    record = _read_bidder_record(bidder_id)
    billing = _billing_data(record)
    billing.update(updates)
    billing["updated_at"] = _to_iso(_now())
    record["billing"] = billing
    _write_bidder_record(bidder_id, record)
    return billing


def _ensure_trial_window(bidder_id: str, billing: dict[str, Any]) -> dict[str, Any]:
    """Initialize a local trial when no Stripe trial/subscription exists yet."""
    status = str(billing.get("subscription_status", "")).strip().lower()
    trial_ends_at = _parse_iso(billing.get("trial_ends_at"))
    if status in _ACTIVE_SUBSCRIPTION_STATUSES or trial_ends_at is not None:
        return billing

    trial_days = _env_int("AGENT_TRIAL_DAYS", default=14, minimum=0, maximum=90)
    started_at = _now()
    ends_at = started_at + timedelta(days=trial_days)

    return _save_billing_data(
        bidder_id,
        {
            "trial_started_at": _to_iso(started_at),
            "trial_ends_at": _to_iso(ends_at),
            "subscription_status": "local_trial",
            "last_event_type": "trial.started",
        },
    )


def _check_trial_and_subscription(
    bidder_id: str,
) -> tuple[str, str | None, str | None]:
    """Return access mode, trial end, and subscription status or raise denial."""
    record = _read_bidder_record(bidder_id)
    billing = _billing_data(record)
    billing = _ensure_trial_window(bidder_id, billing)

    now = _now()
    status = str(billing.get("subscription_status", "")).strip().lower() or None
    trial_ends = _parse_iso(billing.get("trial_ends_at"))
    trial_ends_iso = _to_iso(trial_ends) if trial_ends else None

    if status in _ACTIVE_SUBSCRIPTION_STATUSES:
        return ("paid", trial_ends_iso, status)

    if trial_ends and now <= trial_ends:
        return ("trial", trial_ends_iso, status)

    raise AgentAccessError(
        status_code=402,
        detail={
            "error": "trial_expired",
            "message": "Trial has expired. Please start a paid plan to continue using the agent.",
            "trial_ends_at": trial_ends_iso,
        },
    )


def _limits_config() -> dict[str, int]:
    return {
        "company_per_minute": _env_int("AGENT_RATE_LIMIT_COMPANY_PER_MINUTE", default=30, minimum=1),
        "company_per_hour": _env_int("AGENT_RATE_LIMIT_COMPANY_PER_HOUR", default=600, minimum=1),
        "company_per_day": _env_int("AGENT_RATE_LIMIT_COMPANY_PER_DAY", default=5000, minimum=1),
        "user_per_minute": _env_int("AGENT_RATE_LIMIT_USER_PER_MINUTE", default=12, minimum=1),
        "user_per_hour": _env_int("AGENT_RATE_LIMIT_USER_PER_HOUR", default=240, minimum=1),
    }


def _rate_limit_file(bidder_id: str) -> Path:
    RATE_LIMITS_DIR.mkdir(parents=True, exist_ok=True)
    return RATE_LIMITS_DIR / f"{bidder_id}.json"


def _load_rate_state(bidder_id: str) -> dict[str, Any]:
    path = _rate_limit_file(bidder_id)
    if not path.exists():
        return {"company_events": [], "users": {}, "updated_at": _to_iso(_now())}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"company_events": [], "users": {}, "updated_at": _to_iso(_now())}

    company_events = raw.get("company_events")
    users = raw.get("users")
    if not isinstance(company_events, list):
        company_events = []
    if not isinstance(users, dict):
        users = {}
    normalized_users: dict[str, list[int]] = {}
    for user_id, events in users.items():
        if isinstance(user_id, str) and isinstance(events, list):
            normalized_users[user_id] = events

    return {
        "company_events": company_events,
        "users": normalized_users,
        "updated_at": str(raw.get("updated_at", _to_iso(_now()))),
    }


def _save_rate_state(bidder_id: str, state: dict[str, Any]) -> None:
    path = _rate_limit_file(bidder_id)
    state["updated_at"] = _to_iso(_now())
    path.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _as_timestamps(events: list[Any]) -> list[int]:
    converted: list[int] = []
    for value in events:
        if isinstance(value, (int, float)):
            converted.append(int(value))
    return converted


def _prune(events: list[int], cutoff: int) -> list[int]:
    return [ts for ts in events if ts >= cutoff]


def _consume_rate_limit(bidder_id: str, user_id: str) -> dict[str, Any]:
    """Consume one request slot, or raise AgentAccessError when exceeded."""
    config = _limits_config()
    now_epoch = int(_now().timestamp())
    min_cutoff = now_epoch - 60
    hour_cutoff = now_epoch - 3600
    day_cutoff = now_epoch - 86_400

    with _rate_limit_lock:
        state = _load_rate_state(bidder_id)

        company_events = _as_timestamps(state.get("company_events", []))
        company_events = _prune(company_events, day_cutoff)

        raw_user_events = state.get("users", {}).get(user_id, [])
        user_events = _as_timestamps(raw_user_events)
        user_events = _prune(user_events, hour_cutoff)

        company_minute_used = len(_prune(company_events, min_cutoff))
        company_hour_used = len(_prune(company_events, hour_cutoff))
        company_day_used = len(company_events)
        user_minute_used = len(_prune(user_events, min_cutoff))
        user_hour_used = len(user_events)

        def _fail(reason: str, retry_after_seconds: int) -> None:
            raise AgentAccessError(
                status_code=429,
                detail={
                    "error": "rate_limited",
                    "reason": reason,
                    "retry_after_seconds": retry_after_seconds,
                },
                headers={"Retry-After": str(max(1, retry_after_seconds))},
            )

        if company_minute_used >= config["company_per_minute"]:
            oldest = min(_prune(company_events, min_cutoff))
            _fail("company_per_minute", 60 - (now_epoch - oldest))

        if company_hour_used >= config["company_per_hour"]:
            oldest = min(_prune(company_events, hour_cutoff))
            _fail("company_per_hour", 3600 - (now_epoch - oldest))

        if company_day_used >= config["company_per_day"]:
            oldest = min(company_events)
            _fail("company_per_day", 86_400 - (now_epoch - oldest))

        if user_minute_used >= config["user_per_minute"]:
            oldest = min(_prune(user_events, min_cutoff))
            _fail("user_per_minute", 60 - (now_epoch - oldest))

        if user_hour_used >= config["user_per_hour"]:
            oldest = min(user_events)
            _fail("user_per_hour", 3600 - (now_epoch - oldest))

        company_events.append(now_epoch)
        user_events.append(now_epoch)
        users = state.get("users", {})
        if not isinstance(users, dict):
            users = {}
        users[user_id] = user_events
        state["users"] = users
        state["company_events"] = company_events
        _save_rate_state(bidder_id, state)

        company_minute_remaining = max(0, config["company_per_minute"] - (company_minute_used + 1))
        company_hour_remaining = max(0, config["company_per_hour"] - (company_hour_used + 1))
        company_day_remaining = max(0, config["company_per_day"] - (company_day_used + 1))
        user_minute_remaining = max(0, config["user_per_minute"] - (user_minute_used + 1))
        user_hour_remaining = max(0, config["user_per_hour"] - (user_hour_used + 1))

    return {
        "limits": config,
        "remaining": {
            "company_per_minute": company_minute_remaining,
            "company_per_hour": company_hour_remaining,
            "company_per_day": company_day_remaining,
            "user_per_minute": user_minute_remaining,
            "user_per_hour": user_hour_remaining,
        },
    }


def enforce_agent_access(bidder_id: str, user_id: str) -> AgentAccessState:
    """Validate billing/trial and consume one rate-limit slot."""
    access_mode, trial_ends_at, subscription_status = _check_trial_and_subscription(bidder_id)
    rate_limits = _consume_rate_limit(bidder_id, user_id)
    return AgentAccessState(
        access_mode=access_mode,
        trial_ends_at=trial_ends_at,
        subscription_status=subscription_status,
        rate_limits=rate_limits,
    )
