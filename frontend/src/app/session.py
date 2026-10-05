"""Per-browser-session state. One instance is created inside ``main(page)`` per session."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from shared.lib.api_client import TokenPair

ROLE_CANDIDATE = "candidate"
ROLE_EXPERT = "expert"
ROLE_ADMIN = "admin"


@dataclass
class Session:
    tokens: TokenPair = field(default_factory=TokenPair)
    user: Optional[Dict[str, Any]] = None
    role: Optional[str] = None

    @property
    def is_authenticated(self) -> bool:
        return bool(self.tokens.access and self.role)

    @property
    def username(self) -> str:
        return str((self.user or {}).get("username", ""))

    def clear(self) -> None:
        self.tokens.clear()
        self.user = None
        self.role = None
