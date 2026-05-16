"""Integration API routes — OAuth connect/disconnect/status for Gmail, Drive, etc.

All endpoints are scoped to a bidder.  The frontend passes ``bidder_id`` as
a query param because OAuth callbacks cannot carry auth headers.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from api.services.integrations.composio import (
    _DEFAULT_TOOLKITS,
    disconnect,
    get_connection_status,
    initiate_oauth,
)

router = APIRouter(prefix="/api/v1/integrations", tags=["integrations"])


# ── schemas ──────────────────────────────────────────────────────────────────


class IntegrationStatus(BaseModel):
    toolkit: str
    status: str = Field(description="connected | not_connected | not_configured")
    connect_url: str | None = Field(
        None, description="OAuth URL to connect (only when not_connected)"
    )


class ConnectionListResponse(BaseModel):
    bidder_id: str
    integrations: list[IntegrationStatus]


class OAuthInitiateRequest(BaseModel):
    toolkit: str = Field(..., description="e.g. GMAIL, GOOGLE_DRIVE")
    bidder_id: str = Field(..., description="VeloBid bidder slug")


class OAuthInitiateResponse(BaseModel):
    toolkit: str
    redirect_url: str | None


# ── routes ───────────────────────────────────────────────────────────────────


@router.get("/status")
async def list_integrations(bidder_id: str) -> ConnectionListResponse:
    """Return connection status for every default toolkit for a bidder."""
    statuses = get_connection_status(bidder_id)

    integrations: list[IntegrationStatus] = []
    for toolkit in _DEFAULT_TOOLKITS:
        status = statuses.get(toolkit, "unknown")
        integrations.append(
            IntegrationStatus(
                toolkit=toolkit,
                status=status,
                connect_url=(
                    None
                    if status == "connected"
                    else f"/api/v1/integrations/connect?toolkit={toolkit}&bidder_id={bidder_id}"
                ),
            )
        )

    return ConnectionListResponse(bidder_id=bidder_id, integrations=integrations)


@router.post("/connect")
async def connect_integration(
    request: Request, body: OAuthInitiateRequest
) -> OAuthInitiateResponse:
    """Start the OAuth flow for a toolkit.

    Returns a URL the frontend should redirect the user to.
    """
    # Build the redirect base from the incoming request
    redirect_base = str(request.base_url).rstrip("/")

    url = initiate_oauth(body.bidder_id, body.toolkit, redirect_base)
    if url is None:
        raise HTTPException(
            status_code=501,
            detail="Composio is not configured. Set COMPOSIO_API_KEY and install composio-core.",
        )

    return OAuthInitiateResponse(toolkit=body.toolkit, redirect_url=url)


@router.get("/oauth/callback")
async def oauth_callback(bidder_id: str, request: Request):
    """OAuth callback — Composio handles token exchange server-side.

    The user is redirected here after granting permissions.
    We simply confirm the connection is now active.
    """
    # Give Composio a moment to finalize the connection
    import asyncio

    await asyncio.sleep(0.5)

    statuses = get_connection_status(bidder_id)
    return {
        "bidder_id": bidder_id,
        "status": "ok",
        "message": "OAuth flow completed. Check /integrations/status for current state.",
        "integrations": statuses,
    }


@router.post("/disconnect")
async def disconnect_integration(body: OAuthInitiateRequest) -> dict:
    """Revoke a bidder's connection to a toolkit."""
    ok = disconnect(body.bidder_id, body.toolkit)
    if not ok:
        raise HTTPException(
            status_code=501,
            detail="Composio is not configured or disconnect failed.",
        )
    return {
        "bidder_id": body.bidder_id,
        "toolkit": body.toolkit,
        "status": "disconnected",
    }
