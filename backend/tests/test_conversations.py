"""Unit and integration tests for Conversations API."""

import pytest
from httpx import AsyncClient


async def create_and_verify_user(client: AsyncClient, phone: str, name: str) -> dict:
    """Helper fixture function to create, verify, and return user response."""
    await client.post("/api/v1/auth/register", json={"phone_number": phone, "display_name": name})
    await client.post("/api/v1/auth/verify", json={"phone_number": phone, "otp": "123456"})
    login_res = await client.post(
        "/api/v1/auth/login", json={"phone_number": phone, "otp": "123456"}
    )
    return login_res.json()["user"]


@pytest.mark.asyncio
async def test_unauthenticated_conversations_rejected(client: AsyncClient):
    """Verify unauthenticated requests to conversations endpoints return 401."""
    res_list = await client.get("/api/v1/conversations")
    assert res_list.status_code == 401

    res_create = await client.post(
        "/api/v1/conversations",
        json={"type": "DIRECT", "participant_ids": ["some-id"]},
    )
    assert res_create.status_code == 401


@pytest.mark.asyncio
async def test_empty_conversation_list(client: AsyncClient):
    """Verify newly authenticated user has empty conversation list."""
    await create_and_verify_user(client, "+15553000001", "User One")
    res = await client.get("/api/v1/conversations")
    assert res.status_code == 200
    assert res.json()["conversations"] == []


@pytest.mark.asyncio
async def test_direct_conversation_creation_and_duplication_reuse(client: AsyncClient):
    """Verify creating a direct conversation persists participants, and re-creation returns existing conversation."""
    alice = await create_and_verify_user(client, "+15553000010", "Alice Direct")

    await client.post("/api/v1/auth/logout")
    bob = await create_and_verify_user(client, "+15553000020", "Bob Direct")

    # Login back as Alice
    await client.post("/api/v1/auth/logout")
    await client.post(
        "/api/v1/auth/login", json={"phone_number": alice["phone_number"], "otp": "123456"}
    )

    # 1. Reject self-conversation -> 400 Bad Request
    res_self = await client.post(
        "/api/v1/conversations",
        json={"type": "DIRECT", "participant_ids": [alice["id"]]},
    )
    assert res_self.status_code == 400
    assert "yourself" in res_self.json()["detail"]

    # 2. Reject non-existent target user -> 404 Not Found
    res_invalid = await client.post(
        "/api/v1/conversations",
        json={"type": "DIRECT", "participant_ids": ["00000000-0000-0000-0000-000000000000"]},
    )
    assert res_invalid.status_code == 404

    # 3. Create DIRECT conversation with Bob -> 201 Created
    res_create = await client.post(
        "/api/v1/conversations",
        json={"type": "DIRECT", "participant_ids": [bob["id"]]},
    )
    assert res_create.status_code == 201
    conv = res_create.json()
    assert conv["type"] == "DIRECT"
    assert len(conv["participants"]) == 2
    assert conv["other_user"]["id"] == bob["id"]
    conv_id = conv["id"]

    # 4. Duplicate creation request between same pair -> 200 OK returning SAME conversation ID
    res_dup = await client.post(
        "/api/v1/conversations",
        json={"type": "DIRECT", "participant_ids": [bob["id"]]},
    )
    assert res_dup.status_code == 200
    assert res_dup.json()["id"] == conv_id

    # 5. Reverse creation request (Bob initiating with Alice) -> 200 OK returning SAME conversation ID
    await client.post("/api/v1/auth/logout")
    await client.post(
        "/api/v1/auth/login", json={"phone_number": bob["phone_number"], "otp": "123456"}
    )

    res_rev = await client.post(
        "/api/v1/conversations",
        json={"type": "DIRECT", "participant_ids": [alice["id"]]},
    )
    assert res_rev.status_code == 200
    assert res_rev.json()["id"] == conv_id


@pytest.mark.asyncio
async def test_conversation_authorization_and_retrieval(client: AsyncClient):
    """Verify only conversation participants can retrieve conversation details."""
    alice = await create_and_verify_user(client, "+15554000010", "Alice Auth")

    await client.post("/api/v1/auth/logout")
    bob = await create_and_verify_user(client, "+15554000020", "Bob Auth")

    await client.post("/api/v1/auth/logout")
    charlie = await create_and_verify_user(client, "+15554000030", "Charlie Outsider")

    # Login as Alice and create conversation with Bob
    await client.post("/api/v1/auth/logout")
    await client.post(
        "/api/v1/auth/login", json={"phone_number": alice["phone_number"], "otp": "123456"}
    )

    res_create = await client.post(
        "/api/v1/conversations",
        json={"type": "DIRECT", "participant_ids": [bob["id"]]},
    )
    conv_id = res_create.json()["id"]

    # Alice can retrieve details -> 200 OK
    res_alice = await client.get(f"/api/v1/conversations/{conv_id}")
    assert res_alice.status_code == 200

    # Bob can retrieve details -> 200 OK
    await client.post("/api/v1/auth/logout")
    await client.post(
        "/api/v1/auth/login", json={"phone_number": bob["phone_number"], "otp": "123456"}
    )

    res_bob = await client.get(f"/api/v1/conversations/{conv_id}")
    assert res_bob.status_code == 200

    # Charlie (non-participant) MUST be rejected -> 403 Forbidden
    await client.post("/api/v1/auth/logout")
    await client.post(
        "/api/v1/auth/login", json={"phone_number": charlie["phone_number"], "otp": "123456"}
    )

    res_charlie = await client.get(f"/api/v1/conversations/{conv_id}")
    assert res_charlie.status_code == 403
    assert "not a participant" in res_charlie.json()["detail"]


@pytest.mark.asyncio
async def test_contact_independence(client: AsyncClient):
    """Verify conversation creation does NOT require target to be in contacts list."""
    user1 = await create_and_verify_user(client, "+15555000010", "User One Indep")

    await client.post("/api/v1/auth/logout")
    user2 = await create_and_verify_user(client, "+15555000020", "User Two Indep")

    # Login as User 1 — note user2 is NOT added as a contact
    await client.post("/api/v1/auth/logout")
    await client.post(
        "/api/v1/auth/login", json={"phone_number": user1["phone_number"], "otp": "123456"}
    )

    res = await client.post(
        "/api/v1/conversations",
        json={"type": "DIRECT", "participant_ids": [user2["id"]]},
    )
    assert res.status_code == 201
    assert res.json()["other_user"]["id"] == user2["id"]
