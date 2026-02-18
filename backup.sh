#!/bin/bash
# backup.sh - Backup script for seminars-app
# Retention: 180 days

set -e

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/data/backups}"
DB_PATH="${DB_PATH:-/data/seminars.db}"
UPLOADS_DIR="${UPLOADS_DIR:-/data/uploads}"
RETENTION_DAYS=180
DATE=$(date +%Y%m%d_%H%M%S)
HOSTNAME=$(hostname)

# Ensure backup directory exists
mkdir -p "$BACKUP_DIR"

# Create backup filename
BACKUP_FILE="$BACKUP_DIR/seminars_backup_${DATE}.db"
UPLOADS_BACKUP="$BACKUP_DIR/seminars_uploads_${DATE}.tar.gz"

echo "Starting backup at $(date)"
echo "Database: $DB_PATH"
echo "Uploads: $UPLOADS_DIR"
echo "Backup: $BACKUP_FILE"

# Check if database exists
if [ ! -f "$DB_PATH" ]; then
    echo "WARNING: Database not found at $DB_PATH"
    echo "Creating empty backup marker..."
    touch "$BACKUP_FILE.empty"
else
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
fi

# Backup uploads directory
if [ -d "$UPLOADS_DIR" ] && [ "$(ls -A $UPLOADS_DIR)" ]; then
    echo "Backing up uploads..."
    tar -czf "$UPLOADS_BACKUP" -C "$(dirname $UPLOADS_DIR)" "$(basename $UPLOADS_DIR)"
    echo "Uploads backed up: $UPLOADS_BACKUP"
else
    echo "No uploads to backup"
fi

# Clean old backups (older than 180 days)
echo "Cleaning backups older than $RETENTION_DAYS days..."
DELETED=$(find "$BACKUP_DIR" -name "seminars_backup_*.db*" -type f -mtime +$RETENTION_DAYS -delete -print | wc -l)
DELETED_UPLOADS=$(find "$BACKUP_DIR" -name "seminars_uploads_*.tar.gz" -type f -mtime +$RETENTION_DAYS -delete -print | wc -l)
echo "Deleted $DELETED old database backup(s) and $DELETED_UPLOADS old uploads backup(s)"

# List remaining backups
echo ""
echo "Current backups:"
ls -lh "$BACKUP_DIR" 2>/dev/null || echo "No backups found"

echo ""
echo "Backup completed at $(date)"
