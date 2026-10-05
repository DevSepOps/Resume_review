#!/usr/bin/env bash
# Runs once on first init of the postgres container (docker-entrypoint-initdb.d).
# Creates a read-only role ONLY if DB_READONLY_PASSWORD is set.
set -euo pipefail

if [ -z "${DB_READONLY_PASSWORD:-}" ]; then
  echo "init: DB_READONLY_PASSWORD not set, skipping read-only role"
  exit 0
fi

DB_READONLY_USER="${DB_READONLY_USER:-read_only_user}"

psql -v ON_ERROR_STOP=1 \
  --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
  -v ro_user="$DB_READONLY_USER" -v ro_pass="$DB_READONLY_PASSWORD" -v db="$POSTGRES_DB" <<'SQL'
-- Read-only role for reporting / debugging.
SELECT format('CREATE ROLE %I LOGIN PASSWORD %L', :'ro_user', :'ro_pass')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :'ro_user')
\gexec

SELECT format('GRANT CONNECT ON DATABASE %I TO %I', :'db', :'ro_user') \gexec
SELECT format('GRANT USAGE ON SCHEMA public TO %I', :'ro_user') \gexec
SELECT format('GRANT SELECT ON ALL TABLES IN SCHEMA public TO %I', :'ro_user') \gexec
-- Tables created later by migrations (run as the owner role) stay readable.
SELECT format('ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO %I', :'ro_user') \gexec
SQL
echo "init: read-only role '${DB_READONLY_USER}' ready"
