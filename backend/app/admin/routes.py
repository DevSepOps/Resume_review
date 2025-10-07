from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from sqlalchemy import or_

from app.core.database import get_db
from app.auth.jwt_auth import get_authenticated_user
from app.auth.role_auth import get_admin_user
from app.users.models import UsersModel, UserRole
from app.admin.schemas import UserRoleUpdate, UserResponse


router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=List[UserResponse])
async def get_all_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    role: Optional[UserRole] = Query(None),
    search: Optional[str] = Query(None),
    current_user: UsersModel = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Getting user's names and pagination"""
    query = db.query(UsersModel)

    if role:
        query = query.filter(UsersModel.role == role)

    if search:
        query = query.filter(
            or_(
                UsersModel.username.ilike(f"%{search}%"),
                UsersModel.email.ilike(f"%{search}%"),
            )
        )

    users = query.offset(skip).limit(limit).all()
    return users


@router.patch("/users/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    user_id: int,
    role_update: UserRoleUpdate,
    current_user: UsersModel = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Change user's role"""
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot change your own role")

    user = db.query(UsersModel).filter(UsersModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.role = role_update.role
    db.commit()
    db.refresh(user)

    return user


@router.patch("/users/{user_id}/activation", response_model=UserResponse)
async def toggle_user_activation(
    user_id: int,
    current_user: UsersModel = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Acitvate/Deactivate user for Admin"""
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")

    user = db.query(UsersModel).filter(UsersModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = not user.is_active
    db.commit()
    db.refresh(user)

    return user


@router.get("/stats")
async def get_system_stats(
    current_user: UsersModel = Depends(get_admin_user), db: Session = Depends(get_db)
):
    """System statistics for Admins"""
    from sqlalchemy import func
    from CV.models import Resume

    total_users = db.query(func.count(UsersModel.id)).scalar()
    total_resumes = db.query(func.count(Resume.id)).scalar()
    users_by_role = (
        db.query(UsersModel.role, func.count(UsersModel.id))
        .group_by(UsersModel.role)
        .all()
    )

    return {
        "total_users": total_users,
        "total_resumes": total_resumes,
        "users_by_role": {role.value: count for role, count in users_by_role},
    }


# ======================= Make an Admin just for Dev =======================
@router.post("/make-admin/{user_id}")
async def make_user_admin(user_id: int, db: Session = Depends(get_db)):
    """Setting Admin, Just for Dev"""
    user = db.query(UsersModel).filter(UsersModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.role = UserRole.ADMIN
    db.commit()

    return {"message": f"User {user.username} is now admin"}


# ======================= Make an Admin just for Dev =======================
