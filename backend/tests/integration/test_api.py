import io
import logging

import pytest
from sqlalchemy import select, text

from app.internal.adapters.db.models import RevokedTokenModel, UserModel
from app.internal.entities import Role
from tests.fixtures.factories import register_payload

PDF = b"%PDF-1.4\n%fake but valid header\n"


def register(client, **kw):
    return client.post("/users/register", json=register_payload(**kw))


def login(client, username="alice", password="Password123"):
    return client.post("/users/login", json={"username": username, "password": password})


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def make_user(client, username, role=None, container=None):
    register(client, username=username, email=f"{username}@example.com")
    if role is not None:
        with container.session_scope() as s:
            s.execute(
                UserModel.__table__.update()
                .where(UserModel.username == username)
                .values(role=role)
            )
            s.commit()
    body = login(client, username).json()
    return body["access_token"], body["refresh_token"]


def upload(client, token, content=PDF, name="cv.pdf", ctype="application/pdf"):
    return client.post(
        "/resumes/upload",
        headers=auth(token),
        files={"resume": (name, io.BytesIO(content), ctype)},
    )


# ---------------- health ----------------
def test_health_and_ready(client):
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/ready").json() == {"status": "ready"}


def test_ready_503_when_db_down(settings, tmp_path):
    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine

    from app.api.http.app import create_app
    from app.api.http.dependencies import Container

    bad = create_engine(f"sqlite:///{tmp_path}/missing/dir/x.db")
    app = create_app(settings, Container(settings, engine=bad))
    with TestClient(app, raise_server_exceptions=False) as c:
        assert c.get("/health").status_code == 200  # liveness never touches the DB
        r = c.get("/ready")
    assert r.status_code == 503
    assert r.json() == {"error": True, "status_code": 503, "detail": "Database unavailable"}


# ---------------- users ----------------
def test_register_login_me_flow(client):
    r = register(client)
    assert r.status_code == 201 and r.json() == {"detail": "User registered successfully"}
    body = login(client).json()
    assert body["token_type"] == "bearer" and body["role"] == "candidate"
    me = client.get("/users/me", headers=auth(body["access_token"])).json()
    assert me["username"] == "alice" and me["github"] is None and "password" not in me


def test_register_cannot_self_assign_role(client):
    """Regression: registration used to accept role=expert."""
    register(client, role="expert")
    assert login(client).json()["role"] == "candidate"
    register(client, username="mallory", email="m@example.com", role="admin")
    assert login(client, "mallory").json()["role"] == "candidate"


def test_register_duplicate_is_409_with_envelope(client):
    register(client)
    r = register(client)
    assert r.status_code == 409
    assert r.json() == {"error": True, "status_code": 409, "detail": "Username or Email already exists"}


def test_register_validation_error_envelope_and_no_password_echo(client):
    r = register(client, password="short", confirm_password="short")
    body = r.json()
    assert r.status_code == 422 and body["error"] is True and body["status_code"] == 422
    assert isinstance(body["detail"], list)
    assert "short" not in r.text.replace("shortest", "")  # input value not echoed


def test_register_rejects_73_byte_password(client):
    pw = "a" * 73
    assert register(client, password=pw, confirm_password=pw).status_code == 422
    pw = "a" * 72
    assert register(client, password=pw, confirm_password=pw).status_code == 201


def test_login_wrong_password_and_inactive(client, container):
    register(client)
    r = login(client, password="Wrong-pass1")
    assert r.status_code == 401 and r.json()["error"] is True
    assert r.headers["www-authenticate"] == "Bearer"
    with container.session_scope() as s:
        s.execute(UserModel.__table__.update().values(is_active=False))
        s.commit()
    assert login(client).status_code == 401


def test_me_requires_valid_token(client):
    assert client.get("/users/me").status_code == 401
    assert client.get("/users/me", headers=auth("garbage")).status_code == 401


def test_refresh_rotation_and_reuse_rejected(client):
    register(client)
    body = login(client).json()
    r = client.post("/users/refresh_token", json={"token": body["refresh_token"]})
    assert r.status_code == 200
    new = r.json()
    assert set(new) == {"access_token", "refresh_token", "token_type"}
    assert client.get("/users/me", headers=auth(new["access_token"])).status_code == 200
    again = client.post("/users/refresh_token", json={"token": body["refresh_token"]})
    assert again.status_code == 401


