"""MessageReceipt model — per-user delivery/read state for each message."""

from sqlalchemy import CheckConstraint, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, generate_uuid


class MessageReceipt(Base):
    """Tracks delivery and read state per recipient per message."""

    __tablename__ = "message_receipts"
    __table_args__ = (
        UniqueConstraint("message_id", "user_id", name="uq_mr_message_user"),
        CheckConstraint("status IN ('SENT', 'DELIVERED', 'READ')", name="ck_mr_status"),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True, default=generate_uuid)
    message_id: Mapped[str] = mapped_column(
        Text,
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[str] = mapped_column(
        Text,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(Text, nullable=False, default="SENT")
    delivered_at: Mapped[str | None] = mapped_column(Text, nullable=True)
    read_at: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    message = relationship("Message", back_populates="receipts")
    user = relationship("User")

    def __repr__(self) -> str:
        return f"<Receipt msg={self.message_id[:8]} user={self.user_id[:8]} {self.status}>"
