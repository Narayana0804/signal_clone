"""Pydantic schemas for Authentication endpoints."""

from pydantic import BaseModel, Field

from app.schemas.user import UserResponse


class RegisterRequest(BaseModel):
    """Request schema for user registration."""

    phone_number: str = Field(..., min_length=7, max_length=20, pattern=r"^\+?[1-9]\d{1,14}$")
    display_name: str = Field(..., min_length=1, max_length=50)


class VerifyOTPRequest(BaseModel):
    """Request schema for OTP verification."""

    phone_number: str = Field(..., min_length=7, max_length=20)
    otp: str = Field(..., min_length=6, max_length=6)


class LoginRequest(BaseModel):
    """Request schema for user login."""

    phone_number: str = Field(..., min_length=7, max_length=20)
    otp: str = Field(..., min_length=6, max_length=6)


class AuthResponse(BaseModel):
    """Response schema for login success."""

    user: UserResponse
    token: str
