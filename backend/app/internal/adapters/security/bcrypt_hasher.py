import bcrypt

MAX_BYTES = 72


class BcryptHasher:
    """bcrypt directly (no passlib). Verifies existing `$2a$/$2b$` hashes."""

    def __init__(self, rounds: int = 12) -> None:
        self._rounds = rounds

    def hash(self, password: str) -> str:
        raw = password.encode("utf-8")
        if len(raw) > MAX_BYTES:
            raise ValueError("password longer than 72 bytes")
        return bcrypt.hashpw(raw, bcrypt.gensalt(self._rounds)).decode("ascii")

    def verify(self, password: str, password_hash: str) -> bool:
        raw = password.encode("utf-8")
        if len(raw) > MAX_BYTES:
            return False
        try:
            return bcrypt.checkpw(raw, password_hash.encode("ascii"))
        except ValueError:  # malformed stored hash
            return False
