"""
Pytest fixtures for seminars-app tests.
"""

import os
import shutil
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from jose import jwt
from sqlmodel import Session

# Keep test database, logs, uploads, and fallback mirror out of tracked repo files.
TEST_RUNTIME_DIR = Path(tempfile.gettempdir()) / "seminars-app-tests"
TEST_DB_PATH = TEST_RUNTIME_DIR / "test_seminars.db"
TEST_UPLOADS_DIR = TEST_RUNTIME_DIR / "uploads"
TEST_LOG_DIR = TEST_RUNTIME_DIR / "logs"
TEST_FALLBACK_MIRROR_DIR = TEST_RUNTIME_DIR / "fallback-mirror"

if TEST_RUNTIME_DIR.exists():
    shutil.rmtree(TEST_RUNTIME_DIR)
TEST_RUNTIME_DIR.mkdir(parents=True, exist_ok=True)

os.environ["DATABASE_URL"] = str(TEST_DB_PATH)
os.environ["UPLOADS_DIR"] = str(TEST_UPLOADS_DIR)
os.environ["LOG_DIR"] = str(TEST_LOG_DIR)
os.environ["FALLBACK_MIRROR_DIR"] = str(TEST_FALLBACK_MIRROR_DIR)

from app.main import app, get_engine, settings, Speaker, Seminar, Room, SQLModel


@pytest.fixture
def client():
    """FastAPI test client."""
    engine = get_engine()
    SQLModel.metadata.create_all(engine)
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
