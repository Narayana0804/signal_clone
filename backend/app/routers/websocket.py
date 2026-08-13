"""WebSocket router for real-time messaging, delivery receipts, and presence updates."""

import hashlib
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.repositories.session_repo import SessionRepository
from app.websockets.manager import ws_manager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websockets"])


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Annotated[str | None, Query()] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,  # type: ignore[assignment]
):
    """WebSocket endpoint for real-time bi-directional events."""
    # Extract token from query parameter or session cookie
    raw_token = token or websocket.cookies.get("session_token")
    if not raw_token:
        logger.warning("WebSocket connection attempt missing token")
        await websocket.close(code=4001, reason="Authentication failed")
        return

    # Validate token against database
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    session_repo = SessionRepository(db)
    session = await session_repo.get_active_session_by_hash(token_hash)
    if not session:
        logger.warning("WebSocket connection attempt with invalid/expired token")
        await websocket.close(code=4001, reason="Authentication failed")
        return

    user_id = session.user_id
    await ws_manager.connect(user_id, websocket)

    try:
        while True:
            data = await websocket.receive_json()
            event_type = data.get("type")
            payload = data.get("payload", {})

            # Handle client-sent events if needed (e.g., message.delivered acknowledgment or typing)
            if event_type == "message.delivered":
                msg_id = payload.get("message_id")
                conv_id = payload.get("conversation_id")
                logger.debug(
                    "Received message.delivered ack for msg_id=%s conv_id=%s from user_id=%s",
                    msg_id,
                    conv_id,
                    user_id,
                )
            elif event_type in ("typing.started", "typing.stopped"):
                conv_id = payload.get("conversation_id")
                logger.debug(
                    "Received %s event for conv_id=%s from user_id=%s", event_type, conv_id, user_id
                )

    except WebSocketDisconnect:
        ws_manager.disconnect(user_id, websocket)
    except Exception as err:
        logger.warning("WebSocket error for user_id=%s: %s", user_id, err)
        ws_manager.disconnect(user_id, websocket)
