# Scheduled Backups Setup Guide

This document describes how to set up daily automated backups using GitHub Actions.

## Overview

The backup script (`backup.sh`) handles:
- Database backup (compressed SQLite)
- Uploaded files backup (CVs, photos, etc.)
- **Fallback mirror backup** (HTML files for offline access)
- Upload to Dropbox (if rclone is configured)
- 180-day retention policy

## Setup

### Step 1: Get Your Fly.io API Token

Run this command to create a token:

```bash
flyctl tokens create deploy -a seminars-app
```

Copy the token (it starts with `FlyV1` or `fo1_`).

### Step 2: Add FLY_API_TOKEN to GitHub

1. Go to your GitHub repository: `https://github.com/inaciog/seminars-app`
2. Click **Settings** tab
3. Click **Secrets and variables** → **Actions** (left sidebar)
4. Click **New repository secret**
5. Fill in:
   - **Name**: `FLY_API_TOKEN`
   - **Value**: (paste the token from step 1)
6. Click **Add secret**

### Step 3: Verify

The workflow is already configured in `.github/workflows/backup.yml`. It will:
- Run daily at 2:00 AM UTC
- SSH into your Fly.io machine
- Run the backup script
- List recent backups

To test manually:
1. Go to the **Actions** tab in your GitHub repo
2. Click **Daily Backup**
3. Click **Run workflow**

## Monitoring Backups

### Check Backup Status via API

```bash
curl "https://seminars-app.fly.dev/api/admin/backup-status?secret=YOUR_API_SECRET"
```

### Check Logs on Fly.io

```bash
# View backup log
fly ssh console --app seminars-app -C "cat /data/backups/backup.log | tail -50"

# Or check app logs
fly logs --app seminars-app | grep -i backup
```

### Manual Backup Trigger

```bash
fly ssh console --app seminars-app -C "/app/backup.sh"
```

## Troubleshooting

### "Backup failed" notifications

1. Check if the app is running:
   ```bash
   fly status --app seminars-app
   ```

2. Check app logs:
   ```bash
   fly logs --app seminars-app
   ```

3. Verify the FLY_API_TOKEN is valid:
   ```bash
   flyctl tokens list
   ```

### Dropbox upload failures

1. Check rclone configuration:
   ```bash
   fly ssh console --app seminars-app
   rclone config show
   ```

2. Test rclone manually:
   ```bash
   rclone ls dropbox:seminars-app/backups/
   ```

### Disk space issues

```bash
fly ssh console --app seminars-app -C "df -h /data && du -sh /data/backups"
```
