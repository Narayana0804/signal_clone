"""Real WebSocket integration tests covering Origin protection, cookie auth, and conversation authorization."""

import pytest
from starlette.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.main import app


def _login_user(client: TestClient, phone: str, name: str) -> tuple[str, str]:
    """Register, verify, login a user. Returns (user_id, session_cookie)."""
    client.post("/api/v1/auth/register", json={"phone_number": phone, "display_name": name})
    client.post("/api/v1/auth/verify", json={"phone_number": phone, "otp": "123456"})
    login_res = client.post("/api/v1/auth/login", json={"phone_number": phone, "otp": "123456"})
    user_id = login_res.json()["user"]["id"]
    session_cookie = login_res.cookies.get("session_token")
    return user_id, session_cookie


def _ws_headers(origin: str, session_cookie: str | None = None) -> dict:
    """Build headers dict for websocket_connect with Origin and optional Cookie."""
    headers: dict[str, str] = {"Origin": origin}
    if session_cookie is not None:
        headers["Cookie"] = f"session_token={session_cookie}"
    return headers


def test_websocket_origin_and_cookie_auth(prepare_database):
    """Verify WebSocket handshake requirements: trusted Origin + valid session cookie."""
    client = TestClient(app)
    user_id, session_cookie = _login_user(client, "+15559000010", "WS User")
    assert session_cookie is not None

    # 1. Valid session cookie + trusted Origin -> Connection ACCEPTED
    with client.websocket_connect(
        "/ws",
        headers=_ws_headers("http://localhost:3000", session_cookie),
    ) as websocket:
        data = websocket.receive_json()
        assert data["type"] == "connection.ready"
        assert data["payload"]["user_id"] == user_id

    # 2. Missing session cookie -> WebSocketDisconnect code 4001
    with (
        pytest.raises(WebSocketDisconnect) as exc2,
        TestClient(app).websocket_connect(
            "/ws",
            headers=_ws_headers("http://localhost:3000"),
        ) as ws2,
    ):
        ws2.receive_json()
    assert exc2.value.code == 4001

    # 3. Invalid session cookie -> WebSocketDisconnect code 4001
    with (
        pytest.raises(WebSocketDisconnect) as exc3,
        TestClient(app).websocket_connect(
            "/ws",
            headers=_ws_headers("http://localhost:3000", "invalid-token-xyz"),
        ) as ws3,
    ):
        ws3.receive_json()
    assert exc3.value.code == 4001

    # 4. Untrusted Origin -> WebSocketDisconnect code 4001
    with (
        pytest.raises(WebSocketDisconnect) as exc4,
        TestClient(app).websocket_connect(
            "/ws",
            headers=_ws_headers("http://malicious-attacker-site.com", session_cookie),
        ) as ws4,
    ):
        ws4.receive_json()
    assert exc4.value.code == 4001

    # 5. Missing Origin -> WebSocketDisconnect code 4001
    with (
        pytest.raises(WebSocketDisconnect) as exc5,
        TestClient(app).websocket_connect(
            "/ws",
            headers={"Cookie": f"session_token={session_cookie}"},
        ) as ws5,
    ):
        ws5.receive_json()
    assert exc5.value.code == 4001


def test_websocket_unauthorized_conversation_action(prepare_database):
    """Verify an authenticated WebSocket user cannot perform actions on conversations they do not participate in."""
    ORIGIN = {"Origin": "http://localhost:3000"}

    c_alice = TestClient(app)
    _, cookie_alice = _login_user(c_alice, "+15559000020", "Alice WS")

    c_bob = TestClient(app)
    bob_id, _ = _login_user(c_bob, "+15559000030", "Bob WS")

    c_charlie = TestClient(app)
    _, cookie_charlie = _login_user(c_charlie, "+15559000040", "Charlie WS")

    # Create Alice & Bob conversation + send message
    conv_res = c_alice.post(
        "/api/v1/conversations",
        json={"type": "DIRECT", "participant_ids": [bob_id]},
        headers=ORIGIN,
    )
    conv_id = conv_res.json()["id"]

    msg_res = c_alice.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"content": "Alice secret message"},
        headers=ORIGIN,
    )
    msg_id = msg_res.json()["id"]

    # Charlie (outsider) connects via WebSocket and attempts unauthorized action
    with c_charlie.websocket_connect(
        "/ws",
        headers=_ws_headers("http://localhost:3000", cookie_charlie),
    ) as charlie_ws:
        charlie_ws.receive_json()  # connection.ready

        charlie_ws.send_json(
            {
                "type": "message.delivered",
                "payload": {"message_id": msg_id, "conversation_id": conv_id},
            }
        )
        err_msg = charlie_ws.receive_json()
        assert err_msg["type"] == "error"
        assert err_msg["payload"]["code"] == "UNAUTHORIZED"
