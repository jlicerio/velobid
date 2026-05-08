"""Pydantic schemas for Stripe billing endpoints."""

from typing import Literal

from pydantic import BaseModel, Field


class CheckoutSessionRequest(BaseModel):
    """Request body for creating a Stripe Checkout session."""

    plan: Literal["starter", "pro", "enterprise"] = Field(
        default="starter",
        description="Subscription plan key mapped to STRIPE_PRICE_ID_<PLAN> env vars.",
    )
    seats: int = Field(
        default=1,
        ge=1,
        le=250,
        description="Seat quantity for per-seat subscription pricing.",
    )
    trial_days: int | None = Field(
        default=None,
        ge=0,
        le=90,
        description="Optional trial length in days. If omitted, server defaults apply.",
    )


class CheckoutSessionResponse(BaseModel):
    """Response body for a Stripe Checkout session creation."""

    session_id: str
    url: str
    customer_id: str


class PortalSessionResponse(BaseModel):
    """Response body for creating a Stripe Customer Portal session."""

    url: str


class BillingStatusResponse(BaseModel):
    """Billing status snapshot for the authenticated bidder/company."""

    configured: bool
    customer_id: str | None = None
    subscription_id: str | None = None
    subscription_status: str | None = None
    price_id: str | None = None
    trial_ends_at: str | None = None
    current_period_end: str | None = None
    cancel_at_period_end: bool | None = None
    last_event_type: str | None = None
    updated_at: str | None = None
