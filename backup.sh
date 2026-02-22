#!/bin/bash
# backup.sh - Robust backup script for seminars-app
# Retention: 180 days
# Includes: Database, uploads, fallback mirror, and automated verification

set -e

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/data/backups}"
DB_PATH="${DB_PATH:-/data/seminars.db}"
UPLOADS_DIR="${UPLOADS_DIR:-/data/uploads}"
FALLBACK_MIRROR_DIR="${FALLBACK_MIRROR_DIR:-fallback-mirror}"
DROPBOX_REMOTE="${DROPBOX_REMOTE:-dropbox:}"
DROPBOX_BACKUP_PATH="${DROPBOX_BACKUP_PATH:-/seminars-app/backups}"
RETENTION_DAYS=180
DATE=$(date +%Y%m%d_%H%M%S)
HOSTNAME=$(hostname)
BACKUP_LOG="$BACKUP_DIR/backup.log"

# Ensure backup directory exists
mkdir -p "$BACKUP_DIR"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$BACKUP_LOG"
}

# Create backup filename
DB_BACKUP="$BACKUP_DIR/seminars_db_${DATE}.db"
UPLOADS_BACKUP="$BACKUP_DIR/seminars_uploads_${DATE}.tar.gz"
MIRROR_BACKUP="$BACKUP_DIR/seminars_mirror_${DATE}.tar.gz"
FULL_BACKUP="$BACKUP_DIR/seminars_full_${DATE}.tar.gz"

log "=========================================="
log "Starting backup at $(date)"
log "Database: $DB_PATH"
log "Uploads: $UPLOADS_DIR"
log "Fallback mirror: $FALLBACK_MIRROR_DIR"
log "Backup directory: $BACKUP_DIR"

# Check if database exists
if [ ! -f "$DB_PATH" ]; then
    log "WARNING: Database not found at $DB_PATH"
    log "Creating empty backup marker..."
    touch "$DB_BACKUP.empty"
else
    # Create SQLite backup (safe copy using SQLite's backup command)
    log "Creating database backup..."
    if sqlite3 "$DB_PATH" ".backup '$DB_BACKUP'"; then
        log "Database backup created successfully"
        
        # Verify backup integrity
        log "Verifying backup integrity..."
        if sqlite3 "$DB_BACKUP" "PRAGMA integrity_check;" | grep -q "ok"; then
            log "Backup integrity verified"
            
            # Compress backup
            log "Compressing database backup..."
            gzip "$DB_BACKUP"
            DB_BACKUP="${DB_BACKUP}.gz"
            DB_SIZE=$(stat -c%s "$DB_BACKUP")
            log "Database backup compressed: $DB_BACKUP ($DB_SIZE bytes)"
        else
            log "ERROR: Backup integrity check failed"
            rm -f "$DB_BACKUP"
            exit 1
        fi
    else
        log "ERROR: Failed to create database backup"
        exit 1
    fi
fi

# Backup uploads directory
if [ -d "$UPLOADS_DIR" ] && [ "$(ls -A $UPLOADS_DIR 2>/dev/null)" ]; then
    log "Backing up uploads..."
    if tar -czf "$UPLOADS_BACKUP" -C "$(dirname $UPLOADS_DIR)" "$(basename $UPLOADS_DIR)"; then
        UPLOADS_SIZE=$(stat -c%s "$UPLOADS_BACKUP")
        log "Uploads backed up: $UPLOADS_BACKUP ($UPLOADS_SIZE bytes)"
    else
        log "ERROR: Failed to backup uploads"
        exit 1
    fi
else
    log "No uploads to backup"
    UPLOADS_BACKUP=""
fi

# Backup fallback mirror directory (HTML recovery files)
if [ -d "$FALLBACK_MIRROR_DIR" ] && [ "$(ls -A $FALLBACK_MIRROR_DIR 2>/dev/null)" ]; then
    log "Backing up fallback mirror..."
    if tar -czf "$MIRROR_BACKUP" "$FALLBACK_MIRROR_DIR"; then
        MIRROR_SIZE=$(stat -c%s "$MIRROR_BACKUP")
        log "Fallback mirror backed up: $MIRROR_BACKUP ($MIRROR_SIZE bytes)"
    else
        log "WARNING: Failed to backup fallback mirror (non-critical)"
        MIRROR_BACKUP=""
    fi
else
    log "No fallback mirror to backup"
    MIRROR_BACKUP=""
fi

# Create full backup manifest
MANIFEST="$BACKUP_DIR/backup_manifest_${DATE}.txt"
{
    echo "Backup Date: $(date)"
    echo "Hostname: $HOSTNAME"
    echo "Database: $DB_BACKUP"
    [ -n "$UPLOADS_BACKUP" ] && echo "Uploads: $UPLOADS_BACKUP"
    [ -n "$MIRROR_BACKUP" ] && echo "Fallback Mirror: $MIRROR_BACKUP"
    echo ""
    echo "File checksums:"
    [ -f "$DB_BACKUP" ] && md5sum "$DB_BACKUP"
    [ -n "$UPLOADS_BACKUP" ] && md5sum "$UPLOADS_BACKUP"
    [ -n "$MIRROR_BACKUP" ] && md5sum "$MIRROR_BACKUP"
} > "$MANIFEST"

