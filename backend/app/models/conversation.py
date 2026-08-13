"""Conversation model."""

from sqlalchemy import CheckConstraint, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, generate_uuid


class Conversation(Base, TimestampMixin):
    """A conversation — either DIRECT (2 users) or GROUP (2+ users)."""

    __tablename__ = "conversations"
    __table_args__ = (CheckConstraint("type IN ('DIRECT', 'GROUP')", name="ck_conversations_type"),)

    id: Mapped[str] = mapped_column(Text, primary_key=True, default=generate_uuid)
    type: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str | None] = mapped_column(Text, nullable=True)  # NULL for DIRECT
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str] = mapped_column(
        Text, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    participants = relationship(
        "ConversationParticipant",
        back_populates="conversation",
        cascade="all, delete-orphan",
    )
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Conversation {self.type} {self.name or self.id[:8]}>"
