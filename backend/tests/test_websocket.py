"""Real WebSocket integration tests covering Origin protection, cookie auth, and conversation authorization."""

import pytest
from starlette.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.main import app


def test_websocket_origin_and_cookie_auth():
    """Verify WebSocket handshake requirements: trusted Origin + valid session cookie."""
    client = TestClient(app)

    # 1. Register & verify user to obtain session cookie
    phone = "+15559000010"
    client.post("/api/v1/auth/register", json={"phone_number": phone, "display_name": "WS User"})
    client.post("/api/v1/auth/verify", json={"phone_number": phone, "otp": "123456"})
    login_res = client.post("/api/v1/auth/login", json={"phone_number": phone, "otp": "123456"})
    session_cookie = login_res.cookies.get("session_token")
    user_id = login_res.json()["user"]["id"]

    # 1. Valid session cookie + trusted Origin -> Connection ACCEPTED
    with client.websocket_connect(
        "/ws",
        headers={"Origin": "http://localhost:3000"},
    ) as websocket:
        data = websocket.receive_json()
        assert data["type"] == "connection.ready"
        assert data["payload"]["user_id"] == user_id

    # 2. Missing session cookie -> WebSocketDisconnect code 4001
    c2 = TestClient(app)
    with (
        pytest.raises(WebSocketDisconnect) as exc2,
        c2.websocket_connect(
            "/ws",
            headers={"Origin": "http://localhost:3000"},
        ) as ws2,
    ):
        ws2.receive_json()
    assert exc2.value.code == 4001

    # 3. Invalid session cookie -> WebSocketDisconnect code 4001
    c3 = TestClient(app)
    c3.cookies.set("session_token", "invalid-token-xyz")
    with (
        pytest.raises(WebSocketDisconnect) as exc3,
        c3.websocket_connect(
            "/ws",
            headers={"Origin": "http://localhost:3000"},
        ) as ws3,
    ):
        ws3.receive_json()
    assert exc3.value.code == 4001

    # 4. Untrusted Origin -> WebSocketDisconnect code 4001
    c4 = TestClient(app)
    c4.cookies.set("session_token", session_cookie)
    with (
        pytest.raises(WebSocketDisconnect) as exc4,
        c4.websocket_connect(
            "/ws",
            headers={"Origin": "http://malicious-attacker-site.com"},
        ) as ws4,
    ):
        ws4.receive_json()
    assert exc4.value.code == 4001

    # 5. Missing Origin -> WebSocketDisconnect code 4001
    c5 = TestClient(app)
    c5.cookies.set("session_token", session_cookie)
    with (
        pytest.raises(WebSocketDisconnect) as exc5,
        c5.websocket_connect(
            "/ws",
        ) as ws5,
    ):
        ws5.receive_json()
    assert exc5.value.code == 4001


def test_websocket_unauthorized_conversation_action():
    """Verify an authenticated WebSocket user cannot perform actions on conversations they do not participate in."""
    # Register Alice
    c_alice = TestClient(app)
    c_alice.post(
        "/api/v1/auth/register", json={"phone_number": "+15559000020", "display_name": "Alice WS"}
    )
    c_alice.post("/api/v1/auth/verify", json={"phone_number": "+15559000020", "otp": "123456"})
    c_alice.post("/api/v1/auth/login", json={"phone_number": "+15559000020", "otp": "123456"})

    # Register Bob
    c_bob = TestClient(app)
    c_bob.post(
        "/api/v1/auth/register", json={"phone_number": "+15559000030", "display_name": "Bob WS"}
    )
    c_bob.post("/api/v1/auth/verify", json={"phone_number": "+15559000030", "otp": "123456"})
    login_bob = c_bob.post(
        "/api/v1/auth/login", json={"phone_number": "+15559000030", "otp": "123456"}
    )
    bob_id = login_bob.json()["user"]["id"]

    # Register Charlie (outsider)
    c_charlie = TestClient(app)
    c_charlie.post(
        "/api/v1/auth/register", json={"phone_number": "+15559000040", "display_name": "Charlie WS"}
    )
    c_charlie.post("/api/v1/auth/verify", json={"phone_number": "+15559000040", "otp": "123456"})
    c_charlie.post("/api/v1/auth/login", json={"phone_number": "+15559000040", "otp": "123456"})

    # Create Alice & Bob conversation + send message
    conv_res = c_alice.post(
        "/api/v1/conversations",
        json={"type": "DIRECT", "participant_ids": [bob_id]},
        headers={"Origin": "http://localhost:3000"},
    )
    conv_id = conv_res.json()["id"]

    msg_res = c_alice.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"content": "Alice secret message"},
        headers={"Origin": "http://localhost:3000"},
    )
    msg_id = msg_res.json()["id"]

    # Charlie (outsider) connects via WebSocket and attempts to acknowledge delivery of Alice's message
    with c_charlie.websocket_connect(
        "/ws",
        headers={"Origin": "http://localhost:3000"},
    ) as charlie_ws:
        charlie_ws.receive_json()  # connection.ready

        # Send unauthorized message.delivered ack
        charlie_ws.send_json(
            {
                "type": "message.delivered",
                "payload": {"message_id": msg_id, "conversation_id": conv_id},
            }
        )
        err_msg = charlie_ws.receive_json()
        assert err_msg["type"] == "error"
        assert err_msg["payload"]["code"] == "UNAUTHORIZED"
