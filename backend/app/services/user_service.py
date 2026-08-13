"""User business logic service."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.user_repo import UserRepository


class UserService:
    """Service encapsulating user-related business rules."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)

    async def search_users(self, query: str, current_user_id: str, limit: int = 20) -> list[User]:
        """Search users by display name or phone number, excluding current user."""
        q = query.strip()
        if not q or len(q) < 2:
            return []

        # Bound limit between 1 and 50
        max_limit = min(max(1, limit), 50)
        return await self.user_repo.search_users(
            query=q,
            exclude_user_id=current_user_id,
            limit=max_limit,
        )
