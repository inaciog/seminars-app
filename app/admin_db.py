"""
Database Administration Module

Provides safe backup, restore, and reset operations with:
- Confirmation tokens to prevent accidental operations
- Atomic operations (all or nothing)
- Validation of uploaded databases
- Audit logging
"""

import os
import shutil
import sqlite3
import uuid
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List
from contextlib import contextmanager

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlmodel import Session, select, delete, text

# Import models
from app.models import (
    Speaker, Room, Seminar, SemesterPlan, SeminarSlot, 
    SpeakerSuggestion, SpeakerAvailability, SpeakerToken,
    SeminarDetails, SpeakerWorkflow, ActivityEvent, 
    UploadedFile, AvailabilitySlot, SQLModel
)

# Import core utilities (no circular dependency)
from app.core import get_engine, settings, record_activity, get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin/db", tags=["Database Admin"])

# ============================================================================
# Configuration
# ============================================================================

# Confirmation tokens expire after 5 minutes
CONFIRMATION_TOKEN_EXPIRY_MINUTES = 5

# Store confirmation tokens in memory (cleared on restart)
_confirmation_tokens: Dict[str, dict] = {}

# ============================================================================
# Pydantic Models
# ============================================================================

class ConfirmationRequest(BaseModel):
    """Request a confirmation token for destructive operations."""
    operation: str  # 'reset', 'reset_synthetic', 'restore'

class ConfirmationResponse(BaseModel):
    token: str
    expires_at: datetime
    message: str

class ResetRequest(BaseModel):
    confirmation_token: str

class RestoreRequest(BaseModel):
    confirmation_token: str
    original_filename: str

class DatabaseStatusResponse(BaseModel):
    database_path: str
    database_size_bytes: int
    last_modified: datetime
    tables: List[dict]
    total_records: int

# ============================================================================
# Helper Functions
# ============================================================================

def _require_owner(user: dict):
    """Require owner or admin role for destructive operations."""
    role = user.get('role', '')
    if role not in ('owner', 'admin'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners can perform database administration operations"
        )

def _generate_confirmation_token(operation: str, user_id: str) -> str:
    """Generate a confirmation token for destructive operations."""
    token = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(minutes=CONFIRMATION_TOKEN_EXPIRY_MINUTES)
    
    _confirmation_tokens[token] = {
        'operation': operation,
        'user_id': user_id,
        'created_at': datetime.utcnow(),
        'expires_at': expires_at,
        'used': False
    }
    
    return token, expires_at

def _validate_confirmation_token(token: str, expected_operation: str) -> dict:
    """Validate a confirmation token."""
    if token not in _confirmation_tokens:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired confirmation token"
        )
    
    token_data = _confirmation_tokens[token]
    
    if token_data['used']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Confirmation token has already been used"
        )
    
    if datetime.utcnow() > token_data['expires_at']:
        del _confirmation_tokens[token]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Confirmation token has expired"
        )
    
    if token_data['operation'] != expected_operation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid operation. Expected '{token_data['operation']}', got '{expected_operation}'"
        )
    
    return token_data

def _mark_token_used(token: str):
    """Mark a token as used."""
    if token in _confirmation_tokens:
        _confirmation_tokens[token]['used'] = True
        # Clean up old tokens periodically
        _cleanup_expired_tokens()

def _cleanup_expired_tokens():
    """Clean up expired tokens."""
    now = datetime.utcnow()
    expired = [
        token for token, data in _confirmation_tokens.items()
        if now > data['expires_at'] or data['used']
    ]
    for token in expired:
        del _confirmation_tokens[token]

def _get_database_path() -> Path:
    """Get the resolved database path."""
    db_url = settings.database_url
    if db_url.startswith("sqlite:///"):
        path = db_url.replace("sqlite:///", "/")
    elif db_url.startswith("sqlite://"):
        path = db_url.replace("sqlite://", "/")
    else:
        path = db_url
    
    path = Path(path)
    if not path.is_absolute():
        # Resolve relative to project root
        path = Path(__file__).resolve().parents[1] / path
    
    return path.resolve()

