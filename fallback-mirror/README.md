This folder stores the plain HTML fallback mirror for seminars data.

The app regenerates all files after key data mutations.

## Files

- **index.html** — Entry point with links to the main files.
- **recovery.html** — Human-readable backup for emergency recovery. Contains full seminar content (title, abstract, speaker, room, logistics), speaker bios, speaker suggestions, and links to uploaded files. Use this to recover information if the app stops working.
- **changelog.html** — Technical/audit tracking: semester plans, slots, suggestions, seminars, files, and recent activity.
- **files/** — Copies of all uploaded files (CVs, papers, etc.) for recovery.

## Backup Strategy

The fallback mirror is automatically backed up via the `backup.sh` script:

1. **Local backup**: The entire `fallback-mirror/` directory is archived as `seminars_mirror_YYYYMMDD_HHMMSS.tar.gz`
2. **Dropbox upload**: If rclone is configured, the archive is uploaded to your Dropbox account
3. **Retention**: Backups are kept for 180 days (both locally and on Dropbox)

## Accessing the Fallback Mirror When Fly.io is Down

### Option 1: Download from Dropbox (Recommended)

1. Log into your Dropbox account
2. Navigate to `/seminars-app/backups/`
3. Download the latest `seminars_mirror_*.tar.gz` file
4. Extract and open `index.html` in your browser

### Option 2: Use Local Backup (if you have SSH access to the server)

```bash
# SSH into your Fly.io machine
fly ssh console

# Navigate to backups
cd /data/backups

# List mirror backups
ls -la seminars_mirror_*.tar.gz

# Download via flyctl
fly sftp get /data/backups/seminars_mirror_YYYYMMDD_HHMMSS.tar.gz
```

### Option 3: Generate from Database Backup

If you have a database backup but no fallback mirror:

```bash
# Restore the database
./restore.sh /path/to/seminars_db_YYYYMMDD_HHMMSS.db.gz

# Start the app locally
./dev.sh

# The fallback mirror will be generated automatically
# Find it at fallback-mirror/index.html
```

## Manual Generation

To manually regenerate the fallback mirror:

```bash
# Trigger via API (requires admin token)
curl -X POST "https://seminars-app.fly.dev/api/admin/refresh-mirror?token=YOUR_TOKEN"
```

Or locally:

```python
from app.main import refresh_fallback_mirror
from sqlmodel import Session
from app.main import engine

with Session(engine) as session:
    refresh_fallback_mirror(session)
```
