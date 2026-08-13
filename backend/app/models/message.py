"""Message model."""

from sqlalchemy import CheckConstraint, ForeignKey, Index, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, generate_uuid, utc_now


class Message(Base):
    """A message within a conversation."""

    __tablename__ = "messages"
    __table_args__ = (
        CheckConstraint("message_type IN ('TEXT', 'SYSTEM')", name="ck_messages_type"),
        Index("ix_messages_conversation_created", "conversation_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True, default=generate_uuid)
    conversation_id: Mapped[str] = mapped_column(
        Text,
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sender_id: Mapped[str] = mapped_column(
        Text,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    message_type: Mapped[str] = mapped_column(Text, nullable=False, default="TEXT")
    reply_to_id: Mapped[str | None] = mapped_column(
        Text, ForeignKey("messages.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[str] = mapped_column(Text, nullable=False, default=utc_now)
    updated_at: Mapped[str | None] = mapped_column(Text, nullable=True)
    deleted_at: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    sender = relationship("User", foreign_keys=[sender_id])
    reply_to = relationship("Message", foreign_keys=[reply_to_id], remote_side="Message.id")
    receipts = relationship(
        "MessageReceipt", back_populates="message", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Message {self.id[:8]} in {self.conversation_id[:8]}>"