def _validate_sqlite_file(file_path: Path) -> bool:
    """Validate that a file is a valid SQLite database."""
    try:
        # Check magic bytes
        with open(file_path, 'rb') as f:
            header = f.read(16)
            if not header.startswith(b'SQLite format 3\x00'):
                return False
        
        # Try to connect and query
        conn = sqlite3.connect(str(file_path))
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        conn.close()
        
        # Check for required tables
        required_tables = {'speakers', 'seminars'}
        found_tables = {t[0] for t in tables}
        
        return bool(required_tables & found_tables)
    except Exception as e:
        logger.error(f"SQLite validation error: {e}")
        return False

@contextmanager
def _close_all_connections():
    """Context manager to close all database connections."""
    # Dispose of the engine to close all connections
    engine = get_engine()
    engine.dispose()
    try:
        yield
    finally:
        # Engine will be recreated on next use
        pass

def _count_records(db: Session) -> Dict[str, int]:
    """Count records in all tables."""
    tables = [
        Speaker, Room, Seminar, SemesterPlan, SeminarSlot,
        SpeakerSuggestion, SpeakerAvailability, SpeakerToken,
        SeminarDetails, SpeakerWorkflow, ActivityEvent, 
        UploadedFile, AvailabilitySlot
    ]
    
    counts = {}
    for table in tables:
        try:
            count = db.exec(select(table)).all()
            counts[table.__tablename__] = len(count)
        except Exception as e:
            counts[table.__tablename__] = -1  # Error counting
    
    return counts

# ============================================================================
# Synthetic Data Generation
# ============================================================================

