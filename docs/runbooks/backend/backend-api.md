# Runbook — Backend API

## 1. Purpose
FastAPI service for auth, resumes and admin. Port 8000, image `docker.io/sepehrmdn/resume-review-backend:<tag>`.
Contract: `docs/architecture/contracts.md`. Design: `docs/architecture/backend-architecture.md`.

## 2. How to Run
Local development:
```bash
cd backend
python -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
pytest                                     # SQLite, no external services
export DATABASE_URL=postgresql+psycopg2://user:pass@localhost:5432/resume_review
export JWT_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(48))')"
alembic upgrade head
python -m app.cmd.server                   # http://localhost:8000/docs (non-production)
```
Container (build context is `backend/`; the Dockerfile lives in `deployments/docker/backend/`):
```bash
docker build -f deployments/docker/backend/Dockerfile -t rr-backend:dev backend
docker run --rm -p 8000:8000 --env-file deployments/docker/backend/env.example rr-backend:dev
```
In compose use `build: { context: ../../backend, dockerfile: ../deployments/docker/backend/Dockerfile }`
(dockerfile is resolved relative to the context). Mount a persistent volume at `/app/data/uploads`.

Environment variables: see `deployments/docker/backend/env.example` and contract section 2.
Generate a secret: `python -c "import secrets; print(secrets.token_urlsafe(48))"`.

Create the first admin (no HTTP endpoint exists for this):
```bash
docker exec -it backend python -m app.cmd.create_admin --username admin --email admin@example.com
# non-interactive: docker exec -e ADMIN_PASSWORD=... backend python -m app.cmd.create_admin ...
```

## 3. How to Deploy
The entrypoint waits for the DB (host/port parsed from `DATABASE_URL`, up to `DB_WAIT_TIMEOUT`), runs `alembic upgrade head`
when `RUN_MIGRATIONS=true`, then starts `uvicorn app.cmd.server:app --workers $WEB_CONCURRENCY --proxy-headers`.
Runs as uid 10001; `/app/data/uploads` must be writable by it.
With several replicas set `RUN_MIGRATIONS=true` on one replica only (or run a one-shot job) and share the uploads volume.
Production requires `ENVIRONMENT=production`, `JWT_SECRET_KEY` >= 32 chars and exact-origin `CORS_ORIGINS`.

Migrations: `alembic revision -m "..." --autogenerate` (needs `DATABASE_URL`), review, commit under `backend/migrations/versions/`.
The initial revision `e3a514dac763` must not be edited.

## 4. Health Checks
- Liveness: `GET /health` -> `{"status":"ok"}` (no DB). Image HEALTHCHECK uses it.
- Readiness: `GET /ready` -> `{"status":"ready"}` or 503 when the DB is unreachable.

## 5. Monitoring
JSON logs on stdout (`ts, level, logger, message, request_id, method, path, status, duration_ms`). Responses carry
`X-Request-ID` and `X-Process-Time`. Alert on rising 5xx counts, `/ready` failures, and "unhandled error" log lines.

## 6. Debugging
`docker logs backend`; find a failing request via its `X-Request-ID`. Set `LOG_LEVEL=DEBUG` or `DB_ECHO=true` temporarily
(SQL is logged; never leave on). 500 responses are generic by design - the stack trace is in the logs.
See `docs/troubleshooting/backend.md`.

## 7. Disaster Recovery
- DB backup: `PGHOST=... PGUSER=... PGPASSWORD=... PGDATABASE=... BACKUP_DIR=/backups backend/scripts/db/backups/db_backup.sh`
  (pg_dump -Fc, 7-day rotation after a successful dump; cron: `0 3 * * *`).
- Restore: `... backend/scripts/db/backups/db_restore.sh /backups/backup_<stamp>.dump` (drops existing objects first).
- Uploads live only in the `UPLOAD_DIR` volume: back it up together with the DB (DB rows reference files by key).
- Optional read-only DB role: set `DB_READONLY_PASSWORD` (and optionally `DB_READONLY_USER`) on the postgres container;
  `backend/scripts/db/init/01-readonly-role.sh` runs on first initialisation only.

## 8. Ownership
Backend team (repo owner: DevSepOps). Contract changes go through `docs/architecture/contracts.md` first.

## 9. Change History
- 2025-10 Rewrite into Lich architecture; revoked-token model (migration `b7c1d2f4a9e0`), admin CLI, health/ready, new Dockerfile.
