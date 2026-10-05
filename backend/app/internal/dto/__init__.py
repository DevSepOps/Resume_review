"""Request/response models. Input validation is delegated to internal.validators."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from app.internal.entities import Role
from app.internal import validators as v


class RegisterRequest(BaseModel):
    # Unknown fields (e.g. a client-sent "role") are ignored: role is always candidate.
    username: str
    email: EmailStr
    password: str
    confirm_password: str
    github: Optional[str] = None

    @field_validator("username")
    @classmethod
    def _username(cls, value: str) -> str:
        return v.validate_username(value)

    @field_validator("email")
    @classmethod
    def _email(cls, value: str) -> str:
        return value.lower()

    @field_validator("password")
    @classmethod
    def _password(cls, value: str) -> str:
        return v.validate_password(value)

    @field_validator("github")
    @classmethod
    def _github(cls, value: Optional[str]) -> Optional[str]:
        return v.validate_github(value)

    @model_validator(mode="after")
    def _passwords_match(self) -> "RegisterRequest":
        if self.password != self.confirm_password:
            raise ValueError("passwords do not match")
        return self


class LoginRequest(BaseModel):
    username: str = Field(max_length=250)
    password: str = Field(max_length=1024)

    @field_validator("username")
    @classmethod
    def _lower(cls, value: str) -> str:
        return value.lower()


class RefreshRequest(BaseModel):
    token: str


class LogoutRequest(BaseModel):
    refresh_token: Optional[str] = None


class RoleUpdateRequest(BaseModel):
    role: Role


class MessageResponse(BaseModel):
    detail: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    role: Role


class TokenPairResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    github: Optional[str] = None
    role: Role
    is_active: bool
    created_date: Optional[datetime] = None


class ResumeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    file_name: str
    file_size: int
    mime_type: str
    created_date: datetime
    updated_date: datetime


class ExpertResumeResponse(ResumeResponse):
    username: str
    email: str
    github: Optional[str] = None


class UploadResponse(BaseModel):
    message: str
    resume: ResumeResponse


class StatsResponse(BaseModel):
    total_users: int
    total_resumes: int
    users_by_role: dict[str, int]
