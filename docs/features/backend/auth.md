# Auth & Users (Backend Module Doc)

## 1. Purpose
Registration, login, JWT access/refresh tokens with rotation and revocation, current-user lookup.

## 2. Entities
- `User` (`id, username, email, password_hash, github, role, is_active, created_date, updated_date`), `Role` = candidate | expert | admin.
  Rules: `is_admin()`, `can_review_resumes()` (expert/admin), `can_delete(resume)`, `can_download(resume)`.
- `TokenClaims(jti, user_id, type, exp)`, `TokenType` = access | refresh, `IssuedToken(token, claims)`.

## 3. Services (Use Cases)
`AuthService`:
- `register(RegisterRequest)` - 409 on duplicate username/email; role forced to candidate.
- `login(LoginRequest)` - 401 on bad credentials or inactive user; returns user + access + refresh tokens.
- `refresh(refresh_token)` - decodes, requires `type=refresh`, not revoked, user active; revokes the old token (atomically) and issues a new pair.
- `logout(access_token, refresh_token?)` - revokes the access token and, if valid and owned by the same user, the refresh token. Idempotent.
- `authenticate_access_token(token)` - signature/expiry, `type=access`, not revoked, user exists and active.

## 4. Ports
`UserRepository`, `RevokedTokenRepository` (`revoke(claims) -> bool` idempotent, `is_revoked`, `purge_expired`),
`PasswordHasher`, `TokenIssuer`.

## 5. Adapters
`SqlUserRepository`, `SqlRevokedTokenRepository` (`revoked_tokens`: id, jti unique, user_id, token_type, expires_at, revoked_at),
`BcryptHasher` (bcrypt 4.x direct), `JwtTokenIssuer` (HS256, claims `jti, sub, type, exp`).

## 6. API Endpoints
| Method | Path | Auth | Result |
|---|---|---|---|
| POST | `/users/register` | - | 201 `{"detail":"User registered successfully"}`, 409 duplicate, 422 invalid |
| POST | `/users/login` | - | 200 `{access_token, refresh_token, token_type, role}`, 401 |
| POST | `/users/refresh_token` | - | body `{token}` -> 200 `{access_token, refresh_token, token_type}`, 401 |
| POST | `/users/logout` | Bearer | optional `{refresh_token}` -> 200 `{"detail":"Successfully logged out"}` |
| GET | `/users/me` | Bearer | `UserResponse` |

## 7. Validation Rules
username 3-50 chars `^[a-zA-Z0-9_.-]+$` (stored lowercase); email valid (stored lowercase); password 8-72 **bytes**,
must match `confirm_password`; github optional, must start with `https://github.com/`. Unknown fields (e.g. `role`) are ignored.
Validation is in `internal/validators`, wired through `internal/dto`.

## 8. Security Model
Access TTL 900 s, refresh TTL 86400 s (env). Each token has a uuid4 `jti`. Revoked jtis are checked on every authenticated request.
Deactivating a user invalidates access immediately (user lookup per request). Passwords are never logged or echoed in 422 responses.
Secret: `JWT_SECRET_KEY` (>= 32 chars in production). Rotating it invalidates all tokens.

## 9. Testing Strategy
Unit (fake ports): `tests/unit/test_auth_service.py`, `test_adapters.py`, `test_validators.py`.
Integration (TestClient + SQLite): `tests/integration/test_api.py`. Regression tests cover self-assigned role, double revoke,
refresh rotation/reuse, legacy `$2b$` hash, 72-byte limit, generic 500.

## 10. Future Improvements
Per-user token revocation ("logout everywhere"), login rate limiting at the proxy, email verification, unit of work for multi-step operations.
