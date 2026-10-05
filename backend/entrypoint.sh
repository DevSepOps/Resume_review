#!/usr/bin/env bash
# Container entrypoint: wait for DB -> (optional) migrate -> serve.
set -euo pipefail

: "${DATABASE_URL:?DATABASE_URL is required}"
RUN_MIGRATIONS="${RUN_MIGRATIONS:-true}"
export DB_WAIT_TIMEOUT="${DB_WAIT_TIMEOUT:-60}"

echo "entrypoint: waiting for database (timeout ${DB_WAIT_TIMEOUT}s)"
python - <<'PY'
import os
import socket
import sys
import time

from sqlalchemy.engine import make_url

url = make_url(os.environ["DATABASE_URL"])
if not url.host:  # e.g. sqlite: nothing to wait for
    sys.exit(0)
host, port = url.host, url.port or 5432
deadline = time.monotonic() + int(os.environ["DB_WAIT_TIMEOUT"])
while True:
    try:
        with socket.create_connection((host, port), timeout=3):
            print(f"entrypoint: database reachable at {host}:{port}")
            break
    except OSError as exc:
        if time.monotonic() >= deadline:
            print(f"entrypoint: database {host}:{port} not reachable: {exc}", file=sys.stderr)
            sys.exit(1)
        time.sleep(1)
PY

if [ "${RUN_MIGRATIONS}" = "true" ]; then
  echo "entrypoint: running migrations"
  alembic upgrade head
fi

echo "entrypoint: starting uvicorn"
exec uvicorn app.cmd.server:app \
  --host 0.0.0.0 --port 8000 \
  --workers "${WEB_CONCURRENCY:-2}" \
  --proxy-headers \
  --forwarded-allow-ips "${FORWARDED_ALLOW_IPS:-127.0.0.1}"
