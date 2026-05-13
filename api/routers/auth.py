"""Authentication and signup API routes."""

from fastapi import APIRouter

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
from api.services import auth as auth_service

router = APIRouter(prefix="/api/v1", tags=["auth"])


@router.post(
    "/auth/signup/start",
    response_model=SignupStartResponse,
    status_code=201,
)
def signup_start(request: SignupStartRequest) -> SignupStartResponse:
    """Initiate a new signup — creates org, admin user, and sends verification email."""
    return auth_service.start_signup(request)


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
