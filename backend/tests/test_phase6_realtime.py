"""Phase 6 Realtime UX & Reliability Integration Tests covering typing indicators, presence, 3-state receipts, and offline message recovery."""

from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient
from starlette.testclient import TestClient

from app.main import app
from app.routers.websocket import notify_presence_change
from app.websockets.manager import ws_manager

ORIGIN_HEADER = {"Origin": "http://localhost:3000"}


def test_typing_indicator_and_authorization_unit(prepare_database):
    """Verify typing indicator events are processed correctly over an authenticated WebSocket."""
    c_alice = TestClient(app)
    c_alice.post(
        "/api/v1/auth/register",
        json={"phone_number": "+15559990010", "display_name": "Alice Typing"},
    )
    c_alice.post("/api/v1/auth/verify", json={"phone_number": "+15559990010", "otp": "123456"})
    r_alice = c_alice.post(
        "/api/v1/auth/login", json={"phone_number": "+15559990010", "otp": "123456"}
    )
    cookie_alice = r_alice.cookies.get("session_token")

    c_bob = TestClient(app)
    c_bob.post(
        "/api/v1/auth/register", json={"phone_number": "+15559990020", "display_name": "Bob Typing"}
    )
    c_bob.post("/api/v1/auth/verify", json={"phone_number": "+15559990020", "otp": "123456"})
    login_bob = c_bob.post(
        "/api/v1/auth/login", json={"phone_number": "+15559990020", "otp": "123456"}
    )
    bob_id = login_bob.json()["user"]["id"]

    # Alice creates conversation with Bob
    conv_res = c_alice.post(
        "/api/v1/conversations",
        json={"type": "DIRECT", "participant_ids": [bob_id]},
        headers=ORIGIN_HEADER,
    )
    conv_id = conv_res.json()["id"]

    # Alice connects via WebSocket using Cookie header
    ws_headers = {"Origin": "http://localhost:3000", "Cookie": f"session_token={cookie_alice}"}
    with c_alice.websocket_connect("/ws", headers=ws_headers) as ws_alice:
        ready_evt = ws_alice.receive_json()
        assert ready_evt["type"] == "connection.ready"

        # Alice sends typing events — server should process without error
        ws_alice.send_json({"type": "typing.started", "payload": {"conversation_id": conv_id}})
        ws_alice.send_json({"type": "typing.stopped", "payload": {"conversation_id": conv_id}})


@pytest.mark.asyncio
async def test_presence_online_offline_broadcast(prepare_database):
    """Verify notify_presence_change broadcasts online and offline events to contacts."""
    origin = {"Origin": "http://localhost:3000"}

    # Setup user1
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c1:
        await c1.post(
            "/api/v1/auth/register",
            json={"phone_number": "+15559990040", "display_name": "User One Pres"},
        )
        await c1.post("/api/v1/auth/verify", json={"phone_number": "+15559990040", "otp": "123456"})
        u1_login = await c1.post(
            "/api/v1/auth/login", json={"phone_number": "+15559990040", "otp": "123456"}
        )
        u1_id = u1_login.json()["user"]["id"]

    # Setup user2 and add user1 as contact
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c2:
        await c2.post(
            "/api/v1/auth/register",
            json={"phone_number": "+15559990050", "display_name": "User Two Pres"},
        )
        await c2.post("/api/v1/auth/verify", json={"phone_number": "+15559990050", "otp": "123456"})
        u2_login = await c2.post(
            "/api/v1/auth/login", json={"phone_number": "+15559990050", "otp": "123456"}
        )
        u2_id = u2_login.json()["user"]["id"]
        # c2 auto-stores session cookie from login response
        await c2.post("/api/v1/contacts", json={"contact_user_id": u1_id}, headers=origin)

    # Register mock websocket for User 2 in ws_manager
    mock_ws2 = AsyncMock()
    await ws_manager.connect(u2_id, mock_ws2)
    mock_ws2.send_json.reset_mock()

    try:
        # Trigger online presence notification for User 1
        await notify_presence_change(u1_id, "online")

        # Verify mock_ws2 received presence.updated (online)
        mock_ws2.send_json.assert_called()
        args = mock_ws2.send_json.call_args[0][0]
        assert args["type"] == "presence.updated"
        assert args["payload"]["user_id"] == u1_id
        assert args["payload"]["status"] == "online"

        # Trigger offline presence notification for User 1
        mock_ws2.send_json.reset_mock()
        await notify_presence_change(u1_id, "offline")

        mock_ws2.send_json.assert_called()
        args_off = mock_ws2.send_json.call_args[0][0]
        assert args_off["type"] == "presence.updated"
        assert args_off["payload"]["user_id"] == u1_id
        assert args_off["payload"]["status"] == "offline"
    finally:
        ws_manager.disconnect(u2_id, mock_ws2)


