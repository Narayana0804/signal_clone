"""WebSocket router for real-time messaging using HTTP-only session cookie authentication."""

import hashlib
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.repositories.message_repo import MessageRepository
from app.repositories.session_repo import SessionRepository
from app.websockets.manager import ws_manager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websockets"])


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """WebSocket endpoint using HTTP-only session cookie authentication."""
    # Extract session_token strictly from HTTP-only cookie
    session_token = websocket.cookies.get("session_token")
    if not session_token:
        logger.warning("WebSocket connection rejected: missing session_token cookie")
        await websocket.close(code=4001, reason="Authentication failed")
        return

    # Hash token and validate active session in database
    token_hash = hashlib.sha256(session_token.encode("utf-8")).hexdigest()
    session_repo = SessionRepository(db)
    session = await session_repo.get_active_session_by_hash(token_hash)
    if not session:
        logger.warning("WebSocket connection rejected: invalid/expired session cookie")
        await websocket.close(code=4001, reason="Authentication failed")
        return

    user_id = session.user_id
    await ws_manager.connect(user_id, websocket)

    try:
        while True:
            data = await websocket.receive_json()
            event_type = data.get("type")
            payload = data.get("payload", {})

            # Handle client delivery acknowledgment
            if event_type == "message.delivered":
                msg_id = payload.get("message_id")
                if msg_id:
                    msg_repo = MessageRepository(db)
                    sender_id = await msg_repo.mark_message_delivered(
                        message_id=msg_id,
                        recipient_user_id=user_id,
                    )
                    await db.commit()

                    if sender_id and sender_id != user_id:
                        # Broadcast message.delivered event to the message sender
                        await ws_manager.broadcast_to_user(
                            user_id=sender_id,
                            event_type="message.delivered",
                            payload={
                                "message_id": msg_id,
                                "recipient_id": user_id,
                            },
                        )

    except WebSocketDisconnect:
        ws_manager.disconnect(user_id, websocket)
    except Exception as err:
        logger.warning("WebSocket error for user_id=%s: %s", user_id, err)
        ws_manager.disconnect(user_id, websocket)
