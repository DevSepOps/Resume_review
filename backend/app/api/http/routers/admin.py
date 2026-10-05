from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.api.http.dependencies import get_admin_service, require_admin
from app.internal.dto import RoleUpdateRequest, StatsResponse, UserResponse
from app.internal.entities import Role, User
from app.internal.services import AdminService

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=list[UserResponse])
def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    role: Optional[Role] = Query(None),
    search: Optional[str] = Query(None, max_length=100),
    _admin: User = Depends(require_admin),
    service: AdminService = Depends(get_admin_service),
):
    return service.list_users(skip, limit, role, search)


@router.patch("/users/{user_id}/role", response_model=UserResponse)
def update_role(
    user_id: int,
    body: RoleUpdateRequest,
    admin: User = Depends(require_admin),
    service: AdminService = Depends(get_admin_service),
):
    return service.set_role(admin, user_id, body.role)


@router.patch("/users/{user_id}/activation", response_model=UserResponse)
def toggle_activation(
    user_id: int,
    admin: User = Depends(require_admin),
    service: AdminService = Depends(get_admin_service),
):
    return service.toggle_activation(admin, user_id)


@router.get("/stats", response_model=StatsResponse)
def stats(
    _admin: User = Depends(require_admin),
    service: AdminService = Depends(get_admin_service),
):
    return service.stats()
