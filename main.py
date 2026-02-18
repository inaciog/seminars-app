"""
Seminars App - Unified Auth Integration

A standalone seminar management system that integrates with the unified
authentication service (inacio-auth.fly.dev).

Auth Flow:
1. User visits app with ?token=xxx from auth service
2. App validates JWT against JWT_SECRET
3. If invalid/missing, redirect to auth service login
4. All API calls include the token
"""

import os
import uuid
import shutil
from datetime import datetime, date, timedelta
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
from pydantic import BaseModel, ConfigDict
from pydantic_settings import BaseSettings

# ============================================================================
# Configuration
# ============================================================================

class Settings(BaseSettings):
    jwt_secret: str = "your-secret-key-change-in-production"
    api_secret: str = "your-api-secret-for-dashboard"
    master_password: str = "i486983nacio:!"
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

engine = create_engine(f"sqlite:///{settings.database_url}", connect_args={"check_same_thread": False})

class Speaker(SQLModel, table=True):
    __tablename__ = "speakers"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    affiliation: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    bio: Optional[str] = None
    cv_path: Optional[str] = None
    photo_path: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    seminars: List["Seminar"] = Relationship(back_populates="speaker")
    availability_slots: List["AvailabilitySlot"] = Relationship(back_populates="speaker")

class Room(SQLModel, table=True):
    __tablename__ = "rooms"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    capacity: Optional[int] = None
    location: Optional[str] = None
    equipment: Optional[str] = None  # JSON string of equipment list
    
    seminars: List["Seminar"] = Relationship(back_populates="room")

class Seminar(SQLModel, table=True):
    __tablename__ = "seminars"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    date: date = Field(index=True)
    start_time: str  # HH:MM format
    end_time: Optional[str] = None
    
    # Foreign keys
    speaker_id: int = Field(foreign_key="speakers.id")
    room_id: Optional[int] = Field(default=None, foreign_key="rooms.id")
    
    # Details
    abstract: Optional[str] = None
    paper_title: Optional[str] = None
    status: str = Field(default="planned")  # planned, confirmed, completed, cancelled
    
    # Bureaucracy tracking
    room_booked: bool = Field(default=False)
    announcement_sent: bool = Field(default=False)
    calendar_invite_sent: bool = Field(default=False)
    website_updated: bool = Field(default=False)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    speaker: Speaker = Relationship(back_populates="seminars")
    room: Optional[Room] = Relationship(back_populates="seminars")
    files: List["UploadedFile"] = Relationship(back_populates="seminar")

class AvailabilitySlot(SQLModel, table=True):
    __tablename__ = "availability_slots"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    speaker_id: int = Field(foreign_key="speakers.id")
    date: date
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
    storage_filename: str  # UUID.bin
    file_category: Optional[str] = None  # cv, photo, paper, other
    description: Optional[str] = None
    
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    
    seminar: Seminar = Relationship(back_populates="files")

# ============================================================================
# Pydantic Models
# ============================================================================

class SpeakerCreate(BaseModel):
    name: str
    affiliation: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    bio: Optional[str] = None

class SpeakerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    affiliation: Optional[str]
    email: Optional[str]
    website: Optional[str]
    bio: Optional[str]
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
    date: date
    start_time: str
    end_time: Optional[str] = None
    speaker_id: int
    room_id: Optional[int] = None
    abstract: Optional[str] = None
    paper_title: Optional[str] = None

class SeminarUpdate(BaseModel):
    title: Optional[str] = None
    date: Optional[date] = None
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

class SeminarResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    title: str
    date: date
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
    speaker: SpeakerResponse
    room: Optional[RoomResponse]

class AvailabilityCreate(BaseModel):
    speaker_id: int
    date: date
    start_time: str
    end_time: str
    notes: Optional[str] = None

# ============================================================================
# Auth
# ============================================================================

security = HTTPBearer(auto_error=False)

def get_db():
    with Session(engine) as session:
        yield session

