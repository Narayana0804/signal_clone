"""Message business logic service implementing strict persistence-before-broadcast flow."""

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import Message
from app.models.user import User
from app.repositories.conversation_repo import ConversationRepository
from app.repositories.message_repo import MessageRepository
from app.schemas.message import MessageResponse, MessageSenderResponse, ReceiptResponse
from app.websockets.manager import ws_manager


def build_message_response(msg: Message, client_id: str | None = None) -> MessageResponse:
    """Format ORM Message into API response schema."""
    sender_out = MessageSenderResponse(
        id=msg.sender.id,
        display_name=msg.sender.display_name,
        avatar_url=msg.sender.avatar_url,
    )
    receipts_out = [
        ReceiptResponse(
            user_id=r.user_id,
            status=r.status,
            delivered_at=r.delivered_at,
            read_at=r.read_at,
        )
        for r in (msg.receipts or [])
    ]
    return MessageResponse(
        id=msg.id,
        conversation_id=msg.conversation_id,
        sender_id=msg.sender_id,
        sender=sender_out,
        content=msg.content,
        message_type=msg.message_type,
        client_id=client_id,
        reply_to_id=msg.reply_to_id,
        created_at=msg.created_at,
        updated_at=msg.updated_at,
        deleted_at=msg.deleted_at,
        receipts=receipts_out,
    )


class MessageService:
    """Service encapsulating persistent messaging business rules."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.msg_repo = MessageRepository(db)
        self.conv_repo = ConversationRepository(db)

    async def send_message(
        self,
        conversation_id: str,
        sender: User,
        content: str,
        message_type: str = "TEXT",
        client_id: str | None = None,
        reply_to_id: str | None = None,
    ) -> MessageResponse:
        """Send a message ensuring strict authenticate -> authorize -> validate -> persist -> commit -> broadcast sequence."""
        # 1. Authorize: Verify sender is an active participant in the conversation
        conv = await self.conv_repo.get_conversation_by_id(conversation_id)
        if not conv:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )

        is_member = await self.conv_repo.is_participant(conversation_id, sender.id)
        if not is_member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a participant in this conversation",
            )

        # 2. Validate: Non-empty content
        clean_content = content.strip()
        if not clean_content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message content cannot be empty",
            )

        # 3. Persist message
        msg = await self.msg_repo.create_message(
            conversation_id=conversation_id,
            sender_id=sender.id,
            content=clean_content,
            message_type=message_type,
            reply_to_id=reply_to_id,
        )

        # 4. Create receipts for all other active conversation participants
        recipient_user_ids = [
            p.user_id for p in conv.participants if p.user_id != sender.id and p.left_at is None
        ]
        if recipient_user_ids:
            await self.msg_repo.create_receipts_for_recipients(msg.id, recipient_user_ids)

        # 5. Update conversation timestamp
        await self.msg_repo.update_conversation_timestamp(conversation_id)

        # 6. Commit transaction to guarantee durability BEFORE broadcasting
        await self.db.commit()

        # Re-fetch full message with relationships
        full_msg = await self.msg_repo.get_message_by_id(msg.id)
        msg_res = build_message_response(full_msg, client_id=client_id)  # type: ignore[arg-type]

        # 7. Broadcast message.created event via WebSocket to online recipients
        if recipient_user_ids:
            await ws_manager.broadcast_to_participants(
                participant_user_ids=recipient_user_ids,
                event_type="message.created",
                payload={"message": msg_res.model_dump()},
            )

        return msg_res

    async def get_messages(
        self,
        conversation_id: str,
        current_user_id: str,
        before: str | None = None,
        limit: int = 50,
    ) -> tuple[list[MessageResponse], bool]:
        """Get paginated messages for a conversation with authorization check."""
        conv = await self.conv_repo.get_conversation_by_id(conversation_id)
        if not conv:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )

        is_member = await self.conv_repo.is_participant(conversation_id, current_user_id)
        if not is_member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a participant in this conversation",
            )

        clamped_limit = max(1, min(limit, 100))
        msgs, has_more = await self.msg_repo.get_conversation_messages(
            conversation_id=conversation_id,
            before_message_id=before,
            limit=clamped_limit,
        )

        items = [build_message_response(m) for m in msgs]
        return items, has_more

    async def mark_read(
        self,
        message_id: str,
        current_user_id: str,
    ) -> int:
        """Mark messages as read up to message_id for current_user_id."""
        msg = await self.msg_repo.get_message_by_id(message_id)
        if not msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found",
            )

        is_member = await self.conv_repo.is_participant(msg.conversation_id, current_user_id)
        if not is_member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a participant in this conversation",
            )

        read_count = await self.msg_repo.mark_messages_read(
            conversation_id=msg.conversation_id,
            user_id=current_user_id,
            target_message_id=message_id,
        )
        await self.db.commit()

        # Broadcast message.read event to message senders/participants
        conv = await self.conv_repo.get_conversation_by_id(msg.conversation_id)
        if conv:
            participant_ids = [p.user_id for p in conv.participants if p.left_at is None]
            await ws_manager.broadcast_to_participants(
                participant_user_ids=participant_ids,
                event_type="message.read",
                payload={
                    "conversation_id": msg.conversation_id,
                    "user_id": current_user_id,
                    "last_read_message_id": message_id,
                },
                exclude_user_id=current_user_id,
            )

        return read_count
