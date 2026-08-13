"""Authentication API router handlers."""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user, get_raw_token
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.auth import AuthResponse, LoginRequest, RegisterRequest, VerifyOTPRequest
from app.schemas.user import UpdateProfileRequest, UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

COOKIE_NAME = "session_token"
COOKIE_MAX_AGE = settings.session_expiry_days * 24 * 60 * 60  # seconds

# In production (cross-site Vercel -> Railway), SameSite=None and Secure=True are required.
# In local development (localhost:3000 -> localhost:8000), SameSite=Lax and Secure=False work.
COOKIE_SAMESITE: Literal["none", "lax"] = "none" if settings.is_production else "lax"
COOKIE_SECURE: bool = settings.is_production


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
async def register(
    req: RegisterRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Register a new user with phone number and display name."""
    service = AuthService(db)
    return await service.register(req)


@router.post(
    "/verify",
    summary="Verify phone number with mock OTP",
)
async def verify_otp(
    req: VerifyOTPRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Verify phone number with mock OTP code '123456'."""
    service = AuthService(db)
    verified = await service.verify_otp(req.phone_number, req.otp)
    return {"verified": verified}


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Login and receive session cookie",
)
async def login(
    req: LoginRequest,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AuthResponse:
    """Login with verified phone number and OTP code. Sets HTTP-only cookie."""
    service = AuthService(db)
    user, raw_token = await service.login(req.phone_number, req.otp)

    # Set HTTP-only cookie (No raw token in response body)
    response.set_cookie(
        key=COOKIE_NAME,
        value=raw_token,
        max_age=COOKIE_MAX_AGE,
        httponly=True,
        samesite=COOKIE_SAMESITE,
        secure=COOKIE_SECURE,
        path="/",
    )

    return AuthResponse(
        user=UserResponse.model_validate(user),
    )


@router.post(
    "/logout",
    summary="Logout and invalidate session",
)
async def logout(
    response: Response,
    raw_token: Annotated[str | None, Depends(get_raw_token)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Logout current user, delete session from DB, and clear cookie."""
    if raw_token:
        service = AuthService(db)
        await service.logout(raw_token)

    response.delete_cookie(
        key=COOKIE_NAME,
        path="/",
        httponly=True,
        samesite=COOKIE_SAMESITE,
        secure=COOKIE_SECURE,
    )

    return {"message": "Logged out"}


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
)
async def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Return currently authenticated user profile."""
    return current_user


@router.patch(
    "/me",
    response_model=UserResponse,
    summary="Update current user profile",
)
async def update_me(
    req: UpdateProfileRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Update current user display name, about status, or avatar URL."""
    repo = UserRepository(db)
    updated_user = await repo.update_profile(
        user=current_user,
        display_name=req.display_name,
        about=req.about,
        avatar_url=req.avatar_url,
    )
    return updated_user
