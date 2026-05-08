"""Authentication helpers for protected API routes."""

from dataclasses import dataclass

from fastapi import Header, HTTPException

from api.services.bidders import get_user, verify_token


@dataclass(frozen=True)
class AuthContext:
    """Minimal authenticated user context from JWT."""

    bidder_id: str
    user_id: str


def get_auth_context(
    authorization: str | None = Header(None, alias="Authorization"),
) -> AuthContext:
    """Validate bearer token and return bidder/user identity."""
    return parse_auth_context(authorization)


def parse_auth_context(authorization: str | None) -> AuthContext:
    """Validate bearer token and return bidder/user identity."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = authorization[7:]
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    bidder_id = payload.get("bidder_id")
    user_id = payload.get("user_id")
    if not bidder_id or not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    if not get_user(bidder_id, user_id):
        raise HTTPException(status_code=401, detail="User not found")

    return AuthContext(bidder_id=bidder_id, user_id=user_id)
