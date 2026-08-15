"""Conversation business logic service."""

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation
from app.repositories.conversation_repo import ConversationRepository
from app.repositories.user_repo import UserRepository


class ConversationService:
    """Service encapsulating conversation management business rules."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.conv_repo = ConversationRepository(db)
        self.user_repo = UserRepository(db)

    async def create_direct_conversation(
        self, current_user_id: str, target_user_id: str
    ) -> tuple[Conversation, bool]:
        """Create or return an existing DIRECT conversation between current user and target user."""
        target_id = target_user_id.strip()

        # 1. Self conversation check
        if target_id == current_user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot start a direct conversation with yourself",
            )

        # 2. Target user existence check
        target_user = await self.user_repo.get_by_id(target_id)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target user not found",
            )

        # 3. Check for existing DIRECT conversation between the pair
        existing = await self.conv_repo.get_direct_conversation_between_users(
            current_user_id, target_id
        )
        if existing:
            return existing, False

        # 4. Create new DIRECT conversation and add both participants
        conv = await self.conv_repo.create_conversation(
            type="DIRECT",
            created_by=current_user_id,
        )
        await self.conv_repo.add_participant(conv.id, current_user_id, role="MEMBER")
        await self.conv_repo.add_participant(conv.id, target_id, role="MEMBER")

        # Re-fetch with eager loaded relationships
        full_conv = await self.conv_repo.get_conversation_by_id(conv.id)
        return full_conv, True  # type: ignore[return-value]

    async def get_user_conversations(self, user_id: str) -> list[Conversation]:
        """Get all active conversations for a user."""
        return await self.conv_repo.get_user_conversations(user_id)

    async def get_conversation_detail(
        self, conversation_id: str, current_user_id: str
    ) -> Conversation:
        """Get conversation details with server-side authorization check."""
        conv = await self.conv_repo.get_conversation_by_id(conversation_id)
        if not conv:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )

        # Authorization check: current_user MUST be an active participant
        is_member = await self.conv_repo.is_participant(conversation_id, current_user_id)
        if not is_member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a participant in this conversation",
            )

        return conv

    async def create_group_conversation(
        self, creator_id: str, name: str, participant_ids: list[str]
    ) -> Conversation:
        """Create a new GROUP conversation with creator as ADMIN and provided members as MEMBER."""
        clean_name = name.strip()
        if not clean_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Group name cannot be empty",
            )

        # Filter and validate unique participant IDs
        unique_member_ids = list(dict.fromkeys(p.strip() for p in participant_ids if p.strip()))
        # Remove creator if included in list to prevent duplicate addition
        other_member_ids = [m_id for m_id in unique_member_ids if m_id != creator_id]

        if not other_member_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Group must contain at least one other participant",
            )

        # Validate that all target users exist
        for m_id in other_member_ids:
            u = await self.user_repo.get_by_id(m_id)
            if not u:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User '{m_id}' not found",
                )

        # Create GROUP conversation
        conv = await self.conv_repo.create_conversation(
            type="GROUP",
            name=clean_name,
            created_by=creator_id,
        )

        # Creator is ADMIN
        await self.conv_repo.add_participant(conv.id, creator_id, role="ADMIN")

        # Other members are MEMBER
        for m_id in other_member_ids:
            await self.conv_repo.add_participant(conv.id, m_id, role="MEMBER")

        await self.db.commit()

        # Re-fetch eager loaded conversation
        full_conv = await self.conv_repo.get_conversation_by_id(conv.id)
        return full_conv  # type: ignore[return-value]

    async def add_group_member(
        self, requester_id: str, conversation_id: str, target_user_id: str
    ) -> Conversation:
        """Add a member to an existing GROUP conversation. Requires ADMIN role."""
        conv = await self.conv_repo.get_conversation_by_id(conversation_id)
        if not conv or conv.type != "GROUP":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Group conversation not found",
            )

        # Check requester is active ADMIN
        req_participant = await self.conv_repo.get_active_participant(conversation_id, requester_id)
        if not req_participant or req_participant.role != "ADMIN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only group admins can add members",
            )

        target_id = target_user_id.strip()
        target_user = await self.user_repo.get_by_id(target_id)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        existing_participant = await self.conv_repo.get_participant(conversation_id, target_id)
        if existing_participant:
            if existing_participant.left_at is None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="User is already an active member of this group",
                )
            # Reactivate previously left member
            await self.conv_repo.reactivate_participant(existing_participant, role="MEMBER")
        else:
            # Add new member
            await self.conv_repo.add_participant(conversation_id, target_id, role="MEMBER")

        await self.db.commit()
        self.db.expire_all()
        full_conv = await self.conv_repo.get_conversation_by_id(conversation_id)
        return full_conv  # type: ignore[return-value]

    async def remove_group_member(
        self, requester_id: str, conversation_id: str, target_user_id: str
    ) -> Conversation:
        """Remove a member from a GROUP conversation. Requires ADMIN role."""
        conv = await self.conv_repo.get_conversation_by_id(conversation_id)
        if not conv or conv.type != "GROUP":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Group conversation not found",
            )

        # Check requester is active ADMIN
        req_participant = await self.conv_repo.get_active_participant(conversation_id, requester_id)
        if not req_participant or req_participant.role != "ADMIN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only group admins can remove members",
            )

        target_id = target_user_id.strip()
        target_participant = await self.conv_repo.get_active_participant(conversation_id, target_id)
        if not target_participant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User is not an active member of this group",
            )

        # Protect against removing creator or removing the sole admin
        active_admins = [p for p in conv.participants if p.left_at is None and p.role == "ADMIN"]
        if target_participant.role == "ADMIN" and len(active_admins) <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove the final admin of the group",
            )

        await self.conv_repo.remove_participant(target_participant)
        await self.db.commit()
        self.db.expire_all()
        full_conv = await self.conv_repo.get_conversation_by_id(conversation_id)
        return full_conv  # type: ignore[return-value]
