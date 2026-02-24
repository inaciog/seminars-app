# AGENTS.md - Seminars App

This file contains essential information for AI agents working on the seminars-app codebase.

## Project Overview

Seminar management system with unified authentication. Manages speakers, rooms, seminar scheduling, and file uploads.

- **App URL**: https://seminars-app.fly.dev
- **Auth Service**: https://inacio-auth.fly.dev
- **Public Page**: https://seminars-app.fly.dev/public

## Architecture

### Backend (Python/FastAPI)

| File | Purpose |
|------|---------|
| `app/main.py` | Main FastAPI app, all routes, models, business logic |
| `app/availability_page.py` | External speaker availability form HTML |
| `app/speaker_info_v6.py` | Speaker info collection form HTML |
| `app/deletion_handlers.py` | Robust deletion logic with cascade |
| `app/templates.py` | HTML templates for external pages |
| `app/logging_config.py` | Audit and request logging |

### Frontend (React/TypeScript/Vite)

| Path | Purpose |
|------|---------|
| `frontend/src/App.tsx` | Main app component with routing |
| `frontend/src/api/client.ts` | API client configuration |
| `frontend/src/modules/seminars/` | Feature modules |
| `frontend/src/components/` | Shared UI components |
| `frontend/src/types/index.ts` | TypeScript type definitions |

### Database Models (SQLModel/SQLite)

Core entities defined in `app/main.py`:
- `Speaker` - Canonical speaker info
- `Room` - Room/venue information
- `Seminar` - Scheduled seminar event
- `SemesterPlan` - Semester planning container
- `SeminarSlot` - Time/place slots for planning
- `SpeakerSuggestion` - Proposed speakers for planning
- `SpeakerToken` - Tokens for external speaker forms
- `SeminarDetails` - Extended speaker/travel info
- `SpeakerWorkflow` - Workflow state tracking
- `ActivityEvent` - Audit log
- `UploadedFile` - File uploads
- `AvailabilitySlot` - Speaker availability (legacy)

## Development Setup

### Quick Start (Recommended)

```bash
# First time setup
./dev.sh --setup    # Installs deps, creates .env, seeds synthetic DB

# Start both backend + frontend
./dev.sh            # Backend: http://localhost:8000, Frontend: http://localhost:3000
```

### Using Make

```bash
make setup          # Install dependencies, create .env
make dev-backend    # Terminal 1: Backend on port 8000
make dev-frontend   # Terminal 2: Frontend on port 3000
make test           # Run pytest
make seed           # Add synthetic test data
```

### Environment Variables

Copy `.env.example` to `.env` and fill in:

| Variable | Required | Description |
|----------|----------|-------------|
| `JWT_SECRET` | Yes | From auth service |
| `API_SECRET` | Yes | For dashboard external API |
| `DATABASE_URL` | No | Default: `./data/seminars.db` |
| `UPLOADS_DIR` | No | Default: `./data/uploads` |
| `APP_URL` | No | Default: `http://localhost:3000` |
| `MASTER_PASSWORD` | No | For speaker token access fallback |

## Authentication Flow

1. User accesses app → Check for `token` cookie/query param
2. No valid token → Redirect to `AUTH_SERVICE_URL/login?returnTo=...`
3. Auth service authenticates → Redirects back with `?token=xxx`
4. App verifies JWT with `JWT_SECRET` → Sets cookie → User is authenticated

### Public Routes (No Auth)
- `/public` - Public seminar listing
- `/speaker/*` - Speaker token pages (availability, info, status)
- `/faculty/*` - Faculty suggestion forms
- `/api/health` - Health check
- `/api/external/*` - Dashboard API (uses `API_SECRET`)

## API Patterns

### Standard CRUD Endpoints
```
GET    /api/speakers
POST   /api/speakers
GET    /api/speakers/{id}
PUT    /api/speakers/{id}
DELETE /api/speakers/{id}
```

### Auth Headers
```
Authorization: Bearer <token>
# OR
?token=<token> query param
```