def test_refresh_rejects_access_token(client):
    register(client)
    body = login(client).json()
    r = client.post("/users/refresh_token", json={"token": body["access_token"]})
    assert r.status_code == 401


def test_refresh_rejects_deactivated_user(client, container):
    register(client)
    body = login(client).json()
    with container.session_scope() as s:
        s.execute(UserModel.__table__.update().values(is_active=False))
        s.commit()
    assert client.post("/users/refresh_token", json={"token": body["refresh_token"]}).status_code == 401


def test_logout_revokes_tokens_and_is_idempotent_at_db_level(client, container):
    register(client)
    body = login(client).json()
    r = client.post(
        "/users/logout",
        headers=auth(body["access_token"]),
        json={"refresh_token": body["refresh_token"]},
    )
    assert r.status_code == 200 and r.json() == {"detail": "Successfully logged out"}
    assert client.get("/users/me", headers=auth(body["access_token"])).status_code == 401
    assert client.post("/users/refresh_token", json={"token": body["refresh_token"]}).status_code == 401
    with container.session_scope() as s:
        assert len(s.scalars(select(RevokedTokenModel)).all()) == 2


def test_logout_without_body(client):
    register(client)
    body = login(client).json()
    assert client.post("/users/logout", headers=auth(body["access_token"])).status_code == 200


def test_revoking_same_token_twice_does_not_500(container):
    """Regression: blacklisting a token twice raised IntegrityError -> 500."""
    from app.internal.adapters.db import SqlRevokedTokenRepository
    from app.internal.adapters.security import JwtTokenIssuer
    from app.internal.entities import TokenType

    issued = JwtTokenIssuer("k" * 40).issue(1, TokenType.ACCESS, 60)
    with container.session_scope() as s:
        repo = SqlRevokedTokenRepository(s)
        assert repo.revoke(issued.claims) is True
        assert repo.revoke(issued.claims) is False
        assert repo.is_revoked(issued.claims.jti)


def test_unique_jti_per_login(client, container):
    register(client)
    t1, t2 = login(client).json(), login(client).json()
    assert t1["access_token"] != t2["access_token"]


def test_legacy_passlib_hash_still_logs_in(client, container):
    """Regression: existing $2b$ hashes must keep working after dropping passlib."""
    import bcrypt

    legacy = bcrypt.hashpw(b"Password123", bcrypt.gensalt(prefix=b"2b")).decode()
    assert legacy.startswith("$2b$")
    register(client)
    with container.session_scope() as s:
        s.execute(UserModel.__table__.update().values(password=legacy))
        s.commit()
    assert login(client).status_code == 200


def test_unhandled_error_returns_generic_500_and_logs_details(client, container, caplog):
    def boom(*a, **k):
        raise RuntimeError("secret internal detail")

    container.auth_service = boom
    with caplog.at_level(logging.ERROR):
        r = client.post("/users/login", json={"username": "a", "password": "b"})
    assert r.status_code == 500
    assert r.json() == {"error": True, "status_code": 500, "detail": "Internal server error"}
    assert "secret internal detail" not in r.text
    assert any(rec.exc_info for rec in caplog.records)


def test_cors_exact_origin_only(client):
    ok = client.options(
        "/users/login",
        headers={"Origin": "http://localhost:8001", "Access-Control-Request-Method": "POST"},
    )
    assert ok.headers.get("access-control-allow-origin") == "http://localhost:8001"
    bad = client.options(
        "/users/login",
        headers={"Origin": "http://evil.example", "Access-Control-Request-Method": "POST"},
    )
    assert bad.headers.get("access-control-allow-origin") is None


