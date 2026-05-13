"""Regression tests for the auth login flow."""

from __future__ import annotations

import importlib

from api.schemas.auth import PendingSignup, UserStatus
from api.services import auth as auth_service
import api.services.security as security_module
from api.services.security import decode_token


def setup_function() -> None:
    auth_service._pending_signups.clear()


def teardown_function() -> None:
    auth_service._pending_signups.clear()


def test_active_user_with_2fa_gets_challenge_token(monkeypatch) -> None:
    password = "CorrectHorse7!"
    monkeypatch.setattr(
        auth_service,
        "verify_password",
        lambda plain_password, hashed_password: plain_password == password,
    )
    signup = PendingSignup(
        company_name="Test Company",
        bidder_display_name="Test",
        primary_contact="Jane Doe",
        admin_email="jane@example.com",
        password_hash="dummy-hash",
        phone=None,
        location=None,
        status=UserStatus.active,
        two_factor_enabled=True,
        totp_secret="JBSWY3DPEHPK3PXP",
        recovery_codes=["RECOVERY-1"],
    )
    auth_service._store_signup(signup)

    response = auth_service.login("jane@example.com", password)

    assert response.challenge_required is True
    assert response.challenge_type == "totp"
    assert response.temp_token
    assert response.access_token is None
    assert response.refresh_token is None
    assert response.user_id is None

    payload = decode_token(response.temp_token)
    assert payload["sub"] == signup.admin_user_id
    assert payload["type"] == "2fa_challenge"


def test_active_user_without_2fa_gets_tokens(monkeypatch) -> None:
    password = "CorrectHorse7!"
    monkeypatch.setattr(
        auth_service,
        "verify_password",
        lambda plain_password, hashed_password: plain_password == password,
    )
    signup = PendingSignup(
        company_name="Test Company",
        bidder_display_name="Test",
        primary_contact="Jane Doe",
        admin_email="jane@example.com",
        password_hash="dummy-hash",
        phone=None,
        location=None,
        status=UserStatus.active,
        two_factor_enabled=False,
    )
    auth_service._store_signup(signup)

    response = auth_service.login("jane@example.com", password)

    assert response.challenge_required is False
    assert response.access_token
    assert response.refresh_token
    assert response.user_id == signup.admin_user_id
    assert response.email == signup.admin_email


def test_jwt_secret_falls_back_to_legacy_env_var(monkeypatch) -> None:
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    monkeypatch.setenv("JWT_SECRET", "legacy-secret-for-test")

    security = importlib.reload(security_module)
    token = security.create_access_token("user-123")

    payload = decode_token(token)
    assert payload["sub"] == "user-123"

    monkeypatch.delenv("JWT_SECRET", raising=False)
    importlib.reload(security)
