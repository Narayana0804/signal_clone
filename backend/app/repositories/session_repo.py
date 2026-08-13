"""Session repository for database operations."""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.base import utc_now
from app.models.session import Session
from app.models.user import User


class SessionRepository:
    """Repository for managing authentication session entities."""

    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def hash_token(raw_token: str) -> str:
        """SHA-256 hash of a raw token."""
        return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    async def create_session(self, user_id: str) -> tuple[Session, str]:
        """Create a new session record and return (Session, raw_token)."""
        raw_token = secrets.token_urlsafe(32)
        token_hash = self.hash_token(raw_token)
        expires_at = (datetime.now(UTC) + timedelta(days=settings.session_expiry_days)).isoformat()

        session = Session(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self.db.add(session)
        await self.db.flush()
        return session, raw_token

    async def get_user_by_token(self, raw_token: str) -> User | None:
        """Find active non-expired user by raw session token."""
        token_hash = self.hash_token(raw_token)
        now_str = utc_now()

        stmt = (
            select(User)
            .join(Session, Session.user_id == User.id)
            .where(Session.token_hash == token_hash)
            .where(Session.expires_at > now_str)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_session_by_token(self, raw_token: str) -> bool:
        """Delete a session by raw token (logout)."""
        token_hash = self.hash_token(raw_token)
        stmt = delete(Session).where(Session.token_hash == token_hash)
        result = await self.db.execute(stmt)
        return result.rowcount > 0

    async def delete_user_sessions(self, user_id: str) -> int:
        """Delete all sessions for a user."""
        stmt = delete(Session).where(Session.user_id == user_id)
        result = await self.db.execute(stmt)
        return result.rowcount
