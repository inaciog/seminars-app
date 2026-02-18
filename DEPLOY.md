# Deployment Instructions

## Prerequisites

1. Fly.io CLI installed and authenticated
2. Access to the auth service JWT_SECRET
3. API_SECRET for dashboard integration

## Setup

### 1. Authenticate with Fly.io

```bash
fly auth login
# OR use token:
fly auth token  # Copy this token
export FLY_API_TOKEN=<your-token>
```

### 2. Create the app

```bash
cd /path/to/seminars-app
fly apps create seminars-app
```

### 3. Create the volume for persistent storage

```bash
fly volumes create seminars_data --size 1 --region iad
```

### 4. Set secrets

```bash
fly secrets set JWT_SECRET="your-jwt-secret-from-auth-service"
fly secrets set API_SECRET="your-api-secret-for-dashboard"
fly secrets set MASTER_PASSWORD="i486983nacio:!"
```

### 5. Deploy

```bash
fly deploy
```

### 6. Configure rclone for backups (optional)

Set up Dropbox backup:
```bash
fly ssh console
# Then inside the container:
apk add rclone
rclone config  # Configure Dropbox
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `JWT_SECRET` | Must match auth-service JWT_SECRET | Yes |
| `API_SECRET` | For dashboard API access | Yes |
| `MASTER_PASSWORD` | For auth fallback | No |
| `DATABASE_URL` | SQLite path (default: /data/seminars.db) | No |
| `UPLOADS_DIR` | Upload storage path (default: /data/uploads) | No |

## URLs

- App: https://seminars-app.fly.dev
- Public page: https://seminars-app.fly.dev/public
- Health: https://seminars-app.fly.dev/api/health

## Dashboard Integration

Add to dashboard-app server.js:

```javascript
seminars: {
  name: 'Seminars',
  url: 'https://seminars-app.fly.dev',
  apiSecret: process.env.SEMINARS_API_SECRET,
  icon: '📚',
  color: '#FF9500'
}
```
