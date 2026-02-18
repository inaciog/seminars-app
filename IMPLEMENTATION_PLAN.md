# Seminars App - Integration Implementation Plan

## Executive Summary

This document outlines the complete implementation plan for extracting the Seminars module from InacioTool into a standalone "seminars-app" that integrates with the unified authentication system (auth-service) and provides external API access for the dashboard-app.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Repository Structure](#repository-structure)
3. [Database Schema Migration](#database-schema-migration)
4. [Authentication Integration](#authentication-integration)
5. [External API for Dashboard](#external-api-for-dashboard)
6. [Fly.io Deployment Configuration](#flyio-deployment-configuration)
7. [Backup Strategy](#backup-strategy)
8. [Dashboard Integration](#dashboard-integration)
9. [Migration Strategy](#migration-strategy)
10. [Implementation Timeline](#implementation-timeline)

---

## Architecture Overview

### Current State
- **InacioTool**: Monolithic Python/FastAPI app with SQLite database
- **Auth**: Custom access code-based authentication within InacioTool
- **Modules**: Seminars, Reimbursements, Teaching in a single codebase

### Target State
```
┌─────────────────────────────────────────────────────────────┐
│                    Unified Auth System                       │
│              https://inacio-auth.fly.dev                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   Login     │  │ JWT Issuer  │  │ Token Validation    │  │
│  │  (password) │  │ (30-day)    │  │  (JWT_SECRET)       │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
    ┌─────────────────┐ ┌──────────┐ ┌─────────────────┐
    │  Dashboard App  │ │Reminders │ │  Seminars App   │
    │  (Aggregator)   │ │   App    │ │  (This Project) │
    └─────────────────┘ └──────────┘ └─────────────────┘
              │                              │
              └──────────────┬───────────────┘
                             ▼
                    ┌─────────────────┐
                    │  External API   │
                    │  (apiSecret)    │
                    └─────────────────┘
```

### Key Changes
1. **Extract Seminars module** into standalone FastAPI app
2. **Replace access code auth** with JWT validation from auth-service
3. **Add external API endpoints** for dashboard integration
4. **Deploy independently** on Fly.io with auto-stop machines
5. **Implement 180-day backup** retention with Dropbox sync

---

## Repository Structure

### New Repository: `inaciog/seminars-app`

```
seminars-app/
├── .github/
│   └── workflows/
│       └── deploy.yml          # GitHub Actions for CI/CD
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py               # Configuration settings
│   ├── auth.py                 # JWT validation middleware
│   ├── database.py             # SQLModel/SQLite setup
│   ├── models.py               # Database models (from InacioTool)
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── seminars.py         # Seminar CRUD endpoints
│   │   ├── speakers.py         # Speaker management
│   │   ├── planning.py         # Semester planning
│   │   ├── files.py            # File upload/download
│   │   └── external.py         # External API for dashboard
│   └── services/
│       ├── __init__.py
│       ├── jwt_validator.py    # JWT validation service
│       └── backup.py           # Backup service
├── uploads/                    # File uploads directory
│   └── .gitkeep
├── data/                       # Database directory (Fly.io volume)
│   └── .gitkeep
├── backups/                    # Local backups (before Dropbox sync)
│   └── .gitkeep
├── tests/
│   ├── __init__.py
│   ├── test_auth.py
│   ├── test_seminars.py
│   └── test_external_api.py
├── scripts/
│   └── backup.sh               # Backup script with 180-day retention
├── Dockerfile
├── fly.toml
├── pyproject.toml
├── requirements.txt
└── README.md
```

---

## Database Schema Migration

### Tables to Migrate (from InacioTool)

```sql
-- Core seminar tables
- speaker
- seminar
- seminartemplate

-- Planning tables
- semesterplan
- seminarslot
- speakersuggestion
- speakeravailability
- speakerinfo
- planningdocument

-- File uploads
- uploaded_files

-- Activity tracking (optional)
- activity
```

### Tables NOT to Migrate

```sql
-- Auth tables (handled by auth-service)
- access_codes

-- Other module tables
- reimbursements_*
- teaching_*
```

### Schema Changes

#### 1. Remove Access Code Dependencies
```python
# OLD: In InacioTool, activities tracked access_code_id
# NEW: Track user_id from JWT token instead

class Activity(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    # OLD: actor_id: Optional[int] = Field(foreign_key="access_codes.id")
    # NEW:
    actor_user_id: Optional[str] = None  # From JWT 'sub' claim
    actor_role: Optional[str] = None     # From JWT 'role' claim
```

#### 2. Add External API Audit Log
```python
class ExternalApiCall(SQLModel, table=True):
    """Audit log for external API calls from dashboard."""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    endpoint: str
    method: str
    caller_ip: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    response_status: int
```

---

## Authentication Integration

### JWT Token Validation

Tokens are issued by auth-service and passed via URL parameter `?token=xxx`.

```python
# app/auth.py

import jwt
from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional

class AuthenticatedUser(BaseModel):
    """User authenticated via JWT from auth-service."""
    user_id: str  # JWT 'sub' claim
    role: str     # Custom claim from auth-service
    permissions: list[str]
    authenticated_at: datetime

# JWT validation settings
JWT_SECRET = os.environ["JWT_SECRET"]  # Same secret as auth-service
JWT_ALGORITHM = "HS256"

async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> AuthenticatedUser:
    """
    Validate JWT token from auth-service.
    
    Supports:
    - Query parameter: ?token=xxx
    - Authorization header: Bearer xxx
    - Cookie: token=xxx
    """
    token = None
    
    # Try query parameter (primary method for this architecture)
    token = request.query_params.get("token")
    
    # Try Authorization header
    if not token and credentials:
        token = credentials.credentials
    
    # Try cookie
    if not token:
        token = request.cookies.get("token")
    
    if not token:
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Provide token via ?token=xxx parameter."
        )
    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        
        # Validate required claims
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token: missing sub claim")
        
        # Extract role from custom claim
        role = payload.get("role", "viewer")
        permissions = payload.get("permissions", [])
        
        # Check token expiration (should be handled by jwt.decode, but double-check)
        exp = payload.get("exp")
        if exp and datetime.utcnow().timestamp() > exp:
            raise HTTPException(status_code=401, detail="Token expired")
        
        return AuthenticatedUser(
            user_id=user_id,
            role=role,
            permissions=permissions,
            authenticated_at=datetime.utcnow()
        )
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Permission checking
def require_permission(permission: str):
    """Dependency factory for requiring a specific permission."""
    async def permission_checker(
        user: AuthenticatedUser = Depends(get_current_user)
    ) -> AuthenticatedUser:
        if permission not in user.permissions and "admin" not in user.permissions:
            raise HTTPException(
                status_code=403,
                detail=f"Permission denied. Required: {permission}"
            )
        return user
    return permission_checker
```

### Role-to-Permission Mapping

```python
# app/config.py

ROLE_PERMISSIONS = {
    "admin": [
        "seminars:read",
        "seminars:write",
        "seminars:planning",
        "seminars:upload",
        "external:read"
    ],
    "seminar_organizer": [
        "seminars:read",
        "seminars:write",
        "seminars:planning",
        "seminars:upload"
    ],
    "seminar_viewer": [
        "seminars:read"
    ],
    "viewer": [
        "seminars:read"
    ]
}
```

---

## External API for Dashboard

### External API Router

```python
# app/routers/external.py

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from datetime import date, timedelta
from typing import Optional

from app.database import get_session
from app.auth import verify_api_secret
from app.models import Seminar, Speaker, SeminarStatus

router = APIRouter(prefix="/api/external", tags=["external"])

async def verify_external_auth(api_secret: str = Query(...)):
    """Verify API secret for service-to-service communication."""
    expected_secret = os.environ["API_SECRET"]
    if api_secret != expected_secret:
        raise HTTPException(status_code=403, detail="Invalid API secret")
    return True

@router.get("/stats")
async def get_stats(
    session: Session = Depends(get_session),
    _: bool = Depends(verify_external_auth)
):
    """Get seminar statistics for dashboard."""
    today = date.today()
    
    # Count upcoming seminars
    upcoming_count = session.exec(
        select(Seminar)
        .where(Seminar.date >= today)
        .where(Seminar.status != SeminarStatus.CANCELLED)
    ).all()
    
    # Count this month's seminars
    month_end = today + timedelta(days=30)
    this_month = session.exec(
        select(Seminar)
        .where(Seminar.date >= today)
        .where(Seminar.date <= month_end)
        .where(Seminar.status != SeminarStatus.CANCELLED)
    ).all()
    
    # Count pending bureaucracy tasks
    pending_tasks = 0
    for seminar in this_month:
        if not seminar.room_booked:
            pending_tasks += 1
        if not seminar.announcement_sent:
            pending_tasks += 1
    
    return {
        "total_upcoming": len(upcoming_count),
        "this_month": len(this_month),
        "pending_tasks": pending_tasks,
        "last_updated": today.isoformat()
    }

@router.get("/upcoming")
async def get_upcoming_seminars(
    limit: int = Query(5, ge=1, le=20),
    session: Session = Depends(get_session),
    _: bool = Depends(verify_external_auth)
):
    """Get upcoming seminars for dashboard display."""
    today = date.today()
    
    seminars = session.exec(
        select(Seminar)
        .where(Seminar.date >= today)
        .where(Seminar.status != SeminarStatus.CANCELLED)
        .order_by(Seminar.date)
        .limit(limit)
    ).all()
    
    result = []
    for sem in seminars:
        speaker_name = None
        if sem.speaker_id:
            speaker = session.get(Speaker, sem.speaker_id)
            speaker_name = speaker.name if speaker else None
        
        result.append({
            "id": sem.id,
            "title": sem.title,
            "date": sem.date.isoformat(),
            "time": f"{sem.start_time.strftime('%H:%M')}",
            "room": sem.room,
            "speaker": speaker_name,
            "status": sem.status.value,
            "room_booked": sem.room_booked,
            "announcement_sent": sem.announcement_sent
        })
    
    return {
        "seminars": result,
        "count": len(result)
    }

@router.get("/pending-tasks")
async def get_pending_tasks(
    days_ahead: int = Query(14, ge=1, le=90),
    session: Session = Depends(get_session),
    _: bool = Depends(verify_external_auth)
):
    """Get pending bureaucracy tasks for dashboard alerts."""
    today = date.today()
    check_date = today + timedelta(days=days_ahead)
    
    seminars = session.exec(
        select(Seminar)
        .where(Seminar.date >= today)
        .where(Seminar.date <= check_date)
        .where(Seminar.status.in_([SeminarStatus.PLANNED, SeminarStatus.CONFIRMED]))
        .order_by(Seminar.date)
    ).all()
    
    pending_tasks = []
    for sem in seminars:
        tasks = []
        if not sem.room_booked:
            tasks.append({"type": "room_booking", "priority": "high"})
        if not sem.announcement_sent:
            tasks.append({"type": "announcement", "priority": "medium"})
        if not sem.calendar_invite_sent:
            tasks.append({"type": "calendar_invite", "priority": "low"})
        
        if tasks:
            speaker_name = None
            if sem.speaker_id:
                speaker = session.get(Speaker, sem.speaker_id)
                speaker_name = speaker.name if speaker else None
            
            pending_tasks.append({
                "seminar_id": sem.id,
                "title": sem.title,
                "date": sem.date.isoformat(),
                "days_until": (sem.date - today).days,
                "speaker": speaker_name,
                "tasks": tasks
            })
    
    return {
        "tasks": pending_tasks,
        "total_count": len(pending_tasks),
        "check_period_days": days_ahead
    }

@router.get("/health")
async def external_health_check():
    """Health check for dashboard monitoring."""
    return {
        "status": "healthy",
        "service": "seminars-app",
        "timestamp": datetime.utcnow().isoformat()
    }
```

---

## Fly.io Deployment Configuration

### fly.toml

```toml
# fly.toml
app = 'seminars-app'
primary_region = 'ams'

[build]
  dockerfile = "Dockerfile"

[env]
  ENVIRONMENT = "production"
  PORT = "8080"
  HOST = "0.0.0.0"
  DATABASE_URL = "sqlite:////data/seminars.db"
  UPLOADS_DIR = "/data/uploads"
  BACKUP_DIR = "/data/backups"

[http_service]
  internal_port = 8080
  force_https = true
  auto_stop_machines = 'stop'
  auto_start_machines = true
  min_machines_running = 0
  processes = ['app']

  [[http_service.checks]]
    interval = '30s'
    timeout = '10s'
    grace_period = '40s'
    method = 'GET'
    path = '/api/health'

[[mounts]]
  source = 'seminars_data'
  destination = '/data'
  processes = ['app']

[[vm]]
  memory = '512mb'
  cpu_kind = 'shared'
  cpus = 1
```

### Dockerfile

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    sqlite3 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# Create necessary directories
RUN mkdir -p /data/uploads /data/backups

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=production
ENV PORT=8080

EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### requirements.txt

```txt
# requirements.txt
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
sqlmodel>=0.0.14
pydantic>=2.5.0
pydantic-settings>=2.1.0
python-multipart>=0.0.6
python-jose[cryptography]>=3.3.0
aiofiles>=23.2.0
httpx>=0.25.0
```

---

## Backup Strategy

### backup.sh Script

```bash
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
```

### GitHub Actions Workflow

```yaml
# .github/workflows/deploy.yml
name: Deploy to Fly.io

on:
  push:
    branches: [main]
  schedule:
    # Run backup daily at 3 AM UTC
    - cron: '0 3 * * *'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Fly.io
        uses: superfly/flyctl-actions/setup-flyctl@master

      - name: Deploy to Fly.io
        run: flyctl deploy --remote-only
        env:
          FLY_API_TOKEN: ${{ secrets.FLY_API_TOKEN }}

  backup:
    runs-on: ubuntu-latest
    if: github.event_name == 'schedule'
    steps:
      - name: Run backup on Fly.io
        uses: superfly/flyctl-actions/setup-flyctl@master

      - name: Execute backup
        run: |
          flyctl ssh console -a seminars-app -C "/app/backup.sh"
        env:
          FLY_API_TOKEN: ${{ secrets.FLY_API_TOKEN }}
```

---

## Dashboard Integration

### Dashboard App Changes

Add to `dashboard-app` configuration:

```javascript
// config/services.js
const SERVICES = {
  auth: {
    url: 'https://inacio-auth.fly.dev',
    jwtSecret: process.env.JWT_SECRET
  },
  seminars: {
    url: 'https://inacio-seminars.fly.dev',
    apiSecret: process.env.SEMINARS_API_SECRET
  },
  reminders: {
    url: 'https://inacio-reminders.fly.dev',
    apiSecret: process.env.REMINDERS_API_SECRET
  }
};

// services/seminars.js
async function getSeminarsStats() {
  const response = await fetch(
    `${SERVICES.seminars.url}/api/external/stats?secret=${SERVICES.seminars.apiSecret}`
  );
  return response.json();
}

async function getUpcomingSeminars(limit = 5) {
  const response = await fetch(
    `${SERVICES.seminars.url}/api/external/upcoming?secret=${SERVICES.seminars.apiSecret}&limit=${limit}`
  );
  return response.json();
}

async function getPendingTasks(daysAhead = 14) {
  const response = await fetch(
    `${SERVICES.seminars.url}/api/external/pending-tasks?secret=${SERVICES.seminars.apiSecret}&days_ahead=${daysAhead}`
  );
  return response.json();
}
```

### Dashboard Widget

```jsx
// components/SeminarsWidget.jsx
import React, { useEffect, useState } from 'react';

export function SeminarsWidget() {
  const [stats, setStats] = useState(null);
  const [upcoming, setUpcoming] = useState([]);

  useEffect(() => {
    // Fetch data from seminars-app via external API
    Promise.all([
      getSeminarsStats(),
      getUpcomingSeminars(3)
    ]).then(([statsData, upcomingData]) => {
      setStats(statsData);
      setUpcoming(upcomingData.seminars);
    });
  }, []);

  return (
    <div className="widget">
      <h3>📚 Seminars</h3>
      {stats && (
        <div className="stats">
          <span>Upcoming: {stats.total_upcoming}</span>
          <span>Pending tasks: {stats.pending_tasks}</span>
        </div>
      )}
      <ul>
        {upcoming.map(seminar => (
          <li key={seminar.id}>
            <a href={`https://inacio-seminars.fly.dev/?token=${userToken}`}>
              {seminar.title} - {seminar.date}
            </a>
            {!seminar.room_booked && <span className="badge">Room needed</span>}
          </li>
        ))}
      </ul>
    </div>
  );
}
```

---

## Migration Strategy

### Phase 1: Setup Repository (Day 1)

1. **Create new repository** `inaciog/seminars-app`
2. **Copy models** from InacioTool seminars module
3. **Setup basic FastAPI structure**
4. **Add JWT authentication**
5. **Create external API endpoints**

### Phase 2: Data Migration (Day 2)

1. **Export data** from InacioTool:
   ```bash
   sqlite3 inaciotool.db ".dump speaker seminar seminartemplate semesterplan seminarslot speakersuggestion speakeravailability speakerinfo planningdocument uploaded_files" > seminars_dump.sql
   ```

2. **Clean SQL dump** (remove access_codes references)

3. **Import to new database**:
   ```bash
   sqlite3 seminars.db < seminars_dump.sql
   ```

### Phase 3: Deploy (Day 3)

1. **Create Fly.io app**:
   ```bash
   fly apps create seminars-app
   fly volumes create seminars_data --size 3
   ```

2. **Set secrets**:
   ```bash
   fly secrets set JWT_SECRET="same-as-auth-service"
   fly secrets set API_SECRET="generate-random-secret"
   fly secrets set DROPBOX_TOKEN="optional"
   ```

3. **Deploy**:
   ```bash
   fly deploy
   ```

### Phase 4: Integration (Day 4)

1. **Update dashboard-app** to include seminars widget
2. **Add seminars-app URL** to dashboard config
3. **Test external API** connectivity

### Phase 5: Cutover (Day 5)

1. **Final data sync** from InacioTool
2. **Update DNS/custom domains** if needed
3. **Archive InacioTool seminars routes** (or add redirects)
4. **Monitor logs** for issues

---

## Implementation Timeline

| Day | Task | Deliverable |
|-----|------|-------------|
| 1 | Repository setup, models, auth | Working local API |
| 2 | External API, file uploads | Complete API with tests |
| 3 | Fly.io config, deployment | Live staging environment |
| 4 | Dashboard integration | Dashboard shows seminar data |
| 5 | Data migration, cutover | Production switch |

---

## Environment Variables Reference

### Required

| Variable | Description | Example |
|----------|-------------|---------|
| `JWT_SECRET` | Same secret as auth-service | `your-jwt-secret` |
| `API_SECRET` | For dashboard integration | `random-api-secret` |
| `DATABASE_URL` | SQLite database path | `sqlite:////data/seminars.db` |

### Optional

| Variable | Description | Default |
|----------|-------------|---------|
| `UPLOADS_DIR` | File upload directory | `/data/uploads` |
| `BACKUP_DIR` | Backup directory | `/data/backups` |
| `DROPBOX_TOKEN` | For backup sync | `None` |
| `PORT` | HTTP port | `8080` |
| `HOST` | Bind address | `0.0.0.0` |

---

## Testing Checklist

### Authentication
- [ ] JWT token validation works
- [ ] Token expiration handled
- [ ] Permission checking works
- [ ] Missing token returns 401
- [ ] Invalid token returns 401

### API Endpoints
- [ ] List seminars
- [ ] Create seminar
- [ ] Update seminar
- [ ] Delete seminar
- [ ] List speakers
- [ ] File upload/download

### External API
- [ ] Stats endpoint with apiSecret
- [ ] Upcoming seminars endpoint
- [ ] Pending tasks endpoint
- [ ] Invalid secret returns 403

### Backup
- [ ] Backup script runs successfully
- [ ] Old backups are cleaned (180 days)
- [ ] Dropbox sync works (if configured)

### Deployment
- [ ] Fly.io health checks pass
- [ ] Auto-stop/start works
- [ ] Volume mount works
- [ ] Environment variables set correctly

---

## Rollback Plan

If issues occur after cutover:

1. **Immediate**: Re-enable InacioTool seminars routes
2. **Data**: Re-import any new data created in seminars-app
3. **Debug**: Check Fly.io logs with `fly logs`
4. **Fix**: Deploy updates to seminars-app
5. **Retry**: Cutover again when ready

---

## Post-Migration Cleanup

After successful migration:

1. Remove seminars module from InacioTool
2. Archive old InacioTool database (keep for history)
3. Update documentation
4. Train users on new URL

---

*Document Version: 1.0*
*Created: 2026-02-18*
*Author: OpenClaw*
