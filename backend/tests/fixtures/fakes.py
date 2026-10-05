"""In-memory fakes for the ports (unit tests)."""

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from itertools import count
from typing import Iterable, Iterator, Optional
from uuid import uuid4

from app.internal.entities import IssuedToken, Resume, Role, TokenClaims, TokenType, User
from app.pkg.errors import Unauthorized


class FakeUserRepo:
    def __init__(self):
        self.items: dict[int, User] = {}
        self._ids = count(1)

    def get_by_id(self, user_id):
        u = self.items.get(user_id)
        return replace(u) if u else None

    def get_by_username(self, username):
        return next((replace(u) for u in self.items.values() if u.username == username), None)

    def get_by_username_or_email(self, username, email):
        return next(
            (replace(u) for u in self.items.values() if u.username == username or u.email == email),
            None,
        )

    def exists_username_or_email(self, username, email):
        return self.get_by_username_or_email(username, email) is not None

    def add(self, user):
        user = replace(user, id=next(self._ids))
        self.items[user.id] = user
        return replace(user)

    def update(self, user):
        self.items[user.id] = replace(user)
        return replace(user)

    def list_users(self, skip, limit, role=None, search=None):
        rows = [u for u in self.items.values() if (role is None or u.role == role)]
        if search:
            rows = [u for u in rows if search in u.username or search in u.email]
        return rows[skip : skip + limit]

    def count(self):
        return len(self.items)

    def count_by_role(self):
        out: dict[Role, int] = {}
        for u in self.items.values():
            out[u.role] = out.get(u.role, 0) + 1
        return out


class FakeResumeRepo:
    def __init__(self, users: FakeUserRepo):
        self.items: dict[int, Resume] = {}
        self._users = users
        self._ids = count(1)
        self.fail_on_add = False

    def add(self, resume):
        if self.fail_on_add:
            raise RuntimeError("db down")
        resume = replace(resume, id=next(self._ids))
        self.items[resume.id] = resume
        return replace(resume)

    def get(self, resume_id):
        return self.items.get(resume_id)

    def list_by_user(self, user_id):
        return [r for r in self.items.values() if r.user_id == user_id]

    def list_with_owner(self, skip, limit):
        rows = list(self.items.values())[skip : skip + limit]
        return [(r, self._users.items[r.user_id]) for r in rows]

    def delete(self, resume_id):
        self.items.pop(resume_id, None)

    def count(self):
        return len(self.items)


class FakeRevokedRepo:
    def __init__(self):
        self.jtis: dict[str, TokenClaims] = {}

    def revoke(self, claims):
        if claims.jti in self.jtis:
            return False
        self.jtis[claims.jti] = claims
        return True

    def is_revoked(self, jti):
        return jti in self.jtis

    def purge_expired(self, now):
        gone = [j for j, c in self.jtis.items() if c.exp < now]
        for j in gone:
            del self.jtis[j]
        return len(gone)


class FakeHasher:
    def hash(self, password):
        return f"hashed:{password}"

    def verify(self, password, password_hash):
        return password_hash == f"hashed:{password}"


class FakeTokens:
    """Opaque tokens kept in a dict; `expire(token)` simulates expiry."""

    def __init__(self):
        self.store: dict[str, TokenClaims] = {}

    def issue(self, user_id, token_type, ttl_seconds):
        claims = TokenClaims(
            str(uuid4()), user_id, token_type, datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
        )
        token = f"tok-{claims.jti}"
        self.store[token] = claims
        return IssuedToken(token, claims)

    def decode(self, token):
        claims = self.store.get(token)
        if claims is None:
            raise Unauthorized("Invalid token")
        if claims.exp < datetime.now(timezone.utc):
            raise Unauthorized("Token expired")
        return claims

    def expire(self, token):
        c = self.store[token]
        self.store[token] = replace(c, exp=datetime.now(timezone.utc) - timedelta(seconds=1))


class FakeStorage:
    def __init__(self):
        self.files: dict[str, bytes] = {}

    def save(self, chunks: Iterable[bytes]):
        buf = bytearray()
        for c in chunks:  # exceptions propagate before anything is stored
            buf.extend(c)
        key = f"{uuid4()}.pdf"
        self.files[key] = bytes(buf)
        return key, len(buf)

    def exists(self, key):
        return key in self.files

    def iter_chunks(self, key) -> Iterator[bytes]:
        yield self.files[key]

    def delete(self, key):
        self.files.pop(key, None)