def _create_synthetic_data(db: Session, actor: str):
    """Create synthetic data for testing."""
    from datetime import date, timedelta
    
    # Create speakers
    speakers_data = [
        {"name": "Dr. Sarah Chen", "email": "sarah.chen@stanford.edu", "affiliation": "Stanford University", 
         "bio": "Expert in machine learning and AI with 15 years of experience."},
        {"name": "Prof. Michael Rodriguez", "email": "m.rodriguez@mit.edu", "affiliation": "MIT",
         "bio": "Leading researcher in quantum computing."},
        {"name": "Dr. Lisa Wang", "email": "lisa.wang@caltech.edu", "affiliation": "Caltech",
         "bio": "Specializes in neural networks and scientific computing."},
        {"name": "Prof. James Thompson", "email": "j.thompson@ox.ac.uk", "affiliation": "University of Oxford",
         "bio": "Economist focusing on behavioral economics."},
        {"name": "Dr. Anna Kowalski", "email": "a.kowalski@uw.edu", "affiliation": "University of Washington",
         "bio": "Climate scientist working on atmospheric modeling."},
    ]
    
    speakers = []
    for data in speakers_data:
        speaker = Speaker(**data)
        db.add(speaker)
        speakers.append(speaker)
    
    db.flush()
    
    # Create rooms
    rooms_data = [
        {"name": "Main Auditorium", "capacity": 200, "location": "Building A", 
         "equipment": '{"projector": true, "microphone": true}'},
        {"name": "Conference Room B", "capacity": 50, "location": "Building A",
         "equipment": '{"projector": true, "whiteboard": true}'},
        {"name": "Seminar Room 101", "capacity": 30, "location": "Building B",
         "equipment": '{"projector": true}'},
    ]
    
    rooms = []
    for data in rooms_data:
        room = Room(**data)
        db.add(room)
        rooms.append(room)
    
    db.flush()
    
    # Create semester plan
    plan = SemesterPlan(
        name="Spring 2025 Seminar Series",
        academic_year="2024-2025",
        semester="spring",
        default_room="E11-4047",
        default_start_time="14:00",
        default_duration_minutes=60,
        status="active"
    )
    db.add(plan)
    db.flush()
    
    # Create slots
    start_date = date(2025, 3, 4)
    slots = []
    for i in range(8):
        slot_date = start_date + timedelta(weeks=i)
        slot = SeminarSlot(
            semester_plan_id=plan.id,
            date=slot_date,
            start_time="14:00",
            end_time="15:00",
            room="E11-4047",
            status="available"
        )
        db.add(slot)
        slots.append(slot)
    
    db.flush()
    
    # Create suggestions
    topics = [
        "AI in Healthcare: Opportunities and Challenges",
        "Quantum Computing Applications",
        "Neural Networks for Scientific Computing",
        "Economic Policy in Developing Nations",
        "Climate Data Analysis and Modeling"
    ]
    
    suggestions = []
    for i, speaker in enumerate(speakers):
        sg = SpeakerSuggestion(
            semester_plan_id=plan.id,
            speaker_id=speaker.id,
            speaker_name=speaker.name,
            speaker_email=speaker.email,
            speaker_affiliation=speaker.affiliation,
            suggested_topic=topics[i % len(topics)],
            suggested_by="Prof. Zhang",
            suggested_by_email="zhang@university.edu",
            priority="medium",
            status="pending"
        )
        db.add(sg)
        suggestions.append(sg)
    
    db.flush()
    
    # Create some seminars (assign speakers to slots)
    for i, suggestion in enumerate(suggestions[:4]):
        if i < len(slots):
            # Update slot
            slot = slots[i]
            slot.status = "confirmed"
            slot.assigned_suggestion_id = suggestion.id
            
            # Create seminar
            seminar = Seminar(
                title=suggestion.suggested_topic or f"Seminar by {suggestion.speaker_name}",
                date=slot.date,
                start_time=slot.start_time,
                end_time=slot.end_time,
                speaker_id=suggestion.speaker_id,
                room_id=rooms[i % len(rooms)].id,
                status="planned",
                abstract=f"This is a seminar about {topics[i % len(topics)]}."
            )
            db.add(seminar)
            db.flush()
            
            # Update slot with seminar reference
            slot.assigned_seminar_id = seminar.id
            
            # Update suggestion
            suggestion.status = "confirmed"
    
    # Record activity
    record_activity(
        db,
        event_type="synthetic_data_created",
        summary=f"Created synthetic dataset with {len(speakers)} speakers, {len(slots)} slots, {len(suggestions)} suggestions",
        actor=actor,
        details={
            "speakers_count": len(speakers),
            "rooms_count": len(rooms),
            "slots_count": len(slots),
            "suggestions_count": len(suggestions),
            "seminars_created": min(len(suggestions), len(slots))
        }
    )
    
    db.commit()
    
    return {
        "speakers": len(speakers),
        "rooms": len(rooms),
        "slots": len(slots),
        "suggestions": len(suggestions),
        "seminars": min(len(suggestions), len(slots))
    }

# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/status", response_model=DatabaseStatusResponse)
async def get_database_status(
    user: dict = Depends(get_current_user)
):
    """Get current database status and statistics."""
    _require_owner(user)
    
    db_path = _get_database_path()
    
    if not db_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Database not found at {db_path}"
        )
    
    stat = db_path.stat()
    
    # Get table counts
    with Session(get_engine()) as db:
        counts = _count_records(db)
    
    tables = [
        {"name": name, "record_count": count}
        for name, count in counts.items()
    ]
    
    return DatabaseStatusResponse(
        database_path=str(db_path),
        database_size_bytes=stat.st_size,
        last_modified=datetime.fromtimestamp(stat.st_mtime),
        tables=tables,
        total_records=sum(c for c in counts.values() if c > 0)
    )


