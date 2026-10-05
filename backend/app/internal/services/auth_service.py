"""Authentication use cases: register, login, refresh, logout, token authentication."""

from datetime import datetime, timezone
from typing import Optional

from app.internal.dto import LoginRequest, RegisterRequest
from app.internal.entities import IssuedToken, Role, TokenType, User
from app.internal.ports import (
    PasswordHasher,
    RevokedTokenRepository,
    TokenIssuer,
    UserRepository,
)
from app.pkg.errors import Conflict, Unauthorized


class AuthService:
    def __init__(
        self,
        users: UserRepository,
        revoked: RevokedTokenRepository,
        hasher: PasswordHasher,
        tokens: TokenIssuer,
        access_ttl_seconds: int,
        refresh_ttl_seconds: int,
    ) -> None:
        self._users = users
        self._revoked = revoked
        self._hasher = hasher
        self._tokens = tokens
        self._access_ttl = access_ttl_seconds
        self._refresh_ttl = refresh_ttl_seconds

    def register(self, data: RegisterRequest) -> User:
        if self._users.exists_username_or_email(data.username, data.email):
            raise Conflict("Username or Email already exists")
        user = User(
            username=data.username,
            email=data.email,
            password_hash=self._hasher.hash(data.password),
            github=data.github,
            role=Role.CANDIDATE,  # never taken from client input
        )
        return self._users.add(user)

    def login(self, data: LoginRequest) -> tuple[User, IssuedToken, IssuedToken]:
        user = self._users.get_by_username(data.username)
        if user is None or not self._hasher.verify(data.password, user.password_hash):
            raise Unauthorized("Invalid username or password")
        if not user.is_active:
            raise Unauthorized("User account is deactivated")
        return user, *self._issue_pair(user.id)

    def refresh(self, refresh_token: str) -> tuple[IssuedToken, IssuedToken]:
        claims = self._tokens.decode(refresh_token)
        if claims.type != TokenType.REFRESH:
            raise Unauthorized("Invalid token type. Expected refresh token.")
        if self._revoked.is_revoked(claims.jti):
            raise Unauthorized("Token has been revoked. Please login again.")
        user = self._users.get_by_id(claims.user_id)
        if user is None or not user.is_active:
            raise Unauthorized("User not found or deactivated")
        # Rotation: revoke() is atomic, a concurrent reuse of the same token loses.
        if not self._revoked.revoke(claims):
            raise Unauthorized("Token has been revoked. Please login again.")
        self._revoked.purge_expired(datetime.now(timezone.utc))
        return self._issue_pair(user.id)

    def logout(self, access_token: str, refresh_token: Optional[str] = None) -> None:
        access = self._tokens.decode(access_token)
        self._revoked.revoke(access)
        if refresh_token:
            try:
                refresh = self._tokens.decode(refresh_token)
            except Unauthorized:
                return  # already expired/invalid: nothing to revoke
            if refresh.type == TokenType.REFRESH and refresh.user_id == access.user_id:
                self._revoked.revoke(refresh)

    def authenticate_access_token(self, token: str) -> User:
        claims = self._tokens.decode(token)
        if claims.type != TokenType.ACCESS:
            raise Unauthorized("Authentication failed, token type not valid")
        if self._revoked.is_revoked(claims.jti):
            raise Unauthorized("Token has been revoked. Please login again.")
        user = self._users.get_by_id(claims.user_id)
        if user is None:
            raise Unauthorized("User not found")
        if not user.is_active:
            raise Unauthorized("User account is deactivated")
        return user

    def _issue_pair(self, user_id: int) -> tuple[IssuedToken, IssuedToken]:
        access = self._tokens.issue(user_id, TokenType.ACCESS, self._access_ttl)
        refresh = self._tokens.issue(user_id, TokenType.REFRESH, self._refresh_ttl)
        return access, refresh


__all__ = ["AuthService"]
