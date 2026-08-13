"""User model."""

from sqlalchemy import Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, generate_uuid


class User(Base, TimestampMixin):
    """Application user account."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(Text, primary_key=True, default=generate_uuid)
    phone_number: Mapped[str] = mapped_column(Text, unique=True, nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    about: Mapped[str] = mapped_column(Text, nullable=False, default="")
    is_verified: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_seen_at: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    contacts = relationship(
        "Contact",
        foreign_keys="Contact.user_id",
        back_populates="owner",
        cascade="all, delete-orphan",
    )
    participations = relationship(
        "ConversationParticipant", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User {self.display_name} ({self.phone_number})>"
