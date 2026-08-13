"""Unit and integration tests for Persistent Messaging & WebSockets."""

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
async def test_message_authorization_send_and_retrieve(client: AsyncClient):
    """Verify message authorization semantics: participants can send/retrieve, outsiders get 403."""
    alice = await create_and_verify_user(client, "+15556000010", "Alice Msg")

    await client.post("/api/v1/auth/logout")
    bob = await create_and_verify_user(client, "+15556000020", "Bob Msg")

    await client.post("/api/v1/auth/logout")
    charlie = await create_and_verify_user(client, "+15556000030", "Charlie Outsider Msg")

    # Login as Alice and create conversation with Bob
    await client.post("/api/v1/auth/logout")
    await client.post(
        "/api/v1/auth/login", json={"phone_number": alice["phone_number"], "otp": "123456"}
    )

    conv_res = await client.post(
        "/api/v1/conversations",
        json={"type": "DIRECT", "participant_ids": [bob["id"]]},
    )
    conv_id = conv_res.json()["id"]

    # 1. Unauthenticated send rejected -> 401
    await client.post("/api/v1/auth/logout")
    unauth_send = await client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"content": "Unauthenticated test"},
    )
    assert unauth_send.status_code == 401

    # 2. Charlie (non-participant) send rejected -> 403
    await client.post(
        "/api/v1/auth/login", json={"phone_number": charlie["phone_number"], "otp": "123456"}
    )
    charlie_send = await client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"content": "I am an intruder!"},
    )
    assert charlie_send.status_code == 403
    assert "not a participant" in charlie_send.json()["detail"]

    # 3. Charlie (non-participant) retrieval rejected -> 403
    charlie_get = await client.get(f"/api/v1/conversations/{conv_id}/messages")
    assert charlie_get.status_code == 403

    # 4. Alice (participant) sends message -> 201 Created
    await client.post("/api/v1/auth/logout")
    await client.post(
        "/api/v1/auth/login", json={"phone_number": alice["phone_number"], "otp": "123456"}
    )

    alice_send = await client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"content": "Hello Bob!", "client_id": "client-uuid-123"},
    )
    assert alice_send.status_code == 201
    msg_data = alice_send.json()
    assert msg_data["content"] == "Hello Bob!"
    assert msg_data["sender_id"] == alice["id"]
    assert msg_data["client_id"] == "client-uuid-123"
    assert len(msg_data["receipts"]) == 1
    assert msg_data["receipts"][0]["user_id"] == bob["id"]
    assert msg_data["receipts"][0]["status"] == "SENT"

    # 5. Bob (participant) retrieves message -> 200 OK
    await client.post("/api/v1/auth/logout")
    await client.post(
        "/api/v1/auth/login", json={"phone_number": bob["phone_number"], "otp": "123456"}
    )

    bob_get = await client.get(f"/api/v1/conversations/{conv_id}/messages")
    assert bob_get.status_code == 200
    msgs = bob_get.json()["messages"]
    assert len(msgs) == 1
    assert msgs[0]["content"] == "Hello Bob!"


@pytest.mark.asyncio
async def test_message_validation_and_read_receipts(client: AsyncClient):
    """Verify empty message validation and mark-as-read watermark functionality."""
    alice = await create_and_verify_user(client, "+15557000010", "Alice Read")

    await client.post("/api/v1/auth/logout")
    bob = await create_and_verify_user(client, "+15557000020", "Bob Read")

    # Login as Alice and create conversation with Bob
    await client.post("/api/v1/auth/logout")
    await client.post(
        "/api/v1/auth/login", json={"phone_number": alice["phone_number"], "otp": "123456"}
    )

    conv_res = await client.post(
        "/api/v1/conversations",
        json={"type": "DIRECT", "participant_ids": [bob["id"]]},
    )
    conv_id = conv_res.json()["id"]

    # Reject whitespace/empty content -> 400
    empty_send = await client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"content": "    "},
    )
    assert empty_send.status_code == 400

    # Alice sends message
    m1 = await client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"content": "First message"},
    )
    m1_id = m1.json()["id"]

    # Bob logs in and reads message -> 200
    await client.post("/api/v1/auth/logout")
    await client.post(
        "/api/v1/auth/login", json={"phone_number": bob["phone_number"], "otp": "123456"}
    )

    read_res = await client.post(f"/api/v1/messages/{m1_id}/read")
    assert read_res.status_code == 200
    assert read_res.json()["read_count"] >= 1

    # Verify conversation list unread count for Bob is now 0
    conv_list = await client.get("/api/v1/conversations")
    c_item = next(c for c in conv_list.json()["conversations"] if c["id"] == conv_id)
    assert c_item["unread_count"] == 0
    assert c_item["last_message"]["content"] == "First message"
