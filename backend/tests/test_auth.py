"""Backend unit/integration tests for authentication endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_registration_and_auth_flow(client: AsyncClient):
    """Comprehensive test suite for authentication requirements."""
    phone = "+15550001111"
    display_name = "Alice Tester"

    # 1. Unauthenticated GET /auth/me -> 401 Unauthorized
    res = await client.get("/api/v1/auth/me")
    assert res.status_code == 401
    assert res.json()["detail"] == "Authentication required"

    # 2. Invalid registration (bad phone number format) -> 422
    res = await client.post(
        "/api/v1/auth/register",
        json={"phone_number": "invalid", "display_name": "Alice"},
    )
    assert res.status_code == 422

    # 3. Successful Registration -> 201 Created
    res = await client.post(
        "/api/v1/auth/register",
        json={"phone_number": phone, "display_name": display_name},
    )
    assert res.status_code == 201
    user_data = res.json()
    assert user_data["phone_number"] == phone
    assert user_data["display_name"] == display_name
    assert user_data["is_verified"] == 0
    user_id = user_data["id"]

    # 4. Duplicate Registration -> 409 Conflict
    res = await client.post(
        "/api/v1/auth/register",
        json={"phone_number": phone, "display_name": "Alice 2"},
    )
    assert res.status_code == 409

    # 5. Login before verification -> 400 Bad Request
    res = await client.post(
        "/api/v1/auth/login",
        json={"phone_number": phone, "otp": "123456"},
    )
    assert res.status_code == 400
    assert "not verified" in res.json()["detail"]

    # 6. Verify with invalid OTP -> 400 Bad Request
    res = await client.post(
        "/api/v1/auth/verify",
        json={"phone_number": phone, "otp": "999999"},
    )
    assert res.status_code == 400

    # 7. Successful OTP verification -> 200 OK
    res = await client.post(
        "/api/v1/auth/verify",
        json={"phone_number": phone, "otp": "123456"},
    )
    assert res.status_code == 200
    assert res.json()["verified"] is True

    # 8. Successful Login -> 200 OK, sets HTTP-only cookie
    res = await client.post(
        "/api/v1/auth/login",
        json={"phone_number": phone, "otp": "123456"},
    )
    assert res.status_code == 200
    auth_data = res.json()
    assert auth_data["user"]["id"] == user_id
    assert auth_data["user"]["is_verified"] == 1
    assert "token" in auth_data
    assert "session_token" in res.cookies

    # 9. Authenticated GET /auth/me using cookie session -> 200 OK
    res = await client.get("/api/v1/auth/me")
    assert res.status_code == 200
    me_data = res.json()
    assert me_data["id"] == user_id
    assert me_data["display_name"] == display_name

    # 10. PATCH /auth/me profile update -> 200 OK
    res = await client.patch(
        "/api/v1/auth/me",
        json={"about": "Hey there! I am using Signal.", "display_name": "Alice Smith"},
    )
    assert res.status_code == 200
    updated = res.json()
    assert updated["display_name"] == "Alice Smith"
    assert updated["about"] == "Hey there! I am using Signal."

    # 11. Logout -> 200 OK, deletes session from server and clears cookie
    res = await client.post("/api/v1/auth/logout")
    assert res.status_code == 200

    # 12. Authenticated request AFTER logout -> 401 Unauthorized (session invalidated)
    res = await client.get("/api/v1/auth/me")
    assert res.status_code == 401
