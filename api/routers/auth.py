"""API routes for user authentication."""
import hashlib
import secrets
from pathlib import Path

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, Field

from api.schemas.bidders import (
    LoginRequest,
    LoginResponse,
    UserInfoResponse,
)
from api.services.bidders import (
    authenticate_user,
    authenticate_user_any_bidder,
    create_token,
    get_bidder_group,
    get_bidder_name,
    get_user,
    verify_token,
)
from api.services.profile_manager import create_bidder_profile

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest):
    """Authenticate a user and return a JWT token."""
    resolved_bidder_id = request.bidder_id
    user = None

    if resolved_bidder_id:
        user = authenticate_user(resolved_bidder_id, request.user_id, request.password)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    else:
        try:
            resolved = authenticate_user_any_bidder(request.user_id, request.password)
        except ValueError as error:
            raise HTTPException(status_code=409, detail=str(error)) from error

        if not resolved:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        resolved_bidder_id, user = resolved

    bidder_name = get_bidder_name(resolved_bidder_id)

    # Auto-create Hermes profile if it doesn't exist yet (lazy on first login)
    try:
        group = get_bidder_group(resolved_bidder_id)
        if group:
            trades = [group.get("trade_domain", "General").lower().replace(" / ", ",")]
            create_bidder_profile(
                bidder_id=resolved_bidder_id,
                company_name=group.get("company_name", bidder_name),
                trades=trades,
                company_context=f"Location: {group.get('location', '')}. Region: {group.get('operating_region', '')}.",
                service_area=group.get("operating_region", ""),
            )
    except Exception:
        pass  # Non-critical — chat will still work, just without profile context

    token = create_token(resolved_bidder_id, request.user_id)

    return LoginResponse(
        token=token,
        user=UserInfoResponse(
            user_id=request.user_id,
            name=user.get("name", request.user_id),
            role=user.get("role", ""),
            email=user.get("email"),
        ),
        bidder_id=resolved_bidder_id,
        bidder_name=bidder_name,
    )


@router.get("/me", response_model=LoginResponse)
def me(authorization: str = Header(..., alias="Authorization")):
    """Get current user info from the JWT token."""
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

    user = get_user(bidder_id, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    bidder_name = get_bidder_name(bidder_id)

    return LoginResponse(
        token=token,
        user=UserInfoResponse(
            user_id=user_id,
            name=user.name,
            role=user.role,
            email=user.email,
        ),
        bidder_id=bidder_id,
        bidder_name=bidder_name,
    )


class SetPasswordRequest(BaseModel):
    """Request to set/reset a user's password."""

    bidder_id: str = Field(..., examples=["air_hero"])
    user_id: str = Field(..., examples=["jose"])
    new_password: str = Field(..., examples=["newpass123"])


def _get_users_path(bidder_id: str) -> Path:
    """Get the users.json path for a bidder group without path traversal."""
    from api.services.bids import PROJECT_ROOT
    bidders_root = (PROJECT_ROOT / "config" / "bidders").resolve()
    bidder_path = (bidders_root / bidder_id).resolve()
    try:
        bidder_path.relative_to(bidders_root)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid bidder group")
    return bidder_path / "users.json"


@router.post("/set-password")
def set_password(request: SetPasswordRequest):
    """Set or reset a user's password. Hashes automatically."""
    users_path = _get_users_path(request.bidder_id)
    if not users_path.exists():
        raise HTTPException(status_code=404, detail="Bidder group not found")

    try:
        users = __import__("json").loads(users_path.read_text(encoding="utf-8-sig"))
        if not isinstance(users, list):
            raise HTTPException(status_code=500, detail="Invalid users file")
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to read users file")

    found = False
    for user in users:
        if user.get("id") == request.user_id:
            salt = secrets.token_hex(16)
            user["password_salt"] = salt
            user["password_hash"] = hashlib.sha256(
                (salt + request.new_password).encode()
            ).hexdigest()
            found = True
            break

    if not found:
        raise HTTPException(status_code=404, detail="User not found")

    users_path.write_text(__import__("json").dumps(users, indent=2), encoding="utf-8")
    return {"message": f"Password updated for '{request.user_id}'"}
