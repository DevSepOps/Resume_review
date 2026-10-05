# System Contracts

Single source of truth for the interfaces between backend, frontend and infrastructure.
Every component MUST conform to this file. Change it first, then the code.

## 1. Services, names and ports

| Service  | Container port | Compose / Swarm name | Helm Service name             | Image                                  |
|----------|----------------|----------------------|-------------------------------|----------------------------------------|
| backend  | 8000           | `backend`            | `<release>-backend`           | `docker.io/sepehrmdn/resume-review-backend:<tag>`  |
| frontend | 8001           | `frontend`           | `<release>-frontend`          | `docker.io/sepehrmdn/resume-review-frontend:<tag>` |
| database | 5432           | `db`                 | `<release>-db`                | `postgres:16-alpine`                   |
| proxy    | 80 / 443       | `proxy`              | (ingress controller)          | `traefik:v3.6`                         |

Image tags produced by CI: `sha-<7 char sha>` always, `latest` on `main`, `vX.Y.Z` on git tags.

Public hostnames are configured, never hardcoded: `APP_DOMAIN` (frontend) and `API_DOMAIN` (backend).

## 2. Backend environment variables

| Variable                    | Required | Default                 | Notes |
|-----------------------------|----------|-------------------------|-------|
| `DATABASE_URL`              | yes      | –                       | `postgresql+psycopg2://user:pass@db:5432/resume_review` |
| `JWT_SECRET_KEY`            | yes      | –                       | ≥ 32 chars; startup fails if missing/short when `ENVIRONMENT=production` |
| `ENVIRONMENT`               | no       | `development`           | `development` \| `test` \| `production` |
| `CORS_ORIGINS`              | no       | `` (none)               | comma-separated list of exact origins |
| `UPLOAD_DIR`                | no       | `/app/data/uploads`     | must be a persistent volume in every deployment |
| `MAX_UPLOAD_MB`             | no       | `10`                    | |
| `ACCESS_TOKEN_TTL_SECONDS`  | no       | `900`                   | |
| `REFRESH_TOKEN_TTL_SECONDS` | no       | `86400`                 | |
| `LOG_LEVEL`                 | no       | `INFO`                  | |
| `DB_ECHO`                   | no       | `false`                 | |
| `RUN_MIGRATIONS`            | no       | `true`                  | entrypoint runs `alembic upgrade head` before serving when true |
| `DB_WAIT_TIMEOUT`           | no       | `60`                    | seconds the entrypoint waits for the DB (host/port parsed from `DATABASE_URL`) |
| `WEB_CONCURRENCY`           | no       | `2`                     | uvicorn workers |
| `FORWARDED_ALLOW_IPS`       | no       | `127.0.0.1`             | proxies trusted for `X-Forwarded-*`; Compose/Swarm set `*` because only the proxy can reach the backend |

Admin bootstrap (no HTTP endpoint for this): `python -m app.cmd.create_admin --username <u> --email <e>`; the password is read from `ADMIN_PASSWORD` env or prompted.

## 3. Frontend environment variables

| Variable          | Required        | Default               | Notes |
|-------------------|-----------------|-----------------------|-------|
| `BACKEND_URL`     | yes (prod)      | `http://backend:8000` | internal URL; the Flet server calls the API server-side |
| `FLET_HOST`       | no              | `0.0.0.0`             | |
| `FLET_PORT`       | no              | `8001`                | |
| `FLET_SECRET_KEY` | yes             | –                     | required by Flet web for signed upload URLs |
| `UPLOAD_TMP_DIR`  | no              | `/tmp/uploads`        | transient browser→Flet uploads, deleted after forwarding |
| `REQUEST_TIMEOUT` | no              | `15`                  | seconds |
| `MAX_UPLOAD_MB`   | no              | `10`                  | client-side size check + Flet upload limit; keep equal to the backend value |
| `LOG_LEVEL`       | no              | `INFO`                | |
| `FLET_OPEN_BROWSER` | no            | `false`               | local development only |

Tokens live only server-side in the per-session app object; they are never sent to the browser.
The frontend serves short-lived PDF download links from `/app/assets/downloads` — every deployment must mount a writable tmpfs/emptyDir there (the root filesystem is read-only).