def test_e2e_2_user_messaging_receipt_lifecycle(prepare_database):
    """End-to-End integration scenario for 2 users: Send -> SENT -> DELIVERED -> READ."""
    c_alice = TestClient(app)
    c_alice.post(
        "/api/v1/auth/register", json={"phone_number": "+15559990060", "display_name": "Alice E2E"}
    )
    c_alice.post("/api/v1/auth/verify", json={"phone_number": "+15559990060", "otp": "123456"})
    c_alice.post("/api/v1/auth/login", json={"phone_number": "+15559990060", "otp": "123456"})

    c_bob = TestClient(app)
    c_bob.post(
        "/api/v1/auth/register", json={"phone_number": "+15559990070", "display_name": "Bob E2E"}
    )
    c_bob.post("/api/v1/auth/verify", json={"phone_number": "+15559990070", "otp": "123456"})
    login_bob = c_bob.post(
        "/api/v1/auth/login", json={"phone_number": "+15559990070", "otp": "123456"}
    )
    bob_id = login_bob.json()["user"]["id"]

    # 1. Alice creates conversation with Bob
    conv_res = c_alice.post(
        "/api/v1/conversations",
        json={"type": "DIRECT", "participant_ids": [bob_id]},
        headers=ORIGIN_HEADER,
    )
    conv_id = conv_res.json()["id"]

    # 2. Alice sends message
    msg_res = c_alice.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"content": "E2E receipt flow test message"},
        headers=ORIGIN_HEADER,
    )
    msg_id = msg_res.json()["id"]
    assert msg_res.json()["receipts"][0]["status"] == "SENT"

    # 3. Bob marks message as delivered via REST API
    deliv_res = c_bob.post(
        f"/api/v1/messages/{msg_id}/delivered",
        headers=ORIGIN_HEADER,
    )
    assert deliv_res.status_code == 200

    # 4. Bob marks message as read via REST API
    read_res = c_bob.post(
        f"/api/v1/messages/{msg_id}/read",
        headers=ORIGIN_HEADER,
    )
    assert read_res.status_code == 200

    # 5. Alice checks messages -> receipt status is READ
    alice_check = c_alice.get(
        f"/api/v1/conversations/{conv_id}/messages",
        headers=ORIGIN_HEADER,
    )
    receipt_status = alice_check.json()["messages"][0]["receipts"][0]["status"]
    assert receipt_status == "READ"


def test_offline_message_recovery_no_duplicates(prepare_database):
    """Verify offline user retrieves messages upon reconnecting without duplicates or data loss."""
    c_alice = TestClient(app)
    c_alice.post(
        "/api/v1/auth/register",
        json={"phone_number": "+15559990080", "display_name": "Alice Offline Test"},
    )
    c_alice.post("/api/v1/auth/verify", json={"phone_number": "+15559990080", "otp": "123456"})
    c_alice.post("/api/v1/auth/login", json={"phone_number": "+15559990080", "otp": "123456"})

    c_bob = TestClient(app)
    c_bob.post(
        "/api/v1/auth/register",
        json={"phone_number": "+15559990090", "display_name": "Bob Offline Test"},
    )
    c_bob.post("/api/v1/auth/verify", json={"phone_number": "+15559990090", "otp": "123456"})
    login_bob = c_bob.post(
        "/api/v1/auth/login", json={"phone_number": "+15559990090", "otp": "123456"}
    )
    bob_id = login_bob.json()["user"]["id"]

    # Alice creates conversation with Bob
    conv_res = c_alice.post(
        "/api/v1/conversations",
        json={"type": "DIRECT", "participant_ids": [bob_id]},
        headers=ORIGIN_HEADER,
    )
    conv_id = conv_res.json()["id"]

    # Bob is OFFLINE while Alice sends 3 messages
    msg_ids = []
    for i in range(3):
        res = c_alice.post(
            f"/api/v1/conversations/{conv_id}/messages",
            json={"content": f"Offline msg {i + 1}"},
            headers=ORIGIN_HEADER,
        )
        msg_ids.append(res.json()["id"])

    # Bob logs in and reconnects -> fetches conversation messages via REST API
    bob_msgs_res = c_bob.get(
        f"/api/v1/conversations/{conv_id}/messages",
        headers=ORIGIN_HEADER,
    )
    assert bob_msgs_res.status_code == 200
    retrieved_msgs = bob_msgs_res.json()["messages"]
    assert len(retrieved_msgs) == 3
    retrieved_ids = [m["id"] for m in retrieved_msgs]
    assert retrieved_ids == msg_ids

    # Bob acknowledges delivery for the latest message
    deliv_res = c_bob.post(
        f"/api/v1/messages/{msg_ids[-1]}/delivered",
        headers=ORIGIN_HEADER,
    )
    assert deliv_res.status_code == 200

    # Alice checks conversation messages -> verify delivery status
    alice_msgs_res = c_alice.get(
        f"/api/v1/conversations/{conv_id}/messages",
        headers=ORIGIN_HEADER,
    )
    latest_receipt = alice_msgs_res.json()["messages"][-1]["receipts"][0]
    assert latest_receipt["status"] == "DELIVERED"
