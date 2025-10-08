#!/usr/bin/env bash

BACKUP_FILE=/devsepops/backend/postgres/db_backups/backup_file.sql #backup-file
DB_CONTAINER=resume_app_db
DB_NAME="resume_db"
DB_USER="user"
DB_PASS="password"
mkdir -p $BACKUP_DIR
docker exec -e PGPASSWORD="$DB_PASS" $DB_CONTAINER psql -U $DB_USER $DB_NAME < $BACKUP_FILE
