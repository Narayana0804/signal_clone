"""Contact model."""

from sqlalchemy import CheckConstraint, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, generate_uuid, utc_now


class Contact(Base):
    """User-to-user contact relationship (directional)."""

    __tablename__ = "contacts"
    __table_args__ = (
        UniqueConstraint("user_id", "contact_user_id", name="uq_contacts_pair"),
        CheckConstraint("user_id != contact_user_id", name="ck_contacts_no_self"),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(
        Text, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    contact_user_id: Mapped[str] = mapped_column(
        Text, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[str] = mapped_column(Text, nullable=False, default=utc_now)

    # Relationships
    owner = relationship("User", foreign_keys=[user_id], back_populates="contacts")
    contact_user = relationship("User", foreign_keys=[contact_user_id])

    def __repr__(self) -> str:
        return f"<Contact {self.user_id} → {self.contact_user_id}>"
