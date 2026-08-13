"""Pydantic schemas for Conversation endpoints."""

from pydantic import BaseModel, Field

from app.schemas.user import UserResponse


class CreateConversationRequest(BaseModel):
    """Request schema for creating a new conversation."""

    type: str = Field("DIRECT", pattern=r"^(DIRECT|GROUP)$")
    name: str | None = Field(None, max_length=100)
    participant_ids: list[str] = Field(..., min_length=1)


class ParticipantResponse(BaseModel):
    """Response schema for a conversation participant."""

    id: str
    user_id: str
    role: str
    joined_at: str
    user: UserResponse


class LastMessagePreview(BaseModel):
    """Preview of the last message in a conversation (Phase 5 preview)."""

    id: str
    content: str
    sender_id: str
    sender_name: str
    created_at: str
    message_type: str = "TEXT"


class ConversationResponse(BaseModel):
    """Response schema for a conversation."""

    id: str
    type: str
    name: str | None = None
    avatar_url: str | None = None
    created_at: str
    updated_at: str
    participants: list[ParticipantResponse]
    other_user: UserResponse | None = None
    last_message: LastMessagePreview | None = None
    unread_count: int = 0


class ConversationListResponse(BaseModel):
    """Response schema for conversation list."""

    conversations: list[ConversationResponse]
