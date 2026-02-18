#!/bin/bash
# backup.sh - Backup script for seminars-app
# Retention: 180 days

set -e

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/data/backups}"
DB_PATH="${DB_PATH:-/data/seminars.db}"
RETENTION_DAYS=180
DATE=$(date +%Y%m%d_%H%M%S)
HOSTNAME=$(hostname)

# Ensure backup directory exists
mkdir -p "$BACKUP_DIR"

# Create backup filename
BACKUP_FILE="$BACKUP_DIR/seminars_backup_${DATE}.db"

echo "Starting backup at $(date)"
echo "Database: $DB_PATH"
echo "Backup: $BACKUP_FILE"

# Check if database exists
if [ ! -f "$DB_PATH" ]; then
    echo "ERROR: Database not found at $DB_PATH"
    exit 1
fi

# Create SQLite backup (safe copy)
echo "Creating database backup..."
sqlite3 "$DB_PATH" ".backup '$BACKUP_FILE'"

# Verify backup
if [ ! -f "$BACKUP_FILE" ]; then
    echo "ERROR: Backup file was not created"
    exit 1
fi

BACKUP_SIZE=$(stat -c%s "$BACKUP_FILE")
echo "Backup created: $BACKUP_FILE ($BACKUP_SIZE bytes)"

# Compress backup
echo "Compressing backup..."
gzip "$BACKUP_FILE"
BACKUP_FILE="${BACKUP_FILE}.gz"
echo "Compressed: $BACKUP_FILE"

# Clean old backups (older than 180 days)
echo "Cleaning backups older than $RETENTION_DAYS days..."
DELETED=$(find "$BACKUP_DIR" -name "seminars_backup_*.db.gz" -type f -mtime +$RETENTION_DAYS -delete -print | wc -l)
echo "Deleted $DELETED old backup(s)"

# List remaining backups
echo ""
echo "Current backups:"
ls -lh "$BACKUP_DIR"/seminars_backup_*.db.gz 2>/dev/null || echo "No backups found"

# Optional: Sync to Dropbox (if DROPBOX_TOKEN is set)
if [ -n "$DROPBOX_TOKEN" ]; then
    echo ""
    echo "Syncing to Dropbox..."
    
    # Upload to Dropbox
    curl -X POST https://content.dropboxapi.com/2/files/upload \
        --header "Authorization: Bearer $DROPBOX_TOKEN" \
        --header "Dropbox-API-Arg: {\"path\": \"/seminars-app/backups/$(basename $BACKUP_FILE)\", \"mode\": \"add\"}" \
        --header "Content-Type: application/octet-stream" \
        --data-binary @"$BACKUP_FILE" || echo "Dropbox upload failed"
fi

echo ""
echo "Backup completed at $(date)"
