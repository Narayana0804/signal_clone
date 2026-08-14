"""Pydantic schemas for Message endpoints."""

from pydantic import BaseModel, Field


class SendMessageRequest(BaseModel):
    """Request schema for sending a message."""

    content: str = Field(..., min_length=1, max_length=10000)
    message_type: str = Field("TEXT", pattern=r"^(TEXT|SYSTEM)$")
    client_id: str | None = Field(None, max_length=64)
    reply_to_id: str | None = Field(None, max_length=64)


class ReceiptResponse(BaseModel):
    """Response schema for a message receipt."""

    user_id: str
    status: str
    delivered_at: str | None = None
    read_at: str | None = None


class MessageSenderResponse(BaseModel):
    """Simplified user profile schema for message senders."""

    id: str
    display_name: str
    avatar_url: str | None = None


class MessageResponse(BaseModel):
    """Response schema for a single message."""

    id: str
    conversation_id: str
    sender_id: str
    sender: MessageSenderResponse
    content: str
    message_type: str = "TEXT"
    client_id: str | None = None
    reply_to_id: str | None = None
    created_at: str
    updated_at: str | None = None
    deleted_at: str | None = None
    receipts: list[ReceiptResponse] = Field(default_factory=list)


class MessageListResponse(BaseModel):
    """Response schema for paginated messages."""

    messages: list[MessageResponse]
    has_more: bool


class ReadReceiptResponse(BaseModel):
    """Response schema for mark-as-read operation."""

    read_count: int
