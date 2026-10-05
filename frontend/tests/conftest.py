from __future__ import annotations

import json
from typing import Any, Callable, Dict, List

import httpx
import pytest

from config.settings import Settings, load_settings


class FakePage:
    """Minimal stand-in for ft.Page (web mode) so SessionApp/views can be exercised without a browser."""

    def __init__(self, route: str = "/") -> None:
        self.web = True
        self.width = 1280
        self.height = 800
        self.route = route
        self.url = "http://localhost:8001/"
        self.session_id = "sess"
        self.views: List[Any] = []
        self.overlay: List[Any] = []
        self.opened: List[Any] = []
        self.tasks: List[Any] = []
        self.went: List[str] = []
        self.updates = 0
        self.on_route_change: Callable = lambda e: None

    def go(self, route: str, **_: Any) -> None:
        self.route = route
        self.went.append(route)
        self.on_route_change(None)

    def update(self, *_: Any) -> None:
        self.updates += 1

    def open(self, control: Any) -> None:
        self.opened.append(control)

    def close(self, control: Any) -> None:
        pass

    def run_task(self, fn: Callable, *a: Any, **k: Any) -> None:
        self.tasks.append(fn)

    def get_upload_url(self, name: str, expires: int) -> str:
        return f"http://localhost:8001/upload?f={name}"


class FakeBackend:
    """httpx.MockTransport handler implementing the slice of the contract the UI uses."""

    def __init__(self, role: str = "candidate") -> None:
        self.role = role
        self.calls: List[httpx.Request] = []
        self.resumes: List[Dict[str, Any]] = [
            {"id": 1, "user_id": 1, "file_name": "cv.pdf", "file_size": 2048,
             "mime_type": "application/pdf", "created_date": "2026-03-12T14:05:00Z", "updated_date": None}]

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.calls.append(request)
        path, method = request.url.path, request.method
        if path == "/users/login":
            body = json.loads(request.content)
            if body["password"] != "password1":
                return httpx.Response(401, json={"error": True, "status_code": 401, "detail": "Invalid credentials"})
            return httpx.Response(200, json={"access_token": f"acc-{body['username']}", "refresh_token": "ref",
                                             "token_type": "bearer", "role": self.role})
        if path == "/users/me":
            return httpx.Response(200, json={"id": 7, "username": "alice", "role": self.role})
        if path == "/resumes/my-resumes":
            return httpx.Response(200, json=self.resumes)
        if path == "/resumes/upload" and method == "POST":
            return httpx.Response(201, json={"message": "ok", "resume": {**self.resumes[0], "id": 2}})
        if path == "/users/logout":
            return httpx.Response(200, json={"detail": "Successfully logged out"})
        return httpx.Response(404, json={"detail": "nope"})


@pytest.fixture
def settings(tmp_path) -> Settings:
    base = load_settings({"FLET_SECRET_KEY": "k", "BACKEND_URL": "http://backend.test",
                          "UPLOAD_TMP_DIR": str(tmp_path / "up")})
    (tmp_path / "up").mkdir()
    return base


@pytest.fixture
def backend() -> FakeBackend:
    return FakeBackend()
