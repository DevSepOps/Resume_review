"""End-to-end-ish tests of the per-session controller using a fake page and a mock backend."""
import httpx

from app.router import SessionApp
from tests.conftest import FakeBackend, FakePage
from features.auth.components.login_view import LoginView
from features.resumes.components.upload_view import UploadView, validate_pdf_choice


def boot(settings, backend, route="/"):
    page = FakePage(route)
    app = SessionApp(page, settings, transport=httpx.MockTransport(backend))
    app.start()
    return page, app


def sign_in(app, username="alice", password="password1"):
    view = app._view
    assert isinstance(view, LoginView)
    view.username.value, view.password.value = username, password
    view._submit()


def test_start_redirects_to_login_and_builds_card(settings, backend):
    page, app = boot(settings, backend)
    assert page.went == ["/", "/login"] or page.went[-1] == "/login"
    assert page.views[-1].route == "/login"
    assert isinstance(app._view, LoginView)
    assert app._view.title.value == "Welcome back"
    assert len(app._view.background.particles) == 24


def test_login_flow_lands_on_resumes_and_loads_list(settings, backend):
    page, app = boot(settings, backend)
    sign_in(app)
    assert app.session.is_authenticated and page.views[-1].route == "/resumes"
    body = app._view.body.controls
    assert len(body) == 1  # one resume row, no loading panel left
    assert any(c.url.path == "/resumes/my-resumes" for c in backend.calls)


def test_wrong_password_shows_inline_error_and_stays(settings, backend):
    page, app = boot(settings, backend)
    view = app._view
    sign_in(app, password="wrongpass")
    assert view.message.visible and "Invalid credentials" in view.message.value
    assert not view.submit_button.disabled and not app.session.is_authenticated


def test_client_validation_blocks_request(settings, backend):
    page, app = boot(settings, backend)
    view = app._view
    sign_in(app, username="", password="")
    assert view.username.error_text and not backend.calls


def test_register_mode_toggle_and_success(settings):
    def handler(req):
        if req.url.path == "/users/register":
            return httpx.Response(201, json={"detail": "User registered successfully"})
        return httpx.Response(404)

    page, app = boot(settings, handler)
    view = app._view
    view._toggle_mode()
    assert view.email.visible and view.confirm.visible and view.submit_button.text == "Create account"
    view.username.value, view.email.value = "bob", "b@x.io"
    view.password.value = view.confirm.value = "password1"
    view._submit()
    assert view.submit_button.text == "Sign in" and "Account created" in view.message.value


def test_two_sessions_do_not_share_state(settings, backend):
    page_a, app_a = boot(settings, backend)
    page_b, app_b = boot(settings, backend)
    sign_in(app_a, username="alice")
    assert app_a.session.is_authenticated
    assert not app_b.session.is_authenticated and app_b.session.tokens.access is None
    assert app_a.session is not app_b.session and app_a.api is not app_b.api
    assert app_a.session.tokens is not app_b.session.tokens
    sign_in(app_b, username="bobby")
    assert app_a.session.tokens.access == "acc-alice" and app_b.session.tokens.access == "acc-bobby"
    app_a.auth.logout()
    assert app_b.session.is_authenticated


def test_role_guard_blocks_candidate_from_review(settings, backend):
    page, app = boot(settings, backend)
    sign_in(app)
    page.go("/review")
    assert page.views[-1].route == "/resumes"
    page.go("/admin/stats")
    assert page.views[-1].route == "/resumes"


def test_expert_can_open_review(settings):
    backend = FakeBackend("expert")
    page, app = boot(settings, backend)
    sign_in(app)
    page.go("/review")
    assert page.views[-1].route == "/review"


def test_logout_via_nav_clears_session(settings, backend):
    page, app = boot(settings, backend)
    sign_in(app)
    logout = [e for e in __import__("app.navigation", fromlist=["x"]).nav_entries_for("candidate") if e.key == "logout"][0]
    app._on_nav_select(logout)
    assert not app.session.is_authenticated and page.views[-1].route == "/login"


def test_session_expiry_redirects_to_login(settings, backend):
    page, app = boot(settings, backend)
    sign_in(app)
    from shared.lib.api_client import ApiError
    assert app.handle_api_error(ApiError("x", 500)) is False
    assert app.handle_api_error(ApiError("expired", 401, kind="session_expired")) is True
    assert page.views[-1].route == "/login" and not app.session.is_authenticated


def test_leaving_login_stops_animation(settings, backend):
    page, app = boot(settings, backend)
    login = app._view
    login.start()
    assert page.tasks
    sign_in(app)
    assert login.background._stopped is True


def test_close_cleans_up(settings, backend):
    page, app = boot(settings, backend)
    sign_in(app)
    app._on_close()
    assert not app.session.is_authenticated


def test_upload_forwards_staged_file_and_deletes_it(settings, backend, tmp_path):
    page = FakePage()
    from features.resumes.services.resume_service import ResumeService
    from shared.lib.api_client import ApiClient, TokenPair
    api = ApiClient("http://b.test", 5, TokenPair("a", "r"), transport=httpx.MockTransport(backend))
    done = []
    view = UploadView(page, ResumeService(api), upload_dir=settings.upload_tmp_dir, max_bytes=1024 * 1024,
                      on_error=lambda e: False, on_done=lambda: done.append(1))
    view.build()
    import os
    staged = "abc_cv.pdf"
    path = os.path.join(settings.upload_tmp_dir, staged)
    open(path, "wb").write(b"%PDF-1.4 hi")
    view._staged = staged
    view._file = type("F", (), {"name": "cv.pdf", "path": None, "size": 11})()
    view._on_upload(type("E", (), {"error": None, "progress": 1.0})())
    assert done == [1] and not os.path.exists(path)
    assert backend.calls[-1].url.path == "/resumes/upload"


def test_upload_error_event_shows_message(settings, backend):
    page = FakePage()
    view = UploadView(page, None, upload_dir=settings.upload_tmp_dir, max_bytes=10,
                      on_error=lambda e: False, on_done=lambda: None)
    view.build()
    view._on_upload(type("E", (), {"error": "boom", "progress": None})())
    assert view.error.visible and "boom" not in view.error.value


def test_validate_pdf_choice():
    assert validate_pdf_choice("a.txt", 5, 10)
    assert validate_pdf_choice("a.pdf", 0, 10)
    assert validate_pdf_choice("a.pdf", 11, 10)
    assert validate_pdf_choice("A.PDF", 5, 10) == ""
