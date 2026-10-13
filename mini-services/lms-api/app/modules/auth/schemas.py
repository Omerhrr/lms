from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field, ConfigDict

from app.modules.auth.models import UserRole


# ---------- requests ----------

class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=2, max_length=255)
    role: Literal["student", "instructor"] = "student"


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class RefreshIn(BaseModel):
    refresh_token: Optional[str] = None


class LogoutIn(BaseModel):
    refresh_token: str | None = None


class ProfileUpdateIn(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=2, max_length=255)
    headline: Optional[str] = Field(default=None, max_length=255)
    bio: Optional[str] = Field(default=None, max_length=2000)
    avatar_url: Optional[str] = Field(default=None, max_length=500)


class ChangePasswordIn(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)


class ForgotPasswordIn(BaseModel):
    email: EmailStr


class ResetPasswordIn(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


# ---------- responses ----------

class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    instructor_requested: bool = False
    avatar_url: Optional[str] = None
    headline: Optional[str] = None
    bio: Optional[str] = None
    created_at: datetime


class SessionOut(BaseModel):
    """Browsers receive the session as HttpOnly cookies; tokens appear here only for
    API clients that send `X-Auth-Mode: bearer`."""
    user: UserOut
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_type: Optional[str] = None


class RefreshedOut(BaseModel):
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_type: Optional[str] = None