# ---------------- resumes ----------------
def test_upload_list_download_delete(client, settings):
    token, _ = make_user(client, "alice")
    r = upload(client, token)
    assert r.status_code == 201
    resume = r.json()["resume"]
    assert resume["file_name"] == "cv.pdf" and resume["file_size"] == len(PDF)
    assert "file_path" not in resume and "storage_key" not in resume

    files = list(__import__("pathlib").Path(settings.UPLOAD_DIR).iterdir())
    assert len(files) == 1 and files[0].suffix == ".pdf" and files[0].name != "cv.pdf"

    assert len(client.get("/resumes/my-resumes", headers=auth(token)).json()) == 1
    d = client.get(f"/resumes/download/{resume['id']}", headers=auth(token))
    assert d.status_code == 200 and d.content == PDF
    assert d.headers["content-type"] == "application/pdf"
    assert "attachment" in d.headers["content-disposition"]

    r = client.delete(f"/resumes/{resume['id']}", headers=auth(token))
    assert r.json() == {"detail": "Resume deleted successfully"}
    assert list(__import__("pathlib").Path(settings.UPLOAD_DIR).iterdir()) == []
    assert client.get(f"/resumes/download/{resume['id']}", headers=auth(token)).status_code == 404


def test_upload_requires_auth(client):
    r = client.post("/resumes/upload", files={"resume": ("a.pdf", PDF, "application/pdf")})
    assert r.status_code == 401


def test_upload_checks_magic_bytes_not_content_type(client, settings):
    """Regression: only the client-declared content_type used to be checked."""
    token, _ = make_user(client, "alice")
    r = upload(client, token, content=b"<script>alert(1)</script>", ctype="application/pdf")
    assert r.status_code == 400 and r.json()["error"] is True
    assert upload(client, token, content=b"", ctype="application/pdf").status_code == 400
    assert list(__import__("pathlib").Path(settings.UPLOAD_DIR).iterdir()) == []
    # a real PDF is accepted even with a wrong declared content type
    assert upload(client, token, ctype="application/octet-stream").status_code == 201


def test_upload_too_large_is_413_not_500(client, settings):
    """Regression: the size HTTPException used to be swallowed into a 500."""
    token, _ = make_user(client, "alice")
    big = b"%PDF-" + b"0" * (1024 * 1024)  # MAX_UPLOAD_MB=1 in tests
    r = upload(client, token, content=big)
    assert r.status_code == 413
    assert r.json()["status_code"] == 413 and r.json()["error"] is True
    assert list(__import__("pathlib").Path(settings.UPLOAD_DIR).iterdir()) == []


def test_upload_filename_is_sanitized(client):
    token, _ = make_user(client, "alice")
    r = upload(client, token, name="../../evil.pdf")
    assert r.json()["resume"]["file_name"] == "evil.pdf"


def test_candidate_cannot_access_others_resume(client):
    alice, _ = make_user(client, "alice")
    bob, _ = make_user(client, "bob")
    rid = upload(client, alice).json()["resume"]["id"]
    assert client.get(f"/resumes/download/{rid}", headers=auth(bob)).status_code == 403
    assert client.delete(f"/resumes/{rid}", headers=auth(bob)).status_code == 403


def test_expert_downloads_any_but_cannot_delete(client, container):
    alice, _ = make_user(client, "alice")
    expert, _ = make_user(client, "eve", Role.EXPERT, container)
    rid = upload(client, alice).json()["resume"]["id"]
    assert client.get(f"/resumes/download/{rid}", headers=auth(expert)).status_code == 200
    assert client.delete(f"/resumes/{rid}", headers=auth(expert)).status_code == 403


def test_admin_can_delete_any(client, container):
    alice, _ = make_user(client, "alice")
    admin, _ = make_user(client, "root", Role.ADMIN, container)
    rid = upload(client, alice).json()["resume"]["id"]
    assert client.delete(f"/resumes/{rid}", headers=auth(admin)).status_code == 200


def test_expert_all_is_role_gated_and_paginated(client, container):
    alice, _ = make_user(client, "alice")
    expert, _ = make_user(client, "eve", Role.EXPERT, container)
    for _ in range(3):
        upload(client, alice)
    assert client.get("/resumes/expert/all", headers=auth(alice)).status_code == 403
    rows = client.get("/resumes/expert/all?skip=1&limit=2", headers=auth(expert)).json()
    assert len(rows) == 2
    assert rows[0]["username"] == "alice" and rows[0]["email"] == "alice@example.com"
    assert "file_path" not in rows[0]
    assert client.get("/resumes/expert/all?limit=201", headers=auth(expert)).status_code == 422


