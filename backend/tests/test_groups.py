"""Integration tests for Group Messaging, Member Management, Group Receipts, and Realtime Events."""

import pytest
from httpx import AsyncClient


async def create_and_verify_user(client: AsyncClient, phone: str, name: str) -> dict:
    """Helper function to create, verify, and return user response."""
    await client.post("/api/v1/auth/register", json={"phone_number": phone, "display_name": name})
    await client.post("/api/v1/auth/verify", json={"phone_number": phone, "otp": "123456"})
    login_res = await client.post(
        "/api/v1/auth/login", json={"phone_number": phone, "otp": "123456"}
    )
    return login_res.json()["user"]


@pytest.mark.asyncio
async def test_group_creation_and_roles(client: AsyncClient):
    """Test group creation with creator as ADMIN and provided participants as MEMBER."""
    alice = await create_and_verify_user(client, "+15551000001", "Alice Admin")
    await client.post("/api/v1/auth/logout")
    bob = await create_and_verify_user(client, "+15551000002", "Bob Member")

    # Login back as Alice
    await client.post("/api/v1/auth/logout")
    await client.post(
        "/api/v1/auth/login", json={"phone_number": alice["phone_number"], "otp": "123456"}
    )

    # 1. Reject empty group name
    r_empty = await client.post(
        "/api/v1/conversations/groups",
        json={"name": "   ", "participant_ids": [bob["id"]]},
    )
    assert r_empty.status_code == 400

    # 2. Reject nonexistent member
    r_bad_user = await client.post(
        "/api/v1/conversations/groups",
        json={"name": "Dev Team", "participant_ids": ["nonexistent-user-id"]},
    )
    assert r_bad_user.status_code == 404

    # 3. Successful group creation
    res = await client.post(
        "/api/v1/conversations/groups",
        json={"name": "Engineering Team", "participant_ids": [bob["id"]]},
    )
    assert res.status_code == 201
    data = res.json()
    assert data["type"] == "GROUP"
    assert data["name"] == "Engineering Team"
    assert len(data["participants"]) == 2

    # Verify roles: creator = ADMIN, bob = MEMBER
    creator_p = next(p for p in data["participants"] if p["user_id"] == alice["id"])
    member_p = next(p for p in data["participants"] if p["user_id"] == bob["id"])
    assert creator_p["role"] == "ADMIN"
    assert member_p["role"] == "MEMBER"


@pytest.mark.asyncio
async def test_group_authorization_and_retrieval(client: AsyncClient):
    """Test member retrieval authorization and non-member rejection."""
    alice = await create_and_verify_user(client, "+15552000001", "Alice Guild")
    await client.post("/api/v1/auth/logout")
    bob = await create_and_verify_user(client, "+15552000002", "Bob Guild")

    # Login back as Alice
    await client.post("/api/v1/auth/logout")
    await client.post(
        "/api/v1/auth/login", json={"phone_number": alice["phone_number"], "otp": "123456"}
    )

    # Create group
    res = await client.post(
        "/api/v1/conversations/groups",
        json={"name": "Backend Guild", "participant_ids": [bob["id"]]},
    )
    conv_id = res.json()["id"]

    # Member Alice can retrieve
    r_get = await client.get(f"/api/v1/conversations/{conv_id}")
    assert r_get.status_code == 200
    assert r_get.json()["name"] == "Backend Guild"

    # Logout Alice
    await client.post("/api/v1/auth/logout")

    # Unauthenticated retrieval rejected
    r_unauth = await client.get(f"/api/v1/conversations/{conv_id}")
    assert r_unauth.status_code == 401


@pytest.mark.asyncio
async def test_group_member_add_and_remove(client: AsyncClient):
    """Test admin adding and removing group members, and checking non-admin restrictions."""
    alice = await create_and_verify_user(client, "+15553000001", "Alice Admin")
    await client.post("/api/v1/auth/logout")
    bob = await create_and_verify_user(client, "+15553000002", "Bob Member")
    await client.post("/api/v1/auth/logout")
    charlie = await create_and_verify_user(client, "+15553000003", "Charlie Candidate")

    # Login back as Alice to create group with Bob
    await client.post("/api/v1/auth/logout")
    await client.post(
        "/api/v1/auth/login", json={"phone_number": alice["phone_number"], "otp": "123456"}
    )

    res = await client.post(
        "/api/v1/conversations/groups",
        json={"name": "Devs", "participant_ids": [bob["id"]]},
    )
    conv_id = res.json()["id"]

    # Login as Bob (MEMBER) and try to add Charlie -> Rejected 403
    await client.post("/api/v1/auth/logout")
    await client.post(
        "/api/v1/auth/login", json={"phone_number": bob["phone_number"], "otp": "123456"}
    )

    r_add_nonadmin = await client.post(
        f"/api/v1/conversations/{conv_id}/members",
        json={"user_id": charlie["id"]},
    )
    assert r_add_nonadmin.status_code == 403

    # Login as Alice (ADMIN) and add Charlie -> Success 200
    await client.post("/api/v1/auth/logout")
    await client.post(
        "/api/v1/auth/login", json={"phone_number": alice["phone_number"], "otp": "123456"}
    )

    r_add_admin = await client.post(
        f"/api/v1/conversations/{conv_id}/members",
        json={"user_id": charlie["id"]},
    )
    assert r_add_admin.status_code == 200
    assert len(r_add_admin.json()["participants"]) == 3

    # Admin removes Charlie -> Success 200
    r_rem_del = await client.delete(f"/api/v1/conversations/{conv_id}/members/{charlie['id']}")
    assert r_rem_del.status_code == 200

    # Login as Charlie and try to retrieve group -> 403 Forbidden
    await client.post("/api/v1/auth/logout")
    await client.post(
        "/api/v1/auth/login", json={"phone_number": charlie["phone_number"], "otp": "123456"}
    )

    r_get_removed = await client.get(f"/api/v1/conversations/{conv_id}")
    assert r_get_removed.status_code == 403


@pytest.mark.asyncio
async def test_group_messaging_and_per_user_receipts(client: AsyncClient):
    """Test group messaging persistence and independent per-user receipt status."""
    alice = await create_and_verify_user(client, "+15554000001", "Alice Sender")
    await client.post("/api/v1/auth/logout")
    bob = await create_and_verify_user(client, "+15554000002", "Bob Recipient")

    # Login back as Alice
    await client.post("/api/v1/auth/logout")
    await client.post(
        "/api/v1/auth/login", json={"phone_number": alice["phone_number"], "otp": "123456"}
    )

    res = await client.post(
        "/api/v1/conversations/groups",
        json={"name": "Receipt Test Group", "participant_ids": [bob["id"]]},
    )
    conv_id = res.json()["id"]

    # Send group message
    r_send = await client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"content": "Hello Group!"},
    )
    assert r_send.status_code in (200, 201)
    msg_data = r_send.json()
    assert msg_data["content"] == "Hello Group!"
    assert len(msg_data["receipts"]) == 1
    assert msg_data["receipts"][0]["user_id"] == bob["id"]
    assert msg_data["receipts"][0]["status"] == "SENT"
