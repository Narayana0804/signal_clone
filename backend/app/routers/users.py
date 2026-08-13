"""Users API router handlers."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.contact import UserSearchResponse
from app.schemas.user import UserResponse
from app.services.user_service import UserService

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.get(
    "/search",
    response_model=UserSearchResponse,
    summary="Search users by display name or phone number",
)
async def search_users(
    q: Annotated[str, Query(min_length=2, description="Search query string")],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
) -> UserSearchResponse:
    """Search for other registered users. Excludes current authenticated user."""
    service = UserService(db)
    users = await service.search_users(
        query=q,
        current_user_id=current_user.id,
        limit=limit,
    )
    return UserSearchResponse(users=[UserResponse.model_validate(u) for u in users])
