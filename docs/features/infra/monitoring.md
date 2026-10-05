# Monitoring Stack (Metricbeat -> Logstash -> Elasticsearch -> Grafana)

## 1. Purpose
Host-level system metrics (CPU, load, memory, network, filesystem) with a Grafana dashboard. Optional: Compose profile `monitoring`, or `docker-stack.monitoring.yml` on Swarm.

## 2. Architecture
- Metricbeat 8.17.0 (`system` module, host `/proc`, `/sys/fs/cgroup`, `/` mounted read-only under `/hostfs`; flags `--strict.perms=false --system.hostfs=/hostfs`) -> Logstash 8.17.0 (`:5044`) -> Elasticsearch 8.17.0 (`http://elasticsearch:9200`, security on, index `metricbeat-YYYY.MM.dd`; other events go to `logstash-YYYY.MM.dd`).
- Grafana OSS 11.4.0 with provisioned datasource uid `elasticsearch-metricbeat` (index `metricbeat-*`, `@timestamp`, basic auth `elastic`) and dashboard `metricbeat-system.json` (all panels reference that uid; host variable uses `host.name.keyword`).
- All Elastic components are on the internal `monitoring_net`; only Grafana is also on `public_net` and routed through Traefik. Elasticsearch/Logstash publish no ports.
- Files: `deployments/docker/monitoring/{logstash,metricbeat,grafana}`.

## 3. Inputs (Variables)
`ELASTIC_PASSWORD`, `ES_JAVA_OPTS` (heap, default `-Xms512m -Xmx512m`; container limit 1.5 GiB), `GRAFANA_ADMIN_USER/PASSWORD`, `GRAFANA_DOMAIN`.
Host kernel setting for Elasticsearch: `vm.max_map_count>=262144` (needed outside single-node dev mode; recommended always).

## 4. Outputs
Grafana at `https://$GRAFANA_DOMAIN`, indices `metricbeat-*`.

## 5. Security Rules
- No credentials in files: Logstash and Grafana read `ELASTIC_PASSWORD` from the environment (the previous config leaked a public IP and password; that password must be considered compromised and rotated wherever it was reused).
- Metricbeat runs as root (needs host /proc) with `cap_drop: ALL` + `DAC_READ_SEARCH`, `SYS_PTRACE`, and no Docker socket.
- Elasticsearch HTTP is plain HTTP on the internal network only. Grafana sign-up disabled, secure cookies, dashboards provisioned read-only.

## 6. Deployment Steps
Compose: `docker compose --profile monitoring up -d`. Swarm: `docker stack deploy -c docker-stack.monitoring.yml resume-mon`.

## 7. Rollback
Remove the profile services (`docker compose --profile monitoring down`); data stays in `es_data`/`grafana_data` unless volumes are removed.

## 8. Monitoring & Alerts
Healthchecks: Elasticsearch `_cluster/health` (green or yellow accepted), Logstash `:9600`, Grafana `/api/health`. No alert rules are provisioned.

## 9. Change History
- Versions aligned (8.17.0 everywhere, previously Metricbeat 7.17 vs ES 8.7), hardcoded IP/password removed, datasource uid fixed, `beat.name` -> `host.name`.
- The dashboard has no panel filter on the host variable (as in the original); the variable is cosmetic until queries add `host.name:$hostname`.
