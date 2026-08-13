"""Router package barrel export."""

from app.routers.auth import router as auth_router
from app.routers.contacts import router as contacts_router
from app.routers.health import router as health_router
from app.routers.users import router as users_router

__all__ = [
    "auth_router",
    "contacts_router",
    "health_router",
    "users_router",
]
