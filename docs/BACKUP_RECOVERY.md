# Seminars App - Backup and Recovery Guide

## Overview

This document describes the backup strategy, automated backup procedures, and recovery processes for the seminars-app.

## Backup Strategy

### What is Backed Up

1. **Database** (`/data/seminars.db`)
   - All seminars, speakers, semester plans, and related data
   - SQLite database with integrity verification
   - Compressed with gzip

2. **Uploaded Files** (`/data/uploads/`)
   - CVs, photos, passports, flight documents
   - Tar.gz archive with full directory structure

3. **Backup Manifest**
   - Metadata about each backup
   - MD5 checksums for integrity verification
   - Timestamp and hostname information

### Backup Schedule

- **Frequency**: Daily at 2:00 AM UTC
- **Retention**: 180 days (6 months)
- **Location**: `/data/backups/` on the persistent volume

### Backup Types

1. **Database Backup**: `seminars_db_YYYYMMDD_HHMMSS.db.gz`
2. **Uploads Backup**: `seminars_uploads_YYYYMMDD_HHMMSS.tar.gz`
3. **Full Backup**: `seminars_full_YYYYMMDD_HHMMSS.tar.gz` (includes both + manifest)

## Automated Backups

### Cron Job

A cron job is configured to run backups automatically:

```bash
0 2 * * * /app/backup.sh
```

This runs daily at 2:00 AM UTC.

### Monitoring Backups

Check backup status by examining the backup log:

```bash
fly ssh console --app seminars-app
cat /data/backups/backup.log | tail -50
```

### Backup Verification

Each backup includes:
- SQLite integrity check (`PRAGMA integrity_check`)
- Archive integrity verification
- MD5 checksums for all files
- Detailed logging

## Manual Backup

To create a manual backup:

```bash
fly ssh console --app seminars-app
/app/backup.sh
```

## Recovery Procedures

### Scenario 1: Database Corruption

1. Access the server:
   ```bash
   fly ssh console --app seminars-app
   ```

2. List available backups:
   ```bash
   ls -la /data/backups/seminars_db_*.gz | tail -10
   ```

3. Stop the application (optional but recommended):
   ```bash
   # Note: This will temporarily make the app unavailable
   ```

4. Restore from backup:
   ```bash
   # Backup current corrupted database
   cp /data/seminars.db /data/seminars.db.corrupted.$(date +%Y%m%d)
   
   # Extract and restore
   gunzip -c /data/backups/seminars_db_YYYYMMDD_HHMMSS.db.gz > /data/seminars.db
   
   # Verify integrity
   sqlite3 /data/seminars.db "PRAGMA integrity_check;"
   ```

5. Restart the application (if stopped)

### Scenario 2: Complete Data Loss

1. Access the server:
   ```bash
   fly ssh console --app seminars-app
   ```

2. Find the latest full backup:
   ```bash
   ls -la /data/backups/seminars_full_*.tar.gz | tail -5
   ```

3. Restore everything:
   ```bash
   cd /data
   
   # Extract full backup
   tar -xzf /data/backups/seminars_full_YYYYMMDD_HHMMSS.tar.gz
   
   # Restore database
   gunzip -c seminars_db_*.db.gz > seminars.db
   
   # Restore uploads
   tar -xzf seminars_uploads_*.tar.gz
   ```

4. Verify the restoration:
   ```bash
   sqlite3 /data/seminars.db "SELECT COUNT(*) FROM seminars;"
   ls -la /data/uploads/
   ```

### Scenario 3: Single File Recovery

To recover a specific uploaded file:

```bash
# Extract uploads backup
tar -xzf /data/backups/seminars_uploads_YYYYMMDD_HHMMSS.tar.gz

# Find and copy the specific file
find uploads/ -name "filename.pdf" -exec cp {} /data/uploads/ \;
```

## Backup Retention Policy

- **Daily backups**: Kept for 180 days
- **After 180 days**: Automatically deleted by the backup script
- **Log retention**: Backup logs are appended indefinitely (monitor size)

## Storage Requirements

Estimate storage needs:
- Database: ~1-10 MB (grows with data)
- Uploads: Variable (depends on file uploads)
- Backups: ~2x current data size (for 180 days retention)

Current volume size: 1GB (can be expanded if needed)

## Troubleshooting

### Backup Failures

Check the backup log:
```bash
cat /data/backups/backup.log | grep -i error
```

Common issues:
1. **Disk full**: Clean old backups or expand volume
2. **Database locked**: App may be writing; retry later
3. **Permission denied**: Check directory permissions

### Restore Failures

1. **Corrupted backup**: Try an older backup
2. **Integrity check fails**: Database may be partially corrupted; try older backup
3. **Missing files**: Check if uploads backup exists

## Best Practices

1. **Test restores periodically** - Don't wait for disaster
2. **Monitor backup logs** - Check daily for errors
3. **Keep offsite copies** - Download critical backups locally
4. **Document changes** - Note any schema changes that might affect restores

## Contact

For backup/restore issues, check:
1. Backup log: `/data/backups/backup.log`
2. Application logs: `fly logs --app seminars-app`
3. Volume status: `fly volumes list --app seminars-app`
