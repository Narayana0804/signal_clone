"""Pydantic schemas package barrel export."""

from app.schemas.auth import AuthResponse, LoginRequest, RegisterRequest, VerifyOTPRequest
from app.schemas.contact import (
    AddContactRequest,
    ContactListResponse,
    ContactResponse,
    UserSearchResponse,
)
from app.schemas.conversation import (
    ConversationListResponse,
    ConversationResponse,
    CreateConversationRequest,
    LastMessagePreview,
    ParticipantResponse,
)
from app.schemas.message import (
    MessageListResponse,
    MessageResponse,
    MessageSenderResponse,
    ReadReceiptResponse,
    ReceiptResponse,
    SendMessageRequest,
)
from app.schemas.user import UpdateProfileRequest, UserResponse

__all__ = [
    "AddContactRequest",
    "AuthResponse",
    "ContactListResponse",
    "ContactResponse",
    "ConversationListResponse",
    "ConversationResponse",
    "CreateConversationRequest",
    "LastMessagePreview",
    "LoginRequest",
    "MessageListResponse",
    "MessageResponse",
    "MessageSenderResponse",
    "ParticipantResponse",
    "ReadReceiptResponse",
    "ReceiptResponse",
    "RegisterRequest",
    "SendMessageRequest",
    "UpdateProfileRequest",
    "UserResponse",
    "UserSearchResponse",
    "VerifyOTPRequest",
]