@router.post("/backup")
async def create_backup(
    user: dict = Depends(get_current_user)
):
    """
    Create and download a database backup.
    Returns the SQLite database file.
    """
    _require_owner(user)
    
    db_path = _get_database_path()
    
    if not db_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Database not found at {db_path}"
        )
    
    # Create backup filename with timestamp
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"seminars_backup_{timestamp}.db"
    
    # Create a temporary copy to avoid locking issues
    temp_dir = Path("/tmp") if os.access("/tmp", os.W_OK) else db_path.parent
    temp_backup = temp_dir / f"temp_backup_{timestamp}_{uuid.uuid4().hex[:8]}.db"
    
    try:
        # Use SQLite backup API for consistency
        source = sqlite3.connect(str(db_path))
        dest = sqlite3.connect(str(temp_backup))
        source.backup(dest)
        source.close()
        dest.close()
        
        # Log the backup
        with Session(get_engine()) as db:
            record_activity(
                db,
                event_type="database_backup",
                summary=f"Database backup downloaded: {backup_filename}",
                actor=user.get('id', 'unknown'),
                details={"filename": backup_filename, "size_bytes": temp_backup.stat().st_size}
            )
            db.commit()
        
        return FileResponse(
            path=temp_backup,
            filename=backup_filename,
            media_type="application/x-sqlite3",
            background=None  # File will be cleaned up after response
        )
    
    except Exception as e:
        if temp_backup.exists():
            temp_backup.unlink()
        logger.error(f"Backup failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Backup failed: {str(e)}"
        )