def verify_token(token: str) -> Optional[dict]:
    """Verify JWT token from auth service."""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        return payload
    except JWTError:
        return None

async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    token: Optional[str] = Query(None)
) -> dict:
    """Get current user from token (header, query param, or cookie)."""
    # Try header first
    auth_token = credentials.credentials if credentials else None
    # Then query param
    if not auth_token:
        auth_token = token
    # Then cookie
    if not auth_token:
        auth_token = request.cookies.get("token")
    
    if not auth_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user = verify_token(auth_token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return user

async def require_auth(request: Request, call_next):
    """Middleware to check auth on HTML routes."""
    # Skip API routes and static files
    if request.url.path.startswith("/api/") or request.url.path.startswith("/static/"):
        return await call_next(request)
    
    # Skip public page
    if request.url.path == "/public":
        return await call_next(request)
    
    # Check for token
    token = request.query_params.get("token") or request.cookies.get("token")
    
    if not token or not verify_token(token):
        # Redirect to auth service
        return_url = f"{settings.app_url}{request.url.path}"
        return RedirectResponse(
            f"{settings.auth_service_url}/login?returnTo={return_url}"
        )
    
    return await call_next(request)

# ============================================================================
# File Upload Helpers
# ============================================================================

def ensure_uploads_dir():
    Path(settings.uploads_dir).mkdir(parents=True, exist_ok=True)

def save_uploaded_file(file: UploadFile, seminar_id: int, category: Optional[str], db: Session) -> UploadedFile:
    ensure_uploads_dir()
    
    original_filename = file.filename or "unnamed"
    original_ext = original_filename.rsplit(".", 1)[-1].lower() if "." in original_filename else ""
    
    # Generate safe filename
    file_id = uuid.uuid4().hex
    storage_filename = f"{file_id}.bin"
    storage_path = Path(settings.uploads_dir) / storage_filename
    
    # Save file
    with open(storage_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    file_size = storage_path.stat().st_size
    content_type = file.content_type or "application/octet-stream"
    
    # Create DB record
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

# ============================================================================
# App Initialization
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    SQLModel.metadata.create_all(engine)
    ensure_uploads_dir()
    yield
    # Shutdown

app = FastAPI(title="Seminars App", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Auth middleware for HTML routes
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    return await require_auth(request, call_next)

# ============================================================================
# HTML Routes
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def index():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Seminars</title>
        <link rel="stylesheet" href="/static/style.css">
    </head>
    <body>
        <div class="container">
            <header>
                <h1>📚 Seminars</h1>
                <button onclick="openModal('seminar-modal')">+ New Seminar</button>
            </header>
            
            <nav>
                <a href="/" class="active">Seminars</a>
                <a href="/speakers">Speakers</a>
                <a href="/rooms">Rooms</a>
                <a href="/public" target="_blank">Public Page ↗</a>
            </nav>
            
            <div class="card">
                <h2>Upcoming Seminars</h2>
                <div id="seminars-list">
                    <p>Loading...</p>
                </div>
            </div>
            
            <div class="card">
                <h2>Speakers</h2>
                <div id="speakers-list">
                    <p>Loading...</p>
                </div>
            </div>
        </div>
        
        <!-- New Seminar Modal -->
        <div id="seminar-modal" class="modal">
            <div class="modal-content">
                <div class="modal-header">
                    <h3>New Seminar</h3>
                    <button class="close-btn" onclick="closeModal('seminar-modal')">&times;</button>
                </div>
                <form id="seminar-form" onsubmit="handleSeminarSubmit(event)">
                    <div class="form-group">
                        <label>Title</label>
                        <input type="text" name="title" required>
                    </div>
                    <div class="form-group">
                        <label>Date</label>
                        <input type="date" name="date" required>
                    </div>
                    <div class="form-group">
                        <label>Start Time</label>
                        <input type="time" name="start_time" required>
                    </div>
                    <div class="form-group">
                        <label>Speaker</label>
                        <select name="speaker_id" id="speaker-select" required>
                            <option value="">Select speaker...</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Room</label>
                        <select name="room_id">
                            <option value="">Select room...</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Abstract</label>
                        <textarea name="abstract" rows="3"></textarea>
                    </div>
                    <button type="submit">Create Seminar</button>
                </form>
            </div>
        </div>
        
        <script src="/static/app.js"></script>
        <script>
            // Modal functions
            function openModal(id) {
                document.getElementById(id).classList.add('active');
                loadSpeakersForSelect();
            }
            
            function closeModal(id) {
                document.getElementById(id).classList.remove('active');
            }
            
            // Load speakers into select
            async function loadSpeakersForSelect() {
                const select = document.getElementById('speaker-select');
                try {
                    const speakers = await api('/speakers');
                    select.innerHTML = '<option value="">Select speaker...</option>' +
                        speakers.map(s => `<option value="${s.id}">${s.name}</option>`).join('');
                } catch (e) {
                    console.error('Failed to load speakers:', e);
                }
            }
            
            // Handle form submit
            async function handleSeminarSubmit(e) {
                e.preventDefault();
                const form = e.target;
                const data = {
                    title: form.title.value,
                    date: form.date.value,
                    start_time: form.start_time.value,
                    speaker_id: parseInt(form.speaker_id.value),
                    room_id: form.room_id.value ? parseInt(form.room_id.value) : null,
                    abstract: form.abstract.value
                };
                
                try {
                    await createSeminar(data);
                    closeModal('seminar-modal');
                    form.reset();
                    loadSeminars();
                } catch (err) {
                    alert('Error: ' + err.message);
                }
            }
        </script>
    </body>
    </html>
    """

@app.get("/public", response_class=HTMLResponse)
async def public_page(db: Session = Depends(get_db)):
    """Public page showing upcoming seminars."""
    today = date.today()
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
    speaker = db.get(Speaker, speaker_id)
    if not speaker:
        raise HTTPException(status_code=404, detail="Speaker not found")
    
    db.delete(speaker)
    db.commit()
    return {"success": True}

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
    room = db.get(Room, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    db.delete(room)
    db.commit()
    return {"success": True}

# ============================================================================
# API Routes - Seminars
# ============================================================================

@app.get("/api/seminars", response_model=List[SeminarResponse])
async def list_seminars(
    upcoming: bool = False,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    statement = select(Seminar).order_by(Seminar.date)
    
    if upcoming:
        today = date.today()
        statement = statement.where(Seminar.date >= today)
    
    return db.exec(statement).all()

@app.post("/api/seminars", response_model=SeminarResponse)
async def create_seminar(seminar: SeminarCreate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    db_seminar = Seminar(**seminar.model_dump())
    db.add(db_seminar)
    db.commit()
    db.refresh(db_seminar)
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
    seminar = db.get(Seminar, seminar_id)
    if not seminar:
        raise HTTPException(status_code=404, detail="Seminar not found")
    
    db.delete(seminar)
    db.commit()
    return {"success": True}

# ============================================================================
# API Routes - Files
# ============================================================================

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

# ============================================================================
# API Routes - External (for Dashboard)
# ============================================================================

@app.get("/api/external/stats")
async def external_stats(secret: str, db: Session = Depends(get_db)):
    """Get statistics for dashboard integration."""
    if secret != settings.api_secret:
        raise HTTPException(status_code=401, detail="Invalid secret")
    
    today = date.today()
    
    # Count upcoming seminars
    upcoming_stmt = select(Seminar).where(Seminar.date >= today)
    upcoming_count = len(db.exec(upcoming_stmt).all())
    
    # Count total speakers
    speakers_stmt = select(Speaker)
    speakers_count = len(db.exec(speakers_stmt).all())
    
    # Count pending tasks
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
    """Get upcoming seminars for dashboard."""
    if secret != settings.api_secret:
        raise HTTPException(status_code=401, detail="Invalid secret")
    
    today = date.today()
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
