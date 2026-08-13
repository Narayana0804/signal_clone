"""FastAPI dependency injection for database sessions and authentication."""

from typing import Annotated

from fastapi import Cookie, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.repositories.session_repo import SessionRepository


async def get_raw_token(
    session_token: Annotated[str | None, Cookie()] = None,
    authorization: Annotated[str | None, Header()] = None,
    x_session_token: Annotated[str | None, Header()] = None,
) -> str | None:
    """Extract raw session token from Cookie or Authorization / X-Session-Token headers."""
    if session_token:
        return session_token

    if x_session_token:
        return x_session_token

    if authorization and authorization.lower().startswith("bearer "):
        return authorization[7:].strip()

    return None


async def get_current_user(
    raw_token: Annotated[str | None, Depends(get_raw_token)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Dependency: retrieve currently authenticated user from session token."""
    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    session_repo = SessionRepository(db)
    user = await session_repo.get_user_by_token(raw_token)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_optional_current_user(
    raw_token: Annotated[str | None, Depends(get_raw_token)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User | None:
    """Dependency: retrieve user if authenticated, else None."""
    if not raw_token:
        return None

    session_repo = SessionRepository(db)
    return await session_repo.get_user_by_token(raw_token)
