#!/usr/bin/env bash
# Restore a pg_dump -Fc archive.  Usage: db_restore.sh <backup.dump>
# Credentials come from the environment: PGHOST PGPORT PGUSER PGPASSWORD PGDATABASE.
# WARNING: --clean drops existing objects in the target database first.
set -euo pipefail

: "${PGHOST:?PGHOST is required}"
: "${PGUSER:?PGUSER is required}"
: "${PGPASSWORD:?PGPASSWORD is required}"
: "${PGDATABASE:?PGDATABASE is required}"
BACKUP_DIR="${BACKUP_DIR:-./backups}"
BACKUP_FILE="${1:-}"

if [ -z "$BACKUP_FILE" ]; then
  echo "usage: $0 <backup.dump>   (BACKUP_DIR=$BACKUP_DIR)" >&2
  ls -1 "$BACKUP_DIR" 2>/dev/null >&2 || true
  exit 2
fi
[ -f "$BACKUP_FILE" ] || { echo "no such file: $BACKUP_FILE" >&2; exit 1; }

pg_restore --clean --if-exists --no-owner --dbname "$PGDATABASE" "$BACKUP_FILE"
echo "restored $BACKUP_FILE into $PGDATABASE"
