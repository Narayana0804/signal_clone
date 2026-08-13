"""User repository for database operations."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import utc_now
from app.models.user import User


class UserRepository:
    """Repository for managing User database entities."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: str) -> User | None:
        """Find user by UUID."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_phone(self, phone_number: str) -> User | None:
        """Find user by phone number."""
        result = await self.db.execute(select(User).where(User.phone_number == phone_number))
        return result.scalar_one_or_none()

    async def create(self, phone_number: str, display_name: str) -> User:
        """Create a new unverified user."""
        user = User(
            phone_number=phone_number,
            display_name=display_name,
            is_verified=0,
        )
        self.db.add(user)
        await self.db.flush()
        return user

    async def mark_verified(self, user: User) -> User:
        """Mark user as verified."""
        user.is_verified = 1
        user.updated_at = utc_now()
        await self.db.flush()
        return user

    async def update_profile(
        self,
        user: User,
        display_name: str | None = None,
        about: str | None = None,
        avatar_url: str | None = None,
    ) -> User:
        """Update user profile fields."""
        if display_name is not None:
            user.display_name = display_name
        if about is not None:
            user.about = about
        if avatar_url is not None:
            user.avatar_url = avatar_url
        user.updated_at = utc_now()
        await self.db.flush()
        return user

    async def update_last_seen(self, user: User) -> User:
        """Update user's last_seen_at timestamp."""
        user.last_seen_at = utc_now()
        await self.db.flush()
        return user

    async def search_users(self, query: str, exclude_user_id: str, limit: int = 20) -> list[User]:
        """Search users by display name or phone number, excluding current user."""
        pattern = f"%{query}%"
        stmt = (
            select(User)
            .where(User.id != exclude_user_id)
            .where((User.display_name.ilike(pattern)) | (User.phone_number.ilike(pattern)))
            .order_by(User.display_name.asc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
