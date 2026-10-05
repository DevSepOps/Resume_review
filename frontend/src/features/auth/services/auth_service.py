"""Authentication use cases. Tokens go to the per-session TokenPair only."""
from __future__ import annotations

import logging
from typing import Optional

from app.session import Session
from shared.lib.api_client import ApiClient, ApiError

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, api: ApiClient, session: Session) -> None:
        self._api = api
        self._session = session

    def login(self, username: str, password: str) -> str:
        """Sign in and return the user's role."""
        data = self._api.request_json(
            "POST", "/users/login", auth=False,
            json={"username": username.strip().lower(), "password": password},
        )
        access, refresh, role = data.get("access_token"), data.get("refresh_token"), data.get("role")
        if not access or not role:
            raise ApiError("Unexpected response from the server.")
        self._api.tokens.set(access, refresh)
        self._session.role = role
        try:
            self._session.user = self._api.request_json("GET", "/users/me")
        except ApiError:
            self._session.user = {"username": username.strip().lower()}
        return role

    def register(self, username: str, email: str, password: str,
                 confirm_password: str, github: Optional[str] = None) -> None:
        payload = {
            "username": username.strip(), "email": email.strip(),
            "password": password, "confirm_password": confirm_password,
        }
        if github and github.strip():
            payload["github"] = github.strip()
        self._api.request_json("POST", "/users/register", auth=False, json=payload)

    def logout(self) -> None:
        """Best-effort server-side revoke, then always clear local state."""
        try:
            if self._api.tokens.access:
                body = {"refresh_token": self._api.tokens.refresh} if self._api.tokens.refresh else None
                self._api.request("POST", "/users/logout", json=body)
        except ApiError:
            logger.info("Logout request failed; clearing local session anyway")
        finally:
            self._session.clear()
