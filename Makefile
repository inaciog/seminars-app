# Seminars App - Local Development
# Run `make dev` to start both backend and frontend (requires two terminals, or use `make dev-all`)

.PHONY: setup dev dev-backend dev-frontend dev-all seed test clean

# Default: show help
help:
	@echo "Seminars App - Local Development"
	@echo ""
	@echo "  make setup       - Install deps, create .env, init DB, seed data"
	@echo "  make dev         - Start backend + frontend (run in two terminals)"
	@echo "  make dev-backend - Start backend only (port 8000)"
	@echo "  make dev-frontend- Start frontend only (port 3000, proxies /api to backend)"
	@echo "  make dev-all     - Start both in one terminal (requires 'concurrently')"
	@echo "  make seed        - Seed database with test data"
	@echo "  make test        - Run backend tests"
	@echo ""
	@echo "Quick start: make setup && make dev-backend (terminal 1) && make dev-frontend (terminal 2)"
	@echo "Then open http://localhost:3000"

setup: .env data-dir
	@echo "Installing Python dependencies..."
	pip install -r requirements.txt
	@echo "Installing frontend dependencies..."
	cd frontend && npm install
	@echo "Initializing database..."
	python -c "from app.main import get_engine; from sqlmodel import SQLModel; SQLModel.metadata.create_all(get_engine()); print('  ✓ Tables created')"
	@echo ""
	@echo "✅ Setup complete. Run 'make seed' to add test data, then 'make dev-backend' and 'make dev-frontend'."

.env:
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "Created .env from .env.example - edit it with your JWT_SECRET and API_SECRET"; \
	else \
		echo ".env already exists"; \
	fi

data-dir:
	@mkdir -p data data/uploads
	@echo "  ✓ Created data/ and data/uploads/"

dev-backend:
	@echo "Starting backend on http://localhost:8000"
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	@echo "Starting frontend on http://localhost:3000 (proxies /api to backend)"
	cd frontend && npm run dev

dev: help
	@echo ""
	@echo "Run in two terminals:"
	@echo "  Terminal 1: make dev-backend"
	@echo "  Terminal 2: make dev-frontend"
	@echo ""
	@echo "Or: make dev-all (if you have 'npx concurrently' available)"

dev-all:
	@command -v npx >/dev/null 2>&1 || { echo "Need npx (comes with npm)"; exit 1; }
	npx concurrently -n "backend,frontend" -c "blue,green" "make dev-backend" "make dev-frontend"

seed:
	@echo "Seeding database with test data..."
	python seed_data.py

test:
	pytest -v

clean:
	rm -rf frontend/node_modules frontend/dist
	rm -f data/seminars.db
	@echo "Cleaned. Run 'make setup' to reinstall."
