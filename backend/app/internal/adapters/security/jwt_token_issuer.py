from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt

from app.internal.entities import IssuedToken, TokenClaims, TokenType
from app.pkg.errors import Unauthorized

ALGORITHM = "HS256"


class JwtTokenIssuer:
    def __init__(self, secret: str) -> None:
        self._secret = secret

    def issue(self, user_id: int, token_type: TokenType, ttl_seconds: int) -> IssuedToken:
        now = datetime.now(timezone.utc)
        claims = TokenClaims(
            jti=str(uuid4()),
            user_id=user_id,
            type=token_type,
            exp=now + timedelta(seconds=ttl_seconds),
        )
        # No "iat": it adds nothing here and a backwards clock step between workers
        # would make PyJWT reject freshly issued tokens as "not yet valid".
        payload = {
            "jti": claims.jti,
            "sub": str(user_id),
            "type": token_type.value,
            "exp": claims.exp,
        }
        return IssuedToken(jwt.encode(payload, self._secret, algorithm=ALGORITHM), claims)

    def decode(self, token: str) -> TokenClaims:
        try:
            data = jwt.decode(
                token,
                self._secret,
                algorithms=[ALGORITHM],
                options={"require": ["exp", "sub", "jti", "type"]},
            )
            return TokenClaims(
                jti=data["jti"],
                user_id=int(data["sub"]),
                type=TokenType(data["type"]),
                exp=datetime.fromtimestamp(data["exp"], tz=timezone.utc),
            )
        except jwt.ExpiredSignatureError as exc:
            raise Unauthorized("Token expired") from exc
        except (jwt.InvalidTokenError, ValueError) as exc:
            raise Unauthorized("Invalid token") from exc
