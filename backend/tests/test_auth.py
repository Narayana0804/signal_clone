"""Granular unit/integration tests for authentication endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_successful_registration(client: AsyncClient):
    """Verify registration creates an unverified user account."""
    res = await client.post(
        "/api/v1/auth/register",
        json={"phone_number": "+15551112222", "display_name": "Alice Tester"},
    )
    assert res.status_code == 201
    data = res.json()
    assert data["phone_number"] == "+15551112222"
    assert data["display_name"] == "Alice Tester"
    assert data["is_verified"] == 0
    assert "id" in data


@pytest.mark.asyncio
async def test_invalid_registration_phone_format(client: AsyncClient):
    """Verify registration rejects invalid phone number formats."""
    res = await client.post(
        "/api/v1/auth/register",
        json={"phone_number": "invalid-phone", "display_name": "Alice"},
    )
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_duplicate_registration_rejected(client: AsyncClient):
    """Verify duplicate phone registration returns 409 Conflict."""
    phone = "+15552223333"
    await client.post(
        "/api/v1/auth/register",
        json={"phone_number": phone, "display_name": "First User"},
    )
    res = await client.post(
        "/api/v1/auth/register",
        json={"phone_number": phone, "display_name": "Second User"},
    )
    assert res.status_code == 409
    assert "already registered" in res.json()["detail"]


@pytest.mark.asyncio
async def test_valid_otp_verification(client: AsyncClient):
    """Verify valid OTP ('123456') marks user as verified."""
    phone = "+15553334444"
    await client.post(
        "/api/v1/auth/register",
        json={"phone_number": phone, "display_name": "Bob"},
    )
    res = await client.post(
        "/api/v1/auth/verify",
        json={"phone_number": phone, "otp": "123456"},
    )
    assert res.status_code == 200
    assert res.json()["verified"] is True


@pytest.mark.asyncio
async def test_invalid_otp_verification_rejected(client: AsyncClient):
    """Verify invalid OTP ('999999') is rejected."""
    phone = "+15554445555"
    await client.post(
        "/api/v1/auth/register",
        json={"phone_number": phone, "display_name": "Charlie"},
    )
    res = await client.post(
        "/api/v1/auth/verify",
        json={"phone_number": phone, "otp": "999999"},
    )
    assert res.status_code == 400
    assert "Invalid OTP" in res.json()["detail"]


@pytest.mark.asyncio
async def test_unverified_login_rejected(client: AsyncClient):
    """Verify login is rejected for unverified users."""
    phone = "+15555556666"
    await client.post(
        "/api/v1/auth/register",
        json={"phone_number": phone, "display_name": "Dave"},
    )
    res = await client.post(
        "/api/v1/auth/login",
        json={"phone_number": phone, "otp": "123456"},
    )
    assert res.status_code == 400
    assert "not verified" in res.json()["detail"]


@pytest.mark.asyncio
async def test_login_invalid_otp_rejected(client: AsyncClient):
    """Verify login with wrong OTP is rejected."""
    phone = "+15556667777"
    await client.post(
        "/api/v1/auth/register",
        json={"phone_number": phone, "display_name": "Eve"},
    )
    await client.post(
        "/api/v1/auth/verify",
        json={"phone_number": phone, "otp": "123456"},
    )
    res = await client.post(
        "/api/v1/auth/login",
        json={"phone_number": phone, "otp": "000000"},
    )
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_successful_login_sets_cookie_without_exposing_token(client: AsyncClient):
    """Verify login issues HTTP-only cookie and does NOT return raw token in body."""
    phone = "+15557778888"
    await client.post(
        "/api/v1/auth/register",
        json={"phone_number": phone, "display_name": "Frank"},
    )
    await client.post(
        "/api/v1/auth/verify",
        json={"phone_number": phone, "otp": "123456"},
    )

    res = await client.post(
        "/api/v1/auth/login",
        json={"phone_number": phone, "otp": "123456"},
    )
    assert res.status_code == 200
    body = res.json()
    assert "user" in body
    assert "token" not in body  # Raw token must NOT be exposed in response body
    assert body["user"]["phone_number"] == phone
    assert "session_token" in res.cookies  # Cookie must be set


@pytest.mark.asyncio
async def test_get_me_authenticated(client: AsyncClient):
    """Verify GET /auth/me returns current user profile when session cookie is present."""
    phone = "+15558889999"
    await client.post(
        "/api/v1/auth/register",
        json={"phone_number": phone, "display_name": "Grace"},
    )
    await client.post(
        "/api/v1/auth/verify",
        json={"phone_number": phone, "otp": "123456"},
    )
    await client.post(
        "/api/v1/auth/login",
        json={"phone_number": phone, "otp": "123456"},
    )

    res = await client.get("/api/v1/auth/me")
    assert res.status_code == 200
    me = res.json()
    assert me["phone_number"] == phone
    assert me["display_name"] == "Grace"


@pytest.mark.asyncio
async def test_get_me_unauthenticated(client: AsyncClient):
    """Verify GET /auth/me returns 401 when no session cookie or token is provided."""
    res = await client.get("/api/v1/auth/me")
    assert res.status_code == 401
    assert res.json()["detail"] == "Authentication required"


@pytest.mark.asyncio
async def test_logout_invalidates_session_and_clears_cookie(client: AsyncClient):
    """Verify logout invalidates server session and clears session cookie."""
    phone = "+15559990000"
    await client.post(
        "/api/v1/auth/register",
        json={"phone_number": phone, "display_name": "Heidi"},
    )
    await client.post(
        "/api/v1/auth/verify",
        json={"phone_number": phone, "otp": "123456"},
    )
    await client.post(
        "/api/v1/auth/login",
        json={"phone_number": phone, "otp": "123456"},
    )

    # Confirm authenticated before logout
    res_before = await client.get("/api/v1/auth/me")
    assert res_before.status_code == 200

    # Logout
    res_logout = await client.post("/api/v1/auth/logout")
    assert res_logout.status_code == 200

    # Request after logout must fail
    res_after = await client.get("/api/v1/auth/me")
    assert res_after.status_code == 401


@pytest.mark.asyncio
async def test_patch_me_profile_success(client: AsyncClient):
    """Verify PATCH /auth/me updates display_name and about status."""
    phone = "+15550009999"
    await client.post(
        "/api/v1/auth/register",
        json={"phone_number": phone, "display_name": "Ivan"},
    )
    await client.post(
        "/api/v1/auth/verify",
        json={"phone_number": phone, "otp": "123456"},
    )
    await client.post(
        "/api/v1/auth/login",
        json={"phone_number": phone, "otp": "123456"},
    )

    res = await client.patch(
        "/api/v1/auth/me",
        json={"display_name": "Ivan Updated", "about": "Available for chat"},
    )
    assert res.status_code == 200
    updated = res.json()
    assert updated["display_name"] == "Ivan Updated"
    assert updated["about"] == "Available for chat"


@pytest.mark.asyncio
async def test_patch_me_unauthenticated(client: AsyncClient):
    """Verify PATCH /auth/me fails with 401 for unauthenticated requests."""
    res = await client.patch(
        "/api/v1/auth/me",
        json={"display_name": "Hacker"},
    )
    assert res.status_code == 401
