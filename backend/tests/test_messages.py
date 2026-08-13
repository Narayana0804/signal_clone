"""Unit and integration tests for Persistent Messaging, WebSockets Cookie Auth, and Receipt State Transitions."""

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
async def test_3_state_receipt_transitions(client: AsyncClient):
    """Verify SENT -> DELIVERED -> READ receipt transitions and authorization."""
    alice = await create_and_verify_user(client, "+15557000010", "Alice Receipt")

    await client.post("/api/v1/auth/logout")
    bob = await create_and_verify_user(client, "+15557000020", "Bob Receipt")

    # Login as Alice and send message
    await client.post("/api/v1/auth/logout")
    await client.post(
        "/api/v1/auth/login", json={"phone_number": alice["phone_number"], "otp": "123456"}
    )

    conv_res = await client.post(
        "/api/v1/conversations",
        json={"type": "DIRECT", "participant_ids": [bob["id"]]},
    )
    conv_id = conv_res.json()["id"]

    msg_res = await client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"content": "State transition test"},
    )
    msg_id = msg_res.json()["id"]
    assert msg_res.json()["receipts"][0]["status"] == "SENT"

    # Bob logs in and acknowledges delivery -> DELIVERED
    await client.post("/api/v1/auth/logout")
    await client.post(
        "/api/v1/auth/login", json={"phone_number": bob["phone_number"], "otp": "123456"}
    )

    deliv_res = await client.post(f"/api/v1/messages/{msg_id}/delivered")
    assert deliv_res.status_code == 200

    # Verify status is now DELIVERED
    msgs_deliv = await client.get(f"/api/v1/conversations/{conv_id}/messages")
    target_receipt = msgs_deliv.json()["messages"][0]["receipts"][0]
    assert target_receipt["status"] == "DELIVERED"
    assert target_receipt["delivered_at"] is not None

    # Bob marks as read -> READ
    read_res = await client.post(f"/api/v1/messages/{msg_id}/read")
    assert read_res.status_code == 200

    msgs_read = await client.get(f"/api/v1/conversations/{conv_id}/messages")
    target_receipt_read = msgs_read.json()["messages"][0]["receipts"][0]
    assert target_receipt_read["status"] == "READ"
    assert target_receipt_read["read_at"] is not None


@pytest.mark.asyncio
async def test_deterministic_pagination_ordering(client: AsyncClient):
    """Verify deterministic pagination ordering and zero missing/duplicate items."""
    user1 = await create_and_verify_user(client, "+15558000010", "User One Pag")

    await client.post("/api/v1/auth/logout")
    user2 = await create_and_verify_user(client, "+15558000020", "User Two Pag")

    await client.post("/api/v1/auth/logout")
    await client.post(
        "/api/v1/auth/login", json={"phone_number": user1["phone_number"], "otp": "123456"}
    )

    conv_res = await client.post(
        "/api/v1/conversations",
        json={"type": "DIRECT", "participant_ids": [user2["id"]]},
    )
    conv_id = conv_res.json()["id"]

    # Send 5 messages
    sent_ids = []
    for i in range(5):
        res = await client.post(
            f"/api/v1/conversations/{conv_id}/messages",
            json={"content": f"Message {i + 1}"},
        )
        sent_ids.append(res.json()["id"])

    # Page 1: limit 3 (returns latest 3 messages: Message 3, 4, 5 in ASC order)
    p1 = await client.get(f"/api/v1/conversations/{conv_id}/messages?limit=3")
    assert p1.status_code == 200
    p1_data = p1.json()
    assert len(p1_data["messages"]) == 3
    assert p1_data["has_more"] is True
    first_msg_p1_id = p1_data["messages"][0]["id"]

    # Page 2: before=first_msg_p1_id, limit 3
    p2 = await client.get(
        f"/api/v1/conversations/{conv_id}/messages?before={first_msg_p1_id}&limit=3"
    )
    assert p2.status_code == 200
    p2_data = p2.json()
    assert len(p2_data["messages"]) == 2
    assert p2_data["has_more"] is False

    # Combine IDs and ensure zero duplicates and 100% complete coverage
    all_retrieved_ids = [m["id"] for m in p2_data["messages"]] + [
        m["id"] for m in p1_data["messages"]
    ]
    assert len(all_retrieved_ids) == 5
    assert len(set(all_retrieved_ids)) == 5
    assert all_retrieved_ids == sent_ids
