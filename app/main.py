"""
Seminars App - Unified Auth Integration

A standalone seminar management system that integrates with the unified
authentication service (inacio-auth.fly.dev).
"""

import os
import uuid
import shutil
import logging
import time
from datetime import datetime, date as date_type, timedelta
from pathlib import Path
from typing import Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, Request, UploadFile, File, Form, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt
from sqlmodel import SQLModel, Field, Session, create_engine, select, Relationship
from pydantic import BaseModel, ConfigDict, field_validator
from pydantic_settings import BaseSettings

# Import logging configuration
from app.logging_config import init_logging, log_audit, log_request

# Import templates
from app.templates import (
    get_invalid_token_html
)
from app.availability_page import get_availability_page_html

# Import speaker info page
from app.speaker_info_v6 import get_speaker_info_page_v6

# Import robust deletion handlers
from app.deletion_handlers import (
    delete_speaker_robust,
    delete_room_robust,
    delete_seminar_robust,
    delete_semester_plan_robust,
    delete_slot_robust,
    delete_suggestion_robust
)

# Initialize logging
init_logging()
logger = logging.getLogger(__name__)

# ============================================================================
# Configuration
# ============================================================================

class Settings(BaseSettings):
    jwt_secret: str = "your-secret-key-change-in-production"
    api_secret: str = "your-api-secret-for-dashboard"
    master_password: str = ""  # Set via MASTER_PASSWORD env var for speaker token access
    database_url: str = "/data/seminars.db"
    uploads_dir: str = "/data/uploads"
    auth_service_url: str = "https://inacio-auth.fly.dev"
    app_url: str = "https://seminars-app.fly.dev"
    
    class Config:
        env_file = ".env"

settings = Settings()

# ============================================================================
# Database Models
# ============================================================================

engine = None

def get_engine():
    global engine
    if engine is None:
        db_url = settings.database_url
        if db_url.startswith("sqlite://"):
            url = db_url
        else:
            url = f"sqlite:///{db_url}"
        engine = create_engine(url, connect_args={"check_same_thread": False})
    return engine

class Speaker(SQLModel, table=True):
    __tablename__ = "speakers"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    affiliation: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    bio: Optional[str] = None
    notes: Optional[str] = None
    cv_path: Optional[str] = None
    photo_path: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    seminars: List["Seminar"] = Relationship(back_populates="speaker")
    availability_slots: List["AvailabilitySlot"] = Relationship(back_populates="speaker")

class Room(SQLModel, table=True):
    __tablename__ = "rooms"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    capacity: Optional[int] = None
    location: Optional[str] = None
    equipment: Optional[str] = None
    
    seminars: List["Seminar"] = Relationship(back_populates="room")

class Seminar(SQLModel, table=True):
    __tablename__ = "seminars"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    date: date_type = Field(index=True)
    start_time: str
    end_time: Optional[str] = None
    
    speaker_id: int = Field(foreign_key="speakers.id")
    room_id: Optional[int] = Field(default=None, foreign_key="rooms.id")
    
    abstract: Optional[str] = None
    paper_title: Optional[str] = None
    status: str = Field(default="planned")
    
    room_booked: bool = Field(default=False)
    announcement_sent: bool = Field(default=False)
    calendar_invite_sent: bool = Field(default=False)
    website_updated: bool = Field(default=False)
    catering_ordered: bool = Field(default=False)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    speaker: Speaker = Relationship(back_populates="seminars")
    room: Optional[Room] = Relationship(back_populates="seminars")
    files: List["UploadedFile"] = Relationship(back_populates="seminar")

class AvailabilitySlot(SQLModel, table=True):
    __tablename__ = "availability_slots"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    speaker_id: int = Field(foreign_key="speakers.id")
    date: date_type
    start_time: str
    end_time: str
    is_available: bool = Field(default=True)
    notes: Optional[str] = None
    
    speaker: Speaker = Relationship(back_populates="availability_slots")

class UploadedFile(SQLModel, table=True):
    __tablename__ = "uploaded_files"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    seminar_id: int = Field(foreign_key="seminars.id")
    
    original_filename: str
    original_extension: Optional[str] = None
    content_type: str
    file_size: int
    storage_filename: str
    file_category: Optional[str] = None
    description: Optional[str] = None
    
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    
    seminar: Seminar = Relationship(back_populates="files")

# New models for semester planning
class SemesterPlan(SQLModel, table=True):
    __tablename__ = "semester_plans"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    academic_year: str
    semester: str
    default_room: str = "TBD"
    default_start_time: str = "14:00"
    default_duration_minutes: int = 60
    status: str = Field(default="draft")  # draft, active, completed, archived
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    slots: List["SeminarSlot"] = Relationship(back_populates="plan")

class SeminarSlot(SQLModel, table=True):
    __tablename__ = "seminar_slots"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    semester_plan_id: int = Field(foreign_key="semester_plans.id")
    date: date_type
    start_time: str
    end_time: str
    room: str
    status: str = Field(default="available")  # available, reserved, confirmed, cancelled
    assigned_seminar_id: Optional[int] = Field(default=None, foreign_key="seminars.id")
    assigned_suggestion_id: Optional[int] = Field(default=None, foreign_key="speaker_suggestions.id")
    
    plan: SemesterPlan = Relationship(back_populates="slots")
    assigned_seminar: Optional[Seminar] = Relationship()

