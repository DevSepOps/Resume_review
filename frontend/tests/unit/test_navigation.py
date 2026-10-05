from app import navigation as nav
from app.session import Session


def authed(role):
    s = Session()
    s.tokens.set("a", "r")
    s.role = role
    return s


def test_unauthenticated_users_are_sent_to_login():
    for path in (nav.RESUMES, nav.UPLOAD, nav.REVIEW, nav.ADMIN_USERS, "/", "/nope"):
        assert nav.resolve(path, Session()) == ("redirect", nav.LOGIN)
    assert nav.resolve(nav.LOGIN, Session()) == ("show", nav.LOGIN)


def test_authenticated_users_skip_login():
    assert nav.resolve("/login", authed("candidate")) == ("redirect", nav.HOME)
    assert nav.resolve("/", authed("candidate")) == ("redirect", nav.HOME)


def test_role_guards():
    assert nav.resolve("/review", authed("candidate")) == ("redirect", nav.HOME)
    assert nav.resolve("/review", authed("expert")) == ("show", "/review")
    assert nav.resolve("/admin/users", authed("expert")) == ("redirect", nav.HOME)
    assert nav.resolve("/admin/stats", authed("admin")) == ("show", "/admin/stats")


def test_query_and_trailing_slash_are_ignored():
    assert nav.resolve("/resumes/?x=1", authed("candidate")) == ("show", "/resumes")


def test_nav_entries_per_role():
    keys = lambda role: [e.key for e in nav.nav_entries_for(role)]
    assert keys("candidate") == ["resumes", "upload", "logout"]
    assert keys("expert") == ["resumes", "upload", "review", "logout"]
    assert keys("admin") == ["resumes", "upload", "review", "users", "stats", "logout"]
    assert nav.nav_entries_for("candidate")[-1].route is None
