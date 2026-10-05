import pytest

from app.internal.entities import Role
from app.internal.services import AdminService
from app.pkg.errors import NotFound, ValidationFailed
from tests.fixtures.factories import UserFactory
from tests.fixtures.fakes import FakeHasher, FakeResumeRepo, FakeUserRepo


@pytest.fixture
def env():
    users = FakeUserRepo()
    svc = AdminService(users, FakeResumeRepo(users), FakeHasher())
    admin = users.add(UserFactory(id=None, username="adm", email="a@x.com", role=Role.ADMIN))
    cand = users.add(UserFactory(id=None, username="cand", email="c@x.com"))
    return svc, users, admin, cand


def test_set_role(env):
    svc, _, admin, cand = env
    assert svc.set_role(admin, cand.id, Role.EXPERT).role == Role.EXPERT
    with pytest.raises(ValidationFailed):
        svc.set_role(admin, admin.id, Role.CANDIDATE)
    with pytest.raises(NotFound):
        svc.set_role(admin, 999, Role.EXPERT)


def test_toggle_activation(env):
    svc, _, admin, cand = env
    assert svc.toggle_activation(admin, cand.id).is_active is False
    assert svc.toggle_activation(admin, cand.id).is_active is True
    with pytest.raises(ValidationFailed):
        svc.toggle_activation(admin, admin.id)
    with pytest.raises(NotFound):
        svc.toggle_activation(admin, 999)


def test_stats_has_all_roles(env):
    svc, *_ = env
    assert svc.stats() == {
        "total_users": 2,
        "total_resumes": 0,
        "users_by_role": {"candidate": 1, "expert": 0, "admin": 1},
    }


def test_list_users_filters(env):
    svc, *_ = env
    assert [u.username for u in svc.list_users(0, 10, Role.ADMIN)] == ["adm"]
    assert [u.username for u in svc.list_users(0, 10, search="cand")] == ["cand"]


def test_ensure_admin_creates_then_is_idempotent(env):
    svc, users, *_ = env
    user, created = svc.ensure_admin("Boss", "Boss@X.com", lambda: "Password123")
    assert created and user.role == Role.ADMIN and user.username == "boss"
    again, created2 = svc.ensure_admin("boss", "boss@x.com", lambda: pytest.fail("no prompt"))
    assert not created2 and again.id == user.id
    assert users.count() == 3


def test_ensure_admin_promotes_existing_and_reactivates(env):
    svc, users, _, cand = env
    users.items[cand.id].is_active = False
    user, created = svc.ensure_admin("cand", "c@x.com", lambda: pytest.fail("no prompt"))
    assert not created and user.role == Role.ADMIN and user.is_active


def test_ensure_admin_validates(env):
    svc, *_ = env
    with pytest.raises(ValidationFailed):
        svc.ensure_admin("x", "x@x.com", lambda: "Password123")
    with pytest.raises(ValidationFailed):
        svc.ensure_admin("newadmin", "n@x.com", lambda: "short")
