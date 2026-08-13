"""Contact business logic service."""

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contact import Contact
from app.repositories.contact_repo import ContactRepository
from app.repositories.user_repo import UserRepository


class ContactService:
    """Service encapsulating contact management business rules."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.contact_repo = ContactRepository(db)
        self.user_repo = UserRepository(db)

    async def get_user_contacts(self, user_id: str) -> list[Contact]:
        """Get list of contacts owned by user."""
        return await self.contact_repo.get_user_contacts(user_id)

    async def add_contact(self, user_id: str, contact_user_id: str) -> Contact:
        """Add a target user as a contact with validation."""
        target_id = contact_user_id.strip()

        # 1. Self contact check
        if target_id == user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot add yourself as a contact",
            )

        # 2. Target user existence check
        target_user = await self.user_repo.get_by_id(target_id)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        # 3. Duplicate relationship check
        existing = await self.contact_repo.get_contact_by_pair(user_id, target_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User is already in your contacts",
            )

        # 4. Create contact relationship
        contact = await self.contact_repo.create(user_id, target_id)
        return contact

    async def remove_contact(self, contact_id: str, user_id: str) -> None:
        """Remove a contact owned by user with ownership validation."""
        deleted = await self.contact_repo.delete(contact_id, user_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contact not found or does not belong to you",
            )
