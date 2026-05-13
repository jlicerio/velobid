"""Tests for auth/signup Pydantic schemas."""

import pytest
from pydantic import ValidationError

from api.schemas.auth import SignupStartRequest


class TestSignupStartRequest:
    """Validate the SignupStartRequest schema constraints."""

    VALID_PAYLOAD = {
        "company_name": "Test Corp",
        "primary_contact": "Jane Doe",
        "admin_email": "jane@testcorp.com",
        "password": "securePass123",
        "accept_terms": True,
    }

    def test_valid_payload(self):
        """A well-formed payload should pass validation."""
        req = SignupStartRequest(**self.VALID_PAYLOAD)
        assert req.company_name == "Test Corp"
        assert req.primary_contact == "Jane Doe"
        assert req.admin_email == "jane@testcorp.com"
        assert req.password == "securePass123"
        assert req.accept_terms is True
        assert req.cf_turnstile_token is None  # optional, defaults to None
        assert req.phone is None
        assert req.location is None

    def test_terms_required(self):
        """accept_terms=False must raise a validation error."""
        payload = {**self.VALID_PAYLOAD, "accept_terms": False}
        with pytest.raises(ValidationError) as exc:
            SignupStartRequest(**payload)
        errors = exc.value.errors()
        assert any("terms of service" in e["msg"].lower() for e in errors)

    def test_terms_missing(self):
        """accept_terms not provided must raise a validation error."""
        payload = {k: v for k, v in self.VALID_PAYLOAD.items() if k != "accept_terms"}
        with pytest.raises(ValidationError) as exc:
            SignupStartRequest(**payload)
        errors = exc.value.errors()
        assert any("accept_terms" in e["loc"] for e in errors)

    def test_invalid_email(self):
        """An invalid email must be rejected."""
        payload = {**self.VALID_PAYLOAD, "admin_email": "not-an-email"}
        with pytest.raises(ValidationError) as exc:
            SignupStartRequest(**payload)
        errors = exc.value.errors()
        assert any("email" in e["msg"].lower() for e in errors)

    def test_short_password(self):
        """Password shorter than 8 characters must be rejected."""
        payload = {**self.VALID_PAYLOAD, "password": "short"}
        with pytest.raises(ValidationError) as exc:
            SignupStartRequest(**payload)
        errors = exc.value.errors()
        assert any("8" in e["msg"] for e in errors)

    def test_long_password(self):
        """Password longer than 128 characters must be rejected."""
        payload = {**self.VALID_PAYLOAD, "password": "a" * 129}
        with pytest.raises(ValidationError) as exc:
            SignupStartRequest(**payload)
        errors = exc.value.errors()
        assert any("128" in e["msg"] for e in errors)

    def test_long_company_name(self):
        """Company name over 200 characters must be rejected."""
        payload = {**self.VALID_PAYLOAD, "company_name": "a" * 201}
        with pytest.raises(ValidationError) as exc:
            SignupStartRequest(**payload)
        errors = exc.value.errors()
        assert any("200" in e["msg"] for e in errors)

    def test_empty_required_fields(self):
        """All required fields must have at least 1 character."""
        for field in ("company_name", "primary_contact"):
            payload = {**self.VALID_PAYLOAD, field: ""}
            with pytest.raises(ValidationError) as exc:
                SignupStartRequest(**payload)
            errors = exc.value.errors()
            assert any(field in str(e["loc"]) for e in errors), f"{field} should be required"

    def test_optional_fields_default_to_none(self):
        """Optional fields phone and location should default to None."""
        req = SignupStartRequest(**self.VALID_PAYLOAD)
        assert req.phone is None
        assert req.location is None
        assert req.bidder_display_name is None

    def test_optional_fields_accepted(self):
        """Optional fields when provided should be accepted."""
        payload = {
            **self.VALID_PAYLOAD,
            "phone": "+1 (555) 123-4567",
            "location": "McAllen, TX",
            "bidder_display_name": "Test",
        }
        req = SignupStartRequest(**payload)
        assert req.phone == "+1 (555) 123-4567"
        assert req.location == "McAllen, TX"
        assert req.bidder_display_name == "Test"

    def test_cf_turnstile_token_optional(self):
        """Turnstile token should be optional (dev-mode)."""
        # Without token
        req = SignupStartRequest(**self.VALID_PAYLOAD)
        assert req.cf_turnstile_token is None

        # With token
        payload = {**self.VALID_PAYLOAD, "cf_turnstile_token": "0.abc123.xyz"}
        req = SignupStartRequest(**payload)
        assert req.cf_turnstile_token == "0.abc123.xyz"

    def test_cf_turnstile_token_max_length(self):
        """Turnstile token longer than 2048 must be rejected."""
        payload = {**self.VALID_PAYLOAD, "cf_turnstile_token": "t" * 2049}
        with pytest.raises(ValidationError) as exc:
            SignupStartRequest(**payload)
        errors = exc.value.errors()
        assert any("2048" in e["msg"] for e in errors)
