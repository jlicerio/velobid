"""Tests for Turnstile (Cloudflare) verification integration."""

import pytest

from api.services.security import verify_turnstile_token


@pytest.mark.asyncio
async def test_verify_turnstile_no_key_passthrough():
    """When TURNSTILE_SECRET_KEY is not set, verify_turnstile_token returns True."""
    result = await verify_turnstile_token(None)
    assert result is True


@pytest.mark.asyncio
async def test_verify_turnstile_no_key_with_token():
    """Without a key set, even a provided token passes (dev mode)."""
    result = await verify_turnstile_token("some-token")
    assert result is True
