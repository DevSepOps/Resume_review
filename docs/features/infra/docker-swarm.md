# Docker Swarm Stack

## 1. Purpose
Run the application on a multi-node Swarm with rolling updates, replicas and an automatic rollback on failed updates.

## 2. Architecture
Files: `deployments/swarm/docker-stack.yml` (core), `docker-stack.monitoring.yml` (Elastic stack, Grafana, Portainer), `traefik/traefik.yml` (swarm static config), `stack.env.example`, `secrets/htpasswd.example`.
Shared files are reused from `deployments/docker` (`proxy/dynamic.yml`, `monitoring/**`) via swarm `configs`, so there is no duplicated copy.

| Service | Replicas | Placement | Notes |
|---|---|---|---|
| docker-socket-proxy | 1 | manager | read-only API filter for Traefik |
| proxy (Traefik) | 1 | manager | host-mode 80/443; `acme.json` is single-writer |
| db | 1 | `node.labels.db == true` | local volume `postgres_data` |
| migrate | 1 job | any | `alembic upgrade head`, restart `on-failure` only |
| backend | 2 | `node.labels.uploads == true` | `RUN_MIGRATIONS=false`, rolling `start-first` |
| frontend | 2 | any | sticky cookie `rr_affinity` |
| elasticsearch/logstash/grafana | 1 each | `node.labels.monitoring == true` | monitoring stack |
| metricbeat | global | every node | |
| portainer | 1 | manager | |

Networks: `resume_public` (overlay), `resume_internal`, `resume_socket`, `resume_monitoring` (overlay, `internal: true`).

## 3. Inputs (Variables)
`stack.env` (from `stack.env.example`), exported into the shell before `docker stack deploy` (stack deploy does not read `.env`). `CFG_REV` versions the immutable configs/secret.

## 4. Outputs
Same public endpoints as Compose.

## 5. Security Rules
- Secrets are env values in the service spec (visible to anyone with `docker service inspect` on a manager). Tradeoff: the backend contract reads plain env vars. Hardening path: Docker `secrets:` + a small entrypoint shim that exports `*_FILE` contents (not implemented). The htpasswd file IS a Docker secret.
- `docker stack deploy` ignores `security_opt` (no `no-new-privileges`), `depends_on` and `restart`; `cap_drop`, `read_only`, tmpfs volumes and limits are applied.
- Internal overlays are `internal: true`; only Traefik publishes ports (host mode keeps client IPs).
- Local volumes are per node (postgres, uploads): constraints pin the tasks; for multi-node uploads use an NFS volume (commented in the stack).

## 6. Deployment Steps
See `docs/runbooks/infra/swarm-deploy.md`.

## 7. Rollback
`docker service rollback resume_backend` (also automatic on failed updates via `failure_action: rollback`), or redeploy with the previous `TAG`.

## 8. Monitoring & Alerts
Healthchecks (`docker service ps`), `docker service logs`, optional monitoring stack.

## 9. Change History
- Replaced `docker-compose.swarm.yml` and `docker-swarm-readme.txt`; removed relative bind mounts and `external: true` volumes; added migrate job, placement labels, v3 swarm provider.
