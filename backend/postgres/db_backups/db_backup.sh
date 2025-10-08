#!/usr/bin/env bash

DATE=$(date "+%F_%H-%M-%S")
BACKUP_DIR=/devsepops/backend/postgres/db_backups/
DB_CONTAINER=resume_app_db
DB_NAME="resume_db"
DB_USER="user"
DB_PASS="password"
mkdir -p $BACKUP_DIR
docker exec -e PGPASSWORD="$DB_PASS" $DB_CONTAINER pg_dump -U $DB_USER $DB_NAME > $BACKUP_DIR/backup_$DATE.sql
find $BACKUP_DIR -mtime +7 -type f -delete

# Do not publish this script and keep it safe
# Use cronjobs for daily backups
# Backup everyday at 03:00 AM
# 0 3 * * * /devsepops/backend/postgres/db_backups//db_backup.sh
