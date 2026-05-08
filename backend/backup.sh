#!/bin/bash

DB_PATH="/var/www/worker/Worker-Zydrunas/backend/instance/worker_hours.db"
BACKUP_DIR="/var/www/worker/Worker-Zydrunas/backend/backups"
KEEP_DAYS=30

mkdir -p "$BACKUP_DIR"

FILENAME="worker_hours_$(date +%Y-%m-%d).db"
sqlite3 "$DB_PATH" ".backup '$BACKUP_DIR/$FILENAME'"

# Remove backups older than KEEP_DAYS days
find "$BACKUP_DIR" -name "*.db" -mtime +$KEEP_DAYS -delete

echo "$(date '+%Y-%m-%d %H:%M:%S') Backup saved: $FILENAME"
