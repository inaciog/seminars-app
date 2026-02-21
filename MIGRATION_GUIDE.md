# Migration Guide: InacioTool Seminars → Seminars App

This guide walks you through migrating the Seminars module from InacioTool to the standalone seminars-app.

## Pre-Migration Checklist

- [ ] Backup current InacioTool database
- [ ] Verify auth-service is running and accessible
- [ ] Verify dashboard-app can be updated
- [ ] Generate new API_SECRET for seminars-app
- [ ] Create Fly.io app and volume

## Step-by-Step Migration

### Step 1: Prepare the New Repository

```bash
# Clone or create the seminars-app repository
git clone https://github.com/inaciog/seminars-app.git
cd seminars-app

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Export Data from InacioTool

```bash
# Navigate to InacioTool directory
cd /path/to/inaciotool

# Export seminars-related tables
sqlite3 data/inaciotool.db <<EOF
.mode insert
.output seminars_export.sql
.output stdout
SELECT 'BEGIN TRANSACTION;';

-- Export speakers
SELECT 'DELETE FROM speaker;';
.output seminars_export.sql
SELECT * FROM speaker;
.output stdout

-- Export seminars
SELECT 'DELETE FROM seminar;';
.output seminars_export.sql
SELECT * FROM seminar;
.output stdout

-- Export semester plans
SELECT 'DELETE FROM semesterplan;';
.output seminars_export.sql
SELECT * FROM semesterplan;
.output stdout

-- Export seminar slots
SELECT 'DELETE FROM seminarslot;';
.output seminars_export.sql
SELECT * FROM seminarslot;
.output stdout

-- Export speaker suggestions
SELECT 'DELETE FROM speakersuggestion;';
.output seminars_export.sql
SELECT * FROM speakersuggestion;
.output stdout

-- Export speaker availability
SELECT 'DELETE FROM speakeravailability;';
.output seminars_export.sql
SELECT * FROM speakeravailability;
.output stdout

-- Export speaker info
SELECT 'DELETE FROM speakerinfo;';
.output seminars_export.sql
SELECT * FROM speakerinfo;
.output stdout

-- Export uploaded files
SELECT 'DELETE FROM uploaded_files;';
.output seminars_export.sql
SELECT * FROM uploaded_files;
.output stdout

SELECT 'COMMIT;';
EOF

# Copy file uploads
mkdir -p seminars-app-uploads
cp -r uploads/seminars/* seminars-app-uploads/ 2>/dev/null || echo "No uploads to copy"
```

### Step 3: Import Data to Seminars App

```bash
cd /path/to/seminars-app

# Initialize database (tables are created on first app startup)
python -c "from app.main import get_engine; from sqlmodel import SQLModel; SQLModel.metadata.create_all(get_engine())"

# Import data
sqlite3 data/seminars.db < /path/to/inaciotool/seminars_export.sql

# Verify import
sqlite3 data/seminars.db "SELECT COUNT(*) FROM speaker;"
sqlite3 data/seminars.db "SELECT COUNT(*) FROM seminar;"
```

### Step 4: Configure Environment Variables

Create `.env` file:

```env
# Required
JWT_SECRET=your-jwt-secret-must-match-auth-service
API_SECRET=generate-a-random-secret-for-dashboard
DATABASE_URL=sqlite:///./data/seminars.db

# Optional
UPLOADS_DIR=./uploads
BACKUP_DIR=./backups
DROPBOX_TOKEN=your-dropbox-token-for-backups
PORT=8080
HOST=0.0.0.0
```

### Step 5: Deploy to Fly.io

```bash
# Login to Fly.io
fly auth login

# Create app (if not already created)
fly apps create seminars-app

# Create volume for persistent storage
fly volumes create seminars_data --size 3 --region ams

# Set secrets
fly secrets set JWT_SECRET="your-jwt-secret"
fly secrets set API_SECRET="your-api-secret"
fly secrets set DROPBOX_TOKEN="your-dropbox-token"  # Optional

# Deploy
fly deploy

# Verify deployment
fly status
fly logs
```

### Step 6: Update Dashboard App

Add to dashboard-app configuration:

```javascript
// config/services.js
const SERVICES = {
  // ... existing services
  seminars: {
    url: 'https://seminars-app.fly.dev',  // or your custom domain
    apiSecret: process.env.SEMINARS_API_SECRET
  }
};
```

Add environment variable to dashboard-app:
```bash
fly secrets set SEMINARS_API_SECRET="your-api-secret" -a dashboard-app
```

### Step 7: Test Integration

1. **Test authentication**:
   ```bash
   # Get token from auth-service
   curl "https://inacio-auth.fly.dev/api/auth/login" \
     -X POST \
     -H "Content-Type: application/json" \
     -d '{"password": "i486983nacio:!"}'
   
   # Use token with seminars-app
   curl "https://seminars-app.fly.dev/api/seminars?token=YOUR_TOKEN"
   ```

2. **Test external API**:
   ```bash
   curl "https://seminars-app.fly.dev/api/external/stats?secret=YOUR_API_SECRET"
   ```

3. **Test dashboard integration**:
   - Visit dashboard-app
   - Verify seminars widget loads
   - Check that upcoming seminars are displayed

### Step 8: Update InacioTool (Optional)

After confirming seminars-app works:

1. Remove seminars routes from InacioTool
2. Add redirect or link to new seminars-app
3. Update documentation

```python
# In InacioTool API, add redirect
@app.get("/api/v1/seminars/{path:path}")
async def redirect_seminars():
    return {
        "message": "Seminars module has moved",
        "new_url": "https://seminars-app.fly.dev"
    }
```

### Step 9: Final Verification

- [ ] All seminars data migrated correctly
- [ ] File uploads accessible
- [ ] Authentication works with auth-service tokens
- [ ] Dashboard shows seminar data
- [ ] Backup script runs successfully
- [ ] Auto-stop machines work correctly

## Rollback Procedure

If issues occur:

1. **Immediate rollback**:
   ```bash
   # Scale down seminars-app
   fly scale count 0 -a seminars-app
   
   # Re-enable InacioTool seminars
   # (restore from backup if needed)
   ```

2. **Data recovery**:
   ```bash
   # Restore from backup
   sqlite3 data/seminars.db ".restore 'backups/seminars_backup_YYYYMMDD_HHMMSS.db'"
   ```

## Post-Migration

- Monitor logs for errors: `fly logs -a seminars-app`
- Verify backups are running: Check Dropbox folder
- Update user documentation with new URL
- Archive old InacioTool database after 30 days

## Troubleshooting

### Database Locked
If you see "database is locked" errors:
```bash
# Check for other connections
lsof data/seminars.db

# Restart the app
fly restart -a seminars-app
```

### JWT Validation Fails
- Verify JWT_SECRET matches auth-service
- Check token hasn't expired
- Ensure token is passed correctly (?token=xxx)

### External API 403 Errors
- Verify API_SECRET is set correctly
- Check secret is being passed as query parameter
- Ensure secrets match between seminars-app and dashboard-app
