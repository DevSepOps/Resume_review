# Docker Compose Stack

## 1. Purpose
Run the whole product (proxy, frontend, backend, PostgreSQL, optional monitoring/ops) on one Docker host.

## 2. Architecture
See `docs/architecture/infra-architecture.md`. Files:
```
deployments/docker/
  docker-compose.yml                 services, networks, volumes, profiles
  docker-compose.override.example.yml  loopback ports for debugging (copy to docker-compose.override.yml)
  .env.example                       template for the gitignored .env
  proxy/        traefik.yml, dynamic.yml, secrets/htpasswd(.example)
  monitoring/   logstash, metricbeat, grafana provisioning + dashboard
  backend/ frontend/                 Dockerfiles (owned by app teams)
```
Services: `docker-socket-proxy`, `proxy` (Traefik v3.6), `db` (postgres:16-alpine), `backend`, `frontend`;
profile `ops`: `portainer`; profile `monitoring`: `elasticsearch`, `logstash`, `metricbeat`, `grafana` (Elastic stack 8.17.0, Grafana OSS 11.4.0).

## 3. Inputs (Variables)
All in `deployments/docker/.env` (see `.env.example`): `TAG`, `*_IMAGE`, `APP_DOMAIN`, `API_DOMAIN`, `GRAFANA_DOMAIN`, `TRAEFIK_DOMAIN`, `PORTAINER_DOMAIN`,
`ACME_EMAIL`, `ACME_CA_SERVER`, `POSTGRES_USER/PASSWORD/DB`, `JWT_SECRET_KEY`, `CORS_ORIGINS`, `FLET_SECRET_KEY`, `ELASTIC_PASSWORD`, `GRAFANA_ADMIN_*`, `ES_JAVA_OPTS`, tuning knobs from contracts.md.
`DATABASE_URL` is assembled in the compose file from the `POSTGRES_*` values (so the password lives in one place; use hex/alphanumeric passwords).
The root `.gitignore` already ignores `.env` and `.env.*` except `.env.example`.

## 4. Outputs
Public endpoints (HTTPS only; HTTP redirects): `https://$APP_DOMAIN`, `https://$API_DOMAIN`, `https://$TRAEFIK_DOMAIN` (basic auth),
`https://$GRAFANA_DOMAIN` (monitoring), `https://$PORTAINER_DOMAIN` (ops). Named volumes: `postgres_data`, `backend_uploads`, `traefik_letsencrypt`, `portainer_data`, `es_data`, `logstash_data`, `grafana_data`.

## 5. Security Rules
- Only the proxy publishes ports. `db` only on `internal_net` (`internal: true`); backend on `public_net` (for Traefik) and `internal_net`.
- `no-new-privileges`, `cap_drop: [ALL]`; `read_only` + tmpfs for backend (`/tmp`; writable data only `/app/data/uploads`), frontend (`/tmp`), db (`/tmp`, `/run/postgresql`), proxy, grafana.
- Non-root user comes from the app Dockerfiles (backend/frontend); Postgres/Grafana/Elastic use their image users.
- Secrets only in `.env` (CHANGE_ME placeholders in the template), never in the compose file. Portainer mounts the real Docker socket (root-equivalent): keep it off by default (`ops` profile).
- No `version:` key (obsolete in Compose v2). Images pinned; app images by `TAG` (use `sha-xxxxxxx`/`vX.Y.Z` in production).

## 6. Deployment Steps
See `docs/runbooks/infra/compose-deploy.md`.

## 7. Rollback
Set `TAG` to the previous value and `docker compose up -d`. Schema downgrades are not automatic (`alembic downgrade` manually).

## 8. Monitoring & Alerts
Container healthchecks (`docker compose ps`), Traefik JSON access logs on stdout, optional Grafana dashboards. See `features/infra/monitoring.md`. No alerting is configured.

## 9. Change History
- Replaced root `docker-compose.prod.yml`; fixed empty `${POSTGRES_*}` interpolation, pinned images, added networks, healthchecks, hardening, profiles.
