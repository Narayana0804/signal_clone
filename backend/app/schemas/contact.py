"""Pydantic schemas for Contacts and User Search endpoints."""

from pydantic import BaseModel, Field

from app.schemas.user import UserResponse


class AddContactRequest(BaseModel):
    """Request schema for adding a contact."""

    contact_user_id: str = Field(..., min_length=1)


class ContactResponse(BaseModel):
    """Response schema for a single contact relationship."""

    id: str
    user: UserResponse
    created_at: str


class ContactListResponse(BaseModel):
    """Response schema for list of contacts."""

    contacts: list[ContactResponse]


class UserSearchResponse(BaseModel):
    """Response schema for user search results."""

    users: list[UserResponse]
