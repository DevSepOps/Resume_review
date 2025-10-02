from pydantic import BaseModel, Field, field_validator, EmailStr
from typing import Optional
from datetime import datetime

class UserRegisterSchema(BaseModel):
    username: str = Field(..., max_length=250, description="User's username")
    password: str = Field(..., description="user password")
    confirm_password: str = Field(..., description="confirm user password")
    email: EmailStr = Field(..., max_length=250, description="User's Email in normal EmailStr format")
    github: str = Field(..., description="User's github link")
    role: Optional[str] = Field("candidate", description="User role: candidate or expert")

    @field_validator("confirm_password")
    def check_passwords_match(cls, confirm_password, validation):
        if not confirm_password == validation.data.get("password"):
            raise ValueError("password doesn't match")
        return confirm_password

    # ✅ ADD role validation
    @field_validator("role")
    def validate_role(cls, role):
        if role and role not in ["candidate", "expert"]:
            raise ValueError("Role must be either 'candidate' or 'expert'")
        return role

class UserLoginSchema(BaseModel):
    username: str = Field(..., max_length=250, description="Username of the user")
    password: str = Field(..., description="User's password")

class UserRefreshTokenSchema(BaseModel):
    token: str = Field(..., description="refresh token of the user")