# Create full tarball including manifest
if [ -f "$DB_BACKUP" ] || [ -n "$UPLOADS_BACKUP" ] || [ -n "$MIRROR_BACKUP" ]; then
    log "Creating full backup package..."
    tar -czf "$FULL_BACKUP" -C "$BACKUP_DIR" \
        $(basename "$DB_BACKUP" 2>/dev/null || true) \
        $(basename "$UPLOADS_BACKUP" 2>/dev/null || true) \
        $(basename "$MIRROR_BACKUP" 2>/dev/null || true) \
        $(basename "$MANIFEST") \
        2>/dev/null || true
    
    if [ -f "$FULL_BACKUP" ]; then
        FULL_SIZE=$(stat -c%s "$FULL_BACKUP")
        log "Full backup created: $FULL_BACKUP ($FULL_SIZE bytes)"
    fi
fi

# Upload to Dropbox if rclone is configured
if command -v rclone &> /dev/null; then
    log "Uploading to Dropbox..."
    
    # Upload full backup
    if [ -f "$FULL_BACKUP" ]; then
        if rclone copy "$FULL_BACKUP" "${DROPBOX_REMOTE}${DROPBOX_BACKUP_PATH}/" 2>/dev/null; then
            log "Full backup uploaded to Dropbox"
        else
            log "WARNING: Failed to upload full backup to Dropbox"
        fi
    fi
    
    # Upload fallback mirror separately for easy access
    if [ -n "$MIRROR_BACKUP" ] && [ -f "$MIRROR_BACKUP" ]; then
        if rclone copy "$MIRROR_BACKUP" "${DROPBOX_REMOTE}${DROPBOX_BACKUP_PATH}/" 2>/dev/null; then
            log "Fallback mirror uploaded to Dropbox"
        else
            log "WARNING: Failed to upload fallback mirror to Dropbox"
        fi
    fi
    
    # Clean old backups from Dropbox (older than RETENTION_DAYS)
    log "Cleaning old backups from Dropbox (older than $RETENTION_DAYS days)..."
    rclone delete --min-age "${RETENTION_DAYS}d" "${DROPBOX_REMOTE}${DROPBOX_BACKUP_PATH}/" 2>/dev/null || true
else
    log "rclone not found, skipping Dropbox upload"
fi

# Clean old backups (older than 180 days)
log "Cleaning backups older than $RETENTION_DAYS days..."
DELETED_DB=$(find "$BACKUP_DIR" -name "seminars_db_*.db*" -type f -mtime +$RETENTION_DAYS -delete -print 2>/dev/null | wc -l)
DELETED_UPLOADS=$(find "$BACKUP_DIR" -name "seminars_uploads_*.tar.gz" -type f -mtime +$RETENTION_DAYS -delete -print 2>/dev/null | wc -l)
DELETED_MIRROR=$(find "$BACKUP_DIR" -name "seminars_mirror_*.tar.gz" -type f -mtime +$RETENTION_DAYS -delete -print 2>/dev/null | wc -l)
DELETED_FULL=$(find "$BACKUP_DIR" -name "seminars_full_*.tar.gz" -type f -mtime +$RETENTION_DAYS -delete -print 2>/dev/null | wc -l)
DELETED_MANIFEST=$(find "$BACKUP_DIR" -name "backup_manifest_*.txt" -type f -mtime +$RETENTION_DAYS -delete -print 2>/dev/null | wc -l)
log "Deleted: $DELETED_DB DB, $DELETED_UPLOADS uploads, $DELETED_MIRROR mirror, $DELETED_FULL full backups, $DELETED_MANIFEST manifests"

# List remaining backups
log ""
log "Current backups:"
ls -lh "$BACKUP_DIR"/*.tar.gz "$BACKUP_DIR"/*.gz 2>/dev/null | tail -25 || log "No backups found"

# Verify latest backup can be restored (test integrity)
if [ -f "$FULL_BACKUP" ]; then
    log ""
    log "Testing backup integrity..."
    if tar -tzf "$FULL_BACKUP" > /dev/null 2>&1; then
        log "Backup archive integrity verified"
    else
        log "WARNING: Backup archive may be corrupted"
    fi
fi

# Report disk usage
log ""
log "Disk usage:"
df -h "$BACKUP_DIR" | tail -1

log ""
log "Backup completed at $(date)"
log "=========================================="

# Return success if we created at least a database backup
[ -f "$DB_BACKUP" ] || [ -f "$DB_BACKUP.empty" ]
