# Seminars App - System Documentation

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Data Models](#data-models)
4. [API Reference](#api-reference)
5. [Authentication](#authentication)
6. [Frontend Components](#frontend-components)
7. [Deployment](#deployment)
8. [Configuration](#configuration)

---

## Overview

The Seminars App is a comprehensive seminar management system designed for academic institutions. It handles speaker management, seminar scheduling, semester planning, and reimbursement tracking.

### Key Features

- **Speaker Management**: Store speaker information, CVs, photos, and contact details
- **Seminar Scheduling**: Schedule seminars with rooms, times, and bureaucracy tracking
- **Semester Planning**: Plan entire semesters with slots and speaker assignments
- **File Uploads**: Store CVs, photos, passports, and flight documents
- **Unified Auth**: Integrates with the central auth service
- **Dashboard Integration**: Provides stats to the main dashboard

---

## Architecture

### Tech Stack

- **Backend**: Python 3.11, FastAPI, SQLModel, SQLite
- **Frontend**: React 18, TypeScript, Tailwind CSS, React Query
- **Auth**: JWT tokens from inacio-auth.fly.dev
- **Deployment**: Fly.io with persistent volumes

### Directory Structure

```
seminars-app/
├── app/
│   └── main.py              # FastAPI application
├── frontend/
│   ├── src/
│   │   ├── api/             # API client
│   │   ├── modules/         # Feature modules
│   │   └── types/           # TypeScript types
│   └── dist/                # Built frontend
├── docs/                    # Documentation
├── backup.sh                # Backup script
├── fly.toml                 # Fly.io configuration
└── Dockerfile
```

### Data Flow

1. User authenticates via auth service
2. Auth service redirects with JWT token
3. Frontend stores token and makes API requests
4. Backend validates JWT and serves data
5. Data persisted to SQLite on volume

---

## Data Models

### Core Entities

#### Speaker
- `id`: Primary key
- `name`: Speaker name (required)
- `affiliation`: Institution/company
- `email`: Contact email
- `website`: Personal/professional website
- `bio`: Biography
- `notes`: Internal notes
- `cv_path`: Path to uploaded CV
- `photo_path`: Path to uploaded photo

#### Seminar
- `id`: Primary key
- `title`: Seminar title (required)
- `date`: Date of seminar
- `start_time`: Start time (HH:MM)
- `end_time`: End time (optional)
- `speaker_id`: Foreign key to Speaker
- `room_id`: Foreign key to Room
- `abstract`: Seminar abstract
- `status`: planned, confirmed, cancelled, completed
- Bureaucracy flags: `room_booked`, `announcement_sent`, `calendar_invite_sent`, etc.

#### Room
- `id`: Primary key
- `name`: Room name (required)
- `capacity`: Seating capacity
- `location`: Building/location
- `equipment`: JSON string of equipment list

#### SemesterPlan
- `id`: Primary key
- `name`: Plan name (e.g., "Spring 2025")
- `academic_year`: e.g., "2024-2025"
- `semester`: Spring, Fall, etc.
- `default_room`: Default room for slots
- `default_start_time`: Default start time
- `default_duration_minutes`: Default slot duration
- `status`: draft, active, completed, archived

#### SeminarSlot
- `id`: Primary key
- `semester_plan_id`: Foreign key to SemesterPlan
- `date`: Slot date
- `start_time`: Start time
- `end_time`: End time
- `room`: Room name
- `status`: available, reserved, confirmed, cancelled
- `assigned_seminar_id`: Foreign key to Seminar (if assigned)

#### SpeakerSuggestion
- `id`: Primary key
- `suggested_by`: Who suggested the speaker
- `speaker_name`: Name of suggested speaker
- `speaker_email`: Email
- `speaker_affiliation`: Institution
- `suggested_topic`: Proposed talk topic
- `priority`: low, medium, high
- `status`: pending, contacted, confirmed, declined

#### SpeakerToken
- `id`: Primary key
- `token`: Unique secure token
- `suggestion_id`: Foreign key to SpeakerSuggestion
- `token_type`: availability or info
- `expires_at`: Token expiration date
- `used_at`: When token was used (optional)

#### SeminarDetails
- `id`: Primary key
- `seminar_id`: Foreign key to Seminar
- Travel info: check-in/out dates, passport, departure city
- Accommodation: nights needed, hotel cost
- Payment: bank details, SWIFT code, beneficiary info

---

## API Reference

### Authentication

All API endpoints (except health check) require authentication via:
- Header: `Authorization: Bearer <token>`
- Or query param: `?token=<token>`

### Core Endpoints

#### Speakers
- `GET /api/speakers` - List all speakers
- `POST /api/speakers` - Create speaker
- `GET /api/speakers/{id}` - Get speaker details
- `PUT /api/speakers/{id}` - Update speaker
- `DELETE /api/speakers/{id}` - Delete speaker

#### Seminars
- `GET /api/seminars` - List seminars
- `POST /api/seminars` - Create seminar
- `GET /api/seminars/{id}` - Get seminar
- `PUT /api/seminars/{id}` - Update seminar
- `DELETE /api/seminars/{id}` - Delete seminar

#### Rooms
- `GET /api/rooms` - List rooms
- `POST /api/rooms` - Create room
- `DELETE /api/rooms/{id}` - Delete room

#### Semester Planning
- `GET /api/v1/seminars/semester-plans` - List plans
- `POST /api/v1/seminars/semester-plans` - Create plan
- `GET /api/v1/seminars/semester-plans/{id}` - Get plan
- `PUT /api/v1/seminars/semester-plans/{id}` - Update plan
- `DELETE /api/v1/seminars/semester-plans/{id}` - Delete plan

#### Slots
- `GET /api/v1/seminars/semester-plans/{id}/slots` - List slots
- `POST /api/v1/seminars/semester-plans/{id}/slots` - Create slot
- `PUT /api/v1/seminars/slots/{id}` - Update slot
- `DELETE /api/v1/seminars/slots/{id}` - Delete slot

#### Speaker Suggestions
- `GET /api/v1/seminars/speaker-suggestions` - List suggestions
- `POST /api/v1/seminars/speaker-suggestions` - Create suggestion
- `PUT /api/v1/seminars/speaker-suggestions/{id}` - Update suggestion
- `DELETE /api/v1/seminars/speaker-suggestions/{id}` - Delete suggestion

#### Speaker Tokens (Links)
- `POST /api/v1/seminars/speaker-tokens/availability` - Create availability link
- `POST /api/v1/seminars/speaker-tokens/info` - Create info link
- `GET /api/v1/seminars/speaker-tokens/verify` - Verify token

#### Files
- `POST /api/v1/seminars/seminars/{id}/upload` - Upload file
- `GET /api/v1/seminars/seminars/{id}/files` - List files
- `DELETE /api/v1/seminars/seminars/{id}/files/{file_id}` - Delete file

#### Seminar Details
- `GET /api/v1/seminars/seminars/{id}/details` - Get full details
- `PUT /api/v1/seminars/seminars/{id}/details` - Update details

#### External (Dashboard)
- `GET /api/external/stats?secret=xxx` - Get stats for dashboard
- `GET /api/external/upcoming?secret=xxx` - Get upcoming seminars

---

## Authentication

### JWT Token Flow

1. User visits app without token → Redirected to auth service
2. User logs in on auth service
3. Auth service generates JWT and redirects back with `?token=xxx`
4. Frontend extracts token, stores in localStorage
5. All API calls include token in Authorization header

### Token Payload
```json
{
  "id": "inacio",
  "name": "Inacio",
  "role": "owner",
  "iat": 1234567890,
  "exp": 1234567890
}
```

### Token Validation
- Tokens signed with `JWT_SECRET` (shared with auth service)
- Expiration: 30 days
- Algorithm: HS256

---

## Frontend Components

### Main Modules

#### SeminarsModule
Main seminars management interface with tabs:
- **Upcoming**: List of upcoming seminars
- **Speakers**: Speaker directory
- **Tasks**: Pending bureaucracy tasks
- **Planning**: Semester planning board

#### SemesterPlanning
Full semester planning interface:
- Create/manage semester plans
- Add time slots
- Manage speaker suggestions
- Assign speakers to slots
- Generate speaker links

#### SeminarDetailsModal
Detailed seminar editing:
- Basic info (title, abstract)
- Travel details
- Accommodation
- Payment/bank info
- File uploads (CV, photo, passport, flight)

### Key Features

- **React Query**: Data fetching with caching
- **Optimistic Updates**: UI updates immediately
- **File Uploads**: Drag-and-drop with progress
- **Responsive Design**: Works on desktop and mobile

---

## Deployment

### Fly.io Configuration

**fly.toml**:
- App name: `seminars-app`
- Region: `iad` (Washington DC)
- Persistent volume: `seminars_data` mounted at `/data`
- Auto-stop/start enabled for cost savings

### Environment Variables

Required secrets (set via `fly secrets set`):
- `JWT_SECRET`: Must match auth service
- `API_SECRET`: For dashboard integration

Environment variables:
- `DATABASE_URL`: `/data/seminars.db`
- `UPLOADS_DIR`: `/data/uploads`
- `BACKUP_DIR`: `/data/backups`

### Deployment Commands

```bash
# Deploy
fly deploy

# View logs
fly logs

# SSH into machine
fly ssh console

# Check volume
fly volumes list
```

---

## Configuration

### Local Development

1. Clone repository
2. Install Python dependencies: `pip install -r requirements.txt`
3. Install frontend dependencies: `cd frontend && npm install`
4. Run backend: `uvicorn app.main:app --reload`
5. Run frontend: `npm run dev`

### Production Checklist

- [ ] Set `JWT_SECRET` secret
- [ ] Set `API_SECRET` secret
- [ ] Verify volume is attached
- [ ] Test backup script
- [ ] Configure cron job for backups
- [ ] Test file uploads
- [ ] Verify auth flow

---

## Troubleshooting

### Common Issues

**"Not authenticated" errors**
- Check JWT_SECRET matches auth service
- Verify token hasn't expired
- Check browser localStorage for token

**File uploads fail**
- Check uploads directory permissions
- Verify volume has space
- Check file size limits

**Database errors**
- Check volume is mounted at /data
- Verify database file exists
- Check disk space

**Missing data after restart**
- Verify persistent volume is attached
- Check data is in /data (not /tmp)
- Review backup/restore procedures

---

## Support

For issues:
1. Check application logs: `fly logs --app seminars-app`
2. Review backup logs: `/data/backups/backup.log`
3. Check volume status: `fly volumes list --app seminars-app`
4. Refer to BACKUP_RECOVERY.md for data recovery
