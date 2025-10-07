from fastapi import Depends, HTTPException, status
from app.users.models import UsersModel, UserRole
from app.auth.jwt_auth import get_authenticated_user


async def get_expert_user(
    current_user: UsersModel = Depends(get_authenticated_user),
) -> UsersModel:
    """Checking if user is expert or not"""
    if current_user.role not in [UserRole.EXPERT, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Expert role required.",
        )
    return current_user


async def get_admin_user(
    current_user: UsersModel = Depends(get_authenticated_user),
) -> UsersModel:
    """Dependency foe checking users role"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Admin role required.",
        )
    return current_user
