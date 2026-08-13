"""ConversationParticipant model — links users to conversations with roles."""

from sqlalchemy import CheckConstraint, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, generate_uuid, utc_now


class ConversationParticipant(Base):
    """A user's membership in a conversation, including role and read position."""

    __tablename__ = "conversation_participants"
    __table_args__ = (
        UniqueConstraint("conversation_id", "user_id", name="uq_cp_conv_user"),
        CheckConstraint("role IN ('ADMIN', 'MEMBER')", name="ck_cp_role"),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True, default=generate_uuid)
    conversation_id: Mapped[str] = mapped_column(
        Text,
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[str] = mapped_column(
        Text,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(Text, nullable=False, default="MEMBER")
    joined_at: Mapped[str] = mapped_column(Text, nullable=False, default=utc_now)
    left_at: Mapped[str | None] = mapped_column(Text, nullable=True)  # NULL = active
    last_read_message_id: Mapped[str | None] = mapped_column(
        Text,
        ForeignKey("messages.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    conversation = relationship("Conversation", back_populates="participants")
    user = relationship("User", back_populates="participations")
    last_read_message = relationship("Message", foreign_keys=[last_read_message_id])

    def __repr__(self) -> str:
        return f"<Participant {self.user_id[:8]} in {self.conversation_id[:8]} ({self.role})>"
