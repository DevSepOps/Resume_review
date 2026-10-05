# Troubleshooting - Infrastructure (Compose / Swarm)

| Symptom | Cause | Fix |
|---|---|---|
| `required variable X is missing a value` | `.env`/shell lacks a required value | fill it in `.env` (Compose) or export `stack.env` (Swarm) |
| Postgres rejects the password / empty creds | `.env` missing or the DB volume was initialised with other creds | check `docker compose config | grep POSTGRES`; for a fresh DB `docker volume rm <project>_postgres_data` (destroys data) |
| `backend` unhealthy, logs "could not translate host name db" | backend not on `internal_net` or db not started | `docker compose ps`; db must be healthy; check networks in `docker compose config` |
| Special chars in DB password break `DATABASE_URL` | password is not URL-encoded | use `openssl rand -hex 24` |
| `proxy` unhealthy / restarting | bad static config, missing `proxy/secrets/htpasswd` (Docker creates a directory instead) | `docker compose logs proxy`; `rm -rf proxy/secrets/htpasswd` if it is a directory, create the file |
| Certificate not issued | DNS wrong, port 80 blocked, or ACME rate limit | check `docker compose logs proxy | grep -i acme`; test with the staging CA; `forbidden domain` errors mean a placeholder `ACME_EMAIL` (example.com) |
| Browser shows Traefik default cert | cert not issued yet, or a router host does not match | verify `APP_DOMAIN`/`API_DOMAIN` and DNS |
| 404 from Traefik | router not created: container unhealthy/not on `resume_public_net`, label typo | `docker compose logs proxy`; dashboard shows routers |
| 404 on `API_DOMAIN/ready` | intentional, `/ready` is not routed publicly | use `/health`, or exec in the container |
| 413 on upload | body over ~11 MiB (`body-limit`) or `MAX_UPLOAD_MB` | raise `MAX_UPLOAD_MB` and `maxRequestBodyBytes` in `proxy/dynamic.yml` |
| 429 responses | rate limits (`rate-limit-*` in `dynamic.yml`); behind a CDN all clients share one IP | tune limits / `ipStrategy` |
| Flet UI disconnects with several replicas | sticky cookie dropped (http, or cookie blocked) | use HTTPS; check `rr_affinity` cookie; or run one replica |
| Uploaded PDFs vanish / permission denied on `/app/data/uploads` | volume owned by root while the app runs non-root | the backend Dockerfile must create and chown `/app/data/uploads` for the app user before the volume is first mounted; or `docker run --rm -v <project>_backend_uploads:/d alpine chown -R <uid>:<gid> /d` |
| Read-only filesystem error in an app container | app writes outside `/tmp` / the uploads volume | set the path to `/tmp`, or add a tmpfs/volume in the compose file |
| Elasticsearch exits: `max virtual memory areas ... too low` | host `vm.max_map_count` | `sudo sysctl -w vm.max_map_count=262144` |
| Grafana panels "No data" / datasource error | ES password mismatch or no `metricbeat-*` index yet | `curl -u elastic:$ELASTIC_PASSWORD http://elasticsearch:9200/_cat/indices` from `monitoring_net` (e.g. `docker compose exec elasticsearch curl ...`); check logstash logs |
| Swarm: service `pending` | placement constraints unsatisfied | add node labels (`docker node update --label-add ...`) |
| Swarm: `network resume_public not found` (monitoring stack) | core stack not deployed first | deploy `docker-stack.yml` first |
| Swarm: `config ... already exists / cannot update` | configs are immutable | bump `CFG_REV` and redeploy |
| Swarm: Traefik "port is missing" | service has `traefik.enable=true` without `loadbalancer.server.port` | add the label under `deploy.labels` |
| `curl: tlsv1 unrecognized name` / browser `ERR_SSL_UNRECOGNIZED_NAME_ALERT` | `sniStrict: true` and no certificate for the requested host yet (ACME failed or the name is local, e.g. `*.localhost`) | Production: fix DNS so ACME can issue, then check the proxy logs for `le.acme`. Local: use `docker-compose.override.example.yml` (direct ports on 127.0.0.1), or add a self-signed cert under `tls.certificates` in a local copy of `proxy/dynamic.yml` |
| Metricbeat container `unhealthy`, but data still arrives | the healthcheck ran `metricbeat test config` without `--strict.perms=false` while the bind-mounted config is owned by the host user | fixed in compose (2026-10-05); the healthcheck now passes `--strict.perms=false` |
| Helm: migrations Job stuck in `Init` with `pg_isready ... no attempt` | the init container runs as a uid without a passwd entry, so `pg_isready` has no default user | fixed in chart 2.0.0 (`-U healthcheck`); upgrade the chart |
