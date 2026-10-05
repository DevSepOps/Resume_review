from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app.internal.adapters.security import BcryptHasher, JwtTokenIssuer
from app.internal.adapters.storage import LocalFileStorage
from app.internal.entities import TokenType
from app.pkg.errors import Unauthorized

SECRET = "x" * 40


def test_bcrypt_roundtrip_and_72_byte_guard():
    h = BcryptHasher()
    hashed = h.hash("Password123")
    assert hashed.startswith("$2b$") and h.verify("Password123", hashed)
    assert not h.verify("wrong-pass", hashed)
    assert not h.verify("a" * 73, hashed)
    with pytest.raises(ValueError):
        h.hash("a" * 73)


def test_bcrypt_verifies_existing_legacy_hashes():
    """Regression: hashes created by passlib ($2a$/$2b$) must still verify."""
    h = BcryptHasher()
    # classic crypt_blowfish test vector for "U*U"
    assert h.verify("U*U", "$2a$05$CCCCCCCCCCCCCCCCCCCCC.E5YPO9kmyuRGyh0XouQYb4YMJKvyOeW")
    assert not h.verify("password", "not-a-hash")


def test_jwt_roundtrip_unique_jti_and_aware_exp():
    t = JwtTokenIssuer(SECRET)
    a, b = t.issue(7, TokenType.ACCESS, 60), t.issue(7, TokenType.ACCESS, 60)
    assert a.claims.jti != b.claims.jti
    got = t.decode(a.token)
    assert got.user_id == 7 and got.type == TokenType.ACCESS
    assert got.exp.tzinfo is not None


def test_jwt_expired_wrong_key_and_missing_claims():
    t = JwtTokenIssuer(SECRET)
    with pytest.raises(Unauthorized, match="expired"):
        t.decode(t.issue(1, TokenType.ACCESS, -10).token)
    with pytest.raises(Unauthorized):
        JwtTokenIssuer("y" * 40).decode(t.issue(1, TokenType.ACCESS, 60).token)
    no_jti = jwt.encode(
        {"sub": "1", "type": "access", "exp": datetime.now(timezone.utc) + timedelta(minutes=1)},
        SECRET,
        algorithm="HS256",
    )
    with pytest.raises(Unauthorized):
        t.decode(no_jti)
    with pytest.raises(Unauthorized):
        t.decode("garbage")


def test_local_storage(tmp_path):
    s = LocalFileStorage(tmp_path / "up")
    key, size = s.save([b"%PDF-", b"abc"])
    assert key.endswith(".pdf") and size == 8
    assert b"".join(s.iter_chunks(key)) == b"%PDF-abc"
    s.delete(key)
    s.delete(key)  # idempotent
    assert not s.exists(key)


def test_local_storage_removes_partial_file_on_error(tmp_path):
    s = LocalFileStorage(tmp_path)

    def boom():
        yield b"abc"
        raise RuntimeError("stream failed")

    with pytest.raises(RuntimeError):
        s.save(boom())
    assert list(tmp_path.iterdir()) == []


def test_local_storage_cannot_escape_root(tmp_path):
    (tmp_path / "secret.txt").write_text("s")
    s = LocalFileStorage(tmp_path / "up")
    assert not s.exists("../secret.txt")
