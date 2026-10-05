# Runbook: Helm Deploy (resume-review)

## 1. Purpose
Install, upgrade and roll back Resume Review on Kubernetes with `deployments/helm/resume-review`.

## 2. How to Run
Prerequisites: Helm 3.12+/4, a cluster with an ingress controller (default class `traefik`), a default StorageClass, optionally cert-manager.
Offline validation (no cluster needed):
```
helm lint deployments/helm/resume-review --set secrets.values.POSTGRES_USER=u --set secrets.values.POSTGRES_PASSWORD=p --set secrets.values.POSTGRES_DB=d --set secrets.values.JWT_SECRET_KEY=$(openssl rand -hex 32) --set secrets.values.FLET_SECRET_KEY=$(openssl rand -hex 16)
helm template t deployments/helm/resume-review -f deployments/helm/resume-review/values-example.yaml | kubeconform -strict -ignore-missing-schemas -summary
```

## 3. How to Deploy
1. Create the Secret (recommended) with keys `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `JWT_SECRET_KEY` (>= 32 chars), `FLET_SECRET_KEY`, `DATABASE_URL` (`postgresql+psycopg2://user:pass@<release>-db:5432/db`, credentials URL-encoded):
   `kubectl -n resume-review create secret generic resume-review-secrets --from-literal=...`
2. Copy and edit `values-example.yaml` (hosts, TLS, image tag, storage classes).
3. Install / upgrade:
   `helm upgrade --install rr deployments/helm/resume-review -n resume-review --create-namespace -f my-values.yaml --wait --timeout 10m`
4. `helm test rr -n resume-review`
5. Create the first admin: `kubectl -n resume-review exec -it deploy/rr-backend -- python -m app.cmd.create_admin --username <u> --email <e>`

Upgrade order: the migration Job runs before the new pods (pre-upgrade). If you changed chart-managed secrets/config in the same upgrade, the Job still sees the old values; use an existing Secret updated beforehand for DB credential changes.
With `--wait` on first install the post-install hook runs after resources are ready; backend readiness only checks DB connectivity, so this does not deadlock.

## 4. Health Checks
Backend `/health` (liveness), `/ready` (readiness, DB). `kubectl -n resume-review get pods,jobs,pvc,ingress`; `helm test rr`.

## 5. Monitoring
Chart ships none; see "Monitoring & Alerts" in `docs/features/infra/helm-chart.md`.

## 6. Debugging
- Pods Pending: PVC unbound (`kubectl describe pvc`; set `*.storageClass`).
- Backend not ready: `kubectl logs deploy/rr-backend`; check DB pod and `DATABASE_URL`.
- API errors right after install: migration Job still running/failed: `kubectl logs job/rr-resume-review-migrate`. Failed hook Job remains for inspection until the next release action; re-run with `helm upgrade`.
- `required` errors at render time list the missing secret value.
- Cannot scale backend: uploads need an RWX StorageClass.
- Postgres "directory exists but is not empty": PGDATA is the `pgdata` subdir, so the volume's `lost+found` is fine; check `fsGroup`/volume permissions.

## 7. Disaster Recovery
- Rollback: `helm history rr -n resume-review`, `helm rollback rr <rev> -n resume-review`. Schema is not reverted; only roll back across migrations that are backward compatible, otherwise restore the DB.
- Backup DB: `kubectl -n resume-review exec rr-db-0 -- sh -c 'pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB"' > backup.sql`; restore with `psql` into a fresh DB.
- Uploads: snapshot the `<fullname>-uploads` PVC (VolumeSnapshot) or copy `/app/data/uploads`.
- `helm uninstall` keeps the uploads PVC and the DB volume (StatefulSet PVCs); delete explicitly when intended.

## 8. Ownership
Infra / DevOps owner of `deployments/helm/`.

## 9. Change History
- 2026-10-05: Initial runbook for rewritten chart v2.0.0.
