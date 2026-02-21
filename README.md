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

See `.env.example` for a template. Key variables:

| Variable | Required | Description |
|----------|----------|-------------|
| JWT_SECRET | Yes | JWT secret from auth service |
| API_SECRET | Yes | Secret for dashboard external API |
| DATABASE_URL | Yes | Path (e.g. `/data/seminars.db`) or full URL (`sqlite:////data/seminars.db`) |
| UPLOADS_DIR | No | Default `/data/uploads` |
| MASTER_PASSWORD | No | For speaker token access (set via env in production) |

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

### Backend

```bash
# Install dependencies
pip install -r requirements.txt

# Copy env template and configure
cp .env.example .env

# Run locally
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend dev server runs on port 3000 and proxies `/api` to the backend (port 8000).

### Tests

```bash
# Backend tests (uses test_seminars.db, created automatically)
pytest
```
