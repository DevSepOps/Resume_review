# Runbook — Frontend (Flet web app)

## 1. Purpose
Serves the Resume Review UI on port 8001 and talks to the backend server-side.

## 2. How to Run
Local: `cd frontend && pip install -r requirements-dev.txt && FLET_SECRET_KEY=dev BACKEND_URL=http://localhost:8000 FLET_PORT=8001 python src/main.py`
(add `FLET_OPEN_BROWSER=true` to open a browser; locally set `UPLOAD_TMP_DIR` to a writable path).
Tests: `cd frontend && pytest --cov`.
Docker: `docker build -f deployments/docker/frontend/Dockerfile -t rr-frontend:dev frontend` then
`docker run -p 8001:8001 -e FLET_SECRET_KEY=$(openssl rand -hex 32) -e BACKEND_URL=http://host.docker.internal:8000 rr-frontend:dev`.

Environment (contract section 3): `BACKEND_URL` (default `http://backend:8000`), `FLET_HOST` (`0.0.0.0`), `FLET_PORT` (`8001`), `FLET_SECRET_KEY` (**required**, the app exits with code 2 and a clear message if unset), `UPLOAD_TMP_DIR` (`/tmp/uploads`), `REQUEST_TIMEOUT` (`15`), plus optional `MAX_UPLOAD_MB` (`10`), `LOG_LEVEL`, `FLET_OPEN_BROWSER`. Template: `deployments/docker/frontend/env.example`.

## 3. How to Deploy
Image `docker.io/sepehrmdn/resume-review-frontend:<tag>` built from `deployments/docker/frontend/Dockerfile` (context `frontend/`). Provide `FLET_SECRET_KEY` as a secret, not in the image. The proxy must forward WebSocket upgrades on `/ws` and route `APP_DOMAIN` to port 8001. Use sticky sessions or one replica (sessions are in memory). The container needs writable `UPLOAD_TMP_DIR` and `/app/assets/downloads` (both owned by uid 10001 in the image; with a read-only root fs mount them as tmpfs).

## 4. Health Checks
`GET /` returns 200 (Flet HTML). Image `HEALTHCHECK` uses python urllib on `http://127.0.0.1:8001/`. It does not check the backend; a dead backend shows friendly "Cannot reach the server" errors in the UI.

## 5. Monitoring
Container logs (uvicorn access log + app logs, no secrets/tokens). Watch for `Configuration error`, `Unexpected error during auth`, `Failed to build route`. No metrics endpoint yet.

## 6. Debugging
See [troubleshooting/frontend.md](../../troubleshooting/frontend.md). Set `LOG_LEVEL=DEBUG`. Check `docker logs`, then `curl -i localhost:8001/`.

## 7. Disaster Recovery
Stateless apart from transient temp files: restart/redeploy the container. Users are signed out on restart (tokens are in memory). Nothing to back up.

## 8. Ownership
Frontend team. Contract owner: lead architect (`docs/architecture/contracts.md`).

## 9. Change History
- 2026-10: Rewritten feature-based; per-session isolation, httpx client with refresh, web upload, new animated nav/login, prod Dockerfile.
