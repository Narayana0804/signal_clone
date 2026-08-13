"""Tests for CSRF / Origin Protection Middleware."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_csrf_protection(client: AsyncClient):
    """Verify Origin header enforcement on cookie-authenticated state-changing requests."""
    phone = "+15559998888"
    await client.post(
        "/api/v1/auth/register",
        json={"phone_number": phone, "display_name": "CSRF Test User"},
    )
    await client.post(
        "/api/v1/auth/verify",
        json={"phone_number": phone, "otp": "123456"},
    )
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"phone_number": phone, "otp": "123456"},
    )
    assert login_res.status_code == 200
    assert "session_token" in client.cookies

    # 1. State-changing request with untrusted origin -> 403 Forbidden
    res_untrusted = await client.post(
        "/api/v1/auth/logout",
        headers={"origin": "http://evil-site.com"},
    )
    assert res_untrusted.status_code == 403
    assert "Untrusted request origin" in res_untrusted.json()["detail"]

    # 2. State-changing request with trusted origin -> 200 OK
    res_trusted = await client.post(
        "/api/v1/auth/logout",
        headers={"origin": "http://localhost:3000"},
    )
    assert res_trusted.status_code == 200
