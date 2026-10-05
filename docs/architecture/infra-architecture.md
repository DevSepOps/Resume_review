# Infrastructure Architecture

Contracts (service names, ports, env vars, images) are defined in [contracts.md](contracts.md).
This file describes how each deployment target realises them.

## Docker Compose

Single-host deployment: `deployments/docker/docker-compose.yml` (+ `.env`, copy of `.env.example`).

```
Internet :80/:443
      |
 [proxy: Traefik v3.6] --- socket_net(internal) --- [docker-socket-proxy] -- /var/run/docker.sock (ro)
      |  public_net
      +--> frontend :8001 (Flet, websockets, sticky cookie)
      +--> backend  :8000 (REST)  ---- internal_net(internal) ---- [db: postgres:16-alpine]
      +--> grafana :3000   (profile monitoring; also on monitoring_net(internal): elasticsearch, logstash, metricbeat)
      +--> portainer :9000 (profile ops)
```

Key decisions
- Only `proxy` publishes host ports (80/443). `db`, `backend`, `frontend` have no host ports; a loopback-only
  `docker-compose.override.example.yml` exists for local debugging.
- `internal_net` and `monitoring_net` are `internal: true` (no egress, no ingress). The database is never on `public_net`.
- Traefik reads container labels through a filtered `tecnativa/docker-socket-proxy` (read-only GET on containers/networks/services/tasks/info),
  so the Traefik process never holds the raw Docker socket.
- Profiles: default = proxy/frontend/backend/db; `monitoring` = Elastic stack + Grafana; `ops` = Portainer.
  Profiles instead of a second compose file keep one validated model, shared networks and one `.env`.
- Secrets: one gitignored `deployments/docker/.env`; each service receives only the variables it needs via `environment:` interpolation.
  `${VAR:?}` makes missing required values a hard error.
- Hardening: `no-new-privileges`, `cap_drop: [ALL]` (+ minimal `cap_add`), `read_only` root filesystems with tmpfs, resource limits, pinned image versions, json-file log rotation.
- No `version:` key: obsolete in Compose v2/the Compose Specification.

Details: [features/infra/docker-compose.md](../features/infra/docker-compose.md), [features/infra/traefik.md](../features/infra/traefik.md),
[features/infra/monitoring.md](../features/infra/monitoring.md), runbook [compose-deploy](../runbooks/infra/compose-deploy.md).

## Docker Swarm

Multi-node deployment: `deployments/swarm/docker-stack.yml` (core) and `docker-stack.monitoring.yml` (Elastic, Grafana, Portainer),
both configured by a gitignored `stack.env` exported into the deploying shell.

- Same services and routing as Compose. Traefik uses `providers.swarm` and reads `deploy.labels`; overlay networks `resume_public`, `resume_internal` (internal), `resume_socket` (internal), `resume_monitoring` (internal).
- Schema migrations run in a one-shot `migrate` service (`alembic upgrade head`, restart on failure only); `backend` replicas run with `RUN_MIGRATIONS=false`.
- Placement by node labels: `db=true` (postgres volume), `uploads=true` (backend, local upload volume), `monitoring=true` (Elastic/Grafana); proxy, socket proxy and Portainer on managers.
- Config files (Traefik, Logstash, Metricbeat, Grafana provisioning) are Swarm `configs`; the Traefik dashboard htpasswd is a Swarm `secret`. Both are immutable, versioned by `CFG_REV`.
- Limits: `security_opt` (no-new-privileges) is ignored by `docker stack deploy`; node-local volumes are not shared between nodes.

Details: [features/infra/docker-swarm.md](../features/infra/docker-swarm.md), runbook [swarm-deploy](../runbooks/infra/swarm-deploy.md).

## Kubernetes (Helm)

See [features/infra/helm-chart.md](../features/infra/helm-chart.md) and [runbooks/infra/helm-deploy.md](../runbooks/infra/helm-deploy.md) (section maintained by the Helm owner).

## Cloud (Terraform/Ansible)

See [features/infra/terraform-aws.md](../features/infra/terraform-aws.md), [features/infra/terraform-azure.md](../features/infra/terraform-azure.md),
[features/infra/ansible.md](../features/infra/ansible.md) and [runbooks/infra/provision-vm.md](../runbooks/infra/provision-vm.md) (section maintained by the Terraform/Ansible owner).
