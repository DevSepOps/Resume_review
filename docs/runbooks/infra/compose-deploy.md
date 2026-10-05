# Runbook - Docker Compose Deploy

## 1. Purpose
Deploy and operate the stack on a single Docker host (Docker Engine 25+, Compose v2).

## 2. How to Run
```bash
cd deployments/docker
cp .env.example .env                       # replace EVERY CHANGE_ME; hex passwords: openssl rand -hex 32
cp proxy/secrets/htpasswd.example proxy/secrets/htpasswd
htpasswd -nbB admin 'strong-password' > proxy/secrets/htpasswd    # or: docker run --rm httpd:2.4-alpine htpasswd -nbB admin 'pw'
docker compose config -q                    # validates interpolation (fails on unset required vars)
docker compose up -d                        # core
docker compose --profile monitoring --profile ops up -d   # optional extras
```
Local debugging without DNS/TLS: `cp docker-compose.override.example.yml docker-compose.override.yml` then use `http://127.0.0.1:8000` (API) and `http://127.0.0.1:8001` (UI).
Create the first admin: `docker compose exec backend python -m app.cmd.create_admin --username <u> --email <e>` (prompts for the password).

## 3. How to Deploy
Prerequisites: DNS A/AAAA records for `APP_DOMAIN`, `API_DOMAIN` (+ `TRAEFIK_DOMAIN`, `GRAFANA_DOMAIN`, `PORTAINER_DOMAIN` if used) pointing at the host; ports 80/443 open (HTTP-01 challenge needs 80).
1. Test certificates first with `ACME_CA_SERVER=https://acme-staging-v02.api.letsencrypt.org/directory`; then `docker compose down`, `docker volume rm <project>_traefik_letsencrypt`, switch to the production CA and `up -d`.
2. Update: set `TAG=sha-xxxxxxx` (or `vX.Y.Z`) in `.env`, `docker compose pull && docker compose up -d`. The backend entrypoint applies Alembic migrations on start (`RUN_MIGRATIONS=true`).
3. To build locally instead: `docker compose build` (needs `deployments/docker/{backend,frontend}/Dockerfile`).
4. Elasticsearch: `sudo sysctl -w vm.max_map_count=262144` (persist in `/etc/sysctl.d/`).

## 4. Health Checks
`docker compose ps` (all `healthy`); `curl -fsS https://$API_DOMAIN/health`; `/ready` is intentionally not routed publicly - check inside: `docker compose exec backend python -c "import urllib.request as u;print(u.urlopen('http://127.0.0.1:8000/ready').read())"`.

## 5. Monitoring
Profile `monitoring` -> `https://$GRAFANA_DOMAIN` (dashboard "metricbeat-system"). Logs: `docker compose logs -f proxy backend`.

## 6. Debugging
See `docs/troubleshooting/infra.md`. Quick: `docker compose logs <svc>`, `docker inspect --format '{{json .State.Health}}' <container>`, `docker compose config` (rendered file).

## 7. Disaster Recovery
- DB backup: `docker compose exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB"' | gzip > backup-$(date +%F).sql.gz`
- Restore into an empty DB: `gunzip -c backup.sql.gz | docker compose exec -T db sh -c 'psql -U "$POSTGRES_USER" "$POSTGRES_DB"'`
- Uploads: `docker run --rm -v <project>_backend_uploads:/d:ro -v "$PWD":/b alpine tar czf /b/uploads.tgz -C /d .`
- Also back up `<project>_traefik_letsencrypt` (certs) and `.env` (secret manager, not git).

## 8. Ownership
Platform/DevOps (infra). Contracts: `docs/architecture/contracts.md`.

## 9. Change History
- Initial runbook for `deployments/docker` (replaces `docker-compose.prod.yml`).
