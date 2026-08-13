"""WebSocket router for real-time messaging using trusted Origin verification and HTTP-only session cookie authentication."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.repositories.conversation_repo import ConversationRepository
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
    """WebSocket endpoint protected by trusted Origin validation and HTTP-only session cookie authentication."""
    # 1. Validate Origin header against configured trusted frontend origins
    origin = websocket.headers.get("origin") or websocket.headers.get("referer")
    if not origin:
        logger.warning("WebSocket connection rejected: missing Origin header")
        await websocket.close(code=4001, reason="Missing Origin header")
        return

    clean_origin = origin.rstrip("/")
    allowed_origins = [o.rstrip("/") for o in settings.cors_origin_list]
    if clean_origin not in allowed_origins:
        logger.warning("WebSocket connection rejected: untrusted Origin '%s'", origin)
        await websocket.close(code=4001, reason="Untrusted Origin")
        return

    # 2. Extract session_token strictly from HTTP-only cookie
    session_token = websocket.cookies.get("session_token")
    if not session_token:
        logger.warning("WebSocket connection rejected: missing session_token cookie")
        await websocket.close(code=4001, reason="Authentication failed")
        return

    # 3. Validate active session and derive authenticated user
    session_repo = SessionRepository(db)
    user = await session_repo.get_user_by_token(session_token)
    if not user:
        logger.warning("WebSocket connection rejected: invalid/expired session cookie")
        await websocket.close(code=4001, reason="Authentication failed")
        return

    user_id = user.id
    await ws_manager.connect(user_id, websocket)

    try:
        while True:
            data = await websocket.receive_json()
            event_type = data.get("type")
            payload = data.get("payload", {})

            # Handle client delivery acknowledgment with server-side authorization check
            if event_type == "message.delivered":
                msg_id = payload.get("message_id")
                if msg_id:
                    msg_repo = MessageRepository(db)
                    msg = await msg_repo.get_message_by_id(msg_id)
                    if msg:
                        # Authorize: user must be a participant in the conversation
                        conv_repo = ConversationRepository(db)
                        is_member = await conv_repo.is_participant(msg.conversation_id, user_id)
                        if is_member:
                            sender_id = await msg_repo.mark_message_delivered(
                                message_id=msg_id,
                                recipient_user_id=user_id,
                            )
                            await db.commit()

                            if sender_id and sender_id != user_id:
                                await ws_manager.broadcast_to_user(
                                    user_id=sender_id,
                                    event_type="message.delivered",
                                    payload={
                                        "message_id": msg_id,
                                        "recipient_id": user_id,
                                    },
                                )
                        else:
                            await ws_manager.send_personal_event(
                                websocket,
                                "error",
                                {
                                    "code": "UNAUTHORIZED",
                                    "message": "Not a participant in this conversation",
                                    "original_type": event_type,
                                },
                            )

    except WebSocketDisconnect:
        ws_manager.disconnect(user_id, websocket)
    except Exception as err:
        logger.warning("WebSocket error for user_id=%s: %s", user_id, err)
        ws_manager.disconnect(user_id, websocket)
