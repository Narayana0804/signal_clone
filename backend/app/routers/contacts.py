"""Contacts API router handlers."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.contact import (
    AddContactRequest,
    ContactListResponse,
    ContactResponse,
)
from app.schemas.user import UserResponse
from app.services.contact_service import ContactService

router = APIRouter(prefix="/api/v1/contacts", tags=["contacts"])


@router.get(
    "",
    response_model=ContactListResponse,
    summary="List current user's contacts",
)
async def list_contacts(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ContactListResponse:
    """Retrieve all contacts for the current user."""
    service = ContactService(db)
    contacts = await service.get_user_contacts(current_user.id)

    items = [
        ContactResponse(
            id=c.id,
            user=UserResponse.model_validate(c.contact_user),
            created_at=c.created_at,
        )
        for c in contacts
    ]
    return ContactListResponse(contacts=items)


@router.post(
    "",
    response_model=ContactResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a new contact",
)
async def add_contact(
    req: AddContactRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ContactResponse:
    """Add another user to contacts list."""
    service = ContactService(db)
    contact = await service.add_contact(
        user_id=current_user.id,
        contact_user_id=req.contact_user_id,
    )
    return ContactResponse(
        id=contact.id,
        user=UserResponse.model_validate(contact.contact_user),
        created_at=contact.created_at,
    )


@router.delete(
    "/{contact_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a contact",
)
async def remove_contact(
    contact_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Remove a contact from contacts list."""
    service = ContactService(db)
    await service.remove_contact(contact_id=contact_id, user_id=current_user.id)
