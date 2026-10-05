#!/usr/bin/env bash
# Logical backup with pg_dump custom format.
# Credentials come from the environment: PGHOST PGPORT PGUSER PGPASSWORD PGDATABASE.
# Cron example (daily 03:00):  0 3 * * * /path/to/db_backup.sh
set -euo pipefail

: "${PGHOST:?PGHOST is required}"
: "${PGUSER:?PGUSER is required}"
: "${PGPASSWORD:?PGPASSWORD is required}"
: "${PGDATABASE:?PGDATABASE is required}"
BACKUP_DIR="${BACKUP_DIR:-./backups}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"

mkdir -p "$BACKUP_DIR"
stamp="$(date '+%F_%H-%M-%S')"
target="$BACKUP_DIR/backup_${stamp}.dump"
tmp="$target.part"

if ! pg_dump -Fc --no-owner --file "$tmp"; then
  rm -f "$tmp"
  echo "backup failed; existing backups left untouched" >&2
  exit 1
fi
mv "$tmp" "$target"
echo "backup written: $target"

# Rotate only after a successful dump.
find "$BACKUP_DIR" -maxdepth 1 -type f -name 'backup_*.dump' -mtime "+$RETENTION_DAYS" -delete
