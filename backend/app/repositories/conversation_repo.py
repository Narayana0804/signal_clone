"""Conversation repository for database operations."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.conversation import Conversation
from app.models.participant import ConversationParticipant


class ConversationRepository:
    """Repository for managing Conversation and Participant entities."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_conversation_by_id(self, conversation_id: str) -> Conversation | None:
        """Find conversation by ID with eager loading of participants and their user profiles."""
        stmt = (
            select(Conversation)
            .options(joinedload(Conversation.participants).joinedload(ConversationParticipant.user))
            .where(Conversation.id == conversation_id)
        )
        result = await self.db.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def get_direct_conversation_between_users(
        self, user1_id: str, user2_id: str
    ) -> Conversation | None:
        """Find existing DIRECT conversation between two specific users."""
        # Query DIRECT conversations where user1 is an active participant
        stmt = (
            select(Conversation)
            .join(
                ConversationParticipant, ConversationParticipant.conversation_id == Conversation.id
            )
            .where(Conversation.type == "DIRECT")
            .where(ConversationParticipant.user_id == user1_id)
            .where(ConversationParticipant.left_at.is_(None))
        )
        result = await self.db.execute(stmt)
        candidates = result.scalars().all()

        for conv in candidates:
            # Check if user2 is also an active participant in this conversation
            stmt_part = select(ConversationParticipant).where(
                (ConversationParticipant.conversation_id == conv.id)
                & (ConversationParticipant.user_id == user2_id)
                & (ConversationParticipant.left_at.is_(None))
            )
            res_part = await self.db.execute(stmt_part)
            if res_part.scalar_one_or_none():
                return await self.get_conversation_by_id(conv.id)

        return None

    async def create_conversation(
        self,
        type: str,
        created_by: str,
        name: str | None = None,
        avatar_url: str | None = None,
    ) -> Conversation:
        """Create a new conversation record."""
        conv = Conversation(
            type=type,
            name=name,
            avatar_url=avatar_url,
            created_by=created_by,
        )
        self.db.add(conv)
        await self.db.flush()
        return conv

    async def add_participant(
        self, conversation_id: str, user_id: str, role: str = "MEMBER"
    ) -> ConversationParticipant:
        """Add a participant to a conversation."""
        part = ConversationParticipant(
            conversation_id=conversation_id,
            user_id=user_id,
            role=role,
        )
        self.db.add(part)
        await self.db.flush()
        return part

    async def get_user_conversations(self, user_id: str) -> list[Conversation]:
        """Get all active conversations for a user, ordered by updated_at DESC."""
        stmt = (
            select(Conversation)
            .join(
                ConversationParticipant, ConversationParticipant.conversation_id == Conversation.id
            )
            .options(joinedload(Conversation.participants).joinedload(ConversationParticipant.user))
            .where(ConversationParticipant.user_id == user_id)
            .where(ConversationParticipant.left_at.is_(None))
            .order_by(Conversation.updated_at.desc())
        )
        result = await self.db.execute(stmt)
        # Deduplicate results from join
        seen = set()
        unique_convs = []
        for conv in result.unique().scalars().all():
            if conv.id not in seen:
                seen.add(conv.id)
                unique_convs.append(conv)
        return unique_convs

    async def is_participant(self, conversation_id: str, user_id: str) -> bool:
        """Check if a user is an active participant in a conversation."""
        stmt = select(ConversationParticipant).where(
            (ConversationParticipant.conversation_id == conversation_id)
            & (ConversationParticipant.user_id == user_id)
            & (ConversationParticipant.left_at.is_(None))
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None
