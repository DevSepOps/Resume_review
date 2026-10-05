# Traefik Reverse Proxy

## 1. Purpose
TLS termination (Let's Encrypt), routing by hostname, rate limiting, request-size limits, security headers and the protected Traefik dashboard, for Compose (`providers.docker`) and Swarm (`providers.swarm`).

## 2. Architecture
- Static config: `deployments/docker/proxy/traefik.yml` (Compose), `deployments/swarm/traefik/traefik.yml` (Swarm).
- Dynamic config (shared): `deployments/docker/proxy/dynamic.yml` - middlewares + TLS options only. Routers/services come from labels.
- Entrypoints: `web :80` (permanent redirect to HTTPS), `websecure :443` (default cert resolver `le`, global `secure-headers` + `compress`), `ping` (127.0.0.1:8082, healthcheck only).
- Docker API access through `tecnativa/docker-socket-proxy` on an `internal` network.
- ACME email/CA are placeholders (`__ACME_EMAIL__`, `__ACME_CA_SERVER__`) rendered by the container entrypoint with `sed`, because Traefik cannot read env vars in a static file and does not allow mixing file and env/flag static config.

Routers (hosts from env via label interpolation)
| Host | Service | Middlewares |
|------|---------|-------------|
| `APP_DOMAIN` | frontend:8001 (sticky cookie `rr_affinity`, websockets pass through) | rate-limit-default, body-limit |
| `API_DOMAIN` | backend:8000 (`/ready` is not routed publicly) | rate-limit-api, body-limit |
| `API_DOMAIN` + `/users/login|register|refresh_token` (priority 100) | backend | rate-limit-auth (10/min, burst 5), body-limit |
| `TRAEFIK_DOMAIN` | `api@internal` | dashboard-auth (basicAuth usersFile), rate-limit-ops |
| `GRAFANA_DOMAIN`, `PORTAINER_DOMAIN` | grafana:3000, portainer:9000 | rate-limit-ops |

## 3. Inputs (Variables)
`APP_DOMAIN`, `API_DOMAIN`, `TRAEFIK_DOMAIN`, `GRAFANA_DOMAIN`, `PORTAINER_DOMAIN`, `ACME_EMAIL`, `ACME_CA_SERVER` (production CA by default; staging URL in `.env.example` comment),
`proxy/secrets/htpasswd` (bcrypt, create with `htpasswd -nbB admin 'password' > htpasswd`; gitignored, `htpasswd.example` provided).

## 4. Outputs
HTTPS endpoints above; certificates in volume `traefik_letsencrypt` (`acme.json`, mode 600).

## 5. Security Rules
- `api.insecure: false`; port 8080 never published; dashboard only via the authenticated HTTPS router.
- Docker socket never mounted into Traefik (read-only filtered proxy). Access log drops all request headers except User-Agent.
- Middlewares: HSTS, nosniff, frameDeny, referrer/permissions policy, `Server` header removed; per-IP rate limits (stricter on API/auth); body buffering limit 11534336 bytes (~11 MiB) for 10 MB PDF uploads + multipart overhead; TLS >= 1.2, `sniStrict`.
- CORS is NOT set in Traefik: the backend owns it (`CORS_ORIGINS`); the old `*` + credentials middleware was invalid and was removed.
- No Content-Security-Policy is injected (Flet web needs inline scripts/wasm); revisit after measuring.
- Behind another LB/CDN, rate limits see its IP: set `ipStrategy.depth`/`excludedIPs` in `dynamic.yml` and `forwardedHeaders.trustedIPs` on the entrypoints.

## 6. Deployment Steps
See compose-deploy / swarm-deploy runbooks. Test with the staging CA first (`ACME_CA_SERVER=https://acme-staging-v02.api.letsencrypt.org/directory`), then delete the `traefik_letsencrypt` volume (or `acme.json`) and switch to production.

## 7. Rollback
Previous image tag `traefik:v3.6` is pinned; restore the previous config files and `docker compose up -d proxy`. Swarm: previous `CFG_REV`.

## 8. Monitoring & Alerts
`traefik healthcheck --ping` container healthcheck; JSON logs on stdout (`docker compose logs proxy`).

## 9. Change History
- v2.10 -> v3.6, file+label routing rewritten for v3 syntax, dashboard secured, CORS middleware removed, ACME email/CA from env.
