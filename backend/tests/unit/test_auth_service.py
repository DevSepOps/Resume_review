import pytest
from pydantic import ValidationError

from app.internal.dto import LoginRequest, RegisterRequest
from app.internal.entities import Role, TokenType
from app.internal.services import AuthService
from app.pkg.errors import Conflict, Unauthorized
from tests.fixtures.fakes import FakeHasher, FakeRevokedRepo, FakeTokens, FakeUserRepo
from tests.fixtures.factories import register_payload


@pytest.fixture
def env():
    users, revoked, tokens = FakeUserRepo(), FakeRevokedRepo(), FakeTokens()
    svc = AuthService(users, revoked, FakeHasher(), tokens, 900, 86400)
    return svc, users, revoked, tokens


def register(svc, **kw):
    return svc.register(RegisterRequest(**register_payload(**kw)))


def login(svc, username="alice", password="Password123"):
    return svc.login(LoginRequest(username=username, password=password))


def test_register_creates_candidate_with_hashed_password(env):
    svc, users, *_ = env
    user = register(svc)
    assert user.role == Role.CANDIDATE
    assert users.items[user.id].password_hash == "hashed:Password123"


def test_register_ignores_client_supplied_role(env):
    """Regression: self-assigned expert/admin role."""
    svc, *_ = env
    for role in ("expert", "admin"):
        user = register(svc, username=f"u_{role}", email=f"{role}@x.com", role=role)
        assert user.role == Role.CANDIDATE


def test_register_duplicate_conflicts(env):
    svc, *_ = env
    register(svc)
    with pytest.raises(Conflict):
        register(svc, email="other@example.com")
    with pytest.raises(Conflict):
        register(svc, username="other")


def test_register_dto_rejects_bad_input():
    with pytest.raises(ValidationError):
        RegisterRequest(**register_payload(confirm_password="different1"))
    with pytest.raises(ValidationError):
        RegisterRequest(**register_payload(password="a" * 73, confirm_password="a" * 73))
    with pytest.raises(ValidationError):
        RegisterRequest(**register_payload(github="https://evil.com/x"))


def test_register_dto_lowercases():
    dto = RegisterRequest(**register_payload(username="ALICE", email="Alice@Example.COM"))
    assert (dto.username, dto.email) == ("alice", "alice@example.com")


def test_login_ok_and_tokens_have_unique_jti(env):
    svc, *_ = env
    register(svc)
    _, a1, r1 = login(svc)
    _, a2, r2 = login(svc)
    assert len({a1.claims.jti, r1.claims.jti, a2.claims.jti, r2.claims.jti}) == 4
    assert a1.claims.type == TokenType.ACCESS and r1.claims.type == TokenType.REFRESH


def test_login_bad_credentials(env):
    svc, *_ = env
    register(svc)
    with pytest.raises(Unauthorized):
        login(svc, password="wrongpass1")
    with pytest.raises(Unauthorized):
        login(svc, username="nobody")


def test_login_inactive_user(env):
    svc, users, *_ = env
    user = register(svc)
    users.items[user.id].is_active = False
    with pytest.raises(Unauthorized):
        login(svc)


def test_authenticate_access_token(env):
    svc, *_ = env
    register(svc)
    _, access, refresh = login(svc)
    assert svc.authenticate_access_token(access.token).username == "alice"
    with pytest.raises(Unauthorized):
        svc.authenticate_access_token(refresh.token)  # wrong type
    with pytest.raises(Unauthorized):
        svc.authenticate_access_token("garbage")


def test_authenticate_rejects_deactivated_and_revoked(env):
    svc, users, *_ = env
    user = register(svc)
    _, access, refresh = login(svc)
    svc.logout(access.token)
    with pytest.raises(Unauthorized):
        svc.authenticate_access_token(access.token)
    _, access2, _ = login(svc)
    users.items[user.id].is_active = False
    with pytest.raises(Unauthorized):
        svc.authenticate_access_token(access2.token)


def test_expired_token_rejected(env):
    svc, _, _, tokens = env
    register(svc)
    _, access, _ = login(svc)
    tokens.expire(access.token)
    with pytest.raises(Unauthorized, match="expired"):
        svc.authenticate_access_token(access.token)


def test_refresh_rotates_and_revokes_old_token(env):
    svc, _, revoked, _ = env
    register(svc)
    _, _, refresh = login(svc)
    new_access, new_refresh = svc.refresh(refresh.token)
    assert revoked.is_revoked(refresh.claims.jti)
    assert new_refresh.claims.jti != refresh.claims.jti
    with pytest.raises(Unauthorized):  # reuse of the old refresh token
        svc.refresh(refresh.token)
    svc.authenticate_access_token(new_access.token)


def test_refresh_rejects_access_token_and_inactive_user(env):
    svc, users, *_ = env
    user = register(svc)
    _, access, refresh = login(svc)
    with pytest.raises(Unauthorized):
        svc.refresh(access.token)
    users.items[user.id].is_active = False
    with pytest.raises(Unauthorized):
        svc.refresh(refresh.token)


def test_logout_revokes_access_and_optional_refresh_and_is_idempotent(env):
    svc, _, revoked, _ = env
    register(svc)
    _, access, refresh = login(svc)
    svc.logout(access.token, refresh.token)
    assert revoked.is_revoked(access.claims.jti)
    assert revoked.is_revoked(refresh.claims.jti)
    svc.logout(access.token, refresh.token)  # second time must not raise


def test_logout_ignores_invalid_or_foreign_refresh_token(env):
    svc, _, revoked, _ = env
    register(svc)
    register(svc, username="bob", email="bob@example.com")
    _, access, _ = login(svc)
    _, _, bob_refresh = login(svc, username="bob")
    svc.logout(access.token, "not-a-token")
    svc.logout(access.token, bob_refresh.token)
    assert not revoked.is_revoked(bob_refresh.claims.jti)
