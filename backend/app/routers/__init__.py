"""Router package barrel export."""

from app.routers.auth import router as auth_router
from app.routers.contacts import router as contacts_router
from app.routers.conversations import router as conversations_router
from app.routers.health import router as health_router
from app.routers.messages import router as messages_router
from app.routers.users import router as users_router
from app.routers.websocket import router as websocket_router

__all__ = [
    "auth_router",
    "contacts_router",
    "conversations_router",
    "health_router",
    "messages_router",
    "users_router",
    "websocket_router",
]
