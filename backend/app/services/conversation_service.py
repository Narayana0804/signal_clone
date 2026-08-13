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
