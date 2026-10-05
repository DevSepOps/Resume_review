# Helm Chart: resume-review

Path: `deployments/helm/resume-review/`. Replaces the removed `deploy/` directory (broken scaffold + raw manifests).

## 1. Purpose
Deploy the Resume Review application (FastAPI backend, Flet frontend, PostgreSQL) to any Kubernetes cluster that already runs an ingress controller. Conforms to `docs/architecture/contracts.md`.

Out of scope (YAGNI): Traefik/ingress controller, ELK, Metricbeat, Portainer, Grafana. Use cluster-level operators instead (see section 8).

## 2. Architecture
```
Ingress (className, 2 hosts)
  appHost -> <release>-frontend:8001  (Deployment, sessionAffinity ClientIP)
  apiHost -> <release>-backend:8000   (Deployment, RUN_MIGRATIONS=false, uploads PVC at /app/data/uploads)
                      |
               <release>-db:5432      (StatefulSet, PVC, PGDATA=.../pgdata)  [db.enabled]
Migrations: Job `<fullname>-migrate`, hook post-install,pre-upgrade
```
Design decisions:
- **Migrations**: one Helm-hook Job runs `alembic upgrade head`; backend pods never migrate (no replica race). `post-install` (not `pre-install`) because the DB StatefulSet belongs to the same release and does not exist yet during pre-install hooks, which would hang. `pre-upgrade` migrates before new pods roll out, so migrations must be backward compatible with the previous app version (expand/contract). The Job has an init container that waits with `pg_isready`, `backoffLimit`, `activeDeadlineSeconds`, and is deleted on success.
- **Secrets**: `secrets.create=true` renders one Secret from values (all required, `JWT_SECRET_KEY` >= 32 chars); `DATABASE_URL` is built whole with URL-encoded credentials and stored in the Secret (no `$(VAR)` expansion). `secrets.create=false` uses `secrets.existingSecret` (recommended in production). Non-secret config lives in ConfigMaps. Pods roll when config or the chart-managed Secret changes (checksum annotations).
- **Uploads**: PVC (`helm.sh/resource-policy: keep`). Default ReadWriteOnce forces `backend.replicas=1` (template `fail`s otherwise) and `Recreate` strategy; ReadWriteMany allows scaling.
- **Database**: single-replica StatefulSet; `db.enabled=false` + `externalDatabase.url` (or `DATABASE_URL` in the existing Secret) for managed Postgres.
- Namespace comes from `helm install -n`; the chart creates no Namespace.

## 3. Inputs (Variables)
See `values.yaml` (commented) and `values-example.yaml`. Key values:

| Key | Default | Notes |
|---|---|---|
| `global.imageRegistry` / `global.imageTag` | `docker.io` / chart appVersion (`v1.0.0`) | tag `latest` is rejected |
| `backend.replicas`, `frontend.replicas` | 1 | backend > 1 needs `uploads.accessMode=ReadWriteMany` |
| `backend.env.*`, `frontend.env.*` | contract defaults | non-secret only |
| `db.enabled`, `db.persistence.size/storageClass` | true, 10Gi | |
| `externalDatabase.url` | "" | required when `db.enabled=false` and `secrets.create=true` |
| `secrets.create`, `secrets.existingSecret` | true, "" | existing Secret keys: `JWT_SECRET_KEY`, `FLET_SECRET_KEY`, `DATABASE_URL`, and with `db.enabled`: `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` |
| `secrets.values.*` | empty | required when `secrets.create=true` |
| `uploads.size/accessMode/storageClass` | 5Gi / RWO / "" | |
| `migrations.enabled` | true | |
| `ingress.*` | enabled, class `traefik`, hosts `app.example.com`/`api.example.com` | `tls.clusterIssuer` adds the cert-manager annotation |
| `networkPolicy.enabled` | false | DB reachable only from backend + migrations pods (requires a CNI that enforces NetworkPolicy) |

## 4. Outputs
Services `<release>-backend:8000`, `<release>-frontend:8001`, `<release>-db:5432`; Ingress `<fullname>`; Job `<fullname>-migrate`; PVC `<fullname>-uploads`; `helm test` pod (curls backend `/ready`). `NOTES.txt` prints endpoints and the admin bootstrap command.

## 5. Security Rules
- Pods: `runAsNonRoot` uid/gid 10001 (postgres 70), `seccompProfile: RuntimeDefault`, `allowPrivilegeEscalation: false`, drop ALL caps, `readOnlyRootFilesystem` with emptyDir `/tmp` (and `/var/run/postgresql` for Postgres), `automountServiceAccountToken: false`.
- No credentials in values defaults, ConfigMaps or rendered env values; secrets only via Secret `secretKeyRef`.
- Note: with `secrets.create=true`, secret values pass through Helm release storage (a Secret in the namespace). Prefer `existingSecret` (sealed-secrets/External Secrets) in production.
- No docker.sock/hostPath/hostNetwork; no `api.insecure` dashboards; the DB Service is ClusterIP only.
- Assumes images run as uid 10001 with `/app` as working dir containing `alembic.ini` (owned by the Docker agent's Dockerfiles; verify).

## 6. Deployment Steps
See `docs/runbooks/infra/helm-deploy.md`.

## 7. Rollback
`helm rollback <release> <rev>` restores app manifests. Database schema is NOT rolled back; migrations must be backward compatible. PVCs (uploads, DB) are retained. Details in the runbook.

## 8. Monitoring & Alerts
Not in the chart. Recommended: `kube-prometheus-stack` (Prometheus, Alertmanager, Grafana) for metrics, and Loki/Promtail or ECK operator for logs. Suggested alerts: backend `/ready` failing (probe failures), pod restarts, DB PVC > 80% full, uploads PVC > 80% full, migration Job failed. The backend does not expose Prometheus metrics yet.

## 9. Change History
- 2026-10-05: Chart rewritten from scratch (v2.0.0); `deploy/` removed. Dropped Traefik, ELK, Metricbeat, Portainer, Grafana from the chart.