### File Uploads
```
POST /api/seminars/{id}/upload
Content-Type: multipart/form-data

Fields:
- file: <binary>
- category: "cv" | "photo" | "paper" | "abstract" | "other"
- description: optional
```

## Key Design Patterns

### Deletion Strategy
Always use robust deletion handlers from `app/deletion_handlers.py`:
- `delete_speaker_robust()` - Checks for related seminars
- `delete_seminar_robust()` - Cleans up files, details, workflows
- `delete_room_robust()` - Reassigns or blocks if seminars exist
- `delete_slot_robust()` - Unlinks seminars
- `delete_suggestion_robust()` - Cleans up tokens, availability
- `delete_semester_plan_robust()` - Cascades to slots, suggestions

### Token System
Speaker tokens for external forms:
```python
# Create token
token = str(uuid.uuid4())
speaker_token = SpeakerToken(
    token=token,
    suggestion_id=suggestion_id,
    token_type="availability",  # or "info", "status"
    expires_at=datetime.utcnow() + timedelta(days=30)
)

# Verify token (public access)
GET /speaker/availability?token=xxx
```

### Fallback Mirror
The app generates `fallback-mirror/recovery.html` and `changelog.html` periodically:
- Human-readable backup of all seminars, speakers, files
- Used for emergency recovery if database is corrupted
- Committed to git as fallback

## Frontend Patterns

### State Management
- **Zustand** for global state
- **React Query (TanStack Query)** for server state
- **React Hook Form** + **Zod** for forms

### API Client (`frontend/src/api/client.ts`)
```typescript
import { api } from '@/api/client';

// Auto-adds auth token from URL or cookie
const { data } = await api.get('/speakers');
```

### Proxy Configuration
Vite dev server proxies to backend:
- `/api/*` → `http://localhost:8000`
- `/speaker/*` → `http://localhost:8000`
- `/img/*` → `http://localhost:8000`

## Testing

```bash
# Run all tests
pytest

# Run specific file
pytest tests/test_auth.py -v
```

Test files:
- `tests/test_auth.py` - Authentication flow
- `tests/test_seminars.py` - Seminar CRUD operations
- `tests/test_external_api.py` - Dashboard external API

## Deployment (Fly.io)

```bash
fly deploy
```

Configuration in `fly.toml`:
- Auto-stop machines (scales to zero)
- Persistent volume mounted at `/data`
- Health checks on `/api/health`

### Production Secrets
```bash
fly secrets set JWT_SECRET="xxx"
fly secrets set API_SECRET="xxx"
fly secrets set MASTER_PASSWORD="xxx"
```

## Backup

```bash
./backup.sh  # Daily cron job, syncs to Dropbox
```

Keeps 180 days of local backups, syncs to cloud storage.

## Common Tasks

### Add a new API endpoint
1. Add Pydantic model for request/response
2. Add route in `app/main.py`
3. Add corresponding frontend type in `frontend/src/types/index.ts`
4. Add API call in appropriate module

### Add a database field
1. Update SQLModel class in `app/main.py`
2. Database auto-migrates on restart (SQLite)
3. Update Pydantic models
4. Update frontend types

### Add a new external page
1. Create HTML generator function (see `app/availability_page.py`)
2. Add route in `app/main.py` under public routes
3. Add proxy rule in `frontend/vite.config.ts` if needed

## Important Notes

1. **Never modify production database directly** - Use API or scripts
2. **Always handle file uploads securely** - Check extensions, validate content
3. **Audit logging** - Use `log_audit()` and `record_activity()` for important actions
4. **Token expiration** - Speaker tokens expire; handle gracefully
5. **Cascade deletes** - Use deletion handlers, never raw SQLModel deletes
6. **Frontend proxy** - Dev server proxies `/api` to backend; production serves static files

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Auth redirect loop | Check `JWT_SECRET` matches auth service |
| Database locked | SQLite only supports one writer; close other connections |
| File uploads fail | Check `UPLOADS_DIR` exists and is writable |
| Frontend 404s | Run `npm run build` in frontend/ or check vite proxy |
| CORS errors | Frontend should proxy `/api`, not call directly |
