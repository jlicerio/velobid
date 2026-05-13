"""Security primitives: password hashing, JWT tokens, TOTP/2FA, recovery codes."""

from __future__ import annotations

import base64
import io
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import pyotp
import qrcode
from fastapi import HTTPException, status
from jose import ExpiredSignatureError, JWTError, jwt
from passlib.context import CryptContext
from qrcode.image.svg import SvgPathImage

# ---------------------------------------------------------------------------
# Configuration helpers
# ---------------------------------------------------------------------------

_JWT_SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY",
    os.getenv(
        "JWT_SECRET",
        "velobid-dev-jwt-secret-change-in-production",
    ),
)
_ENCRYPTION_KEY = os.getenv(
    "ENCRYPTION_KEY",
    "velobid-dev-encryption-key-change-in-production",
)
_JWT_ALGORITHM = "HS256"
_ACCESS_TOKEN_EXPIRE_MINUTES = 15
_REFRESH_TOKEN_EXPIRE_DAYS = 7

# ---------------------------------------------------------------------------
# Password hashing  (passlib + bcrypt)
# ---------------------------------------------------------------------------

_password_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password using passlib bcrypt (or argon2 if available).

    Returns the hash string suitable for storage.
    """
    if not password:
        raise ValueError("Password must not be empty")
    return _password_ctx.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against its bcrypt hash.

    Returns ``True`` if the password matches, ``False`` otherwise.
    """
    if not plain_password or not hashed_password:
        return False
    return _password_ctx.verify(plain_password, hashed_password)


# ---------------------------------------------------------------------------
# JWT creation & decoding  (python-jose)
# ---------------------------------------------------------------------------


def create_access_token(
    subject: str,
    extra_claims: dict[str, Any] | None = None,
    expires_delta_minutes: int = _ACCESS_TOKEN_EXPIRE_MINUTES,
) -> str:
    """Create a signed JWT access token.

    The *subject* should be the user's unique identifier (user_id).  An
    optional *extra_claims* dict can be merged into the payload.

    Returns the encoded JWT string.
    """
    now = datetime.now(tz=timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "iat": now,
        "exp": now + timedelta(minutes=expires_delta_minutes),
        "type": "access",
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, _JWT_SECRET_KEY, algorithm=_JWT_ALGORITHM)


def create_refresh_token(
    subject: str,
    expires_delta_days: int = _REFRESH_TOKEN_EXPIRE_DAYS,
) -> str:
    """Create a signed JWT refresh token with a longer expiry.

    Returns the encoded JWT string.
    """
    now = datetime.now(tz=timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "iat": now,
        "exp": now + timedelta(days=expires_delta_days),
        "type": "refresh",
    }
    return jwt.encode(payload, _JWT_SECRET_KEY, algorithm=_JWT_ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    """Decode and verify a JWT token.

    Returns the payload dict on success.

    Raises
    ------
    HTTPException (401)
        If the token is invalid, expired, or cannot be decoded.
    """
    try:
        payload: dict[str, Any] = jwt.decode(
            token,
            _JWT_SECRET_KEY,
            algorithms=[_JWT_ALGORITHM],
        )
        return payload
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ---------------------------------------------------------------------------
# Secure random tokens
# ---------------------------------------------------------------------------

_VERIFICATION_TOKEN_EXPIRE_MINUTES = 15


def generate_secure_token(length: int = 32) -> str:
    """Generate a cryptographically secure random token string (hex).

    The returned token is *length* bytes encoded as hex characters, so the
    string will be ``2 * length`` characters long.
    """
    return secrets.token_hex(length)


def generate_verification_token(subject: str) -> str:
    """Generate a signed JWT token for email verification (15 min expiry).

    Uses :func:`create_access_token` with a ``type: "email_verify"`` claim
    so the token can be distinguished from regular access tokens.

    Parameters
    ----------
    subject
        The user's unique identifier (user_id) to embed in the token.

    Returns
    -------
    str
        The encoded JWT string.
    """
    return create_access_token(
        subject=subject,
        extra_claims={"type": "email_verify"},
        expires_delta_minutes=_VERIFICATION_TOKEN_EXPIRE_MINUTES,
    )


def verify_verification_token(token: str) -> str | None:
    """Verify an email verification JWT token.

    Returns the user_id (the ``sub`` claim) if valid, or ``None`` if the
    token is invalid, expired, or not an email-verify token.
    """
    try:
        payload = jwt.decode(
            token,
            _JWT_SECRET_KEY,
            algorithms=[_JWT_ALGORITHM],
        )
        if payload.get("type") != "email_verify":
            return None
        return payload.get("sub")
    except (JWTError, ExpiredSignatureError):
        return None


# ---------------------------------------------------------------------------
# TOTP / 2FA  (pyotp)
# ---------------------------------------------------------------------------


def generate_totp_secret() -> str:
    """Generate a new TOTP secret encoded in base32.

    Returns the secret string suitable for storing alongside the user record.
    """
    return pyotp.random_base32()


def get_totp_provisioning_uri(
    secret: str,
    email: str,
    issuer: str = "VeloBid",
) -> str:
    """Generate an ``otpauth://`` provisioning URI for QR-code display.

    Parameters
    ----------
    secret
        The TOTP secret (base32 string).
    email
        The user's email address (used as the label).
    issuer
        The issuer name shown in authenticator apps.

    Returns
    -------
    str
        A ``otpauth://totp/...`` URI.
    """
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=email, issuer_name=issuer)


def get_totp_qr_svg_base64(provisioning_uri: str) -> str | None:
    """Generate a QR code SVG and return it as a base64-encoded data URI.

    Parameters
    ----------
    provisioning_uri
        The ``otpauth://`` URI returned by :func:`get_totp_provisioning_uri`.

    Returns
    -------
    str
        A base64-encoded string suitable for embedding in an ``<img>`` tag
        (``data:image/svg+xml;base64,...``), or ``None`` if generation fails.
    """
    try:
        qr = qrcode.make(provisioning_uri, image_factory=SvgPathImage)
        buf = io.BytesIO()
        qr.save(buf)
        buf.seek(0)
        svg_bytes = buf.getvalue()
        encoded = base64.b64encode(svg_bytes).decode("ascii")
        return f"data:image/svg+xml;base64,{encoded}"
    except Exception:
        return None


def verify_totp_code(secret: str, code: str) -> bool:
    """Validate a TOTP code against a secret.

    Parameters
    ----------
    secret
        The TOTP secret (base32 string).
    code
        The 6-digit code provided by the authenticator app.

    Returns
    -------
    bool
        ``True`` if the code is valid, ``False`` otherwise.
    """
    if not secret or not code:
        return False
    try:
        totp = pyotp.TOTP(secret)
        return totp.verify(code)
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Recovery codes
# ---------------------------------------------------------------------------


def _generate_readable_code() -> str:
    """Create a single readable recovery code in the form ``velobid-XXXX-XXXX``."""
    part1 = secrets.token_hex(3).upper()
    part2 = secrets.token_hex(3).upper()
    return f"velobid-{part1}-{part2}"


def generate_recovery_codes(count: int = 8) -> list[str]:
    """Generate *count* one-time recovery codes.

    Each code is a readable string prefixed with ``velobid-`` (e.g.
    ``velobid-A1B2C3-D4E5F6``).  These codes should be stored as hashed
    values and presented to the user exactly once.

    Parameters
    ----------
    count
        How many codes to generate (default 8).

    Returns
    -------
    list[str]
        A list of recovery code strings.
    """
    return [_generate_readable_code() for _ in range(count)]
