"""WebSocket router for real-time messaging using trusted Origin verification, presence updates, and typing indicators."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager, suppress
from urllib.parse import urlparse

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.base import utc_now
from app.models.user import User
from app.repositories.contact_repo import ContactRepository
from app.repositories.conversation_repo import ConversationRepository
from app.repositories.message_repo import MessageRepository
from app.repositories.session_repo import SessionRepository
from app.repositories.user_repo import UserRepository
from app.websockets.manager import ws_manager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websockets"])


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Helper context manager to obtain short-lived DB sessions in WebSocket handlers."""
    from app.main import app

    get_db_fn = app.dependency_overrides.get(get_db, get_db)
    try:
        async for db in get_db_fn():
            yield db
            break
    except BaseException:
        pass


async def notify_presence_change(user_id: str, status_str: str):
    """Notify contacts of user's presence state change and update last_seen_at timestamp using short-lived session."""
    try:
        async with get_db_session() as db:
            if db is None:
                return
            user_repo = UserRepository(db)
            user_obj = await user_repo.get_by_id(user_id)
            now_str = utc_now()
            if user_obj:
                user_obj.last_seen_at = now_str
                await db.commit()

            contact_repo = ContactRepository(db)
            conv_repo = ConversationRepository(db)

            added_by_users = await contact_repo.get_users_who_added_contact(user_id)
            saved_contacts = await contact_repo.get_user_contacts(user_id)
            saved_user_ids = [c.contact_user_id for c in saved_contacts]

            user_convs = await conv_repo.get_user_conversations(user_id)
            co_participants = [
                p.user_id for conv in user_convs for p in conv.participants if p.user_id != user_id
            ]

            target_user_ids = list(set(added_by_users + saved_user_ids + co_participants))
            if target_user_ids:
                await ws_manager.broadcast_to_participants(
                    participant_user_ids=target_user_ids,
                    event_type="presence.updated",
                    payload={
                        "user_id": user_id,
                        "status": status_str,
                        "last_seen_at": now_str,
                    },
                )
    except Exception as err:
        logger.warning("Failed to notify presence change for user_id=%s: %s", user_id, err)


async def authenticate_ws_session(session_token: str) -> User | None:
    """Validate active session token using a short-lived DB session."""
    try:
        async with get_db_session() as db:
            if db is None:
                return None
            session_repo = SessionRepository(db)
            return await session_repo.get_user_by_token(session_token)
    except Exception as err:
        logger.warning("Failed to authenticate WS session: %s", err)
        return None


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint protected by trusted Origin validation, presence updates, and typing indicators."""
    # 1. Validate Origin header against configured trusted frontend origins
    raw_origin = websocket.headers.get("origin")
    if not raw_origin:
        referer = websocket.headers.get("referer")
        if referer:
            parsed = urlparse(referer)
            if parsed.scheme and parsed.netloc:
                raw_origin = f"{parsed.scheme}://{parsed.netloc}"

    if not raw_origin:
        await websocket.close(code=4001, reason="Missing Origin header")
        return

    clean_origin = raw_origin.rstrip("/")
    allowed_origins = [o.rstrip("/") for o in settings.cors_origin_list]
    if clean_origin not in allowed_origins:
        await websocket.close(code=4001, reason="Untrusted Origin")
        return

    # 2. Extract session_token strictly from HTTP-only cookie
    session_token = websocket.cookies.get("session_token")
    if not session_token:
        await websocket.close(code=4001, reason="Authentication failed")
        return

    # 3. Validate active session and derive authenticated user
    user = await authenticate_ws_session(session_token)
    if not user:
        await websocket.close(code=4001, reason="Authentication failed")
        return

    user_id = user.id
    display_name = user.display_name
    was_online = ws_manager.is_user_online(user_id)
    await ws_manager.connect(user_id, websocket)

    # If first connection for this user, broadcast presence.updated ("online")
    if not was_online:
        await notify_presence_change(user_id, "online")

    try:
        while True:
            data = await websocket.receive_json()
            event_type = data.get("type")
            payload = data.get("payload", {})

            # 4. Handle delivery acknowledgment
            if event_type == "message.delivered":
                msg_id = payload.get("message_id")
                if msg_id:
                    async with get_db_session() as db:
                        if db is None:
                            continue
                        msg_repo = MessageRepository(db)
                        msg = await msg_repo.get_message_by_id(msg_id)
                        if msg:
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

            # 5. Handle typing.started
            elif event_type == "typing.started":
                conv_id = payload.get("conversation_id")
                if conv_id:
                    async with get_db_session() as db:
                        if db is None:
                            continue
                        conv_repo = ConversationRepository(db)
                        is_member = await conv_repo.is_participant(conv_id, user_id)
                        if is_member:
                            conv = await conv_repo.get_conversation_by_id(conv_id)
                            if conv:
                                participant_ids = [
                                    p.user_id
                                    for p in conv.participants
                                    if p.user_id != user_id and p.left_at is None
                                ]
                                await ws_manager.broadcast_to_participants(
                                    participant_user_ids=participant_ids,
                                    event_type="typing.started",
                                    payload={
                                        "conversation_id": conv_id,
                                        "user_id": user_id,
                                        "display_name": display_name,
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

            # 6. Handle typing.stopped
            elif event_type == "typing.stopped":
                conv_id = payload.get("conversation_id")
                if conv_id:
                    async with get_db_session() as db:
                        if db is None:
                            continue
                        conv_repo = ConversationRepository(db)
                        is_member = await conv_repo.is_participant(conv_id, user_id)
                        if is_member:
                            conv = await conv_repo.get_conversation_by_id(conv_id)
                            if conv:
                                participant_ids = [
                                    p.user_id
                                    for p in conv.participants
                                    if p.user_id != user_id and p.left_at is None
                                ]
                                await ws_manager.broadcast_to_participants(
                                    participant_user_ids=participant_ids,
                                    event_type="typing.stopped",
                                    payload={
                                        "conversation_id": conv_id,
                                        "user_id": user_id,
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
        if not ws_manager.is_user_online(user_id):
            with suppress(BaseException):
                await notify_presence_change(user_id, "offline")
    except BaseException:
        ws_manager.disconnect(user_id, websocket)
        if not ws_manager.is_user_online(user_id):
            with suppress(BaseException):
                await notify_presence_change(user_id, "offline")
