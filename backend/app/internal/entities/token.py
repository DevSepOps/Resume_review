from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class TokenType(str, Enum):
    ACCESS = "access"
    REFRESH = "refresh"


@dataclass(frozen=True)
class TokenClaims:
    jti: str
    user_id: int
    type: TokenType
    exp: datetime  # timezone-aware UTC


@dataclass(frozen=True)
class IssuedToken:
    token: str
    claims: TokenClaims
