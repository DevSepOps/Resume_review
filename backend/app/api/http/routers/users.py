from typing import Optional

from fastapi import APIRouter, Depends

from app.api.http.dependencies import get_access_token, get_auth_service, get_current_user
from app.internal.dto import (
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    TokenPairResponse,
    UserResponse,
)
from app.internal.entities import User
from app.internal.services import AuthService

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/register", status_code=201, response_model=MessageResponse)
def register(data: RegisterRequest, auth: AuthService = Depends(get_auth_service)):
    auth.register(data)
    return MessageResponse(detail="User registered successfully")


@router.post("/login", response_model=LoginResponse)
def login(data: LoginRequest, auth: AuthService = Depends(get_auth_service)):
    user, access, refresh = auth.login(data)
    return LoginResponse(
        access_token=access.token, refresh_token=refresh.token, role=user.role
    )


@router.post("/refresh_token", response_model=TokenPairResponse)
def refresh_token(data: RefreshRequest, auth: AuthService = Depends(get_auth_service)):
    access, refresh = auth.refresh(data.token)
    return TokenPairResponse(access_token=access.token, refresh_token=refresh.token)


@router.post("/logout", response_model=MessageResponse)
def logout(
    body: Optional[LogoutRequest] = None,
    token: str = Depends(get_access_token),
    _user: User = Depends(get_current_user),
    auth: AuthService = Depends(get_auth_service),
):
    auth.logout(token, body.refresh_token if body else None)
    return MessageResponse(detail="Successfully logged out")


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)):
    return user
