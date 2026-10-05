import json

import httpx
import pytest

from app.session import Session
from features.admin.services.admin_service import AdminService
from features.auth.services.auth_service import AuthService
from features.resumes.models import Resume
from features.resumes.services.resume_service import ResumeService
from features.review.services.review_service import ReviewService
from shared.lib.api_client import ApiClient, ApiError


def api_for(handler, session=None):
    session = session or Session()
    return ApiClient("http://b.test", 5, session.tokens, transport=httpx.MockTransport(handler)), session


def test_login_stores_tokens_role_and_user(backend):
    api, session = api_for(backend)
    role = AuthService(api, session).login(" Alice ", "password1")
    assert role == "candidate" and session.is_authenticated
    assert session.tokens.access == "acc-alice" and session.username == "alice"
    assert json.loads(backend.calls[0].content)["username"] == "alice"


def test_login_failure_leaves_session_empty(backend):
    api, session = api_for(backend)
    with pytest.raises(ApiError) as exc:
        AuthService(api, session).login("alice", "wrong")
    assert "Invalid credentials" in exc.value.message and not session.is_authenticated


def test_register_omits_blank_github():
    sent = {}

    def handler(req):
        sent.update(json.loads(req.content))
        return httpx.Response(201, json={"detail": "User registered successfully"})

    api, session = api_for(handler)
    AuthService(api, session).register("bob", "b@x.io", "password1", "password1", "  ")
    assert "github" not in sent and sent["username"] == "bob"


def test_logout_sends_refresh_token_and_always_clears(backend):
    api, session = api_for(backend)
    auth = AuthService(api, session)
    auth.login("alice", "password1")
    auth.logout()
    last = backend.calls[-1]
    assert last.url.path == "/users/logout" and json.loads(last.content) == {"refresh_token": "ref"}
    assert not session.is_authenticated and session.user is None


def test_logout_clears_even_if_server_down(backend):
    def down(req):
        raise httpx.ConnectError("x")

    api, session = api_for(down)
    session.tokens.set("a", "r")
    session.role = "candidate"
    AuthService(api, session).logout()
    assert not session.is_authenticated


def test_resume_list_uses_created_date(backend):
    api, _ = api_for(backend)
    items = ResumeService(api).list_mine()
    assert items == [Resume(1, "cv.pdf", 2048, "2026-03-12T14:05:00Z")]


def test_resume_list_rejects_malformed_payload():
    api, _ = api_for(lambda r: httpx.Response(200, json={"not": "a list"}))
    with pytest.raises(ApiError):
        ResumeService(api).list_mine()
    api, _ = api_for(lambda r: httpx.Response(200, json=[{"no_id": 1}]))
    with pytest.raises(ApiError):
        ResumeService(api).list_mine()


def test_upload_sends_multipart_with_sanitised_name(backend):
    api, _ = api_for(backend)
    result = ResumeService(api).upload("../evil name.pdf", b"%PDF-1.4 data")
    req = backend.calls[-1]
    assert req.headers["content-type"].startswith("multipart/form-data")
    assert b'name="resume"' in req.content and b'filename="evil_name.pdf"' in req.content
    assert b"%PDF-1.4 data" in req.content and result.id == 2


def test_delete_and_download_paths():
    seen = []

    def handler(req):
        seen.append((req.method, req.url.path))
        if req.method == "DELETE":
            return httpx.Response(200, json={"detail": "Resume deleted successfully"})
        return httpx.Response(200, content=b"%PDF-", headers={"content-type": "application/pdf"})

    api, _ = api_for(handler)
    svc = ResumeService(api)
    svc.delete(5)
    name, data = svc.download(5, "a b.pdf")
    assert seen == [("DELETE", "/resumes/5"), ("GET", "/resumes/download/5")]
    assert (name, data) == ("a_b.pdf", b"%PDF-")


def test_review_list_clamps_params_and_parses_owner():
    captured = {}

    def handler(req):
        captured.update(dict(req.url.params))
        return httpx.Response(200, json=[{"id": 3, "file_name": "x.pdf", "file_size": 1, "created_date": None,
                                          "username": "carl", "email": "c@x.io", "github": None}])

    api, _ = api_for(handler)
    items = ReviewService(api).list_all(skip=-5, limit=9999)
    assert captured == {"skip": "0", "limit": "200"} and items[0].username == "carl"


def test_admin_service_calls():
    seen = []

    def handler(req):
        seen.append((req.method, req.url.path, dict(req.url.params), req.content))
        if req.url.path == "/admin/stats":
            return httpx.Response(200, json={"total_users": 1, "total_resumes": 2, "users_by_role": {}})
        if req.url.path == "/admin/users":
            return httpx.Response(200, json=[])
        return httpx.Response(200, json={"id": 2})

    api, _ = api_for(handler)
    svc = AdminService(api)
    svc.list_users(search=" bo ", role="expert")
    svc.set_role(2, "admin")
    svc.toggle_activation(2)
    assert svc.stats()["total_resumes"] == 2
    assert seen[0][2] == {"skip": "0", "limit": "100", "search": "bo", "role": "expert"}
    assert seen[1][:2] == ("PATCH", "/admin/users/2/role") and json.loads(seen[1][3]) == {"role": "admin"}
    assert seen[2][:2] == ("PATCH", "/admin/users/2/activation")
    with pytest.raises(ApiError):
        svc.set_role(2, "root")
