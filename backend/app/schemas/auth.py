from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

EmailField = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", max_length=255)


class LoginRequest(BaseModel):
    email: str = EmailField
    password: str = Field(min_length=8)
    mfa_code: str | None = Field(default=None, min_length=6, max_length=8)
    recovery_code: str | None = Field(default=None, min_length=8, max_length=32)


class RegisterRequest(BaseModel):
    email: str = EmailField
    full_name: str = Field(min_length=2, max_length=160)
    password: str = Field(min_length=8)
    role: str = "Security Analyst"


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str
    role: str
    is_active: bool
    is_verified: bool
    mfa_enabled: bool
    force_password_change: bool = False
    permissions: list[str] = []
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserRead


class PasswordRequest(BaseModel):
    email: str = EmailField


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=12)


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=8)
    new_password: str = Field(min_length=12)


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(min_length=20)


class LogoutRequest(BaseModel):
    access_token: str | None = None
    refresh_token: str | None = None


class VerifyEmailRequest(BaseModel):
    email: str = EmailField
    token: str


class MfaVerifyRequest(BaseModel):
    code: str = Field(min_length=6, max_length=8)
