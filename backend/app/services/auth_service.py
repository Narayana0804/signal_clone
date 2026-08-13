"""Authentication business logic service."""

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.session_repo import SessionRepository
from app.repositories.user_repo import UserRepository
from app.schemas.auth import RegisterRequest

MOCK_OTP = "123456"


class AuthService:
    """Service encapsulating authentication business rules."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)
        self.session_repo = SessionRepository(db)

    async def register(self, req: RegisterRequest) -> User:
        """Register a new user account."""
        phone = req.phone_number.strip()
        existing = await self.user_repo.get_by_phone(phone)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Phone number is already registered",
            )

        user = await self.user_repo.create(
            phone_number=phone,
            display_name=req.display_name.strip(),
        )
        return user

    async def verify_otp(self, phone_number: str, otp: str) -> bool:
        """Verify phone number with mock OTP ('123456')."""
        if otp.strip() != MOCK_OTP:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid OTP verification code",
            )

        phone = phone_number.strip()
        user = await self.user_repo.get_by_phone(phone)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found for given phone number",
            )

        await self.user_repo.mark_verified(user)
        return True

    async def login(self, phone_number: str, otp: str) -> tuple[User, str]:
        """Authenticate user and issue a session token."""
        if otp.strip() != MOCK_OTP:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid OTP verification code",
            )

        phone = phone_number.strip()
        user = await self.user_repo.get_by_phone(phone)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        if not user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User phone number is not verified. Please verify OTP first.",
            )

        # Update last seen
        await self.user_repo.update_last_seen(user)

        # Create new session
        session, raw_token = await self.session_repo.create_session(user.id)
        return user, raw_token

    async def logout(self, raw_token: str) -> bool:
        """Invalidate user session."""
        return await self.session_repo.delete_session_by_token(raw_token)
