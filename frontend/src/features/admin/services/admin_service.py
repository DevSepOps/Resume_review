from __future__ import annotations

from typing import Any, Dict, List, Optional

from shared.lib.api_client import ApiClient, ApiError

ROLES = ("candidate", "expert", "admin")


class AdminService:
    def __init__(self, api: ApiClient) -> None:
        self._api = api

    def list_users(self, search: str = "", role: Optional[str] = None,
                   skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        params: Dict[str, Any] = {"skip": max(0, skip), "limit": max(1, min(limit, 200))}
        if search.strip():
            params["search"] = search.strip()
        if role in ROLES:
            params["role"] = role
        data = self._api.request_json("GET", "/admin/users", params=params)
        if not isinstance(data, list):
            raise ApiError("Unexpected response from the server.")
        return data

    def set_role(self, user_id: int, role: str) -> Dict[str, Any]:
        if role not in ROLES:
            raise ApiError("Unknown role.")
        return self._api.request_json("PATCH", f"/admin/users/{int(user_id)}/role", json={"role": role})

    def toggle_activation(self, user_id: int) -> Dict[str, Any]:
        return self._api.request_json("PATCH", f"/admin/users/{int(user_id)}/activation")

    def stats(self) -> Dict[str, Any]:
        data = self._api.request_json("GET", "/admin/stats")
        if not isinstance(data, dict):
            raise ApiError("Unexpected response from the server.")
        return data