# ---------------- admin ----------------
def test_make_admin_endpoint_is_gone(client):
    """Regression: unauthenticated POST /admin/make-admin/{id} allowed privilege escalation."""
    register(client)
    assert client.post("/admin/make-admin/1").status_code in (404, 405)
    assert login(client).json()["role"] == "candidate"


def test_admin_endpoints_forbidden_for_non_admin(client, container):
    alice, _ = make_user(client, "alice")
    expert, _ = make_user(client, "eve", Role.EXPERT, container)
    for tok in (alice, expert):
        r = client.get("/admin/users", headers=auth(tok))
        assert r.status_code == 403, r.text
        assert client.get("/admin/stats", headers=auth(tok)).status_code == 403
    assert client.get("/admin/stats").status_code == 401


def test_admin_stats_works(client, container):
    """Regression: /admin/stats had a broken import and always failed."""
    admin, _ = make_user(client, "root", Role.ADMIN, container)
    alice, _ = make_user(client, "alice")
    upload(client, alice)
    r = client.get("/admin/stats", headers=auth(admin))
    assert r.status_code == 200
    assert r.json() == {
        "total_users": 2,
        "total_resumes": 1,
        "users_by_role": {"candidate": 1, "expert": 0, "admin": 1},
    }


def test_admin_user_management(client, container):
    admin, _ = make_user(client, "root", Role.ADMIN, container)
    make_user(client, "alice")
    users = client.get("/admin/users", headers=auth(admin)).json()
    assert {u["username"] for u in users} == {"root", "alice"}
    assert [u["username"] for u in client.get("/admin/users?role=admin", headers=auth(admin)).json()] == ["root"]
    assert [u["username"] for u in client.get("/admin/users?search=ALI", headers=auth(admin)).json()] == ["alice"]
    alice_id = next(u["id"] for u in users if u["username"] == "alice")
    root_id = next(u["id"] for u in users if u["username"] == "root")

    r = client.patch(f"/admin/users/{alice_id}/role", headers=auth(admin), json={"role": "expert"})
    assert r.status_code == 200 and r.json()["role"] == "expert"
    assert client.patch(f"/admin/users/{root_id}/role", headers=auth(admin), json={"role": "candidate"}).status_code == 400
    assert client.patch("/admin/users/999/role", headers=auth(admin), json={"role": "expert"}).status_code == 404

    r = client.patch(f"/admin/users/{alice_id}/activation", headers=auth(admin))
    assert r.json()["is_active"] is False
    assert login(client, "alice").status_code == 401
    assert client.patch(f"/admin/users/{root_id}/activation", headers=auth(admin)).status_code == 400


def test_updated_date_changes_on_update(client, container):
    """Regression: updated_date had server_onupdate (no-op); now onupdate=func.now()."""
    from sqlalchemy.orm import Session

    register(client)
    with container.session_scope() as s:
        m = s.scalar(select(UserModel))
        col = UserModel.__table__.c.updated_date
        assert col.onupdate is not None
        s.execute(text("UPDATE users SET updated_date = '2000-01-01 00:00:00'"))
        s.commit()
        s.expire_all()
        m = s.scalar(select(UserModel))
        m.github = "https://github.com/alice"
        s.commit()
        s.refresh(m)
        assert m.updated_date.year != 2000


def test_resume_lists_should_be_newest_first(client, container):
    token, _ = make_user(client, "orderer")
    upload(client, token, name="first.pdf")
    upload(client, token, name="second.pdf")
    expert, _ = make_user(client, "orderexpert", role=Role.EXPERT, container=container)

    mine = client.get("/resumes/my-resumes", headers=auth(token)).json()
    review = client.get("/resumes/expert/all", headers=auth(expert)).json()

    assert [r["file_name"] for r in mine] == ["second.pdf", "first.pdf"]
    assert [r["file_name"] for r in review][:2] == ["second.pdf", "first.pdf"]
