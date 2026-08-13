"""Messages API router handlers."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.message import (
    MessageListResponse,
    MessageResponse,
    ReadReceiptResponse,
    SendMessageRequest,
)
from app.services.message_service import MessageService

router = APIRouter(prefix="/api/v1", tags=["messages"])


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Send a message to a conversation",
)
async def send_message(
    conversation_id: str,
    req: SendMessageRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    """Send a message to a conversation. Derives sender_id from authenticated session."""
    service = MessageService(db)
    return await service.send_message(
        conversation_id=conversation_id,
        sender=current_user,
        content=req.content,
        message_type=req.message_type,
        client_id=req.client_id,
        reply_to_id=req.reply_to_id,
    )


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=MessageListResponse,
    summary="Get paginated messages for a conversation",
)
async def get_messages(
    conversation_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    before: Annotated[
        str | None, Query(description="Message ID cursor for backward pagination")
    ] = None,
    limit: Annotated[int, Query(ge=1, le=100, description="Max messages to return")] = 50,
) -> MessageListResponse:
    """Retrieve messages for a conversation with cursor-based pagination."""
    service = MessageService(db)
    messages, has_more = await service.get_messages(
        conversation_id=conversation_id,
        current_user_id=current_user.id,
        before=before,
        limit=limit,
    )
    return MessageListResponse(messages=messages, has_more=has_more)


@router.post(
    "/messages/{message_id}/read",
    response_model=ReadReceiptResponse,
    summary="Mark messages as read up to message_id",
)
async def mark_message_read(
    message_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ReadReceiptResponse:
    """Mark messages in a conversation as read up to the specified message_id."""
    service = MessageService(db)
    read_count = await service.mark_read(
        message_id=message_id,
        current_user_id=current_user.id,
    )
    return ReadReceiptResponse(read_count=read_count)