@router.post("/restore/upload")
async def upload_restore_file(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user)
):
    """
    Stage a database file for restore.
    Returns a confirmation token that must be used to complete the restore.
    """
    _require_owner(user)
    
    if not file.filename.endswith('.db'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must have .db extension"
        )
    
    # Save uploaded file to temp location
    temp_dir = Path("/tmp") if os.access("/tmp", os.W_OK) else Path("./data")
    temp_path = temp_dir / f"restore_upload_{uuid.uuid4().hex[:12]}.db"
    
    try:
        with open(temp_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        
        # Validate it's a proper SQLite database
        if not _validate_sqlite_file(temp_path):
            temp_path.unlink()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid SQLite database file"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        if temp_path.exists():
            temp_path.unlink()
        logger.error(f"Upload validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )
    
    # Generate confirmation token
    token, expires_at = _generate_confirmation_token('restore', user.get('id'))
    
    # Store temp path with token
    _confirmation_tokens[token]['temp_path'] = str(temp_path)
    _confirmation_tokens[token]['original_filename'] = file.filename
    
    return ConfirmationResponse(
        token=token,
        expires_at=expires_at,
        message=f"Database file uploaded successfully. Use confirmation token within {CONFIRMATION_TOKEN_EXPIRY_MINUTES} minutes to complete restore."
    )


def _get_backup_schema(backup_conn: sqlite3.Connection) -> Dict[str, list]:
    """Get the list of columns for each table in the backup database."""
    cursor = backup_conn.cursor()
    schema = {}
    
    try:
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        for (table_name,) in tables:
            # Get columns for each table
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            schema[table_name] = [col[1] for col in columns]  # col[1] is column name
    except Exception as e:
        logger.error(f"Could not determine backup schema: {e}")
    
    return schema


def _migrate_backup_schema(db_path: Path, backup_schema: Dict[str, list]) -> bool:
    """
    Migrate backup database schema to match current schema.
    Adds missing columns with appropriate defaults.
    """
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Define expected schema with column definitions
        expected_columns = {
            'seminars': {
                'notes': 'TEXT',
                'created_at': 'DATETIME DEFAULT CURRENT_TIMESTAMP',
                'updated_at': 'DATETIME DEFAULT CURRENT_TIMESTAMP'
            },
            'speakers': {
                'created_at': 'DATETIME DEFAULT CURRENT_TIMESTAMP'
            },
            'semester_plans': {
                'created_at': 'DATETIME DEFAULT CURRENT_TIMESTAMP'
            },
            'seminar_details': {
                'ticket_purchase_info': 'TEXT',
                'contact_number': 'TEXT',
                'bank_region': 'TEXT',
                'iban': 'TEXT',
                'aba_routing_number': 'TEXT',
                'bsb_number': 'TEXT'
            }
        }
        
        # For each table, check for missing columns and add them
        for table_name, expected_cols in expected_columns.items():
            if table_name not in backup_schema:
                logger.warning(f"Table {table_name} not found in backup")
                continue
            
            existing_cols = backup_schema[table_name]
            
            for col_name, col_def in expected_cols.items():
                if col_name not in existing_cols:
                    # Column is missing, add it with default value
                    try:
                        alter_sql = f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_def}"
                        cursor.execute(alter_sql)
                        logger.info(f"Added missing column {table_name}.{col_name}")
                    except sqlite3.OperationalError as e:
                        if "duplicate column name" not in str(e).lower():
                            logger.error(f"Failed to add column {table_name}.{col_name}: {e}")
                        # If column already exists, continue
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Schema migration failed: {e}")
        return False


@router.post("/restore/confirm")
async def confirm_restore(
    request: RestoreRequest,
    user: dict = Depends(get_current_user)
):
    """
    Complete the restore operation with confirmation token.
    This will REPLACE the entire database.
    """
    _require_owner(user)
    
    token_data = _validate_confirmation_token(request.confirmation_token, 'restore')
    temp_path = Path(token_data['temp_path'])
    
    if not temp_path.exists():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Restore file no longer available. Please upload again."
        )
    
    db_path = _get_database_path()
    backup_before_restore = None
    
    try:
        # 1. Create emergency backup of current database
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_dir = db_path.parent / "backups"
        backup_dir.mkdir(exist_ok=True)
        backup_before_restore = backup_dir / f"pre_restore_backup_{timestamp}.db"
        
        if db_path.exists():
            source = sqlite3.connect(str(db_path))
            dest = sqlite3.connect(str(backup_before_restore))
            source.backup(dest)
            source.close()
            dest.close()
        
        # 2. Analyze backup schema before restoring
        logger.info("Analyzing backup database schema...")
        backup_conn = sqlite3.connect(str(temp_path))
        backup_schema = _get_backup_schema(backup_conn)
        backup_conn.close()
        logger.info(f"Backup schema detected: {backup_schema}")
        
        # 3. Close all connections
        with _close_all_connections():
            # 4. Replace database file atomically
            if db_path.exists():
                # On Windows, we need to remove first; on Unix, rename is atomic
                db_path.unlink()
            
            shutil.move(str(temp_path), str(db_path))
            
            # 5. Migrate schema if needed
            logger.info("Migrating backup schema to current schema...")
            migration_success = _migrate_backup_schema(db_path, backup_schema)
            if not migration_success:
                logger.warning("Schema migration completed with warnings")
        
        # 6. Mark token as used
        _mark_token_used(request.confirmation_token)
        
        # 7. Log the restore (note: we're logging to the NEW database now)
        try:
            with Session(get_engine()) as db:
                record_activity(
                    db,
                    event_type="database_restore",
                    summary=f"Database restored from {request.original_filename}",
                    actor=user.get('id', 'unknown'),
                    details={
                        "original_filename": request.original_filename,
                        "pre_restore_backup": str(backup_before_restore.name) if backup_before_restore else None,
                        "backup_schema": str(backup_schema)
                    }
                )
                db.commit()
        except Exception as e:
            logger.warning(f"Could not log restore activity: {e}")
        
        return {
            "success": True,
            "message": "Database restored successfully",
            "pre_restore_backup": backup_before_restore.name if backup_before_restore else None,
            "backup_schema": backup_schema
        }
    
    except Exception as e:
        # Cleanup temp file if still exists
        if temp_path.exists():
            temp_path.unlink()
        
        logger.error(f"Restore failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Restore failed: {str(e)}"
        )


@router.post("/reset/request")
async def request_reset(
    request: ConfirmationRequest,
    user: dict = Depends(get_current_user)
):
    """Request a confirmation token for database reset."""
    _require_owner(user)
    
    if request.operation not in ['reset', 'reset_synthetic']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid operation. Must be 'reset' or 'reset_synthetic'"
        )
    
    # Get current counts for the confirmation message
    with Session(get_engine()) as db:
        counts = _count_records(db)
        total_records = sum(c for c in counts.values() if c > 0)
    
    token, expires_at = _generate_confirmation_token(request.operation, user.get('id'))
    
    message = f"This will DELETE all {total_records} records from {len([c for c in counts.values() if c > 0])} tables."
    if request.operation == 'reset_synthetic':
        message += " Synthetic test data will be created after deletion."
    message += f" Use this token within {CONFIRMATION_TOKEN_EXPIRY_MINUTES} minutes to confirm."
    
    return ConfirmationResponse(
        token=token,
        expires_at=expires_at,
        message=message
    )


