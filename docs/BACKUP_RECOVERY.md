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

4. **Fallback HTML Mirror** (`fallback-mirror/`)
   - **recovery.html** — Human-readable backup: full seminar content (abstract, speaker, logistics), speaker bios, suggestions. Use for emergency recovery.
   - **changelog.html** — Technical tracking: plans, slots, activity, files.
   - **index.html** — Entry point with links to both.
   - Backed up as `seminars_mirror_YYYYMMDD_HHMMSS.tar.gz` and uploaded to Dropbox for offsite access

### Backup Schedule

- **Frequency**: Daily at 2:00 AM UTC
- **Retention**: 180 days (6 months)
- **Local Location**: `/data/backups/` on the persistent volume
- **Offsite Location**: Dropbox (if rclone is configured)

### Backup Types

1. **Database Backup**: `seminars_db_YYYYMMDD_HHMMSS.db.gz`
2. **Uploads Backup**: `seminars_uploads_YYYYMMDD_HHMMSS.tar.gz`
3. **Fallback Mirror**: `seminars_mirror_YYYYMMDD_HHMMSS.tar.gz` (HTML recovery files)
4. **Full Backup**: `seminars_full_YYYYMMDD_HHMMSS.tar.gz` (includes all above + manifest)

## Automated Backups

### Automated Backups

Backups run daily at 2:00 AM UTC via **GitHub Actions**.

**Setup:**
1. Create a Fly.io token: `flyctl tokens create deploy -a seminars-app`
2. Add it to GitHub: Repository Settings → Secrets and variables → Actions → New repository secret
3. Name: `FLY_API_TOKEN`, Value: (the token from step 1)

The workflow in `.github/workflows/backup.yml` runs automatically. Monitor in the Actions tab.

See [SCHEDULED_BACKUPS.md](SCHEDULED_BACKUPS.md) for details.

### Offsite Backups (Dropbox)

The backup script automatically uploads backups to Dropbox if `rclone` is configured:

1. Configure rclone with your Dropbox account:
   ```bash
   rclone config
   ```

2. Set environment variables (optional):
   ```bash
   DROPBOX_REMOTE="dropbox:"
   DROPBOX_BACKUP_PATH="/seminars-app/backups"
   ```

3. The backup script will automatically:
   - Upload full backups to Dropbox
   - Upload fallback mirror separately for easy access
   - Clean old backups (older than 180 days) from Dropbox

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

### Scenario 3: Fly.io Down - Access Fallback Mirror

If the app and Fly.io are unavailable, access your data via the fallback mirror:

#### Option 1: Download from Dropbox (Recommended)

1. Log into your Dropbox account
2. Navigate to `/seminars-app/backups/`
3. Download the latest `seminars_mirror_*.tar.gz` file
4. Extract and open `index.html` in your browser:
   ```bash
   tar -xzf seminars_mirror_20260222_114518.tar.gz
   open fallback-mirror/index.html
   ```

#### Option 2: Download from Fly.io (if SSH still works)

```bash
# List available mirror backups
fly ssh console --app seminars-app -C "ls -la /data/backups/seminars_mirror_*.tar.gz"

# Download via sftp
fly sftp get /data/backups/seminars_mirror_YYYYMMDD_HHMMSS.tar.gz

# Extract and view
tar -xzf seminars_mirror_YYYYMMDD_HHMMSS.tar.gz
open fallback-mirror/index.html
```

### Scenario 4: Single File Recovery

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
2. **Monitor backup logs** - Check daily for errors: `cat /data/backups/backup.log | tail -20`
3. **Keep offsite copies** - Verify Dropbox uploads are working
4. **Document changes** - Note any schema changes that might affect restores
5. **Verify fallback mirror updates** - Download the latest mirror from Dropbox periodically and verify it opens correctly
6. **Test offline access** - Ensure you can open the fallback mirror HTML files without internet

## Contact

For backup/restore issues, check:
1. Backup log: `/data/backups/backup.log`
2. Application logs: `fly logs --app seminars-app`
3. Volume status: `fly volumes list --app seminars-app`
