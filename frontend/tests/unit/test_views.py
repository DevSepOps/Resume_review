import json
import os

import httpx
import pytest

from features.admin.components.admin_view import StatsView, UsersView
from features.admin.services.admin_service import AdminService
from features.resumes.components.my_resumes_view import MyResumesView
from features.resumes.models import Resume
from features.resumes.services.resume_service import ResumeService
from features.review.components.review_view import ReviewView
from features.review.services.review_service import ReviewService
from shared.components.downloader import Downloader
from shared.lib.api_client import ApiClient, ApiError, TokenPair
from tests.conftest import FakePage

USER = {"id": 2, "username": "bob", "email": "b@x.io", "role": "candidate", "is_active": True,
        "created_date": "2026-01-01T00:00:00Z"}
RESUME = {"id": 4, "file_name": "cv.pdf", "file_size": 10, "created_date": "2026-03-12T14:05:00Z",
          "username": "bob", "email": "b@x.io", "github": "https://github.com/bob"}


@pytest.fixture
def env(tmp_path):
    state = {"calls": []}

    def handler(req):
        state["calls"].append((req.method, req.url.path))
        p = req.url.path
        if p.startswith("/resumes/download"):
            return httpx.Response(200, content=b"%PDF-1")
        if p == "/resumes/expert/all":
            return httpx.Response(200, json=[RESUME] * 50)
        if p == "/resumes/my-resumes":
            return httpx.Response(200, json=[RESUME])
        if p == "/admin/users":
            return httpx.Response(200, json=[USER, {**USER, "id": 1}])
        if p == "/admin/stats":
            return httpx.Response(200, json={"total_users": 3, "total_resumes": 4,
                                             "users_by_role": {"candidate": 2, "expert": 1, "admin": 0}})
        if req.method in ("PATCH", "DELETE"):
            return httpx.Response(200, json=USER)
        return httpx.Response(404)

    api = ApiClient("http://b.test", 5, TokenPair("a", "r"), transport=httpx.MockTransport(handler))
    page = FakePage()
    downloader = Downloader(page, str(tmp_path / "dl"))
    return page, api, downloader, state, tmp_path


def test_downloader_web_stages_file_and_opens_dialog(env):
    page, _, downloader, _, tmp = env
    downloader.deliver("my cv.pdf", b"%PDF-")
    assert len(page.opened) == 1
    url = page.opened[0].actions[0].url
    assert url.startswith("/dl/") and url.endswith("/my_cv.pdf")  # root-relative (see download_path)
    token = url.split("/")[-2]
    assert open(os.path.join(tmp, "dl", token, "my_cv.pdf"), "rb").read() == b"%PDF-"


def test_my_resumes_load_download_delete(env):
    page, api, downloader, state, _ = env
    view = MyResumesView(page, ResumeService(api), downloader, lambda e: False, lambda: None)
    view.build()
    view.load()
    assert len(view.body.controls) == 1
    resume = Resume.from_api(RESUME)
    view._download(resume)
    assert page.opened  # dialog offered
    view._delete(resume)
    assert ("DELETE", "/resumes/4") in state["calls"]
    view._confirm_delete(resume)
    assert page.opened[-1].modal


def test_my_resumes_error_state_and_session_expiry(env):
    page, api, downloader, _, _ = env
    api.tokens.clear()
    handled = []
    broken = ApiClient("http://b.test", 5, TokenPair("a", "r"),
                       transport=httpx.MockTransport(lambda r: httpx.Response(500)))
    view = MyResumesView(page, ResumeService(broken), downloader, lambda e: handled.append(e) or False, lambda: None)
    view.build()
    view.load()
    assert "temporarily unavailable" in view.body.controls[0].content.controls[1].value
    expired = MyResumesView(page, ResumeService(broken), downloader,
                            lambda e: True, lambda: None)
    expired.build()
    before = page.updates
    expired.load()
    assert page.updates == before  # handled by on_error: no further rendering


def test_review_view_paginates(env):
    page, api, downloader, state, _ = env
    view = ReviewView(page, ReviewService(api), downloader, lambda e: False)
    view.build()
    view.load()
    assert len(view.body.controls) == 51  # 50 rows + "Load more"
    view._load_more()
    assert len(view._resumes) == 100
    view._download(Resume.from_api(RESUME))
    assert page.opened


def test_users_view_role_change_toggle_and_self_protection(env):
    page, api, _, state, _ = env
    view = UsersView(page, AdminService(api), current_user_id=1, on_error=lambda e: False)
    view.build()
    view.load()
    assert len(view.body.controls) == 2
    row_me = view.body.controls[1].content.controls
    assert row_me[2].disabled is True and row_me[3].controls[1].disabled is True
    event = type("E", (), {"control": type("C", (), {"value": "expert"})()})()
    view._change_role(event, 2, "candidate")
    view._toggle(event, 2)
    assert ("PATCH", "/admin/users/2/role") in state["calls"]
    assert ("PATCH", "/admin/users/2/activation") in state["calls"]


def test_users_view_reverts_on_error(env):
    page, _, _, _, _ = env
    failing = ApiClient("http://b.test", 5, TokenPair("a", "r"), transport=httpx.MockTransport(
        lambda r: httpx.Response(403, json={"detail": "x"})))
    view = UsersView(page, AdminService(failing), 1, lambda e: False)
    ctrl = type("C", (), {"value": "admin"})()
    view._change_role(type("E", (), {"control": ctrl})(), 2, "candidate")
    assert ctrl.value == "candidate" and page.opened  # snackbar shown


def test_stats_view_renders_tiles(env):
    page, api, _, _, _ = env
    view = StatsView(page, AdminService(api), lambda e: False)
    view.build()
    view.load()
    assert len(view.body.controls[0].controls) == 5
