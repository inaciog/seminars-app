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

## Local Development

Test the app locally before deploying.

### Quick start

**Single script** (easiest):

```bash
./dev.sh --setup   # first time: install deps, create .env, synthetic DB
./dev.sh           # start backend + frontend
```

Uses a local synthetic database (`./data/seminars.db`) — never touches production.

**Or with Makefile**:

```bash
make setup
# Edit .env with your JWT_SECRET and API_SECRET
make seed          # optional: test data
make dev-backend   # terminal 1 → http://localhost:8000
make dev-frontend  # terminal 2 → http://localhost:3000
```

Then open **http://localhost:3000**. The frontend proxies `/api` to the backend.

### Auth for local testing

Local runs use the same auth flow as production. Set `APP_URL=http://localhost:3000` and ensure your auth service allows `http://localhost:3000` as a valid redirect.

### Manual setup

```bash
# Backend
pip install -r requirements.txt
cp .env.example .env   # edit with JWT_SECRET, API_SECRET
uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend && npm install && npm run dev
```

### Run both in one terminal

```bash
./dev.sh       # or: make dev-all
```

### Tests

```bash
make test
# or: pytest
```
