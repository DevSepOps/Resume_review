# Runbook - Docker Swarm Deploy

## 1. Purpose
Deploy the core stack (and optionally monitoring) on a Docker Swarm cluster.

## 2. How to Run
```bash
# 1. Init (first manager) and join workers
docker swarm init --advertise-addr <manager-ip>
docker swarm join-token worker             # run the printed command on each worker

# 2. Label nodes (placement constraints in the stack)
docker node update --label-add db=true       <db-node>        # postgres_data lives here
docker node update --label-add uploads=true  <uploads-node>   # backend replicas + backend_uploads volume (often the same node as db)
docker node update --label-add monitoring=true <mon-node>     # only for docker-stack.monitoring.yml
# on the monitoring node: sudo sysctl -w vm.max_map_count=262144

# 3. Configure
cd deployments/swarm
cp stack.env.example stack.env             # replace every CHANGE_ME, set TAG=sha-xxxxxxx
mkdir -p secrets && htpasswd -nbB admin 'strong-password' > secrets/htpasswd

# 4. Deploy (stack deploy does NOT read .env: export the variables into the shell)
set -a; . ./stack.env; set +a
docker stack deploy --with-registry-auth -c docker-stack.yml resume
docker stack deploy --with-registry-auth -c docker-stack.monitoring.yml resume-mon   # optional, after the core stack
```
Validate before deploying: `docker stack config -c docker-stack.yml >/dev/null` (with variables exported) or `docker compose --env-file stack.env -f docker-stack.yml config -q`.

## 3. How to Deploy
- Update: change `TAG` in `stack.env`, re-export, re-run `docker stack deploy`. The `migrate` job re-runs because its image changed; backend/frontend roll with `start-first` and roll back automatically if the new tasks fail their healthchecks.
- Migration ordering: Swarm does not order the `migrate` job before the backend update. Use expand/contract (backward-compatible) migrations, or run `docker service update --image ...:<TAG> resume_migrate` first and wait for `Complete` before updating the backend.
- Config/secret change: Swarm configs/secrets are immutable. Edit the file, increase `CFG_REV` in `stack.env`, re-export and redeploy; remove old ones with `docker config rm` / `docker secret rm` later.
- Uploads storage: `backend_uploads` is a node-local volume, hence the `uploads=true` constraint (a single node holds the files). For several nodes switch the volume to NFS (commented `driver_opts` in the stack) and drop the constraint.
- Secrets tradeoff: values are plain env in the service spec (visible via `docker service inspect`); restrict manager access. See features/infra/docker-swarm.md.

## 4. Health Checks
`docker stack services resume`, `docker service ps resume_backend --no-trunc`, `docker service logs resume_migrate`, `curl -fsS https://$API_DOMAIN/health`.

## 5. Monitoring
`resume-mon` stack -> `https://$GRAFANA_DOMAIN`. Metricbeat runs globally (one per node).

## 6. Debugging
- Service stuck `pending`: no node satisfies the constraints (`docker service ps --no-trunc`; check labels with `docker node inspect <n> --format '{{.Spec.Labels}}'`).
- Traefik shows no routers: labels must be under `deploy.labels`, `loadbalancer.server.port` set, service attached to `resume_public`. `docker service logs resume_proxy`.
- `migrate` failing: `docker service logs resume_migrate`; it retries up to 10 times then stays failed (fix, then `docker service update --force resume_migrate`).
- More in `docs/troubleshooting/infra.md`.

## 7. Disaster Recovery
- Backups: `docker exec $(docker ps -q -f name=resume_db) sh -c 'pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB"' | gzip > backup.sql.gz` on the db node; tar the `resume_backend_uploads` and `resume_traefik_letsencrypt` volumes the same way as in the compose runbook.
- Node loss: relabel a replacement node and restore volumes from backup before the constrained tasks can start.
- Rollback: `docker service rollback resume_backend` / `resume_frontend`.

## 8. Ownership
Platform/DevOps.

## 9. Change History
- Initial runbook for `deployments/swarm` (replaces `docker-swarm-readme.txt`, which created external volumes/network by hand).
