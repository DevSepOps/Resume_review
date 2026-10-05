# System Overview

Resume Review lets candidates upload PDF resumes, experts review them and admins manage users.
The interface contract between all components is [contracts.md](contracts.md).

## 1. Components

```
                 Internet
                    │ 80 → 443 (redirect)
              ┌─────▼──────┐   TLS (Let's Encrypt), secure headers, rate limits,
              │   proxy    │   request-body limit, basic-auth dashboard
              │ Traefik v3 │◄── docker-socket-proxy (read-only Docker API)
              └──┬──────┬──┘
   APP_DOMAIN    │      │   API_DOMAIN (public API, /ready not routed)
       ┌─────────▼──┐ ┌─▼──────────┐
       │  frontend  │ │  backend   │  FastAPI, Lich architecture
       │  Flet web  ├─►            │  JWT (jti + revocation), bcrypt,
       │  :8001     │ │  :8000     │  PDF magic-byte validation
       └────────────┘ └──┬─────┬───┘
     per-session state   │     │ uploads volume (/app/data/uploads)
     server-side tokens  │  ┌──▼──────────┐
                         └──►  db         │  PostgreSQL 16, internal network only
                            └─────────────┘

  optional profile "monitoring":  metricbeat → logstash → elasticsearch ← grafana
  optional profile "ops":         portainer
```

| Component | Code | Docs |
|-----------|------|------|
| Backend API | `backend/` | [backend-architecture.md](backend-architecture.md) |
| Frontend (Flet) | `frontend/` | [frontend-architecture.md](frontend-architecture.md) |
| Compose / Swarm / Traefik / monitoring | `deployments/docker`, `deployments/swarm` | [infra-architecture.md](infra-architecture.md) |
| Kubernetes | `deployments/helm/resume-review` | [../features/infra/helm-chart.md](../features/infra/helm-chart.md) |
| Cloud VM + provisioning | `infra/terraform`, `infra/ansible` | [../features/infra/terraform-aws.md](../features/infra/terraform-aws.md), [../features/infra/ansible.md](../features/infra/ansible.md) |
| CI/CD | `.github/workflows` | [../features/infra/ci-cd.md](../features/infra/ci-cd.md) |

## 2. Request flows

**Browser → UI.** The browser loads the Flet web client from `APP_DOMAIN` and keeps a websocket open.
All UI logic runs in the frontend container, one isolated `SessionApp` per browser session.

**UI → API.** The frontend calls the backend server-side at `BACKEND_URL` (`http://backend:8000`) with
the session's bearer token. Tokens never reach the browser. A 401 triggers one refresh-and-retry
(refresh tokens rotate).

**Upload.** Browser → signed Flet upload URL → temp file in the frontend → streamed to
`POST /resumes/upload` → the backend validates `%PDF-` and the size, stores `<uuid>.pdf` in the uploads volume → temp file deleted.

**Download.** The frontend fetches the PDF with the user's token and stages it under
`/downloads/<128-bit token>/` for 120 s. The browser opens that root-relative link.

**Direct API clients** use `API_DOMAIN` through Traefik. Auth endpoints have a stricter rate limit.

## 3. Deployment targets

| Target | Entry point | Migrations | Verified (2026-10-05) |
|--------|-------------|------------|-----------------------|
| Docker Compose (single VM) | `deployments/docker/docker-compose.yml` | backend entrypoint (`RUN_MIGRATIONS=true`) | full stack + monitoring end-to-end, real browser |
| Docker Swarm | `deployments/swarm/docker-stack.yml` | one-shot `migrate` service | config validated only |
| Kubernetes (Helm) | `deployments/helm/resume-review` | `post-install,pre-upgrade` hook Job | installed, tested, upgraded on a local kind cluster |
| Cloud VM | `infra/terraform/envs/*` + `infra/ansible` | via Compose | `validate` / lint only |

## 4. Security model (summary)

- Roles: `candidate` (default, the only self-registrable role), `expert`, `admin`. Admins are bootstrapped with the
  `python -m app.cmd.create_admin` CLI; there is no HTTP route that grants privileges.
- JWT access (15 min) and refresh (24 h) tokens with a unique `jti`. Logout and refresh rotation revoke by `jti`.
- Secrets come only from env or secret stores. `.env`, vault files and htpasswd are gitignored, and only examples are committed.
- Containers run as non-root with read-only root filesystems, `no-new-privileges` and all capabilities dropped (except where an image needs specific ones).
- Only the proxy publishes ports. The database sits on an internal network (Compose) or behind a NetworkPolicy (Helm).

## 5. Change History

- 2026-10-05 — Created during the clean-architecture refactor (see `agentlog.md`).
