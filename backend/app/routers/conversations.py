"""Conversations API router handlers."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.conversation import Conversation
from app.models.user import User
from app.repositories.message_repo import MessageRepository
from app.schemas.conversation import (
    AddGroupMemberRequest,
    ConversationListResponse,
    ConversationResponse,
    CreateConversationRequest,
    CreateGroupRequest,
    LastMessagePreview,
    ParticipantResponse,
)
from app.schemas.user import UserResponse
from app.services.conversation_service import ConversationService
from app.websockets.manager import ws_manager

router = APIRouter(prefix="/api/v1/conversations", tags=["conversations"])


async def build_conversation_response(
    conv: Conversation, current_user_id: str, db: AsyncSession
) -> ConversationResponse:
    """Format ORM Conversation model into API response, populating other_user, last_message, and unread_count."""
    participants_out = []
    other_user_out = None

    for p in conv.participants:
        if p.left_at is not None:
            continue
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

    # Fetch last message and unread count from MessageRepository
    msg_repo = MessageRepository(db)
    last_msg = await msg_repo.get_last_message(conv.id)
    unread_count = await msg_repo.get_unread_count(conv.id, current_user_id)

    last_msg_out = None
    if last_msg:
        sender_name = last_msg.sender.display_name if last_msg.sender else "Unknown"
        last_msg_out = LastMessagePreview(
            id=last_msg.id,
            content=last_msg.content,
            sender_id=last_msg.sender_id,
            sender_name=sender_name,
            created_at=last_msg.created_at,
            message_type=last_msg.message_type,
        )

    return ConversationResponse(
        id=conv.id,
        type=conv.type,
        name=display_name,
        avatar_url=conv.avatar_url
        or (other_user_out.avatar_url if other_user_out and conv.type == "DIRECT" else None),
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        participants=participants_out,
        other_user=other_user_out if conv.type == "DIRECT" else None,
        last_message=last_msg_out,
        unread_count=unread_count,
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
    """Create a new DIRECT or GROUP conversation."""
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

        return await build_conversation_response(conv, current_user.id, db)

    if req.type == "GROUP":
        if not req.name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Group name is required",
            )
        conv = await service.create_group_conversation(
            creator_id=current_user.id,
            name=req.name,
            participant_ids=req.participant_ids,
        )
        response.status_code = status.HTTP_201_CREATED
        conv_res = await build_conversation_response(conv, current_user.id, db)

        # Broadcast group.created event via WebSocket
        target_ids = [
            p.user_id
            for p in conv.participants
            if p.user_id != current_user.id and p.left_at is None
        ]
        if target_ids:
            await ws_manager.broadcast_to_participants(
                participant_user_ids=target_ids,
                event_type="group.created",
                payload={"conversation": conv_res.model_dump()},
            )

        return conv_res

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid conversation type",
    )


@router.post(
    "/groups",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new group conversation",
)
async def create_group(
    req: CreateGroupRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ConversationResponse:
    """Dedicated endpoint to create a new GROUP conversation."""
    service = ConversationService(db)
    conv = await service.create_group_conversation(
        creator_id=current_user.id,
        name=req.name,
        participant_ids=req.participant_ids,
    )
    conv_res = await build_conversation_response(conv, current_user.id, db)

    # Broadcast group.created event via WebSocket
    target_ids = [
        p.user_id for p in conv.participants if p.user_id != current_user.id and p.left_at is None
    ]
    if target_ids:
        await ws_manager.broadcast_to_participants(
            participant_user_ids=target_ids,
            event_type="group.created",
            payload={"conversation": conv_res.model_dump()},
        )

    return conv_res


@router.post(
    "/{conversation_id}/members",
    response_model=ConversationResponse,
    summary="Add a member to a group conversation",
)
async def add_group_member(
    conversation_id: str,
    req: AddGroupMemberRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ConversationResponse:
    """Add a target user to an existing group conversation (Admin only)."""
    service = ConversationService(db)
    conv = await service.add_group_member(
        requester_id=current_user.id,
        conversation_id=conversation_id,
        target_user_id=req.user_id,
    )
    conv_res = await build_conversation_response(conv, current_user.id, db)

    # Broadcast group.member_added and group.updated
    active_user_ids = [p.user_id for p in conv.participants if p.left_at is None]
    added_p = next((p for p in conv_res.participants if p.user_id == req.user_id.strip()), None)
    if active_user_ids:
        await ws_manager.broadcast_to_participants(
            participant_user_ids=active_user_ids,
            event_type="group.member_added",
            payload={
                "conversation_id": conversation_id,
                "member": added_p.model_dump() if added_p else None,
                "conversation": conv_res.model_dump(),
            },
        )

    return conv_res


@router.delete(
    "/{conversation_id}/members/{user_id}",
    response_model=ConversationResponse,
    summary="Remove a member from a group conversation",
)
async def remove_group_member(
    conversation_id: str,
    user_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ConversationResponse:
    """Remove a target user from a group conversation (Admin only)."""
    service = ConversationService(db)
    conv = await service.remove_group_member(
        requester_id=current_user.id,
        conversation_id=conversation_id,
        target_user_id=user_id,
    )
    conv_res = await build_conversation_response(conv, current_user.id, db)

    # Broadcast group.member_removed to remaining active participants plus the removed user
    active_user_ids = [p.user_id for p in conv.participants if p.left_at is None]
    notify_ids = list(set([*active_user_ids, user_id]))
    if notify_ids:
        await ws_manager.broadcast_to_participants(
            participant_user_ids=notify_ids,
            event_type="group.member_removed",
            payload={
                "conversation_id": conversation_id,
                "user_id": user_id,
                "conversation": conv_res.model_dump(),
            },
        )

    return conv_res


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
    items = [await build_conversation_response(c, current_user.id, db) for c in convs]
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
    return await build_conversation_response(conv, current_user.id, db)
