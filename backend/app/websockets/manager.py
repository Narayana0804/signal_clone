"""WebSocket Connection Manager handling real-time user connections and event broadcasts."""

import logging
import uuid
from typing import Any

from fastapi import WebSocket

from app.models.base import utc_now

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages active WebSocket connections per user ID."""

    def __init__(self):
        # Map user_id -> set of active WebSocket instances
        self.active_connections: dict[str, set[WebSocket]] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        """Accept WebSocket connection and register under user_id."""
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        logger.info(
            "WebSocket connected for user_id=%s (total active sockets: %d)",
            user_id,
            len(self.active_connections[user_id]),
        )

        # Send connection.ready event
        await self.send_personal_event(
            websocket,
            "connection.ready",
            {"user_id": user_id},
        )

    def disconnect(self, user_id: str, websocket: WebSocket):
        """Remove disconnected WebSocket from user's connection set."""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        logger.info("WebSocket disconnected for user_id=%s", user_id)

    def make_event_envelope(self, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Wrap payload into consistent WebSocket event envelope format."""
        return {
            "type": event_type,
            "event_id": str(uuid.uuid4()),
            "timestamp": utc_now(),
            "payload": payload,
        }

    async def send_personal_event(
        self, websocket: WebSocket, event_type: str, payload: dict[str, Any]
    ):
        """Send an event directly to a single WebSocket connection."""
        envelope = self.make_event_envelope(event_type, payload)
        try:
            await websocket.send_json(envelope)
        except Exception as err:
            logger.warning("Failed to send WebSocket event to connection: %s", err)

    async def broadcast_to_user(self, user_id: str, event_type: str, payload: dict[str, Any]):
        """Broadcast an event to all active WebSocket connections for a user."""
        if user_id not in self.active_connections:
            return

        envelope = self.make_event_envelope(event_type, payload)
        dead_sockets = set()
        for ws in self.active_connections[user_id]:
            try:
                await ws.send_json(envelope)
            except Exception as err:
                logger.warning("Failed to broadcast to user_id=%s: %s", user_id, err)
                dead_sockets.add(ws)

        for ws in dead_sockets:
            self.disconnect(user_id, ws)

    async def broadcast_to_participants(
        self,
        participant_user_ids: list[str],
        event_type: str,
        payload: dict[str, Any],
        exclude_user_id: str | None = None,
    ):
        """Broadcast an event to multiple participant user IDs."""
        for uid in participant_user_ids:
            if exclude_user_id and uid == exclude_user_id:
                continue
            await self.broadcast_to_user(uid, event_type, payload)


# Global singleton ConnectionManager instance
ws_manager = ConnectionManager()
