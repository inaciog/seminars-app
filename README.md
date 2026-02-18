# seminars-app

Seminar management system integrated with unified authentication.

## Features

- Speaker management with availability tracking
- Room booking management
- Seminar scheduling with automated bureaucracy tasks
- File uploads (photos, CVs, papers)
- Public seminar page for external viewers
- Dashboard integration for unified overview

## Architecture

- **Backend**: Python/FastAPI
- **Database**: SQLite (with backups to Dropbox)
- **Auth**: JWT tokens from unified auth service
- **Deployment**: Fly.io with auto-stop machines

## Environment Variables

```env
# Required
JWT_SECRET=your-jwt-secret-from-auth-service
API_SECRET=your-api-secret-for-dashboard
DATABASE_URL=sqlite:////data/seminars.db

# Optional
UPLOADS_DIR=/data/uploads
BACKUP_DIR=/data/backups
DROPBOX_TOKEN=your-dropbox-token
PORT=8080
HOST=0.0.0.0
```

## API Endpoints

### Auth
All endpoints require `?token=xxx` from auth service or `Authorization: Bearer xxx` header.

### Seminars
- `GET /api/seminars` - List all seminars
- `POST /api/seminars` - Create new seminar
- `GET /api/seminars/{id}` - Get seminar details
- `PUT /api/seminars/{id}` - Update seminar
- `DELETE /api/seminars/{id}` - Delete seminar

### Speakers
- `GET /api/speakers` - List speakers
- `POST /api/speakers` - Add speaker
- `GET /api/speakers/{id}/availability` - Get availability

### External API (for Dashboard)
- `GET /api/external/stats?secret=xxx` - Get statistics
- `GET /api/external/upcoming?secret=xxx` - Get upcoming seminars
- `GET /api/external/pending-tasks?secret=xxx` - Get pending tasks

## Deployment

```bash
fly deploy
```

## Backup

Backups run daily via cron:
- Local backups kept for 180 days
- Synced to Dropbox

```bash
./backup.sh
```

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
uvicorn app.main:app --reload

# Run tests
pytest
```