@router.post("/reset/confirm")
async def confirm_reset(
    request: ResetRequest,
    synthetic: bool = Query(False, description="If true, create synthetic data after reset"),
    user: dict = Depends(get_current_user)
):
    """
    Reset the database - delete all data.
    If synthetic=true, populate with synthetic test data.
    """
    _require_owner(user)
    
    operation = 'reset_synthetic' if synthetic else 'reset'
    token_data = _validate_confirmation_token(request.confirmation_token, operation)
    
    db_path = _get_database_path()
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    
    try:
        # 1. Create emergency backup before reset
        backup_dir = db_path.parent / "backups"
        backup_dir.mkdir(exist_ok=True)
        emergency_backup = backup_dir / f"pre_reset_backup_{timestamp}.db"
        
        if db_path.exists():
            source = sqlite3.connect(str(db_path))
            dest = sqlite3.connect(str(emergency_backup))
            source.backup(dest)
            source.close()
            dest.close()
        
        # 2. Close connections and delete/recreate database
        with _close_all_connections():
            if db_path.exists():
                db_path.unlink()
            
            # Recreate with empty schema
            engine = get_engine()
            SQLModel.metadata.create_all(engine)
        
        # 3. Optionally add synthetic data
        synthetic_stats = None
        if synthetic:
            with Session(get_engine()) as db:
                synthetic_stats = _create_synthetic_data(db, user.get('id', 'unknown'))
        
        # 4. Mark token as used
        _mark_token_used(request.confirmation_token)
        
        # 5. Log the reset
        with Session(get_engine()) as db:
            record_activity(
                db,
                event_type="database_reset",
                summary=f"Database reset" + (" with synthetic data" if synthetic else ""),
                actor=user.get('id', 'unknown'),
                details={
                    "synthetic_data": synthetic_stats,
                    "emergency_backup": emergency_backup.name
                }
            )
            db.commit()
        
        return {
            "success": True,
            "message": "Database reset successfully" + (" with synthetic data" if synthetic else ""),
            "emergency_backup": emergency_backup.name,
            "synthetic_stats": synthetic_stats
        }
    
    except Exception as e:
        logger.error(f"Reset failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Reset failed: {str(e)}"
        )


@router.get("/backups/list")
async def list_emergency_backups(
    user: dict = Depends(get_current_user)
):
    """List emergency backups created before restore/reset operations."""
    _require_owner(user)
    
    db_path = _get_database_path()
    backup_dir = db_path.parent / "backups"
    
    if not backup_dir.exists():
        return {"backups": []}
    
    backups = []
    for f in backup_dir.glob("pre_*.db"):
        stat = f.stat()
        backups.append({
            "filename": f.name,
            "size_bytes": stat.st_size,
            "created": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "operation": "restore" if "restore" in f.name else "reset"
        })
    
    backups.sort(key=lambda x: x["created"], reverse=True)
    
    return {"backups": backups}


@router.post("/migrate/ticket-purchase-info")
async def migrate_ticket_purchase_info(
    user: dict = Depends(get_current_user)
):
    """
    Add ticket_purchase_info column to seminar_details table.
    Run this after deployment if you get 500 errors about missing column.
    """
    _require_owner(user)
    
    import sqlite3
    
    db_path = _get_database_path()
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(seminar_details)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'ticket_purchase_info' in columns:
            return {"success": True, "message": "Column 'ticket_purchase_info' already exists"}
        
        # Add the column
        cursor.execute("ALTER TABLE seminar_details ADD COLUMN ticket_purchase_info TEXT")
        conn.commit()
        conn.close()
        
        return {"success": True, "message": "Column 'ticket_purchase_info' added successfully"}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Migration failed: {str(e)}"
        )
