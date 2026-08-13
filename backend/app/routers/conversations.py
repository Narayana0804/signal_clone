"""Conversations API router handlers."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.conversation import Conversation
from app.models.user import User
from app.schemas.conversation import (
    ConversationListResponse,
    ConversationResponse,
    CreateConversationRequest,
    ParticipantResponse,
)
from app.schemas.user import UserResponse
from app.services.conversation_service import ConversationService

router = APIRouter(prefix="/api/v1/conversations", tags=["conversations"])


def build_conversation_response(conv: Conversation, current_user_id: str) -> ConversationResponse:
    """Format ORM Conversation model into API response, populating other_user for DIRECT chats."""
    participants_out = []
    other_user_out = None

    for p in conv.participants:
        user_res = UserResponse.model_validate(p.user)
        participants_out.append(
            ParticipantResponse(
                id=p.id,
                user_id=p.user_id,
                role=p.role,
                joined_at=p.joined_at,
                user=user_res,
            )
        )
        if p.user_id != current_user_id and other_user_out is None:
            other_user_out = user_res

    # For DIRECT conversations, name defaults to the other user's display_name if name is not set
    display_name = conv.name
    if conv.type == "DIRECT" and not display_name and other_user_out:
        display_name = other_user_out.display_name

    return ConversationResponse(
        id=conv.id,
        type=conv.type,
        name=display_name,
        avatar_url=conv.avatar_url or (other_user_out.avatar_url if other_user_out else None),
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        participants=participants_out,
        other_user=other_user_out,
        last_message=None,  # Phase 5 messaging will populate
        unread_count=0,  # Phase 5 messaging will calculate
    )


@router.post(
    "",
    response_model=ConversationResponse,
    summary="Create or retrieve a direct/group conversation",
)
async def create_conversation(
    req: CreateConversationRequest,
    response: Response,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ConversationResponse:
    """Create a new DIRECT conversation or return existing conversation between the pair."""
    service = ConversationService(db)

    if req.type == "DIRECT":
        if not req.participant_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="participant_ids must contain target user ID",
            )
        target_user_id = req.participant_ids[0]
        conv, created_new = await service.create_direct_conversation(
            current_user_id=current_user.id,
            target_user_id=target_user_id,
        )
        if created_new:
            response.status_code = status.HTTP_201_CREATED
        else:
            response.status_code = status.HTTP_200_OK

        return build_conversation_response(conv, current_user.id)

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Group conversations are not yet implemented in Phase 4",
    )


@router.get(
    "",
    response_model=ConversationListResponse,
    summary="List current user's conversations",
)
async def list_conversations(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ConversationListResponse:
    """Retrieve all active conversations for the authenticated user."""
    service = ConversationService(db)
    convs = await service.get_user_conversations(current_user.id)
    items = [build_conversation_response(c, current_user.id) for c in convs]
    return ConversationListResponse(conversations=items)


@router.get(
    "/{conversation_id}",
    response_model=ConversationResponse,
    summary="Get conversation details",
)
async def get_conversation(
    conversation_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ConversationResponse:
    """Get details of a specific conversation. Requires participant membership."""
    service = ConversationService(db)
    conv = await service.get_conversation_detail(
        conversation_id=conversation_id,
        current_user_id=current_user.id,
    )
    return build_conversation_response(conv, current_user.id)
