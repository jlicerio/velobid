"""Authentication and signup API routes."""

import hashlib
import secrets
from pathlib import Path

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, Field

from api.schemas.auth import (
    EmailVerifyRequest,
    EmailVerifyResponse,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    ResetPasswordRequest,
    ResetPasswordResponse,
    SignupStartRequest,
    SignupStartResponse,
    TwoFAChallengeRequest,
    TwoFAChallengeResponse,
    TwoFASetupConfirmRequest,
    TwoFASetupConfirmResponse,
    TwoFASetupStartRequest,
    TwoFASetupStartResponse,
)
from api.schemas.bidders import (
    LoginRequest as BiddersLoginRequest,
    LoginResponse as BiddersLoginResponse,
    UserInfoResponse as BiddersUserInfoResponse,
)
from api.services import auth as auth_service
from api.services.bidders import (
    get_bidder_group,
    get_bidder_name,
    get_user,
    verify_token as bidders_verify_token,
)
from api.services.profile_manager import create_bidder_profile

router = APIRouter(prefix="/api/v1", tags=["auth"])


# ============================================================================
# New signup / 2FA / email-based auth system
# ============================================================================


@router.post(
    "/auth/signup/start",
    response_model=SignupStartResponse,
    status_code=201,
)
async def signup_start(request: SignupStartRequest) -> SignupStartResponse:
    """Initiate a new signup — creates org, admin user, and sends verification email."""
    return await auth_service.start_signup(request)


@router.post(
    "/auth/email/verify",
    response_model=EmailVerifyResponse,
)
def email_verify(request: EmailVerifyRequest) -> EmailVerifyResponse:
    """Verify the signup email using the signed token sent via email."""
    return auth_service.verify_email(request.token)


@router.post(
    "/auth/2fa/setup/start",
    response_model=TwoFASetupStartResponse,
)
def twofa_setup_start(
    request: TwoFASetupStartRequest,
) -> TwoFASetupStartResponse:
    """Start TOTP 2FA setup — returns provisioning URI and secret."""
    return auth_service.start_2fa_setup(request.temp_token)


@router.post(
    "/auth/2fa/setup/confirm",
    response_model=TwoFASetupConfirmResponse,
)
def twofa_setup_confirm(
    request: TwoFASetupConfirmRequest,
) -> TwoFASetupConfirmResponse:
    """Confirm TOTP 2FA setup by validating a 6-digit code — activates the account."""
    return auth_service.confirm_2fa_setup(request.temp_token, request.totp_code)


@router.post(
    "/auth/login",
    response_model=LoginResponse,
)
def login(request: LoginRequest) -> LoginResponse:
    """Authenticate with email and password — may return 2FA challenge."""
    return auth_service.login(request.email, request.password)


@router.post(
    "/auth/2fa/challenge",
    response_model=TwoFAChallengeResponse,
)
def twofa_challenge(request: TwoFAChallengeRequest) -> TwoFAChallengeResponse:
    """Complete 2FA challenge with a TOTP or recovery code."""
    return auth_service.challenge_2fa(request.temp_token, request.code)


@router.post(
    "/auth/password/forgot",
    response_model=ForgotPasswordResponse,
)
def forgot_password(request: ForgotPasswordRequest) -> ForgotPasswordResponse:
    """Request a password reset email."""
    return auth_service.forgot_password(request.email)


@router.post(
    "/auth/password/reset",
    response_model=ResetPasswordResponse,
)
def reset_password(request: ResetPasswordRequest) -> ResetPasswordResponse:
    """Reset password using the signed token from the reset email."""
    auth_service.reset_password(request.token, request.new_password)
    return ResetPasswordResponse()


@router.post(
    "/auth/token/refresh",
)
def token_refresh(request: RefreshTokenRequest) -> dict:
    """Exchange a refresh token for a new access/refresh token pair."""
    return auth_service.refresh_access_token(request.refresh_token)


# ============================================================================
# Legacy bidders-based endpoints (me, set-password, login by bidder_id)
# ============================================================================


@router.post("/auth/bidders/login", response_model=BiddersLoginResponse)
def bidders_login(request: BiddersLoginRequest):
    """Authenticate a bidders-based user and return a JWT token.

    Legacy: uses bidder_id + user_id + password scheme.
    """
    resolved_bidder_id = request.bidder_id
    user = None

    if resolved_bidder_id:
        from api.services.bidders import authenticate_user

        user = authenticate_user(resolved_bidder_id, request.user_id, request.password)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    else:
        from api.services.bidders import authenticate_user_any_bidder

        try:
            resolved = authenticate_user_any_bidder(
                request.user_id, request.password
            )
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
            trades = [
                group.get("trade_domain", "General").lower().replace(" / ", ",")
            ]
            from api.services.bidders import create_token

            create_bidder_profile(
                bidder_id=resolved_bidder_id,
                company_name=group.get("company_name", bidder_name),
                trades=trades,
                company_context=(
                    f"Location: {group.get('location', '')}. "
                    f"Region: {group.get('operating_region', '')}."
                ),
                service_area=group.get("operating_region", ""),
            )
    except Exception:
        pass  # Non-critical — chat will still work, just without profile context

    from api.services.bidders import create_token

    token = create_token(resolved_bidder_id, request.user_id)

    return BiddersLoginResponse(
        token=token,
        user=BiddersUserInfoResponse(
            user_id=request.user_id,
            name=user.get("name", request.user_id),
            role=user.get("role", ""),
            email=user.get("email"),
        ),
        bidder_id=resolved_bidder_id,
        bidder_name=bidder_name,
    )


@router.get("/auth/me", response_model=BiddersLoginResponse)
def me(authorization: str = Header(..., alias="Authorization")):
    """Get current user info from the JWT token (legacy bidders-based)."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = authorization[7:]
    payload = bidders_verify_token(token)
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

    return BiddersLoginResponse(
        token=token,
        user=BiddersUserInfoResponse(
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


@router.post("/auth/set-password")
def set_password(request: SetPasswordRequest):
    """Set or reset a user's password. Hashes automatically."""
    users_path = _get_users_path(request.bidder_id)
    if not users_path.exists():
        raise HTTPException(status_code=404, detail="Bidder group not found")

    try:
        import json

        users = json.loads(users_path.read_text(encoding="utf-8-sig"))
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

    import json

    users_path.write_text(json.dumps(users, indent=2), encoding="utf-8")
    return {"message": f"Password updated for '{request.user_id}'"}