class SpeakerSuggestion(SQLModel, table=True):
    __tablename__ = "speaker_suggestions"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    suggested_by: str
    suggested_by_email: Optional[str] = None
    speaker_id: Optional[int] = Field(default=None, foreign_key="speakers.id")
    speaker_name: str
    speaker_email: Optional[str] = None
    speaker_affiliation: Optional[str] = None
    suggested_topic: Optional[str] = None
    reason: Optional[str] = None
    priority: str = Field(default="medium")  # low, medium, high
    status: str = Field(default="pending")  # pending, contacted, confirmed, declined
    semester_plan_id: Optional[int] = Field(default=None, foreign_key="semester_plans.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    speaker: Optional[Speaker] = Relationship()
    availability: List["SpeakerAvailability"] = Relationship(back_populates="suggestion")

class SpeakerAvailability(SQLModel, table=True):
    __tablename__ = "speaker_availability"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    suggestion_id: int = Field(foreign_key="speaker_suggestions.id")
    date: date_type
    preference: str = Field(default="available")  # preferred, available, not_preferred
    
    suggestion: SpeakerSuggestion = Relationship(back_populates="availability")

class SpeakerToken(SQLModel, table=True):
    __tablename__ = "speaker_tokens"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    token: str = Field(index=True, unique=True)
    suggestion_id: int = Field(foreign_key="speaker_suggestions.id")
    token_type: str  # 'availability' or 'info'
    seminar_id: Optional[int] = Field(default=None, foreign_key="seminars.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime
    used_at: Optional[datetime] = None
    
    suggestion: SpeakerSuggestion = Relationship()
    seminar: Optional[Seminar] = Relationship()

class SeminarDetails(SQLModel, table=True):
    __tablename__ = "seminar_details"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    seminar_id: int = Field(foreign_key="seminars.id", unique=True)
    
    # Travel info
    check_in_date: Optional[date_type] = None
    check_out_date: Optional[date_type] = None
    passport_number: Optional[str] = None
    passport_country: Optional[str] = None
    departure_city: Optional[str] = None
    travel_method: Optional[str] = "flight"
    estimated_travel_cost: Optional[float] = None
    
    # Accommodation
    needs_accommodation: bool = Field(default=True)
    accommodation_nights: Optional[int] = None
    estimated_hotel_cost: Optional[float] = None
    
    # Payment info
    payment_email: Optional[str] = None
    beneficiary_name: Optional[str] = None
    bank_account_number: Optional[str] = None
    bank_name: Optional[str] = None
    bank_address: Optional[str] = None
    swift_code: Optional[str] = None
    currency: Optional[str] = "USD"
    beneficiary_address: Optional[str] = None
    
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    seminar: Seminar = Relationship()

# ============================================================================
# Pydantic Models
# ============================================================================

class SpeakerCreate(BaseModel):
    name: str
    affiliation: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    bio: Optional[str] = None
    notes: Optional[str] = None

class SpeakerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    affiliation: Optional[str]
    email: Optional[str]
    website: Optional[str]
    bio: Optional[str]
    notes: Optional[str]
    cv_path: Optional[str]
    photo_path: Optional[str]

class RoomCreate(BaseModel):
    name: str
    capacity: Optional[int] = None
    location: Optional[str] = None
    equipment: Optional[str] = None

class RoomResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    capacity: Optional[int]
    location: Optional[str]
    equipment: Optional[str]

class SeminarCreate(BaseModel):
    title: str
    date: date_type
    start_time: str
    end_time: Optional[str] = None
    speaker_id: int
    room_id: Optional[int] = None
    abstract: Optional[str] = None
    paper_title: Optional[str] = None

class SeminarUpdate(BaseModel):
    title: Optional[str] = None
    date: Optional[date_type] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    speaker_id: Optional[int] = None
    room_id: Optional[int] = None
    abstract: Optional[str] = None
    paper_title: Optional[str] = None
    status: Optional[str] = None
    room_booked: Optional[bool] = None
    announcement_sent: Optional[bool] = None
    calendar_invite_sent: Optional[bool] = None
    website_updated: Optional[bool] = None
    catering_ordered: Optional[bool] = None

class SeminarResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    title: str
    date: date_type
    start_time: str
    end_time: Optional[str]
    speaker_id: int
    room_id: Optional[int]
    abstract: Optional[str]
    paper_title: Optional[str]
    status: str
    room_booked: bool
    announcement_sent: bool
    calendar_invite_sent: bool
    website_updated: bool
    catering_ordered: bool
    speaker: Optional[SpeakerResponse] = None
    room: Optional[str]  # Just the room name, not full object
    
    @field_validator('room', mode='before')
    @classmethod
    def extract_room_name(cls, v):
        if v is None:
            return None
        if isinstance(v, Room):
            return v.name
        return str(v)

# Semester Planning Pydantic Models
class SemesterPlanCreate(BaseModel):
    name: str
    academic_year: str
    semester: str
    default_room: str = "TBD"
    default_start_time: str = "14:00"
    default_duration_minutes: int = 60
    notes: Optional[str] = None

class SemesterPlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    academic_year: str
    semester: str
    default_room: str
    default_start_time: str
    default_duration_minutes: int
    status: str
    notes: Optional[str]
    created_at: datetime

class SeminarSlotCreate(BaseModel):
    date: date_type
    start_time: str
    end_time: str
    room: str

class SeminarSlotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    semester_plan_id: int
    date: date_type
    start_time: str
    end_time: str
    room: str
    status: str
    assigned_seminar_id: Optional[int]

class SpeakerSuggestionCreate(BaseModel):
    suggested_by: str
    suggested_by_email: Optional[str] = None
    speaker_id: Optional[int] = None
    speaker_name: str
    speaker_email: Optional[str] = None
    speaker_affiliation: Optional[str] = None
    suggested_topic: Optional[str] = None
    reason: Optional[str] = None
    priority: str = "medium"
    semester_plan_id: Optional[int] = None

class SpeakerSuggestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    suggested_by: str
    suggested_by_email: Optional[str]
    speaker_id: Optional[int]
    speaker_name: str
    speaker_email: Optional[str]
    speaker_affiliation: Optional[str]
    suggested_topic: Optional[str]
    reason: Optional[str]
    priority: str
    status: str
    semester_plan_id: Optional[int]
    created_at: datetime
    availability: List[dict] = []

class SpeakerAvailabilityCreate(BaseModel):
    date: date_type
    preference: str = "available"

class AssignSpeakerRequest(BaseModel):
    suggestion_id: int
    slot_id: int

class AssignSeminarRequest(BaseModel):
    """Assign an existing seminar (e.g. orphan) to a slot."""
    seminar_id: int
    slot_id: int

class SpeakerTokenCreate(BaseModel):
    suggestion_id: int
    token_type: str  # 'availability' or 'info'
    seminar_id: Optional[int] = None

class SpeakerTokenResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    token: str
    suggestion_id: int
    token_type: str
    seminar_id: Optional[int]
    created_at: datetime
    expires_at: datetime
    link: str

class SpeakerTokenVerifyRequest(BaseModel):
    token: str

class SpeakerAvailabilitySubmit(BaseModel):
    availabilities: List[SpeakerAvailabilityCreate]

class SpeakerInfoSubmit(BaseModel):
    speaker_name: Optional[str] = None
    final_talk_title: Optional[str] = None
    passport_number: Optional[str] = None
    passport_country: Optional[str] = None
    departure_city: Optional[str] = None
    travel_method: Optional[str] = None
    estimated_travel_cost: Optional[str] = None  # From form; parsed to float in handler
    needs_accommodation: bool = True
    check_in_date: Optional[date_type] = None
    check_out_date: Optional[date_type] = None
    accommodation_nights: Optional[str] = None  # From form; parsed to int in handler
    estimated_hotel_cost: Optional[str] = None  # From form; parsed to float in handler
    payment_email: Optional[str] = None
    beneficiary_name: Optional[str] = None
    bank_name: Optional[str] = None
    swift_code: Optional[str] = None
    bank_account_number: Optional[str] = None
    bank_address: Optional[str] = None
    beneficiary_address: Optional[str] = None
    currency: Optional[str] = "USD"
    talk_title: Optional[str] = None
    abstract: Optional[str] = None
    needs_projector: bool = True
    needs_microphone: bool = False

class SeminarDetailsUpdate(BaseModel):
    title: Optional[str] = None
    abstract: Optional[str] = None
    check_in_date: Optional[str] = None
    check_out_date: Optional[str] = None
    passport_number: Optional[str] = None
    passport_country: Optional[str] = None
    payment_email: Optional[str] = None
    beneficiary_name: Optional[str] = None
    bank_account_number: Optional[str] = None
    bank_name: Optional[str] = None
    bank_address: Optional[str] = None
    swift_code: Optional[str] = None
    currency: Optional[str] = None
    beneficiary_address: Optional[str] = None
    departure_city: Optional[str] = None
    travel_method: Optional[str] = None
    estimated_travel_cost: Optional[str] = None
    needs_accommodation: Optional[bool] = None
    accommodation_nights: Optional[str] = None
    estimated_hotel_cost: Optional[str] = None
    
    def get_date_or_none(self, field_value: Optional[str]) -> Optional[date_type]:
        """Convert string date to date object or None if empty."""
        if not field_value or field_value.strip() == '':
            return None
        try:
            return date_type.fromisoformat(field_value)
        except ValueError:
            return None

class SeminarDetailsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    seminar_id: int
    check_in_date: Optional[date_type]
    check_out_date: Optional[date_type]
    passport_number: Optional[str]
    passport_country: Optional[str]
    payment_email: Optional[str]
    beneficiary_name: Optional[str]
    bank_account_number: Optional[str]
    bank_name: Optional[str]
    bank_address: Optional[str]
    swift_code: Optional[str]
    currency: Optional[str]
    beneficiary_address: Optional[str]
    departure_city: Optional[str]
    travel_method: Optional[str]
    estimated_travel_cost: Optional[float]
    needs_accommodation: bool
    accommodation_nights: Optional[int]
    estimated_hotel_cost: Optional[float]
    updated_at: datetime

# ============================================================================
# Auth
# ============================================================================

security = HTTPBearer(auto_error=False)

def get_db():
    with Session(get_engine()) as session:
        yield session

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

async def require_auth(request: Request, call_next):
    """Middleware to check auth on HTML routes."""
    path = request.url.path
    
    # Skip API routes, static files, and React assets
    if path.startswith("/api/") or path.startswith("/static/") or path.startswith("/assets/"):
        return await call_next(request)
    
    # Skip public pages
    if path == "/public":
        return await call_next(request)
    
    # Skip speaker token pages (public access)
    if path.startswith("/speaker/"):
        return await call_next(request)
    
    # Check for token
    token = request.query_params.get("token") or request.cookies.get("token")
    
    if not token or not verify_token(token):
        return_url = f"{settings.app_url}{request.url.path}"
        return RedirectResponse(
            f"{settings.auth_service_url}/login?returnTo={return_url}"
        )
    
    return await call_next(request)

# ============================================================================
# Data Migration
# ============================================================================

async def run_data_migration(engine):
    """Run safe data migration to add missing columns and relationships."""
    from sqlalchemy import text
    
    logger.info("Running data migration...")
    
    with engine.connect() as conn:
        # Add slot_id to seminars if not exists (without UNIQUE constraint first)
        try:
            conn.execute(text("ALTER TABLE seminars ADD COLUMN slot_id INTEGER"))
            conn.commit()
            logger.info("Added seminars.slot_id column")
        except Exception as e:
            if "duplicate column name" in str(e):
                logger.info("seminars.slot_id already exists")
            else:
                logger.error(f"Error adding slot_id: {e}")
        
        # Add suggestion_id to seminars if not exists
        try:
            conn.execute(text("ALTER TABLE seminars ADD COLUMN suggestion_id INTEGER"))
            conn.commit()
            logger.info("Added seminars.suggestion_id column")
        except Exception as e:
            if "duplicate column name" in str(e):
                logger.info("seminars.suggestion_id already exists")
            else:
                logger.error(f"Error adding suggestion_id: {e}")
        
        # Add assigned_suggestion_id to seminar_slots if not exists
        try:
            conn.execute(text("ALTER TABLE seminar_slots ADD COLUMN assigned_suggestion_id INTEGER"))
            conn.commit()
            logger.info("Added seminar_slots.assigned_suggestion_id column")
        except Exception as e:
            if "duplicate column name" in str(e):
                logger.info("seminar_slots.assigned_suggestion_id already exists")
            else:
                logger.error(f"Error adding assigned_suggestion_id: {e}")
        
        # Migrate data: update seminars with slot_id from seminar_slots
        try:
            result = conn.execute(text("""
                UPDATE seminars 
                SET slot_id = (
                    SELECT id FROM seminar_slots 
                    WHERE assigned_seminar_id = seminars.id
                )
                WHERE slot_id IS NULL AND id IN (
                    SELECT assigned_seminar_id FROM seminar_slots WHERE assigned_seminar_id IS NOT NULL
                )
            """))
            conn.commit()
            if result.rowcount > 0:
                logger.info(f"Migrated {result.rowcount} seminars with slot_id")
        except Exception as e:
            logger.error(f"Error migrating slot_id: {e}")
        
        # Migrate data: update seminars with suggestion_id
        try:
            result = conn.execute(text("""
                UPDATE seminars 
                SET suggestion_id = (
                    SELECT assigned_suggestion_id 
                    FROM seminar_slots 
                    WHERE assigned_seminar_id = seminars.id AND assigned_suggestion_id IS NOT NULL
                )
                WHERE suggestion_id IS NULL AND slot_id IS NOT NULL
            """))
            conn.commit()
            if result.rowcount > 0:
                logger.info(f"Migrated {result.rowcount} seminars with suggestion_id")
        except Exception as e:
            logger.error(f"Error migrating suggestion_id: {e}")
        
        # Try to match remaining seminars to suggestions by speaker_id
        try:
            result = conn.execute(text("""
                UPDATE seminars 
                SET suggestion_id = (
                    SELECT ss.id 
                    FROM speaker_suggestions ss
                    JOIN seminar_slots sl ON sl.semester_plan_id = ss.semester_plan_id
                    WHERE ss.speaker_id = seminars.speaker_id
                    AND sl.id = seminars.slot_id
                    AND ss.status = 'confirmed'
                    LIMIT 1
                )
                WHERE suggestion_id IS NULL AND speaker_id IS NOT NULL AND slot_id IS NOT NULL
            """))
            conn.commit()
            if result.rowcount > 0:
                logger.info(f"Matched {result.rowcount} additional seminars to suggestions")
        except Exception as e:
            logger.error(f"Error matching suggestions: {e}")
    
    logger.info("Data migration complete")

# ============================================================================
# App Initialization
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        Path(settings.uploads_dir).mkdir(parents=True, exist_ok=True)
        Path(settings.uploads_dir).parent.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass  # May fail in tests or read-only env; non-fatal for DB init

    eng = get_engine()
    SQLModel.metadata.create_all(eng)
    
    # Run data migration
    await run_data_migration(eng)
    
    yield

app = FastAPI(title="Seminars App", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Get client IP
    client_ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "unknown")
    
    # Process request
    response = await call_next(request)
    
    # Calculate duration
    duration_ms = (time.time() - start_time) * 1000
    
    # Get user from token if available
    user = None
    try:
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
            user = payload.get("id", "unknown")
    except (JWTError, ValueError):
        pass  # Invalid or expired token - log without user
    
    # Log the request
    log_request(
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        duration_ms=duration_ms,
        user=user,
        ip=client_ip
    )
    
    return response

FRONTEND_DIST_DIR = Path("frontend/dist")
FRONTEND_ASSETS_DIR = FRONTEND_DIST_DIR / "assets"

# check_dir=False avoids import-time crashes when frontend artifacts are not bundled yet.
app.mount("/assets", StaticFiles(directory=str(FRONTEND_ASSETS_DIR), check_dir=False), name="assets")
if not FRONTEND_ASSETS_DIR.exists():
    logger.warning(f"Frontend assets directory not found at startup: {FRONTEND_ASSETS_DIR}")


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    return await require_auth(request, call_next)

# ============================================================================
# HTML Routes
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def index():
    index_file = FRONTEND_DIST_DIR / "index.html"
    if not index_file.exists():
        logger.warning(f"Frontend index file not found: {index_file}")
        return HTMLResponse(
            content=(
                "<html><body style='font-family:sans-serif;padding:2rem'>"
                "<h2>Seminars frontend is not available yet</h2>"
                "<p>The backend is running, but frontend build artifacts are missing.</p>"
                "<p>Please run <code>npm --prefix frontend run build</code> and redeploy.</p>"
                "</body></html>"
            ),
            status_code=503,
        )

    with index_file.open("r") as f:
        return f.read()

@app.get("/public", response_class=HTMLResponse)
async def public_page(db: Session = Depends(get_db)):
    today = date_type.today()
    statement = select(Seminar).where(Seminar.date >= today).order_by(Seminar.date).limit(10)
    seminars = db.exec(statement).all()
    
    seminars_html = ""
    for s in seminars:
        speaker_name = s.speaker.name if s.speaker else "TBD"
        affiliation = s.speaker.affiliation or "" if s.speaker else ""
        room_name = s.room.name if s.room else "TBD"
        
        seminars_html += f"""
        <div class="seminar">
            <div class="date">{s.date.strftime("%b %d, %Y")} at {s.start_time}</div>
            <h3>{s.title}</h3>
            <p class="speaker">{speaker_name} {f"({affiliation})" if affiliation else ""}</p>
            <p class="room">📍 {room_name}</p>
            {f'<p class="abstract">{s.abstract}</p>' if s.abstract else ''}
        </div>
        """
    
    if not seminars_html:
        seminars_html = "<p>No upcoming seminars scheduled.</p>"
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Upcoming Seminars</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, sans-serif;
                background: #f5f5f7;
                color: #1d1d1f;
                line-height: 1.6;
                padding: 40px 20px;
            }}
            .container {{ max-width: 800px; margin: 0 auto; }}
            h1 {{ margin-bottom: 30px; text-align: center; }}
            .seminar {{
                background: #fff;
                border-radius: 12px;
                padding: 24px;
                margin-bottom: 20px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }}
            .date {{
                color: #0a84ff;
                font-weight: 600;
                font-size: 14px;
                text-transform: uppercase;
                margin-bottom: 8px;
            }}
            h3 {{ margin-bottom: 8px; }}
            .speaker {{ color: #666; margin-bottom: 4px; }}
            .room {{ color: #999; font-size: 14px; margin-bottom: 12px; }}
            .abstract {{ color: #444; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📚 Upcoming Seminars</h1>
            {seminars_html}
        </div>
    </body>
    </html>
    """

# Speaker token pages (public, no auth required)
@app.get("/speaker/availability/{token}", response_class=HTMLResponse)
async def speaker_availability_page(token: str, db: Session = Depends(get_db)):
    """Public page for speaker to submit availability."""
    # Verify token
    statement = select(SpeakerToken).where(
        SpeakerToken.token == token,
        SpeakerToken.expires_at > datetime.utcnow(),
        SpeakerToken.used_at.is_(None),
        SpeakerToken.token_type == "availability"
    )
    db_token = db.exec(statement).first()
    
    if not db_token:
        return HTMLResponse(content=get_invalid_token_html(), status_code=404)
    
    suggestion = db_token.suggestion
    plan = db.get(SemesterPlan, suggestion.semester_plan_id) if suggestion.semester_plan_id else None
    
    # Get semester date range
    semester_start = None
    semester_end = None
    if plan:
        # Get all slots for this plan to determine date range
        slots = db.exec(select(SeminarSlot).where(SeminarSlot.semester_plan_id == plan.id)).all()
        if slots:
            dates = [slot.date for slot in slots]
            semester_start = min(dates).isoformat()
            semester_end = max(dates).isoformat()
    
    return HTMLResponse(content=get_availability_page_html(
        speaker_name=suggestion.speaker_name,
        speaker_email=suggestion.speaker_email,
        speaker_affiliation=suggestion.speaker_affiliation,
        suggested_topic=suggestion.suggested_topic,
        semester_plan=plan.name if plan else None,
        token=token,
        semester_start=semester_start,
        semester_end=semester_end
    ))

@app.get("/speaker/info/{token}", response_class=HTMLResponse)
async def speaker_info_page(token: str, db: Session = Depends(get_db)):
    """Public page for speaker to submit detailed info."""
    # Verify token - allow viewing even if used, but not expired
    statement = select(SpeakerToken).where(
        SpeakerToken.token == token,
        SpeakerToken.expires_at > datetime.utcnow(),
        SpeakerToken.token_type == "info"
    )
    db_token = db.exec(statement).first()
    
    if not db_token:
        return HTMLResponse(content=get_invalid_token_html(), status_code=404)
    
    suggestion = db_token.suggestion
    seminar = db_token.seminar
    
    return HTMLResponse(content=get_speaker_info_page_v6(
        speaker_name=suggestion.speaker_name,
        speaker_email=suggestion.speaker_email,
        speaker_affiliation=suggestion.speaker_affiliation,
        seminar_title=seminar.title if seminar else None,
        seminar_date=seminar.date.strftime('%B %d, %Y') if seminar else None,
        token=token,
        seminar_id=seminar.id if seminar else None
    ))

@app.get("/test-js", response_class=HTMLResponse)
async def test_js_page():
    """Simple test page for JavaScript debugging."""
    return HTMLResponse(content="""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>JS Test</title>
</head>
<body>
    <h1>JavaScript Test Page</h1>
    <div id="status" style="background:#ff0;padding:10px;">Loading...</div>
    <div id="log" style="margin-top:20px;font-family:monospace;"></div>
    
    <script>
        function log(msg) {
            document.getElementById('log').innerHTML += '<div>' + msg + '</div>';
            document.getElementById('status').textContent = msg;
        }
        
        log('Script 1 running');
        
        const testObj = {};
        log('Object created');
        
        function testFunc() {
            log('Function called');
        }
        
        testFunc();
        log('Script 1 complete');
    </script>
    
    <p>Between scripts</p>
    
    <script>
        log('Script 2 running');
        document.getElementById('status').style.background = '#4caf50';
        document.getElementById('status').style.color = '#fff';
        log('All scripts complete - SUCCESS');
    </script>
</body>
</html>""")


@app.get("/test-speaker-info", response_class=HTMLResponse)
async def test_speaker_info_page():
    """Minimal test of speaker info page structure."""
    return HTMLResponse(content="""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Speaker Info Test</title>
</head>
<body>
    <h1>Speaker Info Test</h1>
    <div id="status" style="background:#ff0;padding:10px;">Loading...</div>
    <div id="log" style="margin-top:20px;font-family:monospace;"></div>
    
    <form id="infoForm">
        <input type="text" id="speakerName" value="Test Speaker">
        <button type="submit">Submit</button>
    </form>
    
    <script>
        function log(msg) {
            document.getElementById('log').innerHTML += '<div>' + msg + '</div>';
            document.getElementById('status').textContent = msg;
        }
        
        log('First script running');
        
        const uploadedFiles = {};
        log('uploadedFiles created');
        
        function setupFileUpload() {
            log('setupFileUpload called');
        }
        
        setupFileUpload();
        log('First script done');
    </script>
    
    <script>
        log('Second script running');
        
        document.getElementById('infoForm').addEventListener('submit', function(e) {
            e.preventDefault();
            log('Form submitted!');
            alert('Form submitted!');
        });
        
        log('Second script done - SUCCESS');
        document.getElementById('status').style.background = '#4caf50';
        document.getElementById('status').style.color = '#fff';
    </script>
</body>
</html>""")

# ============================================================================
# API Routes - Speakers
# ============================================================================

@app.get("/api/speakers", response_model=List[SpeakerResponse])
async def list_speakers(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    statement = select(Speaker).order_by(Speaker.name)
    return db.exec(statement).all()

@app.post("/api/speakers", response_model=SpeakerResponse)
async def create_speaker(speaker: SpeakerCreate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    db_speaker = Speaker(**speaker.model_dump())
    db.add(db_speaker)
    db.commit()
    db.refresh(db_speaker)
    return db_speaker

@app.get("/api/speakers/{speaker_id}", response_model=SpeakerResponse)
async def get_speaker(speaker_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    speaker = db.get(Speaker, speaker_id)
    if not speaker:
        raise HTTPException(status_code=404, detail="Speaker not found")
    return speaker

@app.put("/api/speakers/{speaker_id}", response_model=SpeakerResponse)
async def update_speaker(speaker_id: int, update: SpeakerCreate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    speaker = db.get(Speaker, speaker_id)
    if not speaker:
        raise HTTPException(status_code=404, detail="Speaker not found")
    
    for key, value in update.model_dump().items():
        setattr(speaker, key, value)
    
    db.commit()
    db.refresh(speaker)
    return speaker

@app.delete("/api/speakers/{speaker_id}")
async def delete_speaker(speaker_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    result = delete_speaker_robust(speaker_id, db)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

# Additional endpoints for frontend compatibility (/api/v1/seminars/*)
@app.get("/api/v1/seminars/speakers", response_model=List[SpeakerResponse])
async def list_speakers_v1(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    statement = select(Speaker).order_by(Speaker.name)
    return db.exec(statement).all()

@app.post("/api/v1/seminars/speakers", response_model=SpeakerResponse)
async def create_speaker_v1(speaker: SpeakerCreate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    db_speaker = Speaker(**speaker.model_dump())
    db.add(db_speaker)
    db.commit()
    db.refresh(db_speaker)
    return db_speaker

@app.put("/api/v1/seminars/speakers/{speaker_id}", response_model=SpeakerResponse)
async def update_speaker_v1(speaker_id: int, update: SpeakerCreate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    speaker = db.get(Speaker, speaker_id)
    if not speaker:
        raise HTTPException(status_code=404, detail="Speaker not found")
    
    for key, value in update.model_dump().items():
        setattr(speaker, key, value)
    
    db.commit()
    db.refresh(speaker)
    return speaker

@app.delete("/api/v1/seminars/speakers/{speaker_id}")
async def delete_speaker_v1(speaker_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    result = delete_speaker_robust(speaker_id, db)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

# ============================================================================
# API Routes - Rooms
# ============================================================================

@app.get("/api/rooms", response_model=List[RoomResponse])
async def list_rooms(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    statement = select(Room).order_by(Room.name)
    return db.exec(statement).all()

@app.post("/api/rooms", response_model=RoomResponse)
async def create_room(room: RoomCreate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    db_room = Room(**room.model_dump())
    db.add(db_room)
    db.commit()
    db.refresh(db_room)
    return db_room

@app.delete("/api/rooms/{room_id}")
async def delete_room(room_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    result = delete_room_robust(room_id, db)
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["error"])
    return result

# ============================================================================
# API Routes - Seminars
# ============================================================================

@app.get("/api/seminars", response_model=List[SeminarResponse])
async def list_seminars(
    upcoming: bool = False,
    in_plan_only: bool = False,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    statement = select(Seminar).order_by(Seminar.date)
    
    if upcoming:
        today = date_type.today()
        statement = statement.where(Seminar.date >= today)
    
    if in_plan_only:
        # Only seminars that are assigned to a slot in a semester plan
        assigned_subq = select(SeminarSlot.assigned_seminar_id).where(
            SeminarSlot.assigned_seminar_id.isnot(None)
        ).distinct()
        statement = statement.where(Seminar.id.in_(assigned_subq))
    
    return db.exec(statement).all()

@app.post("/api/seminars", response_model=SeminarResponse)
async def create_seminar(seminar: SeminarCreate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    db_seminar = Seminar(**seminar.model_dump())
    db.add(db_seminar)
    db.commit()
    db.refresh(db_seminar)
    log_audit("SEMINAR_CREATE", user.get('id'), {"seminar_id": db_seminar.id, "title": db_seminar.title})
    logger.info(f"Seminar created: {db_seminar.title} (ID: {db_seminar.id}) by {user.get('id')}")
    return db_seminar

@app.get("/api/seminars/{seminar_id}", response_model=SeminarResponse)
async def get_seminar(seminar_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    seminar = db.get(Seminar, seminar_id)
    if not seminar:
        raise HTTPException(status_code=404, detail="Seminar not found")
    return seminar

@app.put("/api/seminars/{seminar_id}", response_model=SeminarResponse)
async def update_seminar(seminar_id: int, update: SeminarUpdate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    seminar = db.get(Seminar, seminar_id)
    if not seminar:
        raise HTTPException(status_code=404, detail="Seminar not found")
    
    update_data = update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(seminar, key, value)
    
    seminar.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(seminar)
    return seminar

@app.delete("/api/seminars/{seminar_id}")
async def delete_seminar(seminar_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    result = delete_seminar_robust(seminar_id, db)
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["error"])
    return result

# Additional endpoints for frontend compatibility (/api/v1/seminars/*)
@app.get("/api/v1/seminars/seminars", response_model=List[SeminarResponse])
async def list_seminars_v1(
    upcoming: bool = False,
    in_plan_only: bool = False,
    orphaned: bool = False,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    statement = select(Seminar).order_by(Seminar.date)
    
    if upcoming:
        today = date_type.today()
        statement = statement.where(Seminar.date >= today)
    
    if in_plan_only:
        # Only seminars that are assigned to a slot in a semester plan
        assigned_subq = select(SeminarSlot.assigned_seminar_id).where(
            SeminarSlot.assigned_seminar_id.isnot(None)
        ).distinct()
        statement = statement.where(Seminar.id.in_(assigned_subq))
    elif orphaned:
        # Only seminars NOT assigned to any slot (orphans)
        assigned_subq = select(SeminarSlot.assigned_seminar_id).where(
            SeminarSlot.assigned_seminar_id.isnot(None)
        ).distinct()
        statement = statement.where(~Seminar.id.in_(assigned_subq))
    
    return db.exec(statement).all()

@app.post("/api/v1/seminars/seminars", response_model=SeminarResponse)
async def create_seminar_v1(seminar: SeminarCreate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    db_seminar = Seminar(**seminar.model_dump())
    db.add(db_seminar)
    db.commit()
    db.refresh(db_seminar)
    return db_seminar

@app.get("/api/v1/seminars/seminars/{seminar_id}", response_model=SeminarResponse)
async def get_seminar_v1(seminar_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    seminar = db.get(Seminar, seminar_id)
    if not seminar:
        raise HTTPException(status_code=404, detail="Seminar not found")
    return seminar

@app.patch("/api/v1/seminars/seminars/{seminar_id}", response_model=SeminarResponse)
async def update_seminar_v1(seminar_id: int, update: SeminarUpdate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    seminar = db.get(Seminar, seminar_id)
    if not seminar:
        raise HTTPException(status_code=404, detail="Seminar not found")
    
    update_data = update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(seminar, key, value)
    
    seminar.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(seminar)
    return seminar

@app.delete("/api/v1/seminars/seminars/{seminar_id}")
async def delete_seminar_v1(seminar_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    result = delete_seminar_robust(seminar_id, db)
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["error"])
    return result

# Seminar details endpoints
@app.get("/api/v1/seminars/seminars/{seminar_id}/details")
async def get_seminar_details_v1(seminar_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    """Get seminar with details."""
    seminar = db.get(Seminar, seminar_id)
    if not seminar:
        raise HTTPException(status_code=404, detail="Seminar not found")
    
    # Get or create details
    details_stmt = select(SeminarDetails).where(SeminarDetails.seminar_id == seminar_id)
    details = db.exec(details_stmt).first()
    
    if not details:
        details = SeminarDetails(seminar_id=seminar_id)
        db.add(details)
        db.commit()
        db.refresh(details)
    
    return {
        "id": seminar.id,
        "title": seminar.title,
        "abstract": seminar.abstract,
        "date": seminar.date.isoformat(),
        "start_time": seminar.start_time,
        "end_time": seminar.end_time,
        "speaker": {
            "id": seminar.speaker.id,
            "name": seminar.speaker.name,
            "email": seminar.speaker.email,
            "affiliation": seminar.speaker.affiliation,
        } if seminar.speaker else None,
        "room": seminar.room.name if seminar.room else None,
        "status": seminar.status,
        "info": {
            "check_in_date": details.check_in_date.isoformat() if details.check_in_date else None,
            "check_out_date": details.check_out_date.isoformat() if details.check_out_date else None,
            "passport_number": details.passport_number,
            "passport_country": details.passport_country,
            "payment_email": details.payment_email,
            "beneficiary_name": details.beneficiary_name,
            "bank_account_number": details.bank_account_number,
            "bank_name": details.bank_name,
            "bank_address": details.bank_address,
            "swift_code": details.swift_code,
            "currency": details.currency,
            "beneficiary_address": details.beneficiary_address,
            "departure_city": details.departure_city,
            "travel_method": details.travel_method,
            "estimated_travel_cost": details.estimated_travel_cost,
            "needs_accommodation": details.needs_accommodation,
            "accommodation_nights": details.accommodation_nights,
            "estimated_hotel_cost": details.estimated_hotel_cost,
        }
    }

@app.put("/api/v1/seminars/seminars/{seminar_id}/details")
async def update_seminar_details_v1(
    seminar_id: int,
    data: SeminarDetailsUpdate,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Update seminar details."""
    seminar = db.get(Seminar, seminar_id)
    if not seminar:
        raise HTTPException(status_code=404, detail="Seminar not found")
    
    # Update seminar fields
    if data.title is not None:
        seminar.title = data.title
    if data.abstract is not None:
        seminar.abstract = data.abstract
    
    # Get or create details
    details_stmt = select(SeminarDetails).where(SeminarDetails.seminar_id == seminar_id)
    details = db.exec(details_stmt).first()
    
    if not details:
        details = SeminarDetails(seminar_id=seminar_id)
        db.add(details)
    
    # Update details fields
    if data.check_in_date is not None:
        details.check_in_date = data.get_date_or_none(data.check_in_date)
    if data.check_out_date is not None:
        details.check_out_date = data.get_date_or_none(data.check_out_date)
    if data.passport_number is not None:
        details.passport_number = data.passport_number
    if data.passport_country is not None:
        details.passport_country = data.passport_country
    if data.payment_email is not None:
        details.payment_email = data.payment_email
    if data.beneficiary_name is not None:
        details.beneficiary_name = data.beneficiary_name
    if data.bank_account_number is not None:
        details.bank_account_number = data.bank_account_number
    if data.bank_name is not None:
        details.bank_name = data.bank_name
    if data.bank_address is not None:
        details.bank_address = data.bank_address
    if data.swift_code is not None:
        details.swift_code = data.swift_code
    if data.currency is not None:
        details.currency = data.currency
    if data.beneficiary_address is not None:
        details.beneficiary_address = data.beneficiary_address
    if data.departure_city is not None:
        details.departure_city = data.departure_city
    if data.travel_method is not None:
        details.travel_method = data.travel_method
    if data.estimated_travel_cost is not None:
        try:
            details.estimated_travel_cost = float(data.estimated_travel_cost) if data.estimated_travel_cost else None
        except ValueError:
            pass
    if data.needs_accommodation is not None:
        details.needs_accommodation = data.needs_accommodation
    if data.accommodation_nights is not None:
        try:
            details.accommodation_nights = int(data.accommodation_nights) if data.accommodation_nights else None
        except ValueError:
            pass
    if data.estimated_hotel_cost is not None:
        try:
            details.estimated_hotel_cost = float(data.estimated_hotel_cost) if data.estimated_hotel_cost else None
        except ValueError:
            pass
    
    details.updated_at = datetime.utcnow()
    seminar.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(details)
    
    return {"success": True, "message": "Details updated successfully"}

# ============================================================================
# API Routes - Semester Planning
# ============================================================================

@app.get("/api/v1/seminars/semester-plans", response_model=List[SemesterPlanResponse])
async def list_semester_plans(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    statement = select(SemesterPlan).order_by(SemesterPlan.created_at.desc())
    return db.exec(statement).all()

@app.post("/api/v1/seminars/semester-plans", response_model=SemesterPlanResponse)
async def create_semester_plan(plan: SemesterPlanCreate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    db_plan = SemesterPlan(**plan.model_dump())
    db.add(db_plan)
    db.commit()
    db.refresh(db_plan)
    return db_plan

@app.get("/api/v1/seminars/semester-plans/{plan_id}", response_model=SemesterPlanResponse)
async def get_semester_plan(plan_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    plan = db.get(SemesterPlan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Semester plan not found")
    return plan

@app.put("/api/v1/seminars/semester-plans/{plan_id}", response_model=SemesterPlanResponse)
async def update_semester_plan(plan_id: int, update: SemesterPlanCreate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    plan = db.get(SemesterPlan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Semester plan not found")
    
    for key, value in update.model_dump().items():
        setattr(plan, key, value)
    
    db.commit()
    db.refresh(plan)
    return plan

@app.delete("/api/v1/seminars/semester-plans/{plan_id}")
async def delete_semester_plan(plan_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    result = delete_semester_plan_robust(plan_id, db)
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["error"])
    return result

# ============================================================================
# API Routes - Seminar Slots
# ============================================================================

@app.get("/api/v1/seminars/semester-plans/{plan_id}/slots", response_model=List[SeminarSlotResponse])
async def list_slots(plan_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    statement = select(SeminarSlot).where(SeminarSlot.semester_plan_id == plan_id).order_by(SeminarSlot.date)
    return db.exec(statement).all()

@app.post("/api/v1/seminars/semester-plans/{plan_id}/slots", response_model=SeminarSlotResponse)
async def create_slot(plan_id: int, slot: SeminarSlotCreate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    db_slot = SeminarSlot(semester_plan_id=plan_id, **slot.model_dump())
    db.add(db_slot)
    db.commit()
    db.refresh(db_slot)
    return db_slot

@app.put("/api/v1/seminars/slots/{slot_id}", response_model=SeminarSlotResponse)
async def update_slot(slot_id: int, update: SeminarSlotCreate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    slot = db.get(SeminarSlot, slot_id)
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")
    
    for key, value in update.model_dump().items():
        setattr(slot, key, value)
    
    db.commit()
    db.refresh(slot)
    return slot

@app.delete("/api/v1/seminars/slots/{slot_id}")
async def delete_slot(slot_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    result = delete_slot_robust(slot_id, db)
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["error"])
    return result

@app.post("/api/v1/seminars/slots/{slot_id}/unassign")
async def unassign_slot(slot_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    slot = db.get(SeminarSlot, slot_id)
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")
    
    slot.assigned_seminar_id = None
    slot.status = "available"
    db.commit()
    return {"success": True}

# ============================================================================
# API Routes - Speaker Suggestions
# ============================================================================

@app.get("/api/v1/seminars/speaker-suggestions", response_model=List[SpeakerSuggestionResponse])
async def list_speaker_suggestions(
    plan_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    statement = select(SpeakerSuggestion)
    if plan_id:
        statement = statement.where(SpeakerSuggestion.semester_plan_id == plan_id)
    statement = statement.order_by(SpeakerSuggestion.created_at.desc())
    
    suggestions = db.exec(statement).all()
    
    # Convert to response with availability
    result = []
    for s in suggestions:
        avail = [{"date": a.date.isoformat(), "preference": a.preference} for a in s.availability]
        result.append({
            "id": s.id,
            "suggested_by": s.suggested_by,
            "suggested_by_email": s.suggested_by_email,
            "speaker_id": s.speaker_id,
            "speaker_name": s.speaker_name,
            "speaker_email": s.speaker_email,
            "speaker_affiliation": s.speaker_affiliation,
            "suggested_topic": s.suggested_topic,
            "reason": s.reason,
            "priority": s.priority,
            "status": s.status,
            "semester_plan_id": s.semester_plan_id,
            "created_at": s.created_at,
            "availability": avail
        })
    return result

@app.post("/api/v1/seminars/speaker-suggestions", response_model=SpeakerSuggestionResponse)
async def create_speaker_suggestion(suggestion: SpeakerSuggestionCreate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    db_suggestion = SpeakerSuggestion(**suggestion.model_dump())
    db.add(db_suggestion)
    db.commit()
    db.refresh(db_suggestion)
    return {
        "id": db_suggestion.id,
        "suggested_by": db_suggestion.suggested_by,
        "suggested_by_email": db_suggestion.suggested_by_email,
        "speaker_id": db_suggestion.speaker_id,
        "speaker_name": db_suggestion.speaker_name,
        "speaker_email": db_suggestion.speaker_email,
        "speaker_affiliation": db_suggestion.speaker_affiliation,
        "suggested_topic": db_suggestion.suggested_topic,
        "reason": db_suggestion.reason,
        "priority": db_suggestion.priority,
        "status": db_suggestion.status,
        "semester_plan_id": db_suggestion.semester_plan_id,
        "created_at": db_suggestion.created_at,
        "availability": []
    }

@app.post("/api/v1/seminars/speaker-suggestions/{suggestion_id}/availability")
async def add_speaker_availability(
    suggestion_id: int,
    availabilities: List[SpeakerAvailabilityCreate],
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    suggestion = db.get(SpeakerSuggestion, suggestion_id)
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    
    for avail in availabilities:
        db_avail = SpeakerAvailability(suggestion_id=suggestion_id, **avail.model_dump())
        db.add(db_avail)
    
    db.commit()
    return {"success": True}

@app.put("/api/v1/seminars/speaker-suggestions/{suggestion_id}", response_model=SpeakerSuggestionResponse)
async def update_speaker_suggestion(suggestion_id: int, update: SpeakerSuggestionCreate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    suggestion = db.get(SpeakerSuggestion, suggestion_id)
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    
    for key, value in update.model_dump().items():
        setattr(suggestion, key, value)
    
    db.commit()
    db.refresh(suggestion)
    
    avail = [{"date": a.date.isoformat(), "preference": a.preference} for a in suggestion.availability]
    return {
        "id": suggestion.id,
        "suggested_by": suggestion.suggested_by,
        "suggested_by_email": suggestion.suggested_by_email,
        "speaker_id": suggestion.speaker_id,
        "speaker_name": suggestion.speaker_name,
        "speaker_email": suggestion.speaker_email,
        "speaker_affiliation": suggestion.speaker_affiliation,
        "suggested_topic": suggestion.suggested_topic,
        "reason": suggestion.reason,
        "priority": suggestion.priority,
        "status": suggestion.status,
        "semester_plan_id": suggestion.semester_plan_id,
        "created_at": suggestion.created_at,
        "availability": avail
    }

@app.delete("/api/v1/seminars/speaker-suggestions/{suggestion_id}")
async def delete_speaker_suggestion(suggestion_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    """Delete a speaker suggestion."""
    result = delete_suggestion_robust(suggestion_id, db)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

# ============================================================================
# API Routes - Speaker Tokens (for speaker access links)
# ============================================================================

import secrets
import string

def generate_token(length: int = 32) -> str:
    """Generate a secure random token."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

@app.post("/api/v1/seminars/speaker-tokens/availability")
async def create_availability_token(
    request: dict,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Create a token for speaker to submit availability."""
    suggestion_id = request.get('suggestion_id')
    
    logger.info(f"Creating availability token - suggestion_id: {suggestion_id}, user: {user.get('id')}")
    
    if not suggestion_id:
        logger.warning("Availability token creation failed: suggestion_id is required")
        raise HTTPException(status_code=400, detail="suggestion_id is required")
    
    suggestion = db.get(SpeakerSuggestion, suggestion_id)
    if not suggestion:
        logger.warning(f"Availability token creation failed: Suggestion {suggestion_id} not found")
        raise HTTPException(status_code=404, detail="Suggestion not found")
    
    # Create token
    token = generate_token()
    expires_at = datetime.utcnow() + timedelta(days=30)
    
    db_token = SpeakerToken(
        token=token,
        suggestion_id=suggestion_id,
        token_type='availability',
        expires_at=expires_at
    )
    db.add(db_token)
    db.commit()
    
    logger.info(f"Availability token created successfully: {token[:8]}... for suggestion {suggestion_id}")
    
    return {"link": f"/speaker/availability/{token}", "token": token}

@app.post("/api/v1/seminars/speaker-tokens/info")
async def create_info_token(
    request: dict,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Create a token for speaker to submit information."""
    suggestion_id = request.get('suggestion_id')
    seminar_id = request.get('seminar_id')
    
    logger.info(f"Creating info token - suggestion_id: {suggestion_id}, seminar_id: {seminar_id}, user: {user.get('id')}")
    
    if not suggestion_id:
        logger.warning("Info token creation failed: suggestion_id is required")
        raise HTTPException(status_code=400, detail="suggestion_id is required")
    
    suggestion = db.get(SpeakerSuggestion, suggestion_id)
    if not suggestion:
        logger.warning(f"Info token creation failed: Suggestion {suggestion_id} not found")
        raise HTTPException(status_code=404, detail="Suggestion not found")
    
    # Validate seminar_id if provided
    if seminar_id:
        seminar = db.get(Seminar, seminar_id)
        if not seminar:
            logger.warning(f"Info token creation failed: Seminar {seminar_id} not found")
            raise HTTPException(status_code=404, detail="Seminar not found")
    
    # Create token
    token = generate_token()
    expires_at = datetime.utcnow() + timedelta(days=30)
    
    db_token = SpeakerToken(
        token=token,
        suggestion_id=suggestion_id,
        seminar_id=seminar_id,
        token_type='info',
        expires_at=expires_at
    )
    db.add(db_token)
    db.commit()
    
    logger.info(f"Info token created successfully: {token[:8]}... for suggestion {suggestion_id}")
    
    return {"link": f"/speaker/info/{token}", "token": token}

@app.get("/api/v1/seminars/speaker-tokens/verify")
async def verify_speaker_token(
    token: str,
    db: Session = Depends(get_db)
):
    """Verify a speaker token and return associated data."""
    statement = select(SpeakerToken).where(
        SpeakerToken.token == token,
        SpeakerToken.expires_at > datetime.utcnow(),
        SpeakerToken.used_at.is_(None)
    )
    db_token = db.exec(statement).first()
    
    if not db_token:
        raise HTTPException(status_code=404, detail="Invalid or expired token")
    
    suggestion = db_token.suggestion
    
    return {
        "valid": True,
        "token_type": db_token.token_type,
        "suggestion": {
            "id": suggestion.id,
            "speaker_name": suggestion.speaker_name,
            "speaker_email": suggestion.speaker_email,
            "speaker_affiliation": suggestion.speaker_affiliation,
            "suggested_topic": suggestion.suggested_topic,
        },
        "seminar": {
            "id": db_token.seminar.id,
            "title": db_token.seminar.title,
            "date": db_token.seminar.date.isoformat(),
            "start_time": db_token.seminar.start_time,
            "end_time": db_token.seminar.end_time,
        } if db_token.seminar else None
    }

@app.post("/api/v1/seminars/speaker-tokens/{token}/submit-availability")
async def submit_speaker_availability(
    token: str,
    data: SpeakerAvailabilitySubmit,
    db: Session = Depends(get_db)
):
    """Submit availability using a speaker token."""
    statement = select(SpeakerToken).where(
        SpeakerToken.token == token,
        SpeakerToken.token_type == 'availability',
        SpeakerToken.expires_at > datetime.utcnow()
    )
    db_token = db.exec(statement).first()
    
    if not db_token:
        raise HTTPException(status_code=404, detail="Invalid or expired token")
    
    # Add availability entries
    for avail in data.availabilities:
        db_avail = SpeakerAvailability(
            suggestion_id=db_token.suggestion_id,
            date=avail.date,
            preference=avail.preference
        )
        db.add(db_avail)
    
    db_token.used_at = datetime.utcnow()
    db.commit()
    
    return {"success": True, "message": "Availability submitted successfully"}

@app.get("/api/v1/seminars/speaker-tokens/{token}/availability")
async def get_speaker_availability_by_token(token: str, db: Session = Depends(get_db)):
    """Get existing availability for a token."""
    statement = select(SpeakerToken).where(
        SpeakerToken.token == token,
        SpeakerToken.token_type == 'availability',
        SpeakerToken.expires_at > datetime.utcnow()
    )
    db_token = db.exec(statement).first()
    
    if not db_token:
        raise HTTPException(status_code=404, detail="Invalid or expired token")
    
    # Get suggestion and availability
    suggestion = db.get(SpeakerSuggestion, db_token.suggestion_id)
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    
    # Get availability entries
    availability = []
    for avail in suggestion.availability:
        availability.append({
            "date": avail.date.isoformat(),
            "preference": avail.preference
        })
    
    return {
        "speaker_name": suggestion.speaker_name,
        "suggested_topic": suggestion.suggested_topic,
        "availability": availability,
        "has_submitted": db_token.used_at is not None
    }

@app.post("/api/v1/seminars/speaker-tokens/{token}/submit-info")
async def submit_speaker_info(
    token: str,
    data: SpeakerInfoSubmit,
    db: Session = Depends(get_db)
):
    """Submit speaker information using a token."""
    statement = select(SpeakerToken).where(
        SpeakerToken.token == token,
        SpeakerToken.token_type == 'info',
        SpeakerToken.expires_at > datetime.utcnow()
    )
    db_token = db.exec(statement).first()
    
    if not db_token:
        raise HTTPException(status_code=404, detail="Invalid or expired token")
    
    # Get or create seminar details
    seminar_id = db_token.seminar_id
    if not seminar_id:
        # If no seminar_id in token, try to find one from the suggestion
        suggestion = db.get(SpeakerSuggestion, db_token.suggestion_id)
        if suggestion and suggestion.speaker_id:
            # Find a seminar for this speaker
            stmt = select(Seminar).where(Seminar.speaker_id == suggestion.speaker_id)
            seminar = db.exec(stmt).first()
            if seminar:
                seminar_id = seminar.id
    
    if not seminar_id:
        raise HTTPException(status_code=400, detail="No seminar associated with this token")
    
    # Get or create seminar details
    stmt = select(SeminarDetails).where(SeminarDetails.seminar_id == seminar_id)
    details = db.exec(stmt).first()
    
    if not details:
        details = SeminarDetails(seminar_id=seminar_id)
        db.add(details)
    
    # Update fields (must match SeminarDetails model and internal modal)
    if data.passport_number is not None:
        details.passport_number = data.passport_number
    if data.passport_country is not None:
        details.passport_country = data.passport_country
    if data.departure_city is not None:
        details.departure_city = data.departure_city
    if data.travel_method is not None:
        details.travel_method = data.travel_method
    if data.estimated_travel_cost is not None and str(data.estimated_travel_cost).strip():
        try:
            details.estimated_travel_cost = float(data.estimated_travel_cost)
        except (ValueError, TypeError):
            pass
    if data.needs_accommodation is not None:
        details.needs_accommodation = data.needs_accommodation
    if data.check_in_date is not None:
        details.check_in_date = data.check_in_date
    if data.check_out_date is not None:
        details.check_out_date = data.check_out_date
    if data.accommodation_nights is not None and str(data.accommodation_nights).strip():
        try:
            details.accommodation_nights = int(float(data.accommodation_nights))
        except (ValueError, TypeError):
            pass
    if data.estimated_hotel_cost is not None and str(data.estimated_hotel_cost).strip():
        try:
            details.estimated_hotel_cost = float(data.estimated_hotel_cost)
        except (ValueError, TypeError):
            pass
    if data.payment_email is not None:
        details.payment_email = data.payment_email
    if data.beneficiary_name is not None:
        details.beneficiary_name = data.beneficiary_name
    if data.bank_name is not None:
        details.bank_name = data.bank_name
    if data.swift_code is not None:
        details.swift_code = data.swift_code
    if data.bank_account_number is not None:
        details.bank_account_number = data.bank_account_number
    if data.bank_address is not None:
        details.bank_address = data.bank_address
    if data.beneficiary_address is not None:
        details.beneficiary_address = data.beneficiary_address
    if data.currency is not None:
        details.currency = data.currency
    
    details.updated_at = datetime.utcnow()
    
    # Update seminar title and abstract if provided
    seminar = db.get(Seminar, seminar_id)
    if seminar:
        if data.final_talk_title:
            seminar.title = data.final_talk_title
        if data.abstract:
            seminar.abstract = data.abstract
        if data.talk_title:  # Fallback
            seminar.title = data.talk_title
    
    # Update speaker name if provided
    if data.speaker_name and seminar and seminar.speaker_id:
        speaker = db.get(Speaker, seminar.speaker_id)
        if speaker:
            speaker.name = data.speaker_name
    
    db_token.used_at = datetime.utcnow()
    db.commit()
    
    return {"success": True, "message": "Information submitted successfully"}

@app.get("/api/v1/seminars/speaker-tokens/{token}/info")
async def get_speaker_info_by_token(token: str, db: Session = Depends(get_db)):
    """Get existing speaker information for a token."""
    statement = select(SpeakerToken).where(
        SpeakerToken.token == token,
        SpeakerToken.token_type == 'info',
        SpeakerToken.expires_at > datetime.utcnow()
    )
    db_token = db.exec(statement).first()
    
    if not db_token:
        raise HTTPException(status_code=404, detail="Invalid or expired token")
    
    # Get suggestion - validate it exists
    suggestion = db.get(SpeakerSuggestion, db_token.suggestion_id)
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found - may have been deleted")
    
    # Get seminar from token
    seminar_id = db_token.seminar_id
    if not seminar_id:
        # Try to find seminar by suggestion's speaker_id
        if suggestion.speaker_id:
            stmt = select(Seminar).where(Seminar.speaker_id == suggestion.speaker_id)
            seminar = db.exec(stmt).first()
            if seminar:
                seminar_id = seminar.id
    
    if not seminar_id:
        # Return basic suggestion info if no seminar exists yet
        return {
            "speaker_name": suggestion.speaker_name,
            "speaker_email": suggestion.speaker_email,
            "speaker_affiliation": suggestion.speaker_affiliation,
            "final_talk_title": suggestion.suggested_topic,
            "has_submitted": db_token.used_at is not None
        }
    
    # Get seminar and details
    seminar = db.get(Seminar, seminar_id)
    if not seminar:
        # Seminar was deleted, return suggestion info
        return {
            "speaker_name": suggestion.speaker_name,
            "speaker_email": suggestion.speaker_email,
            "speaker_affiliation": suggestion.speaker_affiliation,
            "final_talk_title": suggestion.suggested_topic,
            "has_submitted": db_token.used_at is not None
        }
    
    details_stmt = select(SeminarDetails).where(SeminarDetails.seminar_id == seminar_id)
    details = db.exec(details_stmt).first()
    
    return {
        "speaker_name": seminar.speaker.name if seminar.speaker else suggestion.speaker_name,
        "final_talk_title": seminar.title if seminar else suggestion.suggested_topic,
        "abstract": seminar.abstract if seminar else None,
        "passport_number": details.passport_number if details else None,
        "passport_country": details.passport_country if details else None,
        "departure_city": details.departure_city if details else None,
        "travel_method": details.travel_method if details else None,
        "estimated_travel_cost": details.estimated_travel_cost if details else None,
        "needs_accommodation": details.needs_accommodation if details else None,
        "check_in_date": details.check_in_date.isoformat() if details and details.check_in_date else None,
        "check_out_date": details.check_out_date.isoformat() if details and details.check_out_date else None,
        "accommodation_nights": details.accommodation_nights if details else None,
        "estimated_hotel_cost": details.estimated_hotel_cost if details else None,
        "payment_email": details.payment_email if details else None,
        "beneficiary_name": details.beneficiary_name if details else None,
        "bank_name": details.bank_name if details else None,
        "swift_code": details.swift_code if details else None,
        "bank_account_number": details.bank_account_number if details else None,
        "bank_address": details.bank_address if details else None,
        "beneficiary_address": details.beneficiary_address if details else None,
        "currency": details.currency if details else None,
        "has_submitted": db_token.used_at is not None
    }

@app.post("/api/v1/seminars/speaker-tokens/{token}/finalize")
async def finalize_speaker_info(token: str, db: Session = Depends(get_db)):
    """Finalize speaker info submission - marks token as used."""
    statement = select(SpeakerToken).where(
        SpeakerToken.token == token,
        SpeakerToken.token_type == 'info',
        SpeakerToken.expires_at > datetime.utcnow()
    )
    db_token = db.exec(statement).first()
    
    if not db_token:
        raise HTTPException(status_code=404, detail="Invalid or expired token")
    
    db_token.used_at = datetime.utcnow()
    db.commit()
    
    return {"success": True, "message": "Submission finalized"}

# ============================================================================
# API Routes - Planning Board
# ============================================================================

@app.get("/api/v1/seminars/semester-plans/{plan_id}/planning-board")
async def get_planning_board(plan_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    plan = db.get(SemesterPlan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Semester plan not found")
    
    # Get slots
    slots_stmt = select(SeminarSlot).where(SeminarSlot.semester_plan_id == plan_id).order_by(SeminarSlot.date)
    slots = db.exec(slots_stmt).all()
    
    # Get suggestions for this plan
    suggestions_stmt = select(SpeakerSuggestion).where(SpeakerSuggestion.semester_plan_id == plan_id)
    suggestions = db.exec(suggestions_stmt).all()
    
    # Build slots response with assigned speaker name
    slots_response = []
    for s in slots:
        slot_data = {
            "id": s.id,
            "date": s.date.isoformat(),
            "start_time": s.start_time,
            "end_time": s.end_time,
            "room": s.room,
            "status": s.status,
            "assigned_seminar_id": s.assigned_seminar_id
        }
        # If slot has an assigned seminar, get the speaker name
        if s.assigned_seminar_id:
            seminar = db.get(Seminar, s.assigned_seminar_id)
            if seminar:
                assigned_suggestion_id = s.assigned_suggestion_id  # Use stored value first
                
                # Access speaker through the relationship
                try:
                    speaker_name = seminar.speaker.name if seminar.speaker else None
                    if speaker_name:
                        slot_data["assigned_speaker_name"] = speaker_name
                except Exception:
                    # If speaker relationship isn't loaded, query it directly
                    speaker = db.get(Speaker, seminar.speaker_id)
                    if speaker:
                        slot_data["assigned_speaker_name"] = speaker.name

                # If no stored suggestion_id, try to find by matching
                if not assigned_suggestion_id:
                    for suggestion in suggestions:
                        if suggestion.semester_plan_id != plan_id:
                            continue
                        if suggestion.status != "confirmed":
                            continue

                        if seminar.speaker_id and suggestion.speaker_id and seminar.speaker_id == suggestion.speaker_id:
                            assigned_suggestion_id = suggestion.id
                            break

                        slot_speaker_name = slot_data.get("assigned_speaker_name")
                        if (
                            slot_speaker_name
                            and suggestion.speaker_name
                            and suggestion.speaker_name.strip().lower() == slot_speaker_name.strip().lower()
                        ):
                            assigned_suggestion_id = suggestion.id
                            break

                if assigned_suggestion_id:
                    slot_data["assigned_suggestion_id"] = assigned_suggestion_id
        slots_response.append(slot_data)
    
    return {
        "slots": slots_response,
        "suggestions": [
            {
                "id": s.id,
                "speaker_id": s.speaker_id,
                "speaker_name": s.speaker_name,
                "speaker_affiliation": s.speaker_affiliation,
                "suggested_by": s.suggested_by,
                "suggested_topic": s.suggested_topic,
                "priority": s.priority,
                "status": s.status,
                "availability": [{"date": a.date.isoformat(), "preference": a.preference} for a in s.availability]
            }
            for s in suggestions
        ]
    }

@app.post("/api/v1/seminars/planning/assign")
async def assign_speaker_to_slot(
    request: AssignSpeakerRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    slot = db.get(SeminarSlot, request.slot_id)
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")
    
    suggestion = db.get(SpeakerSuggestion, request.suggestion_id)
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    
    # Find or create speaker based on suggestion
    speaker_id = suggestion.speaker_id
    if not speaker_id:
        # Try to find existing speaker by name
        speaker_stmt = select(Speaker).where(Speaker.name == suggestion.speaker_name)
        existing_speaker = db.exec(speaker_stmt).first()
        if existing_speaker:
            speaker_id = existing_speaker.id
        else:
            # Create a new speaker from suggestion data
            new_speaker = Speaker(
                name=suggestion.speaker_name,
                email=suggestion.speaker_email,
                affiliation=suggestion.speaker_affiliation
            )
            db.add(new_speaker)
            db.commit()
            db.refresh(new_speaker)
            speaker_id = new_speaker.id
            # Update suggestion with the new speaker_id
            suggestion.speaker_id = speaker_id
    
    # Create a seminar from the suggestion
    seminar = Seminar(
        title=suggestion.suggested_topic or f"Seminar by {suggestion.speaker_name}",
        date=slot.date,
        start_time=slot.start_time,
        end_time=slot.end_time,
        speaker_id=speaker_id,
        room_id=None,
        status="planned"
    )
    db.add(seminar)
    db.commit()
    db.refresh(seminar)
    
    # Assign seminar to slot
    slot.assigned_seminar_id = seminar.id
    slot.assigned_suggestion_id = suggestion.id
    slot.status = "confirmed"
    suggestion.status = "confirmed"
    
    db.commit()
    return {"success": True, "seminar_id": seminar.id}

@app.post("/api/v1/seminars/planning/assign-seminar")
async def assign_seminar_to_slot(
    request: AssignSeminarRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Assign an existing seminar (e.g. orphan) to an empty slot."""
    slot = db.get(SeminarSlot, request.slot_id)
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")
    if slot.assigned_seminar_id:
        raise HTTPException(status_code=400, detail="Slot already has an assigned seminar")
    
    seminar = db.get(Seminar, request.seminar_id)
    if not seminar:
        raise HTTPException(status_code=404, detail="Seminar not found")
    
    # Update seminar to match slot date/time
    seminar.date = slot.date
    seminar.start_time = slot.start_time
    seminar.end_time = slot.end_time
    seminar.updated_at = datetime.utcnow()
    
    # Assign to slot
    slot.assigned_seminar_id = seminar.id
    slot.assigned_suggestion_id = None  # No suggestion for reassigned orphans
    slot.status = "confirmed"
    
    db.commit()
    return {"success": True, "seminar_id": seminar.id}

# ============================================================================
# API Routes - Files
# ============================================================================

def ensure_uploads_dir():
    Path(settings.uploads_dir).mkdir(parents=True, exist_ok=True)

def save_uploaded_file(file: UploadFile, seminar_id: int, category: Optional[str], db: Session) -> UploadedFile:
    ensure_uploads_dir()
    
    original_filename = file.filename or "unnamed"
    original_ext = original_filename.rsplit(".", 1)[-1].lower() if "." in original_filename else ""
    
    file_id = uuid.uuid4().hex
    storage_filename = f"{file_id}.bin"
    storage_path = Path(settings.uploads_dir) / storage_filename
    
    with open(storage_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    file_size = storage_path.stat().st_size
    content_type = file.content_type or "application/octet-stream"
    
    uploaded = UploadedFile(
        seminar_id=seminar_id,
        original_filename=original_filename,
        original_extension=original_ext if original_ext else None,
        content_type=content_type,
        file_size=file_size,
        storage_filename=storage_filename,
        file_category=category,
    )
    db.add(uploaded)
    db.commit()
    db.refresh(uploaded)
    
    return uploaded

@app.post("/api/v1/seminars/speaker-tokens/{token}/upload")
async def upload_file_with_token(
    token: str,
    file: UploadFile = File(...),
    category: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Upload file using a speaker token (no regular auth required)."""
    # Verify token
    statement = select(SpeakerToken).where(
        SpeakerToken.token == token,
        SpeakerToken.token_type == 'info',
        SpeakerToken.expires_at > datetime.utcnow()
    )
    db_token = db.exec(statement).first()
    
    if not db_token:
        raise HTTPException(status_code=404, detail="Invalid or expired token")
    
    # Get seminar_id from token or find it via suggestion
    seminar_id = db_token.seminar_id
    if not seminar_id:
        suggestion = db.get(SpeakerSuggestion, db_token.suggestion_id)
        if suggestion and suggestion.speaker_id:
            stmt = select(Seminar).where(Seminar.speaker_id == suggestion.speaker_id)
            seminar = db.exec(stmt).first()
            if seminar:
                seminar_id = seminar.id
    
    if not seminar_id:
        raise HTTPException(status_code=400, detail="No seminar associated with this token")
    
    uploaded = save_uploaded_file(file, seminar_id, category, db)
    log_audit("FILE_UPLOAD", f"token:{token[:8]}", {"seminar_id": seminar_id, "file": file.filename, "category": category})
    logger.info(f"File uploaded via token: {file.filename} for seminar {seminar_id}")
    return {"success": True, "file_id": uploaded.id, "message": "File uploaded successfully"}

@app.get("/api/v1/seminars/speaker-tokens/{token}/files")
async def list_files_with_token(token: str, db: Session = Depends(get_db)):
    """List files for a seminar using a speaker token (no regular auth required)."""
    # Verify token
    statement = select(SpeakerToken).where(
        SpeakerToken.token == token,
        SpeakerToken.token_type == 'info',
        SpeakerToken.expires_at > datetime.utcnow()
    )
    db_token = db.exec(statement).first()
    
    if not db_token:
        raise HTTPException(status_code=404, detail="Invalid or expired token")
    
    # Get seminar_id from token or find it via suggestion
    seminar_id = db_token.seminar_id
    if not seminar_id:
        suggestion = db.get(SpeakerSuggestion, db_token.suggestion_id)
        if suggestion and suggestion.speaker_id:
            stmt = select(Seminar).where(Seminar.speaker_id == suggestion.speaker_id)
            seminar = db.exec(stmt).first()
            if seminar:
                seminar_id = seminar.id
    
    if not seminar_id:
        return []  # No seminar yet, return empty list
    
    statement = select(UploadedFile).where(UploadedFile.seminar_id == seminar_id)
    files = db.exec(statement).all()
    
    return [
        {
            "id": f.id,
            "original_filename": f.original_filename,
            "file_category": f.file_category,
            "file_size": f.file_size,
            "content_type": f.content_type,
            "uploaded_at": f.uploaded_at.isoformat() if f.uploaded_at else None
        }
        for f in files
    ]

@app.get("/api/v1/seminars/speaker-tokens/{token}/files/{file_id}/download")
async def download_file_with_token(token: str, file_id: int, db: Session = Depends(get_db)):
    """Download a file using a speaker token (no regular auth required)."""
    # Verify token
    statement = select(SpeakerToken).where(
        SpeakerToken.token == token,
        SpeakerToken.token_type == 'info',
        SpeakerToken.expires_at > datetime.utcnow()
    )
    db_token = db.exec(statement).first()
    
    if not db_token:
        raise HTTPException(status_code=404, detail="Invalid or expired token")
    
    # Get seminar_id from token
    seminar_id = db_token.seminar_id
    if not seminar_id:
        suggestion = db.get(SpeakerSuggestion, db_token.suggestion_id)
        if suggestion and suggestion.speaker_id:
            stmt = select(Seminar).where(Seminar.speaker_id == suggestion.speaker_id)
            seminar = db.exec(stmt).first()
            if seminar:
                seminar_id = seminar.id
    
    if not seminar_id:
        raise HTTPException(status_code=404, detail="No seminar associated with this token")
    
    # Get file and verify it belongs to this seminar
    file_record = db.get(UploadedFile, file_id)
    if not file_record or file_record.seminar_id != seminar_id:
        raise HTTPException(status_code=404, detail="File not found")
    
    file_path = Path(settings.uploads_dir) / file_record.storage_filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    log_audit("FILE_DOWNLOAD", f"token:{token[:8]}", {"file_id": file_id, "filename": file_record.original_filename})
    logger.info(f"File downloaded via token: {file_record.original_filename}")
    
    return FileResponse(
        path=file_path,
        filename=file_record.original_filename,
        media_type=file_record.content_type
    )

@app.delete("/api/v1/seminars/speaker-tokens/{token}/files/{file_id}")
async def delete_file_with_token(token: str, file_id: int, db: Session = Depends(get_db)):
    """Delete a file using a speaker token (no regular auth required)."""
    # Verify token
    statement = select(SpeakerToken).where(
        SpeakerToken.token == token,
        SpeakerToken.token_type == 'info',
        SpeakerToken.expires_at > datetime.utcnow()
    )
    db_token = db.exec(statement).first()
    
    if not db_token:
        raise HTTPException(status_code=404, detail="Invalid or expired token")
    
    # Get seminar_id from token
    seminar_id = db_token.seminar_id
    if not seminar_id:
        suggestion = db.get(SpeakerSuggestion, db_token.suggestion_id)
        if suggestion and suggestion.speaker_id:
            stmt = select(Seminar).where(Seminar.speaker_id == suggestion.speaker_id)
            seminar = db.exec(stmt).first()
            if seminar:
                seminar_id = seminar.id
    
    if not seminar_id:
        raise HTTPException(status_code=404, detail="No seminar associated with this token")
    
    # Get file and verify it belongs to this seminar
    file_record = db.get(UploadedFile, file_id)
    if not file_record or file_record.seminar_id != seminar_id:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Delete from disk
    file_path = Path(settings.uploads_dir) / file_record.storage_filename
    if file_path.exists():
        file_path.unlink()
    
    # Delete from database
    db.delete(file_record)
    db.commit()
    
    log_audit("FILE_DELETE", f"token:{token[:8]}", {"file_id": file_id, "filename": file_record.original_filename})
    logger.info(f"File deleted via token: {file_record.original_filename}")
    
    return {"success": True, "message": "File deleted successfully"}

@app.post("/api/seminars/{seminar_id}/files")
async def upload_file(
    seminar_id: int,
    file: UploadFile = File(...),
    category: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    seminar = db.get(Seminar, seminar_id)
    if not seminar:
        raise HTTPException(status_code=404, detail="Seminar not found")
    
    uploaded = save_uploaded_file(file, seminar_id, category, db)
    log_audit("FILE_UPLOAD", user.get('id'), {"seminar_id": seminar_id, "file": file.filename, "category": category})
    logger.info(f"File uploaded: {file.filename} for seminar {seminar_id} by {user.get('id')}")
    return {"success": True, "file_id": uploaded.id}

@app.get("/api/seminars/{seminar_id}/files")
async def list_files(seminar_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    statement = select(UploadedFile).where(UploadedFile.seminar_id == seminar_id)
    return db.exec(statement).all()

@app.get("/api/files/{file_id}/download")
async def download_file(file_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    file_record = db.get(UploadedFile, file_id)
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
    
    file_path = Path(settings.uploads_dir) / file_record.storage_filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    return FileResponse(
        path=file_path,
        filename=file_record.original_filename,
        media_type=file_record.content_type
    )

# Additional upload endpoint for frontend compatibility
@app.post("/api/v1/seminars/seminars/{seminar_id}/upload")
async def upload_file_v1(
    seminar_id: int,
    file: UploadFile = File(...),
    file_category: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Upload file for a seminar (frontend compatibility endpoint)."""
    seminar = db.get(Seminar, seminar_id)
    if not seminar:
        raise HTTPException(status_code=404, detail="Seminar not found")
    
    uploaded = save_uploaded_file(file, seminar_id, file_category, db)
    log_audit("FILE_UPLOAD", user.get('id'), {"seminar_id": seminar_id, "file": file.filename, "category": file_category})
    logger.info(f"File uploaded: {file.filename} for seminar {seminar_id} by {user.get('id')}")
    return {"success": True, "file_id": uploaded.id, "message": "File uploaded successfully"}

# Additional files endpoints for frontend compatibility
@app.get("/api/v1/seminars/seminars/{seminar_id}/files")
async def list_files_v1(seminar_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    """List files for a seminar (frontend compatibility endpoint)."""
    statement = select(UploadedFile).where(UploadedFile.seminar_id == seminar_id)
    files = db.exec(statement).all()
    return [
        {
            "id": f.id,
            "original_filename": f.original_filename,
            "file_category": f.file_category,
            "file_size": f.file_size,
            "content_type": f.content_type,
            "uploaded_at": f.uploaded_at.isoformat()
        }
        for f in files
    ]

@app.delete("/api/v1/seminars/seminars/{seminar_id}/files/{file_id}")
async def delete_file_v1(
    seminar_id: int,
    file_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Delete a file (frontend compatibility endpoint)."""
    file_record = db.get(UploadedFile, file_id)
    if not file_record or file_record.seminar_id != seminar_id:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Delete from disk
    file_path = Path(settings.uploads_dir) / file_record.storage_filename
    if file_path.exists():
        file_path.unlink()
    
    # Delete from database
    db.delete(file_record)
    db.commit()
    
    return {"success": True, "message": "File deleted successfully"}

@app.get("/api/v1/seminars/seminars/{seminar_id}/files/{file_id}/download")
async def download_file_v1(
    seminar_id: int,
    file_id: int,
    access_code: Optional[str] = Query(None),
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Download a file (frontend compatibility endpoint)."""
    file_record = db.get(UploadedFile, file_id)
    if not file_record or file_record.seminar_id != seminar_id:
        raise HTTPException(status_code=404, detail="File not found")
    
    file_path = Path(settings.uploads_dir) / file_record.storage_filename
    if not file_path.exists():
        logger.error(f"File not found on disk: {file_path}")
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    log_audit("FILE_DOWNLOAD", user.get('id'), {"file_id": file_id, "filename": file_record.original_filename})
    logger.info(f"File downloaded: {file_record.original_filename} by {user.get('id')}")
    
    return FileResponse(
        path=file_path,
        filename=file_record.original_filename,
        media_type=file_record.content_type
    )

# ============================================================================
# API Routes - External (for Dashboard)
# ============================================================================

@app.get("/api/external/stats")
async def external_stats(secret: str, db: Session = Depends(get_db)):
    if secret != settings.api_secret:
        raise HTTPException(status_code=401, detail="Invalid secret")
    
    today = date_type.today()
    
    upcoming_stmt = select(Seminar).where(Seminar.date >= today)
    upcoming_count = len(db.exec(upcoming_stmt).all())
    
    speakers_stmt = select(Speaker)
    speakers_count = len(db.exec(speakers_stmt).all())
    
    pending_stmt = select(Seminar).where(
        (Seminar.date >= today) & 
        ((Seminar.room_booked == False) | 
         (Seminar.announcement_sent == False) |
         (Seminar.calendar_invite_sent == False))
    )
    pending_count = len(db.exec(pending_stmt).all())
    
    return {
        "upcoming_seminars": upcoming_count,
        "total_speakers": speakers_count,
        "pending_tasks": pending_count
    }

@app.get("/api/external/upcoming")
async def external_upcoming(secret: str, limit: int = 5, db: Session = Depends(get_db)):
    if secret != settings.api_secret:
        raise HTTPException(status_code=401, detail="Invalid secret")
    
    today = date_type.today()
    statement = (
        select(Seminar)
        .where(Seminar.date >= today)
        .order_by(Seminar.date)
        .limit(limit)
    )
    seminars = db.exec(statement).all()
    
    return {
        "seminars": [
            {
                "id": s.id,
                "title": s.title,
                "date": s.date.isoformat(),
                "start_time": s.start_time,
                "speaker": s.speaker.name if s.speaker else "TBD",
                "affiliation": s.speaker.affiliation if s.speaker else None,
                "room": s.room.name if s.room else "TBD",
                "pending_tasks": sum([
                    not s.room_booked,
                    not s.announcement_sent,
                    not s.calendar_invite_sent
                ])
            }
            for s in seminars
        ]
    }

# ============================================================================
# Health Check
# ============================================================================

@app.get("/api/health")
async def health():
    return {"status": "ok"}
