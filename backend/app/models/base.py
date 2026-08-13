"""SQLAlchemy declarative base with common columns."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def generate_uuid() -> str:
    """Generate a new UUID v4 string."""
    return str(uuid.uuid4())


def utc_now() -> str:
    """Return current UTC time as ISO 8601 string."""
    return datetime.now(UTC).isoformat()


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    pass


class TimestampMixin:
    """Mixin that adds created_at and updated_at columns."""

    created_at: Mapped[str] = mapped_column(Text, nullable=False, default=utc_now)
    updated_at: Mapped[str] = mapped_column(Text, nullable=False, default=utc_now, onupdate=utc_now)
