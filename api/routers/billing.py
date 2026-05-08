"""Stripe billing API routes."""

from fastapi import APIRouter, Depends, Header, HTTPException, Request

from api.schemas.billing import (
    BillingStatusResponse,
    CheckoutSessionRequest,
    CheckoutSessionResponse,
    PortalSessionResponse,
)
from api.services.auth_guard import AuthContext, get_auth_context
from api.services.bidders import get_bidder_name, get_user
from api.services.stripe_billing import (
    BillingConfigurationError,
    create_checkout_session,
    create_portal_session,
    get_billing_status,
    process_webhook,
)

router = APIRouter(prefix="/api/v1/billing", tags=["billing"])


@router.get("/status", response_model=BillingStatusResponse)
def billing_status(
    auth: AuthContext = Depends(get_auth_context),
) -> BillingStatusResponse:
    """Return billing state for the currently authenticated bidder/company."""
    return BillingStatusResponse(**get_billing_status(auth.bidder_id))


@router.post("/checkout-session", response_model=CheckoutSessionResponse)
def billing_checkout_session(
    body: CheckoutSessionRequest,
    auth: AuthContext = Depends(get_auth_context),
) -> CheckoutSessionResponse:
    """Create a Stripe hosted Checkout session for subscription signup."""
    user = get_user(auth.bidder_id, auth.user_id)
    email = user.email if user else None
    bidder_name = get_bidder_name(auth.bidder_id)

    try:
        data = create_checkout_session(
            bidder_id=auth.bidder_id,
            user_id=auth.user_id,
            user_email=email,
            bidder_name=bidder_name,
            plan=body.plan,
            seats=body.seats,
            trial_days=body.trial_days,
        )
    except BillingConfigurationError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=502, detail=f"Stripe checkout failed: {error}") from error

    return CheckoutSessionResponse(**data)


@router.post("/portal-session", response_model=PortalSessionResponse)
def billing_portal_session(
    auth: AuthContext = Depends(get_auth_context),
) -> PortalSessionResponse:
    """Create a Stripe customer portal session for billing self-service."""
    try:
        data = create_portal_session(auth.bidder_id)
    except BillingConfigurationError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=502, detail=f"Stripe portal failed: {error}") from error

    return PortalSessionResponse(**data)


@router.post("/webhook")
@router.post("/stripe/webhook")
async def billing_webhook(
    request: Request,
    stripe_signature: str | None = Header(None, alias="Stripe-Signature"),
) -> dict[str, str]:
    """Receive and process Stripe webhook events."""
    payload = await request.body()

    try:
        event_type = process_webhook(payload=payload, signature=stripe_signature)
    except BillingConfigurationError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=502, detail=f"Stripe webhook failed: {error}") from error

    return {"received": "true", "event_type": event_type}
