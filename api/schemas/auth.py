"""Pydantic schemas for auth/signup API requests and responses."""

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class UserStatus(str, Enum):
    pending_email_verification = "pending_email_verification"
    email_verified_pending_2fa = "email_verified_pending_2fa"
    active = "active"
    locked = "locked"
    disabled = "disabled"


class OrgStatus(str, Enum):
    pending_owner_verification = "pending_owner_verification"
    active = "active"
    suspended = "suspended"


class UserRole(str, Enum):
    owner_admin = "owner_admin"
    estimator = "estimator"
    viewer = "viewer"


# ---------------------------------------------------------------------------
# Signup Start
# ---------------------------------------------------------------------------


class SignupStartRequest(BaseModel):
    """Initial signup payload — org info + admin user credentials."""

    model_config = ConfigDict(populate_by_name=True)

    company_name: str = Field(
        ..., min_length=1, max_length=200, examples=["Air Hero LLC"]
    )
    bidder_display_name: str | None = Field(None, max_length=200, examples=["Air Hero"])
    primary_contact: str = Field(
        ..., min_length=1, max_length=200, examples=["Jose Exiga"]
    )
    admin_email: EmailStr = Field(..., examples=["jose@airhero.com"])
    password: str = Field(..., min_length=8, max_length=128)
    phone: str | None = Field(None, max_length=30, examples=["+1 (956) 586-2118"])
    location: str | None = Field(None, max_length=200, examples=["McAllen, TX"])
    accept_terms: bool = Field(..., description="Must accept terms to proceed")
    cf_turnstile_token: str | None = Field(
        None,
        max_length=2048,
        description="Cloudflare Turnstile widget token for abuse protection",
    )

    @field_validator("accept_terms")
    @classmethod
    def terms_must_be_accepted(cls, v: bool) -> bool:
        if not v:
            raise ValueError("You must accept the terms of service")
        return v


class SignupStartResponse(BaseModel):
    """Returned after successful signup initiation."""

    signup_id: str = Field(..., description="Temporary signup session ID")
    email: str = Field(..., description="Masked admin email")
    message: str = Field("Verification email sent. Please check your inbox.")
    expires_in_minutes: int = 30


# ---------------------------------------------------------------------------
# Email Verification
# ---------------------------------------------------------------------------


class EmailVerifyRequest(BaseModel):
    """Token from the verification link sent via email."""

    token: str = Field(..., description="Signed email verification token")


class EmailVerifyResponse(BaseModel):
    """Returned after successful email verification."""

    email: str
    status: UserStatus = UserStatus.email_verified_pending_2fa
    temp_token: str = Field(..., description="Temporary token for 2FA setup step")
    message: str = "Email verified. Please set up two-factor authentication."


# ---------------------------------------------------------------------------
# 2FA Setup
# ---------------------------------------------------------------------------


class TwoFASetupStartRequest(BaseModel):
    """Initiate TOTP setup — requires temp token from email verification."""

    temp_token: str = Field(..., description="Temp token from email verification step")


class TwoFASetupStartResponse(BaseModel):
    """TOTP provisioning info to display to user."""

    provisioning_uri: str = Field(..., description="otpauth:// URI for QR code")
    secret: str = Field(..., description="Plain-text TOTP secret (show once)")
    qr_svg_base64: str | None = Field(None, description="Base64-encoded QR code SVG")
    has_recovery_codes: bool = False


class TwoFASetupConfirmRequest(BaseModel):
    """Confirm TOTP setup by submitting a valid code."""

    temp_token: str = Field(..., description="Temp token from email verification step")
    totp_code: str = Field(
        ..., min_length=6, max_length=6, description="6-digit TOTP code"
    )


class RecoveryCodeResponse(BaseModel):
    """A single recovery code (shown once)."""

    code: str = Field(..., description="Recovery code in plain text")


class TwoFASetupConfirmResponse(BaseModel):
    """Returned after successful 2FA enrollment — activation complete."""

    user_id: str
    email: str
    status: UserStatus = UserStatus.active
    org_status: OrgStatus = OrgStatus.active
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    recovery_codes: list[RecoveryCodeResponse] = Field(
        ..., description="One-time recovery codes (save these)"
    )
    message: str = "Account activated. Save your recovery codes."


# ---------------------------------------------------------------------------
# Login / Challenge
# ---------------------------------------------------------------------------


class LoginRequest(BaseModel):
    """User login with email and password."""

    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """Login response — may require 2FA challenge."""

    challenge_required: bool = False
    challenge_type: str | None = "totp"  # 'totp' or 'recovery'
    temp_token: str | None = Field(
        None, description="Temp token to use in 2FA challenge step"
    )
    access_token: str | None = None
    refresh_token: str | None = None
    user_id: str | None = None
    email: str | None = None
    status: UserStatus | None = None


class TwoFAChallengeRequest(BaseModel):
    """Submit a TOTP or recovery code to complete login."""

    temp_token: str = Field(..., description="Temp token from login response")
    code: str = Field(
        ..., min_length=6, max_length=32, description="TOTP or recovery code"
    )


class TwoFAChallengeResponse(BaseModel):
    """Successful 2FA challenge response."""

    access_token: str
    refresh_token: str
    user_id: str
    email: str


# ---------------------------------------------------------------------------
# Password Reset
# ---------------------------------------------------------------------------


class ForgotPasswordRequest(BaseModel):
    """Request a password reset email."""

    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    """Password reset email sent confirmation."""

    message: str = "If that email is registered, a reset link has been sent."


class ResetPasswordRequest(BaseModel):
    """Submit a password reset with token."""

    token: str
    new_password: str = Field(..., min_length=8, max_length=128)


class ResetPasswordResponse(BaseModel):
    """Password reset confirmation."""

    message: str = "Password updated successfully."


# ---------------------------------------------------------------------------
# Token Refresh
# ---------------------------------------------------------------------------


class RefreshTokenRequest(BaseModel):
    """Exchange a refresh token for a new access token."""

    refresh_token: str


class RefreshTokenResponse(BaseModel):
    """New access token."""

    access_token: str
    refresh_token: str


# ---------------------------------------------------------------------------
# Internal / State Models
# ---------------------------------------------------------------------------


class PendingSignup(BaseModel):
    """In-memory signup session state (before DB is available)."""

    signup_id: str = Field(default_factory=lambda: str(uuid4()))
    company_name: str
    bidder_display_name: str | None
    primary_contact: str
    admin_email: str
    password_hash: str
    phone: str | None
    location: str | None
    org_id: str = Field(default_factory=lambda: str(uuid4()))
    admin_user_id: str = Field(default_factory=lambda: str(uuid4()))
    bidder_id: str = Field(default_factory=lambda: str(uuid4()))
    status: UserStatus = UserStatus.pending_email_verification
    org_status: OrgStatus = OrgStatus.pending_owner_verification
    email_verification_token: str | None = None
    email_verification_expires_at: datetime | None = None
    totp_secret: str | None = None
    two_factor_enabled: bool = False
    recovery_codes: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
