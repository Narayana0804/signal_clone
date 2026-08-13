"""Pydantic schemas for User models."""

from pydantic import BaseModel, ConfigDict, Field


class UserResponse(BaseModel):
    """User response schema."""

    id: str
    phone_number: str
    display_name: str
    avatar_url: str | None = None
    about: str = ""
    is_verified: int = 0
    created_at: str
    last_seen_at: str | None = None

    model_config = ConfigDict(from_attributes=True)


class UpdateProfileRequest(BaseModel):
    """Request schema for updating user profile."""

    display_name: str | None = Field(None, min_length=1, max_length=50)
    about: str | None = Field(None, max_length=140)
    avatar_url: str | None = Field(None, max_length=255)