## 4. HTTP API (backend)

Error envelope for every non-2xx response:
```json
{"error": true, "status_code": 401, "detail": "Human readable message or validation list"}
```
Internal errors return `{"error": true, "status_code": 500, "detail": "Internal server error"}` (details only in logs).

### Health
| Method | Path      | Auth | Response |
|--------|-----------|------|----------|
| GET    | `/health` | –    | `200 {"status":"ok"}` — liveness, no DB access |
| GET    | `/ready`  | –    | `200 {"status":"ready"}` or `503` when DB unreachable |

### Users
| Method | Path                    | Auth   | Body / Response |
|--------|-------------------------|--------|-----------------|
| POST   | `/users/register`       | –      | `{username, email, password, confirm_password, github?}` → `201 {"detail":"User registered successfully"}`; `409` duplicate. Role is always `candidate`. |
| POST   | `/users/login`          | –      | `{username, password}` → `200 {"access_token","refresh_token","token_type":"bearer","role"}`; `401` bad creds or inactive |
| POST   | `/users/refresh_token`  | –      | `{token}` → `200 {"access_token","refresh_token","token_type":"bearer"}`; old refresh token is revoked; revoked/expired/inactive → `401` |
| POST   | `/users/logout`         | Bearer | optional `{refresh_token}` → `200 {"detail":"Successfully logged out"}`; revokes access (+ refresh if given) |
| GET    | `/users/me`             | Bearer | `200 UserResponse` |

Validation: username 3–50 chars `^[a-zA-Z0-9_.-]+$` (stored lowercase); email valid (stored lowercase); password 8–72 **bytes**; github optional, if present must be an `https://github.com/` URL.

### Resumes
| Method | Path                         | Auth                 | Response |
|--------|------------------------------|----------------------|----------|
| POST   | `/resumes/upload`            | Bearer               | multipart field `resume` (PDF, ≤ `MAX_UPLOAD_MB`, must start with `%PDF-`) → `201 {"message", "resume": ResumeResponse}`; `400` not PDF; `413` too large |
| GET    | `/resumes/my-resumes`        | Bearer               | `200 [ResumeResponse]` newest first |
| GET    | `/resumes/download/{id}`     | Bearer (owner, expert, admin) | `200 application/pdf` attachment |
| DELETE | `/resumes/{id}`              | Bearer (owner or admin)       | `200 {"detail":"Resume deleted successfully"}` |
| GET    | `/resumes/expert/all`        | Bearer (expert, admin)        | `?skip=0&limit=50 (max 200)` → `200 [ExpertResumeResponse]` newest first |

### Admin (role `admin` only)
| Method | Path                               | Response |
|--------|------------------------------------|----------|
| GET    | `/admin/users`                     | `?skip&limit&role&search` → `[UserResponse]` |
| PATCH  | `/admin/users/{id}/role`           | `{role}` → `UserResponse`; cannot change own role |
| PATCH  | `/admin/users/{id}/activation`     | toggles `is_active` → `UserResponse`; cannot deactivate self |
| GET    | `/admin/stats`                     | `{"total_users", "total_resumes", "users_by_role": {"candidate":n,"expert":n,"admin":n}}` |

### Schemas
```
UserResponse        = {id, username, email, github|null, role: "candidate"|"expert"|"admin", is_active, created_date}
ResumeResponse      = {id, user_id, file_name, file_size, mime_type, created_date, updated_date}
ExpertResumeResponse= ResumeResponse + {username, email, github|null}
```
Storage paths are never returned by the API.

## 5. Repository layout (target)

```
backend/            Lich architecture (see docs/architecture/backend-architecture.md)
frontend/           Flet app, feature-based (see docs/architecture/frontend-architecture.md)
deployments/
  docker/           docker-compose.yml, backend/, frontend/, proxy/, monitoring/
  swarm/            docker-stack.yml + swarm-specific config
  helm/resume-review/
infra/
  terraform/        envs/<env>/, modules/<module>/
  ansible/          inventories/, roles/, playbooks/, group_vars/
docs/               runbooks/, features/, architecture/, troubleshooting/, onboarding/
agentlog.md         change log (maintained by the lead)
```
