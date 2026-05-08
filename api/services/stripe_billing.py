"""Stripe billing service layer for checkout, portal, and webhook state sync."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import stripe

from api.services.bidders import BIDDERS_DIR, get_bidder_group

_STRIPE_SECRET_KEY_ENV = "STRIPE_SECRET_KEY"
_STRIPE_PRICE_ID_ENV = "STRIPE_PRICE_ID"
_STRIPE_ENABLED_ENV = "STRIPE_ENABLED"
_STRIPE_WEBHOOK_SECRET_ENV = "STRIPE_WEBHOOK_SECRET"
_STRIPE_SUCCESS_URL_ENV = "STRIPE_CHECKOUT_SUCCESS_URL"
_STRIPE_CANCEL_URL_ENV = "STRIPE_CHECKOUT_CANCEL_URL"
_STRIPE_PORTAL_RETURN_URL_ENV = "STRIPE_PORTAL_RETURN_URL"
_STRIPE_SUCCESS_URL_ENV_LEGACY = "STRIPE_BILLING_SUCCESS_URL"
_STRIPE_CANCEL_URL_ENV_LEGACY = "STRIPE_BILLING_CANCEL_URL"
_STRIPE_PORTAL_RETURN_URL_ENV_LEGACY = "STRIPE_BILLING_PORTAL_RETURN_URL"
_STRIPE_TRIAL_DAYS_ENV = "STRIPE_DEFAULT_TRIAL_DAYS"
_APP_BASE_URL_ENV = "APP_BASE_URL"


class BillingConfigurationError(RuntimeError):
    """Raised when required Stripe configuration is missing."""


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _epoch_to_iso(value: Any) -> str | None:
    """Convert epoch seconds to ISO8601 UTC."""
    if not isinstance(value, (int, float)):
        return None
    return datetime.fromtimestamp(value, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _get_env(name: str) -> str:
    """Return a required non-empty environment variable."""
    value = os.getenv(name, "").strip()
    if not value:
        raise BillingConfigurationError(f"{name} is required")
    return value


def _get_optional_env(*names: str) -> str | None:
    """Return the first non-empty env var from the provided names."""
    for name in names:
        value = os.getenv(name, "").strip()
        if value:
            return value
    return None


def _is_enabled() -> bool:
    """Return whether billing is enabled (defaults to true)."""
    raw = os.getenv(_STRIPE_ENABLED_ENV, "true").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def _get_app_base_url() -> str:
    """Return the configured app base URL with a localhost fallback for dev."""
    return os.getenv(_APP_BASE_URL_ENV, "http://localhost:5173").rstrip("/")


def _get_success_url() -> str:
    """Return checkout success URL from env or build from app base URL."""
    configured = _get_optional_env(
        _STRIPE_SUCCESS_URL_ENV,
        _STRIPE_SUCCESS_URL_ENV_LEGACY,
    )
    if configured:
        return configured
    return f"{_get_app_base_url()}/billing/success?session_id={{CHECKOUT_SESSION_ID}}"


def _get_cancel_url() -> str:
    """Return checkout cancel URL from env or build from app base URL."""
    configured = _get_optional_env(
        _STRIPE_CANCEL_URL_ENV,
        _STRIPE_CANCEL_URL_ENV_LEGACY,
    )
    if configured:
        return configured
    return f"{_get_app_base_url()}/billing/cancel"


def _get_portal_return_url() -> str:
    """Return customer portal return URL from env or build from app base URL."""
    configured = _get_optional_env(
        _STRIPE_PORTAL_RETURN_URL_ENV,
        _STRIPE_PORTAL_RETURN_URL_ENV_LEGACY,
    )
    if configured:
        return configured
    return f"{_get_app_base_url()}/settings/billing"


def _default_trial_days() -> int | None:
    """Return default trial days from env if configured and valid."""
    raw = os.getenv(_STRIPE_TRIAL_DAYS_ENV, "").strip()
    if not raw:
        return None
    try:
        parsed = int(raw)
    except ValueError as error:
        raise BillingConfigurationError(
            f"{_STRIPE_TRIAL_DAYS_ENV} must be an integer"
        ) from error
    if parsed < 0 or parsed > 90:
        raise BillingConfigurationError(
            f"{_STRIPE_TRIAL_DAYS_ENV} must be between 0 and 90"
        )
    return parsed


def _configure_stripe() -> None:
    """Configure Stripe SDK with a required secret key."""
    if not _is_enabled():
        raise BillingConfigurationError("Stripe billing is disabled (STRIPE_ENABLED=false)")
    stripe.api_key = _get_env(_STRIPE_SECRET_KEY_ENV)


def _resolve_price_id(plan: str) -> str:
    """Resolve Stripe price ID from plan-specific or default env vars."""
    normalized_plan = plan.strip().lower()
    plan_specific = f"STRIPE_PRICE_ID_{normalized_plan.upper()}"
    price_id = _get_optional_env(plan_specific, _STRIPE_PRICE_ID_ENV)
    if price_id:
        return price_id

    raise BillingConfigurationError(
        f"Missing Stripe price id for plan '{normalized_plan}'. "
        f"Set {plan_specific} or {_STRIPE_PRICE_ID_ENV}."
    )


def _bidder_file_path(bidder_id: str) -> Path:
    return BIDDERS_DIR / bidder_id / "bidder.json"


def _read_bidder_record(bidder_id: str) -> dict[str, Any]:
    path = _bidder_file_path(bidder_id)
    if not path.exists():
        raise FileNotFoundError(f"Bidder '{bidder_id}' not found")
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _write_bidder_record(bidder_id: str, data: dict[str, Any]) -> None:
    path = _bidder_file_path(bidder_id)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _billing_data(record: dict[str, Any]) -> dict[str, Any]:
    raw = record.get("billing")
    if isinstance(raw, dict):
        return dict(raw)
    return {}


def _save_billing_data(bidder_id: str, updates: dict[str, Any]) -> dict[str, Any]:
    """Merge and persist billing state into a bidder profile."""
    record = _read_bidder_record(bidder_id)
    billing = _billing_data(record)
    billing.update(updates)
    billing["updated_at"] = _now_iso()
    record["billing"] = billing
    _write_bidder_record(bidder_id, record)
    return billing


def _find_bidder_by_customer(customer_id: str) -> str | None:
    """Resolve a bidder ID from a persisted Stripe customer ID."""
    for bidder_dir in sorted(BIDDERS_DIR.iterdir()):
        if not bidder_dir.is_dir():
            continue
        bidder_file = bidder_dir / "bidder.json"
        if not bidder_file.exists():
            continue
        try:
            record = json.loads(bidder_file.read_text(encoding="utf-8-sig"))
        except Exception:
            continue
        billing = record.get("billing")
        if isinstance(billing, dict) and billing.get("customer_id") == customer_id:
            return bidder_dir.name
    return None


def _ensure_customer(
    bidder_id: str,
    bidder_name: str,
    user_email: str | None,
) -> str:
    """Return an existing Stripe customer ID or create one."""
    _configure_stripe()
    record = _read_bidder_record(bidder_id)
    billing = _billing_data(record)
    existing = str(billing.get("customer_id", "")).strip()

    if existing:
        try:
            stripe.Customer.retrieve(existing)
            return existing
        except Exception:
            # If the record is stale or invalid, create a fresh customer below.
            pass

    created = stripe.Customer.create(
        name=bidder_name,
        email=user_email,
        metadata={"bidder_id": bidder_id},
    )
    customer_id = str(created.get("id", "")).strip()
    if not customer_id:
        raise RuntimeError("Stripe customer was created without an ID")

    _save_billing_data(
        bidder_id,
        {
            "customer_id": customer_id,
            "customer_email": user_email,
        },
    )
    return customer_id


def get_billing_status(bidder_id: str) -> dict[str, Any]:
    """Return persisted billing status for one bidder/company."""
    try:
        record = _read_bidder_record(bidder_id)
    except FileNotFoundError:
        return {"configured": False}

    billing = _billing_data(record)
    return {
        "configured": bool(billing),
        "customer_id": billing.get("customer_id"),
        "subscription_id": billing.get("subscription_id"),
        "subscription_status": billing.get("subscription_status"),
        "price_id": billing.get("price_id"),
        "trial_ends_at": billing.get("trial_ends_at"),
        "current_period_end": billing.get("current_period_end"),
        "cancel_at_period_end": billing.get("cancel_at_period_end"),
        "last_event_type": billing.get("last_event_type"),
        "updated_at": billing.get("updated_at"),
    }


def create_checkout_session(
    bidder_id: str,
    user_id: str,
    user_email: str | None,
    bidder_name: str,
    plan: str = "starter",
    seats: int = 1,
    trial_days: int | None = None,
) -> dict[str, str]:
    """Create a Stripe hosted Checkout session for subscription signup."""
    _configure_stripe()
    normalized_plan = plan.strip().lower()
    price_id = _resolve_price_id(normalized_plan)
    customer_id = _ensure_customer(bidder_id, bidder_name, user_email)
    effective_trial_days = trial_days if trial_days is not None else _default_trial_days()

    subscription_data: dict[str, Any] = {
        "metadata": {
            "bidder_id": bidder_id,
            "user_id": user_id,
        }
    }
    if effective_trial_days:
        subscription_data["trial_period_days"] = effective_trial_days

    session = stripe.checkout.Session.create(
        mode="subscription",
        customer=customer_id,
        line_items=[{"price": price_id, "quantity": seats}],
        success_url=_get_success_url(),
        cancel_url=_get_cancel_url(),
        client_reference_id=bidder_id,
        metadata={
            "bidder_id": bidder_id,
            "user_id": user_id,
            "plan": normalized_plan,
            "seats": str(seats),
        },
        subscription_data=subscription_data,
    )

    session_id = str(session.get("id", "")).strip()
    url = str(session.get("url", "")).strip()
    if not session_id or not url:
        raise RuntimeError("Stripe checkout session response is missing required fields")

    _save_billing_data(
        bidder_id,
        {
            "customer_id": customer_id,
            "checkout_session_id": session_id,
            "price_id": price_id,
            "plan": normalized_plan,
            "seat_quantity": seats,
            "trial_days": effective_trial_days,
            "last_event_type": "checkout.session.created",
        },
    )
    return {
        "session_id": session_id,
        "url": url,
        "customer_id": customer_id,
    }


def create_portal_session(bidder_id: str) -> dict[str, str]:
    """Create a Stripe customer portal session for billing management."""
    _configure_stripe()

    bidder = get_bidder_group(bidder_id)
    if bidder is None:
        raise FileNotFoundError(f"Bidder '{bidder_id}' not found")

    record = _read_bidder_record(bidder_id)
    billing = _billing_data(record)
    customer_id = str(billing.get("customer_id", "")).strip()

    if not customer_id:
        primary_email = bidder.get("contact_email")
        customer_id = _ensure_customer(bidder_id, bidder.get("company_name", bidder_id), primary_email)

    session = stripe.billing_portal.Session.create(
        customer=customer_id,
        return_url=_get_portal_return_url(),
    )
    url = str(session.get("url", "")).strip()
    if not url:
        raise RuntimeError("Stripe portal session response is missing URL")

    _save_billing_data(
        bidder_id,
        {
            "customer_id": customer_id,
            "last_event_type": "billing.portal.session.created",
        },
    )
    return {"url": url}


def _update_from_subscription(
    bidder_id: str,
    subscription: dict[str, Any],
    event_type: str,
) -> None:
    """Persist common subscription fields from webhook payloads."""
    items = subscription.get("items", {})
    price_id = None
    if isinstance(items, dict):
        data = items.get("data", [])
        if isinstance(data, list) and data:
            first = data[0]
            if isinstance(first, dict):
                price = first.get("price", {})
                if isinstance(price, dict):
                    price_id = price.get("id")

    _save_billing_data(
        bidder_id,
        {
            "customer_id": subscription.get("customer"),
            "subscription_id": subscription.get("id"),
            "subscription_status": subscription.get("status"),
            "price_id": price_id,
            "trial_ends_at": _epoch_to_iso(subscription.get("trial_end")),
            "current_period_end": _epoch_to_iso(subscription.get("current_period_end")),
            "cancel_at_period_end": bool(subscription.get("cancel_at_period_end", False)),
            "last_event_type": event_type,
        },
    )


def _update_from_checkout_completed(session: dict[str, Any]) -> None:
    """Persist customer/subscription IDs when checkout completes."""
    bidder_id = ""
    metadata = session.get("metadata")
    if isinstance(metadata, dict):
        bidder_id = str(metadata.get("bidder_id", "")).strip()

    if not bidder_id:
        bidder_id = str(session.get("client_reference_id", "")).strip()

    if not bidder_id:
        return

    _save_billing_data(
        bidder_id,
        {
            "customer_id": session.get("customer"),
            "subscription_id": session.get("subscription"),
            "last_event_type": "checkout.session.completed",
        },
    )


def _update_from_invoice(invoice: dict[str, Any], event_type: str) -> None:
    """Persist payment state from invoice events."""
    customer_id = str(invoice.get("customer", "")).strip()
    if not customer_id:
        return

    bidder_id = _find_bidder_by_customer(customer_id)
    if not bidder_id:
        return

    subscription_status = None
    if event_type == "invoice.paid":
        subscription_status = "active"
    elif event_type == "invoice.payment_failed":
        subscription_status = "past_due"

    _save_billing_data(
        bidder_id,
        {
            "customer_id": customer_id,
            "subscription_status": subscription_status,
            "last_event_type": event_type,
        },
    )


def process_webhook(payload: bytes, signature: str | None) -> str:
    """Verify and process a Stripe webhook event payload."""
    _configure_stripe()
    webhook_secret = _get_env(_STRIPE_WEBHOOK_SECRET_ENV)

    if not signature:
        raise ValueError("Missing Stripe-Signature header")

    try:
        event = stripe.Webhook.construct_event(payload, signature, webhook_secret)
    except Exception as error:
        raise ValueError(f"Invalid webhook signature: {error}") from error

    event_type = str(event.get("type", "")).strip()
    data = event.get("data", {})
    obj = data.get("object", {}) if isinstance(data, dict) else {}
    if not isinstance(obj, dict):
        obj = {}

    if event_type == "checkout.session.completed":
        _update_from_checkout_completed(obj)
        return event_type

    if event_type in {"customer.subscription.created", "customer.subscription.updated", "customer.subscription.deleted"}:
        customer_id = str(obj.get("customer", "")).strip()
        bidder_id = _find_bidder_by_customer(customer_id)

        metadata = obj.get("metadata")
        if not bidder_id and isinstance(metadata, dict):
            bidder_id = str(metadata.get("bidder_id", "")).strip() or None

        if bidder_id:
            _update_from_subscription(bidder_id, obj, event_type)
        return event_type

    if event_type in {"invoice.paid", "invoice.payment_failed"}:
        _update_from_invoice(obj, event_type)
        return event_type

    # Accepted but not persisted: webhook can include many non-critical events.
    return event_type or "unhandled"
