"""Contact repository for database operations."""

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.contact import Contact


class ContactRepository:
    """Repository for managing Contact database entities."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_contacts(self, user_id: str) -> list[Contact]:
        """Get all contacts owned by user, with contact_user profile joined."""
        stmt = (
            select(Contact)
            .options(joinedload(Contact.contact_user))
            .where(Contact.user_id == user_id)
            .order_by(Contact.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_users_who_added_contact(self, contact_user_id: str) -> list[str]:
        """Get user IDs of all users who have saved contact_user_id as a contact."""
        stmt = select(Contact.user_id).where(Contact.contact_user_id == contact_user_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_contact_by_pair(self, user_id: str, contact_user_id: str) -> Contact | None:
        """Find contact relationship between user and contact_user."""
        stmt = select(Contact).where(
            (Contact.user_id == user_id) & (Contact.contact_user_id == contact_user_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, contact_id: str) -> Contact | None:
        """Find contact by ID."""
        stmt = (
            select(Contact)
            .options(joinedload(Contact.contact_user))
            .where(Contact.id == contact_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, user_id: str, contact_user_id: str) -> Contact:
        """Create a new contact relationship."""
        contact = Contact(
            user_id=user_id,
            contact_user_id=contact_user_id,
        )
        self.db.add(contact)
        await self.db.flush()
        # Fetch with joined contact_user relationship
        return await self.get_by_id(contact.id)  # type: ignore[return-value]

    async def delete(self, contact_id: str, user_id: str) -> bool:
        """Delete contact owned by user."""
        stmt = delete(Contact).where((Contact.id == contact_id) & (Contact.user_id == user_id))
        result = await self.db.execute(stmt)
        return result.rowcount > 0
