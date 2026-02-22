#!/usr/bin/env bash
# Run the seminars app locally: backend + frontend in one terminal.
# Uses a local synthetic database - never touches production data.
# Usage: ./dev.sh [--setup]
#   --setup  Run setup first (install deps, create .env, init DB)

set -e
cd "$(dirname "$0")"

# Local-only paths - never used in production (fly.toml uses /data/...)
export DATABASE_URL=./data/seminars.db
export UPLOADS_DIR=./data/uploads

if [[ "$1" == "--setup" ]]; then
  echo "Running setup..."
  make setup
  echo ""
  echo "Seeding synthetic database..."
  python seed_data.py
  echo ""
fi

# Ensure .env exists
if [[ ! -f .env ]]; then
  echo "No .env found. Run: ./dev.sh --setup"
  exit 1
fi

# Ensure data dir
mkdir -p data data/uploads

# Seed synthetic DB if it doesn't exist (first run without --setup)
if [[ ! -f data/seminars.db ]]; then
  echo "Initializing synthetic database..."
  python seed_data.py
  echo ""
fi

# Cleanup on exit
cleanup() {
  echo ""
  echo "Shutting down..."
  kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
  exit 0
}
trap cleanup SIGINT SIGTERM

echo "Starting backend on http://localhost:8000"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

echo "Starting frontend on http://localhost:3000"
(cd frontend && npm run dev) &
FRONTEND_PID=$!

echo ""
echo "✅ App running. Open http://localhost:3000"
echo "   Press Ctrl+C to stop both"
echo ""

wait
