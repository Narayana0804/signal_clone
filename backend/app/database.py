"""SQLAlchemy async engine and session factory for SQLite."""

import contextlib
import logging
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

logger = logging.getLogger(__name__)

engine = create_async_engine(
    settings.database_url,
    echo=settings.environment == "development",
    connect_args={"check_same_thread": False, "timeout": 30.0},
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db() -> None:
    """Initialize the database — enable WAL mode and ensure table schema exists."""
    from app.models.base import Base

    async with engine.begin() as conn:
        await conn.exec_driver_sql("PRAGMA journal_mode=WAL")
        await conn.exec_driver_sql("PRAGMA foreign_keys=ON")
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database initialized with WAL mode, foreign keys, and metadata schema")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency: yield an async database session."""
    async with async_session_factory() as session:
        try:
            yield session  # type: ignore[misc]
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        except BaseException:
            with contextlib.suppress(Exception):
                await session.rollback()
            raise
