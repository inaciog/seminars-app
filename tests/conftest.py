"""
Pytest fixtures for seminars-app tests.
"""

import os
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from jose import jwt
from sqlmodel import Session

# Use file-based SQLite for tests (in-memory gives each connection its own DB)
os.environ["DATABASE_URL"] = "./test_seminars.db"
# Use local dirs for tests (avoids /data which may not exist or be writable)
os.environ.setdefault("UPLOADS_DIR", "./test_uploads")

from app.main import app, get_engine, settings, Speaker, Seminar, Room, SQLModel


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Headers with valid JWT for authenticated requests."""
    payload = {
        "sub": "test-user",
        "id": "test-user",
        "role": "admin",
        "exp": datetime.utcnow() + timedelta(days=1),
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def db_session():
    """Database session for direct data setup in tests."""
    engine = get_engine()
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
