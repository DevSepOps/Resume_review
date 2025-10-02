from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional
from users.models import UserRole

class UserRoleUpdate(BaseModel):
    role: UserRole = Field(
        ...,
        description="""
        New role for the user
        
        Available options:
        - candidate: Regular user who can upload resumes
        - expert: Can review all resumes  
        - admin: Full system access with user management
        """
    )

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: UserRole
    is_active: bool
    created_date: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class UserListFilters(BaseModel):
    role: Optional[UserRole] = Field(
        None,
        description="""
        Filter users by role
        
        Options:
        - candidate
        - expert  
        - admin
        """
    )
    is_active: Optional[bool] = Field(
        None, 
        description="Filter by active status (true/false)"
    )
