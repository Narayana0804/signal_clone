"""Message repository for database operations."""

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.base import utc_now
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.message_receipt import MessageReceipt
from app.models.participant import ConversationParticipant


class MessageRepository:
    """Repository for managing Message and MessageReceipt entities."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_message(
        self,
        conversation_id: str,
        sender_id: str,
        content: str,
        message_type: str = "TEXT",
        reply_to_id: str | None = None,
    ) -> Message:
        """Create a new Message record."""
        msg = Message(
            conversation_id=conversation_id,
            sender_id=sender_id,
            content=content,
            message_type=message_type,
            reply_to_id=reply_to_id,
        )
        self.db.add(msg)
        await self.db.flush()
        return msg

    async def create_receipts_for_recipients(
        self, message_id: str, recipient_user_ids: list[str]
    ) -> list[MessageReceipt]:
        """Create SENT receipts for all recipient users in conversation."""
        receipts = []
        for uid in recipient_user_ids:
            receipt = MessageReceipt(
                message_id=message_id,
                user_id=uid,
                status="SENT",
            )
            self.db.add(receipt)
            receipts.append(receipt)
        if receipts:
            await self.db.flush()
        return receipts

    async def get_message_by_id(self, message_id: str) -> Message | None:
        """Fetch message by ID with eager loading of sender and receipts."""
        stmt = (
            select(Message)
            .options(
                joinedload(Message.sender),
                joinedload(Message.receipts),
            )
            .where(Message.id == message_id)
        )
        result = await self.db.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def get_conversation_messages(
        self,
        conversation_id: str,
        before_message_id: str | None = None,
        limit: int = 50,
    ) -> tuple[list[Message], bool]:
        """Get paginated messages for a conversation using before cursor, returned in chronological ASC order."""
        stmt = (
            select(Message)
            .options(
                joinedload(Message.sender),
                joinedload(Message.receipts),
            )
            .where(Message.conversation_id == conversation_id)
            .where(Message.deleted_at.is_(None))
        )

        if before_message_id:
            before_msg = await self.get_message_by_id(before_message_id)
            if before_msg:
                stmt = stmt.where(Message.created_at < before_msg.created_at)

        # Order DESC with limit + 1 to check has_more
        stmt = stmt.order_by(Message.created_at.desc()).limit(limit + 1)
        result = await self.db.execute(stmt)
        raw_msgs = result.unique().scalars().all()

        has_more = len(raw_msgs) > limit
        msgs = raw_msgs[:limit]

        # Reverse to chronological order ASC for chat view
        msgs.reverse()
        return msgs, has_more

    async def mark_messages_read(
        self, conversation_id: str, user_id: str, target_message_id: str
    ) -> int:
        """Mark all messages in conversation up to target_message_id as READ for user_id, updating last_read_message_id watermark."""
        target_msg = await self.get_message_by_id(target_message_id)
        if not target_msg or target_msg.conversation_id != conversation_id:
            return 0

        now_ts = utc_now()

        # 1. Update participant watermark
        stmt_part = (
            update(ConversationParticipant)
            .where(ConversationParticipant.conversation_id == conversation_id)
            .where(ConversationParticipant.user_id == user_id)
            .values(last_read_message_id=target_message_id)
        )
        await self.db.execute(stmt_part)

        # 2. Find receipts to update
        subq = select(Message.id).where(
            (Message.conversation_id == conversation_id)
            & (Message.created_at <= target_msg.created_at)
        )
        stmt_receipts = (
            update(MessageReceipt)
            .where(MessageReceipt.user_id == user_id)
            .where(MessageReceipt.message_id.in_(subq))
            .where(MessageReceipt.status != "READ")
            .values(status="READ", read_at=now_ts)
        )
        res = await self.db.execute(stmt_receipts)
        return res.rowcount

    async def update_conversation_timestamp(self, conversation_id: str):
        """Update conversation's updated_at timestamp."""
        stmt = (
            update(Conversation)
            .where(Conversation.id == conversation_id)
            .values(updated_at=utc_now())
        )
        await self.db.execute(stmt)

    async def get_last_message(self, conversation_id: str) -> Message | None:
        """Get the latest non-deleted message for a conversation preview."""
        stmt = (
            select(Message)
            .options(joinedload(Message.sender))
            .where(Message.conversation_id == conversation_id)
            .where(Message.deleted_at.is_(None))
            .order_by(Message.created_at.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def get_unread_count(self, conversation_id: str, user_id: str) -> int:
        """Compute unread message count for a user in a conversation based on read watermark."""
        # Find participant's last_read_message_id
        stmt_part = select(ConversationParticipant.last_read_message_id).where(
            (ConversationParticipant.conversation_id == conversation_id)
            & (ConversationParticipant.user_id == user_id)
            & (ConversationParticipant.left_at.is_(None))
        )
        res_part = await self.db.execute(stmt_part)
        last_read_id = res_part.scalar_one_or_none()

        stmt_count = select(func.count(Message.id)).where(
            (Message.conversation_id == conversation_id)
            & (Message.sender_id != user_id)
            & (Message.deleted_at.is_(None))
        )

        if last_read_id:
            last_read_msg = await self.get_message_by_id(last_read_id)
            if last_read_msg:
                stmt_count = stmt_count.where(Message.created_at > last_read_msg.created_at)

        res_count = await self.db.execute(stmt_count)
        return res_count.scalar_one() or 0
