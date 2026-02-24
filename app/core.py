"""
Core utilities shared across the application.

This module contains shared resources to avoid circular imports.
"""

import logging
import json
from datetime import datetime
from typing import Optional
from pathlib import Path

from sqlmodel import create_engine, Session
from pydantic_settings import BaseSettings

# Initialize logging first
from app.logging_config import init_logging
init_logging()
logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    jwt_secret: str = "your-secret-key-change-in-production"
    api_secret: str = "your-api-secret-for-dashboard"
    master_password: str = ""  # Set via MASTER_PASSWORD env var for speaker token access
    database_url: str = "/data/seminars.db"
    uploads_dir: str = "/data/uploads"
    auth_service_url: str = "https://inacio-auth.fly.dev"
    app_url: str = "https://seminars-app.fly.dev"
    feature_semester_plan_v2: bool = False
    fallback_mirror_dir: str = "fallback-mirror"

    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore PORT, HOST, etc. from .env (used by Fly.io, not by app)


settings = Settings()

# Database engine singleton
_engine = None


def get_engine():
    """Get or create the database engine."""
    global _engine
    if _engine is None:
        db_url = settings.database_url
        if db_url.startswith("sqlite://"):
            url = db_url
        else:
            url = f"sqlite:///{db_url}"
        _engine = create_engine(url, connect_args={"check_same_thread": False})
    return _engine


def get_db():
    """Get a database session."""
    with Session(get_engine()) as session:
        yield session


def record_activity(
    db: Session,
    event_type: str,
    summary: str,
    semester_plan_id: Optional[int] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    actor: Optional[str] = None,
    details: Optional[dict] = None,
):
    """Record an activity event."""
    from app.models import ActivityEvent  # Import here to avoid circular imports
    
    evt = ActivityEvent(
        semester_plan_id=semester_plan_id,
        event_type=event_type,
        summary=summary,
        entity_type=entity_type,
        entity_id=entity_id,
        actor=actor,
        details_json=json.dumps(details or {}, ensure_ascii=True),
    )
    db.add(evt)


# ============================================================================
# Authentication (defined here to avoid circular imports)
# ============================================================================

from typing import Optional
from fastapi import Depends, HTTPException, Query, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

security = HTTPBearer(auto_error=False)


def verify_token(token: str) -> Optional[dict]:
    """Verify JWT token from auth service."""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        logger.debug(f"Token verified for user: {payload.get('id', 'unknown')}")
        return payload
    except JWTError as e:
        logger.warning(f"Token verification failed: {str(e)}")
        return None


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    token: Optional[str] = Query(None),
    access_code: Optional[str] = Query(None)
) -> dict:
    """Get current user from token (header, query param, or cookie)."""
    auth_token = credentials.credentials if credentials else None
    if not auth_token:
        auth_token = token
    if not auth_token:
        auth_token = access_code  # Support access_code query param for file downloads
    if not auth_token:
        auth_token = request.cookies.get("token")
    
    if not auth_token:
        logger.warning(f"Authentication failed: No token provided - {request.method} {request.url.path}")
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user = verify_token(auth_token)
    if not user:
        logger.warning(f"Authentication failed: Invalid token - {request.method} {request.url.path}")
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return user
