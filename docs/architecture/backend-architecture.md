# Backend Architecture (Lich)

FastAPI service. Contract with frontend/infra: [contracts.md](contracts.md).

## Layout

```
backend/
  app/
    cmd/            server.py (ASGI app), create_admin.py (admin bootstrap CLI)
    internal/
      entities/     User/Role, Resume, TokenClaims  - pure domain rules, no third-party imports
      ports/        Protocols: UserRepository, ResumeRepository, RevokedTokenRepository,
                    FileStorage, PasswordHasher, TokenIssuer
      services/     AuthService, ResumeService, AdminService (use cases)
      adapters/     db/ (SQLAlchemy models + repositories), storage/ (local FS),
                    security/ (bcrypt, PyJWT)
      dto/          pydantic request/response models
      validators/   username/password/github/PDF-stream helpers
    api/http/       app.py (create_app), dependencies.py (composition root), errors.py, routers/
    pkg/            config (settings), logger (JSON logging), errors (DomainError hierarchy)
  migrations/       alembic (env.py reads DATABASE_URL from settings)
  scripts/db/       postgres init + backup/restore scripts
  tests/            unit/ (fakes for ports), integration/ (TestClient + SQLite), fixtures/
```

The package is named `app` so `app.cmd` does not shadow the stdlib `cmd` module.

## Dependency rules

| Layer      | May import                                             | Must not import            |
|------------|--------------------------------------------------------|----------------------------|
| entities   | stdlib only                                            | everything else            |
| validators | pkg.errors                                             | adapters, frameworks       |
| dto        | entities, validators, pydantic                         | adapters, services         |
| ports      | entities                                               | implementations            |
| services   | entities, ports, dto, validators, pkg.errors           | adapters, sqlalchemy, fastapi |
| adapters   | entities, ports, pkg.*                                 | services, api              |
| api        | services, dto, entities, pkg.*                         | adapters - **except** `api/http/dependencies.py`, the composition root |

Check: `grep -rnE "^\s*(from|import) .*(adapters|sqlalchemy|fastapi)" backend/app/internal/{entities,services}` returns nothing.

## Composition root

`api/http/dependencies.py` defines `Container`: settings, lazily created SQLAlchemy engine/session factory
(importing the app never opens a DB connection), local file storage, bcrypt hasher, JWT issuer.
`create_app(settings=None, container=None)` stores it in `app.state.container`; per-request FastAPI dependencies
open a session and build the services around it. Tests pass their own `Container` (SQLite `StaticPool`,
tmp upload dir) - no monkeypatching.

## Request flow

```
HTTP request
  -> middleware (X-Request-ID, X-Process-Time, access log)  [CORS only for exact origins]
  -> router function (api/http/routers/*)
       -> Depends(get_current_user): Bearer token -> AuthService.authenticate_access_token
            -> TokenIssuer.decode (signature, exp)  -> RevokedTokenRepository.is_revoked(jti)
            -> UserRepository.get_by_id (must exist and be active)
       -> pydantic DTO validation (uses internal.validators)       <- input validated before services
       -> Service method (use case; role checks via entity methods)
            -> ports (repositories / storage / hasher)  <- adapters (SQLAlchemy, FS, bcrypt)
       -> response DTO
  <- DomainError / HTTPException / RequestValidationError / Exception
       -> api/http/errors.py -> {"error": true, "status_code": N, "detail": ...}
```

Error mapping: NotFound 404, Conflict 409, Unauthorized 401 (+`WWW-Authenticate: Bearer`), Forbidden 403,
ValidationFailed 400, PayloadTooLarge 413, ServiceUnavailable 503, request validation 422 (input values are
stripped so passwords are never echoed), anything else 500 with the generic message `Internal server error`
(details only in logs).

## Security decisions

- Registration role is always `candidate`; admins are created with `python -m app.cmd.create_admin`.
- bcrypt used directly (no passlib); passwords limited to 72 bytes; legacy `$2a$/$2b$` hashes verify.
- Every JWT has `jti` (uuid4); revocation by jti in `revoked_tokens` (unique, idempotent, race-safe);
  refresh rotates (old refresh token revoked); expiry validated by PyJWT; no `iat` claim (avoids clock-skew rejections).
- Uploads: `%PDF-` magic check on the stream, size limit enforced while streaming (413), stored as
  `<uuid4>.pdf`; storage keys/paths never leave the server; `Path(key).name` prevents traversal.
- Settings fail fast: `DATABASE_URL`/`JWT_SECRET_KEY` required, secret >= 32 chars in production, `*` CORS rejected.
- Logging is JSON on stdout; no secrets/tokens are logged. Docs UI/OpenAPI are disabled in production.

## Persistence

Tables: `users`, `resumes` (column `file_path` holds the storage key), `revoked_tokens`.
Timestamps are `timestamptz`; `updated_date` uses `onupdate=func.now()`. `GET /ready` runs `SELECT 1`.
Expired `revoked_tokens` rows are purged opportunistically on refresh.

## Known limitations

- Each repository write commits on its own (no unit-of-work): `refresh` (revoke old, issue new) is not one transaction.
- Uploaded files live on a local volume (`UPLOAD_DIR`), so replicas must share the volume (or run one backend).
- No rate limiting in-app; do it at the proxy.
