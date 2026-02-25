"""
Seminars App - Unified Auth Integration

A standalone seminar management system that integrates with the unified
authentication service (inacio-auth.fly.dev).
"""

import os
import json
import subprocess
from urllib.parse import quote
import uuid
import shutil
import logging
import time
from datetime import datetime, date as date_type, timedelta
from pathlib import Path
from typing import Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, Request, UploadFile, File, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload

# Import all models from models module
from app.models import (
    SQLModel, Speaker, Room, Seminar, SemesterPlan, SeminarSlot,
    SpeakerSuggestion, SpeakerAvailability, SpeakerToken,
    SeminarDetails, SpeakerWorkflow, ActivityEvent,
    UploadedFile, AvailabilitySlot
)

# Import core utilities
from app.core import settings, get_engine, get_db, record_activity, verify_token, get_current_user, create_editor_token
from pydantic import BaseModel, ConfigDict, field_validator, model_validator
from pydantic_settings import BaseSettings

# Import logging configuration
from app.logging_config import init_logging, log_audit, log_request

# Import templates
from app.templates import (
    get_invalid_token_html,
    get_external_header_with_logos,
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
# Database Models Section
# ============================================================================

# Note: Models are defined in app/models.py
# Core utilities (settings, get_engine, record_activity) are in app/core.py

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
    notes: Optional[str] = None

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
    notes: Optional[str] = None
    speaker: Optional[SpeakerResponse] = None
    room: Optional[str]  # Just the room name, not full object
    
    @field_validator('room', mode='before')
    @classmethod
    def extract_room_name(cls, v):
        if v is None:
            return None
        if isinstance(v, Room):
            return v.name
        return str(v) if v else None

# Semester Planning Pydantic Models
class SemesterPlanCreate(BaseModel):
    name: str
    academic_year: str = ""
    semester: str = ""
    default_room: str = "TBD"
    default_start_time: str = "14:00"
    default_duration_minutes: int = 60
    notes: Optional[str] = None

class SemesterPlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    academic_year: str = ""
    semester: str = ""
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
    room: Optional[str] = None
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
    ticket_purchase_info: Optional[str] = None
    
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
    ticket_purchase_info: Optional[str]
    updated_at: datetime

class SpeakerWorkflowUpdate(BaseModel):
    request_available_dates_sent: Optional[bool] = None
    availability_dates_received: Optional[bool] = None
    speaker_notified_of_date: Optional[bool] = None
    meal_ok: Optional[bool] = None
    guesthouse_hotel_reserved: Optional[bool] = None
    proposal_submitted: Optional[bool] = None
    proposal_approved: Optional[bool] = None

class ActivityEventResponse(BaseModel):
    id: int
    semester_plan_id: Optional[int]
    event_type: str
    summary: str
    entity_type: Optional[str]
    entity_id: Optional[int]
    actor: Optional[str]
    details: Optional[dict]
    created_at: datetime

# ============================================================================
# Auth
# ============================================================================

async def require_auth(request: Request, call_next):
    """Middleware to check auth on HTML routes."""
    path = request.url.path
    
    # Skip API routes, static files, and React assets
    if path.startswith("/api/") or path.startswith("/static/") or path.startswith("/assets/") or path.startswith("/img/"):
        return await call_next(request)
    
    # Skip public pages
    if path == "/public":
        return await call_next(request)
    
    # Skip speaker token pages and faculty suggestion form (public access)
    if path.startswith("/speaker/") or path.startswith("/faculty/"):
        return await call_next(request)
    
    # Skip root path - let frontend handle authentication
    # Frontend will show login screen with editor password option
    if path == "/" or path == "/index.html":
        return await call_next(request)
    
    # Check for token
    token = request.query_params.get("token") or request.cookies.get("token")
    
    if not token or not verify_token(token):
        return_url = f"{settings.app_url}{request.url.path}"
        return RedirectResponse(
            f"{settings.auth_service_url}/login?returnTo={return_url}"
        )
    
    return await call_next(request)

def get_or_create_workflow(db: Session, suggestion_id: int) -> SpeakerWorkflow:
    stmt = select(SpeakerWorkflow).where(SpeakerWorkflow.suggestion_id == suggestion_id)
    workflow = db.exec(stmt).first()
    if workflow:
        return workflow
    workflow = SpeakerWorkflow(suggestion_id=suggestion_id)
    db.add(workflow)
    db.flush()
    return workflow

def build_speaker_status(workflow: Optional[SpeakerWorkflow], suggestion: SpeakerSuggestion) -> dict:
    """Build simplified speaker status with 4-step flow."""
    if not workflow:
        return {
            "code": "waiting_availability",
            "title": "Waiting for Date Availability",
            "message": "Please submit your available dates using the availability link provided in our email.",
            "step": 1,
        }
    
    # Step 1: Waiting for availability (if availability not received yet)
    if not workflow.availability_dates_received:
        return {
            "code": "waiting_availability",
            "title": "Waiting for Date Availability",
            "message": "Please submit your available dates using the availability link provided in our email.",
            "step": 1,
        }
    
    # Step 2: Date assigned (availability received but proposal not submitted)
    if workflow.availability_dates_received and not workflow.proposal_submitted:
        return {
            "code": "date_assigned",
            "title": "Date Assigned",
            "message": "Your seminar date has been assigned. Please submit your seminar information and proposal.",
            "step": 2,
        }
    
    # Step 3: Information submitted (proposal submitted but not approved)
    if workflow.proposal_submitted and not workflow.proposal_approved:
        return {
            "code": "info_submitted",
            "title": "Information Submitted",
            "message": "Your proposal has been submitted and is currently under review.",
            "step": 3,
        }
    
    # Step 4: Proposal approved
    if workflow.proposal_approved:
        return {
            "code": "proposal_approved",
            "title": "Proposal Approved",
            "message": "Your proposal has been approved. You can now purchase your travel tickets.",
            "step": 4,
        }
    
    return {
        "code": "waiting_availability",
        "title": "Waiting for Date Availability",
        "message": "Please submit your available dates using the availability link provided in our email.",
        "step": 1,
    }

def refresh_fallback_mirror(db: Session):
    mirror_dir = Path(settings.fallback_mirror_dir)
    if not mirror_dir.is_absolute():
        # Resolve relative to project root (parent of app/) so it works regardless of cwd
        mirror_dir = Path(__file__).resolve().parents[1] / mirror_dir
    mirror_dir.mkdir(parents=True, exist_ok=True)

    plans = db.exec(select(SemesterPlan).order_by(SemesterPlan.created_at.desc())).all()
    suggestions = db.exec(select(SpeakerSuggestion).order_by(SpeakerSuggestion.created_at.desc())).all()
    slots = db.exec(select(SeminarSlot).order_by(SeminarSlot.date.desc())).all()
    seminars = db.exec(select(Seminar).order_by(Seminar.date.asc())).all()
    files = db.exec(select(UploadedFile).order_by(UploadedFile.uploaded_at.desc())).all()
    activities = db.exec(select(ActivityEvent).order_by(ActivityEvent.created_at.desc()).limit(200)).all()
    speakers = db.exec(select(Speaker).order_by(Speaker.name)).all()
    all_details = {d.seminar_id: d for d in db.exec(select(SeminarDetails)).all()}

    def esc(value: Optional[str]) -> str:
        text = value or ""
        return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    def safe_filename(name: str) -> str:
        s = "".join(c for c in (name or "file") if c.isalnum() or c in "._- ")
        return s[:80] if s else "file"

    ts = datetime.utcnow().isoformat()

    # Resolve uploads dir (may be relative)
    uploads_base = Path(settings.uploads_dir)
    if not uploads_base.is_absolute():
        uploads_base = Path(__file__).resolve().parents[1] / uploads_base

    # Copy uploaded files to mirror for recovery (clear and re-copy to remove deleted files)
    files_dir = mirror_dir / "files"
    if files_dir.exists():
        for p in files_dir.iterdir():
            if p.is_file():
                try:
                    p.unlink()
                except OSError:
                    pass
    files_dir.mkdir(exist_ok=True)
    file_mirror_names: dict[int, str] = {}
    for f in files:
        src = uploads_base / f.storage_filename
        if src.exists():
            ext = Path(f.original_filename or "").suffix or ""
            mirror_name = f"{f.id}_{safe_filename(f.original_filename or 'file')}{ext}"
            dst = files_dir / mirror_name
            try:
                shutil.copy2(src, dst)
                file_mirror_names[f.id] = f"files/{mirror_name}"
            except Exception as e:
                logger.warning(f"Could not copy file {f.id} to fallback mirror: {e}")

    # -------------------------------------------------------------------------
    # File 1: recovery.html - Human-readable backup for emergency recovery
    # Full seminar and speaker content: abstract, bio, travel, etc.
    # -------------------------------------------------------------------------
    recovery_sections = []

    # Seminars (full content)
    for s in seminars:
        speaker = s.speaker
        room = s.room
        details = all_details.get(s.id)
        speaker_name = speaker.name if speaker else "TBD"
        speaker_aff = speaker.affiliation or "" if speaker else ""
        speaker_email = speaker.email or "" if speaker else ""
        room_name = room.name if room else "TBD"

        parts = [
            f"<h2>{esc(s.title)}</h2>",
            f"<p><strong>Date:</strong> {s.date.isoformat()} | <strong>Time:</strong> {s.start_time or ''}-{s.end_time or ''} | <strong>Room:</strong> {esc(room_name)} | <strong>Status:</strong> {esc(s.status)}</p>",
            f"<p><strong>Speaker:</strong> {esc(speaker_name)} ({esc(speaker_aff)})" + (f" &lt;{esc(speaker_email)}&gt;" if speaker_email else "") + "</p>",
        ]
        if s.abstract:
            parts.append(f"<h3>Abstract</h3><p>{esc(s.abstract)}</p>")
        if s.paper_title:
            parts.append(f"<p><strong>Paper title:</strong> {esc(s.paper_title)}</p>")
        if details:
            detail_parts = []
            if details.check_in_date or details.check_out_date:
                detail_parts.append(f"Travel: {details.check_in_date or '?'} to {details.check_out_date or '?'}")
            if details.departure_city:
                detail_parts.append(f"Departure: {esc(details.departure_city)}")
            if details.travel_method:
                detail_parts.append(f"Method: {esc(details.travel_method)}")
            if details.needs_accommodation is not None:
                detail_parts.append(f"Accommodation: {'Yes' if details.needs_accommodation else 'No'}")
            if details.accommodation_nights:
                detail_parts.append(f"Nights: {details.accommodation_nights}")
            if details.payment_email:
                detail_parts.append(f"Payment email: {esc(details.payment_email)}")
            if details.beneficiary_name:
                detail_parts.append(f"Beneficiary: {esc(details.beneficiary_name)}")
            if details.bank_name:
                detail_parts.append(f"Bank: {esc(details.bank_name)}")
            if detail_parts:
                parts.append(f"<h3>Logistics</h3><p>{' | '.join(detail_parts)}</p>")

        # Files for this seminar (with links to mirrored copies)
        sem_files = [f for f in files if f.seminar_id == s.id]
        if sem_files:
            file_links = []
            for f in sem_files:
                if f.id in file_mirror_names:
                    file_links.append(f'<a href="{quote(file_mirror_names[f.id], safe="/")}">{esc(f.original_filename)}</a>')
                else:
                    file_links.append(esc(f.original_filename))
            parts.append(f"<p><strong>Files:</strong> {', '.join(file_links)}</p>")

        section_content = "\n".join(parts)
        recovery_sections.append(f'<div class="seminar-block">{section_content}</div>')

    recovery_seminars_html = "\n\n".join(recovery_sections) if recovery_sections else "<p>No seminars.</p>"

    # Speakers (full content)
    speaker_sections = []
    for sp in speakers:
        parts = [
            f"<h3>{esc(sp.name)}</h3>",
            f"<p><strong>Affiliation:</strong> {esc(sp.affiliation or '-')} | <strong>Email:</strong> {esc(sp.email or '-')}</p>",
        ]
        if sp.website:
            parts.append(f"<p><strong>Website:</strong> {esc(sp.website)}</p>")
        if sp.bio:
            parts.append(f"<p>{esc(sp.bio)}</p>")
        speaker_sections.append("\n".join(parts))

    recovery_speakers_html = "\n<hr>\n".join(speaker_sections) if speaker_sections else "<p>No speakers.</p>"

    # Speaker suggestions (planned speakers)
    sugg_sections = []
    for sg in suggestions:
        sugg_sections.append(
            f"<p><strong>{esc(sg.speaker_name)}</strong> ({esc(sg.speaker_affiliation or '-')}) "
            f"| Plan {sg.semester_plan_id or '-'} | Status: {esc(sg.status)}<br>"
            f"Suggested topic: {esc(sg.suggested_topic or '-')}"
            + (f" | Reason: {esc(sg.reason)}" if sg.reason else "")
            + "</p>"
        )
    recovery_suggestions_html = "\n".join(sugg_sections) if sugg_sections else "<p>No suggestions.</p>"

    # All uploaded files (with links to mirrored copies)
    if files:
        all_file_links = []
        for f in sorted(files, key=lambda x: (x.seminar_id, x.original_filename or "")):
            label = f"{esc(f.original_filename)} (seminar {f.seminar_id})"
            if f.id in file_mirror_names:
                all_file_links.append(f'<a href="{quote(file_mirror_names[f.id], safe="/")}">{label}</a>')
            else:
                all_file_links.append(label)
        recovery_files_html = "<p>" + " | ".join(all_file_links) + "</p>"
    else:
        recovery_files_html = "<p>No uploaded files.</p>"

    recovery_html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Seminars Recovery Backup</title>
<style>body{{font-family:Georgia,serif;margin:24px;max-width:800px;}}h1{{border-bottom:1px solid #ccc;}}h2{{margin-top:1.5em;}}h3{{margin-top:1em;font-size:1em;}}p{{line-height:1.5;}}.seminar-block{{margin-bottom:2em;padding-bottom:1.5em;border-bottom:1px solid #eee;}}</style></head>
<body>
<h1>Seminars Recovery Backup</h1>
<p><em>Human-readable backup for emergency recovery. Generated: {ts} UTC</em></p>
<p>Use this file to recover seminar and speaker information if the app stops working.</p>

<h2>Seminar Series</h2>
{recovery_seminars_html}

<h2>Speakers</h2>
{recovery_speakers_html}

<h2>Speaker Suggestions (Planning)</h2>
{recovery_suggestions_html}

<h2>Uploaded Files</h2>
{recovery_files_html}
</body></html>"""

    (mirror_dir / "recovery.html").write_text(recovery_html, encoding="utf-8")

    # -------------------------------------------------------------------------
    # File 2: changelog.html - Technical/audit tracking
    # Plans, slots, suggestions, activity, files
    # -------------------------------------------------------------------------
    rows_plans = "".join(
        f"<tr><td>{p.id}</td><td>{esc(p.name)}</td><td>{esc(p.status)}</td><td>{esc(p.default_room)}</td></tr>"
        for p in plans
    )
    rows_suggestions = "".join(
        f"<tr><td>{s.id}</td><td>{s.semester_plan_id or ''}</td><td>{esc(s.speaker_name)}</td><td>{esc(s.speaker_affiliation)}</td><td>{esc(s.status)}</td></tr>"
        for s in suggestions
    )
    rows_slots = "".join(
        f"<tr><td>{sl.id}</td><td>{sl.semester_plan_id}</td><td>{sl.date.isoformat()}</td><td>{esc(sl.start_time)}-{esc(sl.end_time)}</td><td>{esc(sl.room)}</td><td>{esc(sl.status)}</td></tr>"
        for sl in slots
    )
    rows_seminars = "".join(
        f"<tr><td>{s.id}</td><td>{esc(s.title)}</td><td>{s.date.isoformat()}</td><td>{esc(s.status)}</td><td>{getattr(s, 'slot_id', '') or ''}</td></tr>"
        for s in seminars
    )
    rows_files = "".join(
        f"<tr><td>{f.id}</td><td>{f.seminar_id}</td><td>{esc(f.original_filename)}</td><td>{esc(f.file_category)}</td><td>{f.uploaded_at.isoformat()}</td></tr>"
        for f in files
    )
    rows_activities = "".join(
        f"<tr><td>{a.created_at.isoformat()}</td><td>{esc(a.event_type)}</td><td>{esc(a.summary)}</td><td>{a.semester_plan_id or ''}</td></tr>"
        for a in activities
    )

    changelog_html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Seminars Changelog &amp; Audit</title>
<style>body{{font-family:Arial,sans-serif;margin:24px;}}table{{border-collapse:collapse;width:100%;margin-bottom:24px;}}th,td{{border:1px solid #ddd;padding:6px 8px;font-size:13px;}}th{{background:#f5f5f5;text-align:left;}}</style></head>
<body>
<h1>Seminars Changelog &amp; Audit</h1>
<p>Generated: {ts} UTC. Tracks plans, slots, suggestions, activity, and files.</p>

<h2>Semester Plans</h2><table><tr><th>ID</th><th>Name</th><th>Status</th><th>Default Room</th></tr>{rows_plans}</table>
<h2>Speaker Suggestions</h2><table><tr><th>ID</th><th>Plan</th><th>Speaker</th><th>Affiliation</th><th>Status</th></tr>{rows_suggestions}</table>
<h2>Slots</h2><table><tr><th>ID</th><th>Plan</th><th>Date</th><th>Time</th><th>Room</th><th>Status</th></tr>{rows_slots}</table>
<h2>Seminars</h2><table><tr><th>ID</th><th>Title</th><th>Date</th><th>Status</th><th>Slot</th></tr>{rows_seminars}</table>
<h2>Files</h2><table><tr><th>ID</th><th>Seminar</th><th>Filename</th><th>Category</th><th>Uploaded At</th></tr>{rows_files}</table>
<h2>Recent Activity</h2><table><tr><th>Time</th><th>Type</th><th>Summary</th><th>Plan</th></tr>{rows_activities}</table>
</body></html>"""

    (mirror_dir / "changelog.html").write_text(changelog_html, encoding="utf-8")

    # index.html links to both
    index_html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Seminars Fallback Mirror</title>
<style>body{{font-family:Arial,sans-serif;margin:24px;}}a{{color:#06c;}}ul{{line-height:2;}}</style></head>
<body>
<h1>Seminars Fallback Mirror</h1>
<p>Generated: {ts} UTC</p>
<ul>
<li><a href="recovery.html"><strong>Recovery</strong></a> — Human-readable backup: seminars (abstract, speaker, logistics), speakers, suggestions. Use for emergency recovery.</li>
<li><a href="changelog.html"><strong>Changelog</strong></a> — Technical tracking: plans, slots, activity, files.</li>
</ul>
</body></html>"""

    (mirror_dir / "index.html").write_text(index_html, encoding="utf-8")

    logger.info(f"Fallback mirror updated at {mirror_dir}")

def ensure_legacy_writes_allowed():
    if settings.feature_semester_plan_v2:
        raise HTTPException(
            status_code=403,
            detail="Legacy write APIs are disabled in V2 mode. Use semester-plan workflows.",
        )

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
    # Build initial fallback mirror snapshot
    with Session(eng) as session:
        try:
            refresh_fallback_mirror(session)
        except Exception as e:
            logger.error(f"Initial fallback mirror generation failed: {e}")
    
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

_APP_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _APP_DIR.parent
FRONTEND_DIST_DIR = _PROJECT_ROOT / "frontend" / "dist"
FRONTEND_ASSETS_DIR = FRONTEND_DIST_DIR / "assets"
IMG_DIR = _PROJECT_ROOT / "img"

# check_dir=False avoids import-time crashes when frontend artifacts are not bundled yet.
app.mount("/assets", StaticFiles(directory=str(FRONTEND_ASSETS_DIR), check_dir=False), name="assets")
if IMG_DIR.exists():
    app.mount("/img", StaticFiles(directory=str(IMG_DIR)), name="img")
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
    """Public page showing all seminars for the current term - academic/professional style."""
    
    # Get current academic year/semester
    today = date_type.today()
    current_year = today.year
    current_month = today.month
    
    # Determine current academic term (Spring: Jan-Jun, Fall: Jul-Dec)
    if current_month <= 6:
        term_name = f"Spring {current_year}"
        start_date = date_type(current_year, 1, 1)
        end_date = date_type(current_year, 6, 30)
    else:
        term_name = f"Fall {current_year}"
        start_date = date_type(current_year, 7, 1)
        end_date = date_type(current_year, 12, 31)
    
    # Get all seminars for the current term, ordered by date
    statement = select(Seminar).options(
        selectinload(Seminar.room),
        selectinload(Seminar.speaker),
        selectinload(Seminar.assigned_slot).selectinload(SeminarSlot.plan)
    ).where(
        Seminar.date >= start_date,
        Seminar.date <= end_date
    ).order_by(Seminar.date)
    
    seminars = db.exec(statement).all()
    
    seminars_html = ""
    for s in seminars:
        speaker = s.speaker
        room = s.room
        
        speaker_name = speaker.name if speaker else "TBD"
        affiliation = speaker.affiliation or "" if speaker else ""
        
        # Get room name with fallback to slot's room or plan's default_room
        room_name = "TBD"
        room_location = ""
        if room:
            room_name = room.name
            room_location = room.location or ""
        elif s.assigned_slot:
            if s.assigned_slot.room:
                room_name = s.assigned_slot.room
            elif s.assigned_slot.plan and s.assigned_slot.plan.default_room:
                room_name = s.assigned_slot.plan.default_room
        
        # Format date: "Mar 15" or "Mar 15-17" for multi-day
        date_str = s.date.strftime("%b %d")
        day_of_week = s.date.strftime("%a")
        
        # Format time
        time_str = s.start_time[:5]  # "14:00" from "14:00:00"
        if s.end_time:
            time_str = f"{s.start_time[:5]}–{s.end_time[:5]}"
        
        # Build seminar row HTML - compact academic style
        seminar_row = f"""
        <tr class="seminar-row">
            <td class="date-cell">
                <div class="day">{day_of_week}</div>
                <div class="date">{date_str}</div>
            </td>
            <td class="time-cell">{time_str}</td>
            <td class="details-cell">
                <div class="title">{s.title}</div>
                <div class="speaker">
                    <span class="speaker-name">{speaker_name}</span>
                    {f'<span class="affiliation">{affiliation}</span>' if affiliation else ''}
                </div>
                {f'<div class="paper">{s.paper_title}</div>' if s.paper_title else ''}
                {f'<div class="abstract-text">{s.abstract}</div>' if s.abstract else ''}
            </td>
            <td class="location-cell">{room_name}</td>
        </tr>
        """
        seminars_html += seminar_row
    
    if not seminars_html:
        seminars_html = """
        <tr>
            <td colspan="4" class="no-seminars">
                No seminars scheduled for this term.
            </td>
        </tr>
        """
    
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Economics Seminars | University of Macau</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            
            :root {{
                --um-blue: #003366;
                --um-dark: #1a1a1a;
                --um-gray: #4a4a4a;
                --um-light: #f5f5f5;
                --um-border: #d0d0d0;
                --um-accent: #0056b3;
            }}
            
            body {{
                font-family: 'Times New Roman', Times, Georgia, serif;
                background: #fff;
                color: var(--um-dark);
                line-height: 1.5;
                min-height: 100vh;
            }}
            
            /* Header with UM branding */
            .header {{
                background: var(--um-blue);
                color: white;
                padding: 0;
                border-bottom: 4px solid #002244;
            }}
            
            .header-top {{
                max-width: 1100px;
                margin: 0 auto;
                padding: 12px 20px;
                display: flex;
                align-items: center;
                gap: 20px;
            }}
            
            .um-logo {{
                font-size: 28px;
                font-weight: bold;
                letter-spacing: 2px;
                font-family: Georgia, serif;
            }}
            
            .um-name {{
                font-size: 14px;
                opacity: 0.9;
                border-left: 1px solid rgba(255,255,255,0.3);
                padding-left: 20px;
                line-height: 1.3;
            }}
            
            .header-bottom {{
                background: #002244;
                padding: 8px 20px;
            }}
            
            .dept-nav {{
                max-width: 1100px;
                margin: 0 auto;
                font-size: 13px;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
            
            .container {{ 
                max-width: 1100px; 
                margin: 0 auto;
                padding: 30px 20px;
            }}
            
            .page-header {{
                margin-bottom: 30px;
                padding-bottom: 15px;
                border-bottom: 2px solid var(--um-blue);
            }}
            
            .page-header h1 {{
                font-size: 28px;
                font-weight: normal;
                color: var(--um-blue);
                margin-bottom: 5px;
                font-family: Georgia, serif;
            }}
            
            .term-badge {{
                display: inline-block;
                font-size: 12px;
                text-transform: uppercase;
                letter-spacing: 1px;
                color: var(--um-gray);
                padding: 4px 12px;
                border: 1px solid var(--um-border);
                margin-top: 8px;
            }}
            
            /* Seminar table - compact academic style */
            .seminars-table {{
                width: 100%;
                border-collapse: collapse;
                font-size: 14px;
            }}
            
            .seminars-table thead {{
                background: var(--um-light);
                border-top: 2px solid var(--um-dark);
                border-bottom: 1px solid var(--um-dark);
            }}
            
            .seminars-table th {{
                text-align: left;
                padding: 10px 12px;
                font-weight: bold;
                font-size: 12px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                color: var(--um-dark);
            }}
            
            .seminars-table td {{
                padding: 16px 12px;
                border-bottom: 1px solid var(--um-border);
                vertical-align: top;
            }}
            
            .seminar-row:hover {{
                background: #fafafa;
            }}
            
            .date-cell {{
                width: 80px;
                text-align: center;
                border-right: 1px solid var(--um-border);
            }}
            
            .date-cell .day {{
                font-size: 11px;
                text-transform: uppercase;
                color: var(--um-gray);
                letter-spacing: 1px;
            }}
            
            .date-cell .date {{
                font-size: 16px;
                font-weight: bold;
                color: var(--um-blue);
            }}
            
            .time-cell {{
                width: 90px;
                font-family: 'Courier New', monospace;
                font-size: 13px;
                color: var(--um-gray);
                border-right: 1px solid var(--um-border);
            }}
            
            .details-cell {{
                padding-left: 20px;
            }}
            
            .details-cell .title {{
                font-size: 16px;
                font-weight: bold;
                color: var(--um-dark);
                margin-bottom: 6px;
                line-height: 1.3;
            }}
            
            .details-cell .speaker {{
                margin-bottom: 4px;
            }}
            
            .speaker-name {{
                font-weight: bold;
                color: var(--um-dark);
            }}
            
            .affiliation {{
                color: var(--um-gray);
                font-style: italic;
                margin-left: 6px;
            }}
            
            .paper {{
                font-style: italic;
                color: var(--um-gray);
                font-size: 13px;
                margin-top: 6px;
                padding-left: 12px;
                border-left: 2px solid var(--um-border);
            }}
            
            .abstract-text {{
                font-size: 13px;
                color: var(--um-gray);
                margin-top: 8px;
                line-height: 1.5;
                text-align: justify;
            }}
            
            .location-cell {{
                width: 120px;
                font-size: 13px;
                color: var(--um-gray);
                text-align: right;
            }}
            
            .no-seminars {{
                text-align: center;
                padding: 40px;
                color: var(--um-gray);
                font-style: italic;
            }}
            
            /* Footer */
            .footer {{
                margin-top: 50px;
                padding: 20px;
                border-top: 1px solid var(--um-border);
                text-align: center;
                font-size: 12px;
                color: var(--um-gray);
            }}
            
            .footer a {{
                color: var(--um-blue);
                text-decoration: none;
            }}
            
            /* Responsive */
            @media (max-width: 768px) {{
                .um-name {{ display: none; }}
                .seminars-table {{ font-size: 13px; }}
                .date-cell {{ width: 60px; }}
                .time-cell {{ width: 70px; }}
                .location-cell {{ width: 80px; }}
                .abstract-text {{ display: none; }}
            }}
        </style>
    </head>
    <body>
        <header class="header">
            <div class="header-top">
                <div class="um-logo">UM</div>
                <div class="um-name">
                    University of Macau<br>
                    <small style="font-size: 11px; opacity: 0.8;">澳門大學</small>
                </div>
            </div>
            <div class="header-bottom">
                <div class="dept-nav">Department of Economics</div>
            </div>
        </header>
        
        <main class="container">
            <div class="page-header">
                <h1>Economics Seminars</h1>
                <div class="term-badge">{term_name}</div>
            </div>
            
            <table class="seminars-table">
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Time</th>
                        <th>Seminar Details</th>
                        <th>Location</th>
                    </tr>
                </thead>
                <tbody>
                    {seminars_html}
                </tbody>
            </table>
        </main>
        
        <footer class="footer">
            <p>Department of Economics, Faculty of Social Sciences, University of Macau</p>
            <p style="margin-top: 5px;">
                <a href="https://www.um.edu.mo">www.um.edu.mo</a> | 
                <a href="mailto:econ@um.edu.mo">econ@um.edu.mo</a>
            </p>
        </footer>
    </body>
    </html>
    """

# Speaker token pages (public, no auth required)
@app.get("/speaker/availability/{token}", response_class=HTMLResponse)
async def speaker_availability_page(token: str, db: Session = Depends(get_db)):
    """Public page for speaker to submit availability. Always updatable (no used_at check)."""
    # Verify token - allow viewing even if previously submitted (speakers can edit anytime)
    statement = select(SpeakerToken).where(
        SpeakerToken.token == token,
        SpeakerToken.expires_at > datetime.utcnow(),
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
    ensure_legacy_writes_allowed()
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
    ensure_legacy_writes_allowed()
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
    require_admin(user)
    ensure_legacy_writes_allowed()
    result = delete_speaker_robust(speaker_id, db)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    refresh_fallback_mirror(db)
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
    require_admin(user)
    result = delete_speaker_robust(speaker_id, db)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    refresh_fallback_mirror(db)
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
    ensure_legacy_writes_allowed()
    db_room = Room(**room.model_dump())
    db.add(db_room)
    db.commit()
    db.refresh(db_room)
    return db_room

@app.delete("/api/rooms/{room_id}")
async def delete_room(room_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    require_admin(user)
    ensure_legacy_writes_allowed()
    result = delete_room_robust(room_id, db)
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["error"])
    refresh_fallback_mirror(db)
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
    statement = select(Seminar).options(
        selectinload(Seminar.room),
        selectinload(Seminar.speaker),
        selectinload(Seminar.assigned_slot).selectinload(SeminarSlot.plan)
    ).order_by(Seminar.date)
    
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
    ensure_legacy_writes_allowed()
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
    ensure_legacy_writes_allowed()
    seminar = db.get(Seminar, seminar_id)
    if not seminar:
        raise HTTPException(status_code=404, detail="Seminar not found")
    
    update_data = update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(seminar, key, value)
    
    seminar.updated_at = datetime.utcnow()
    record_activity(
        db=db,
        event_type="SEMINAR_UPDATED",
        summary=f"Updated seminar '{seminar.title}'",
        entity_type="seminar",
        entity_id=seminar.id,
        actor=user.get("id"),
    )
    db.commit()
    db.refresh(seminar)
    refresh_fallback_mirror(db)
    return seminar

@app.delete("/api/seminars/{seminar_id}")
async def delete_seminar(seminar_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    require_admin(user)
    ensure_legacy_writes_allowed()
    result = delete_seminar_robust(seminar_id, db)
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["error"])
    refresh_fallback_mirror(db)
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
    statement = select(Seminar).options(
        selectinload(Seminar.room),
        selectinload(Seminar.speaker),
        selectinload(Seminar.assigned_slot).selectinload(SeminarSlot.plan)
    ).order_by(Seminar.date)
    
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
    record_activity(
        db=db,
        event_type="SEMINAR_UPDATED",
        summary=f"Updated seminar '{seminar.title}'",
        entity_type="seminar",
        entity_id=seminar.id,
        actor=user.get("id"),
    )
    db.commit()
    db.refresh(seminar)
    refresh_fallback_mirror(db)
    return seminar

@app.delete("/api/v1/seminars/seminars/{seminar_id}")
async def delete_seminar_v1(seminar_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    require_admin(user)
    result = delete_seminar_robust(seminar_id, db)
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["error"])
    refresh_fallback_mirror(db)
    return result

# Seminar details endpoints
@app.get("/api/v1/seminars/seminars/{seminar_id}/details")
async def get_seminar_details_v1(seminar_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    """Get seminar with details."""
    statement = select(Seminar).options(
        selectinload(Seminar.room),
        selectinload(Seminar.speaker)
    ).where(Seminar.id == seminar_id)
    seminar = db.exec(statement).first()
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
    
    # Get room - use seminar's room, or fall back to semester plan's default_room
    room_name = seminar.room.name if seminar.room else None
    default_room = None
    if not room_name:
        # Find the slot this seminar is assigned to
        slot_stmt = select(SeminarSlot).where(SeminarSlot.assigned_seminar_id == seminar_id)
        slot = db.exec(slot_stmt).first()
        if slot and slot.semester_plan_id:
            plan = db.get(SemesterPlan, slot.semester_plan_id)
            if plan:
                default_room = plan.default_room
                room_name = plan.default_room
    
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
        "room": room_name,
        "default_room": default_room,
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
            "ticket_purchase_info": getattr(details, 'ticket_purchase_info', None),
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
    if data.room is not None and data.room.strip() != '':
        # Find or create room by name
        room_stmt = select(Room).where(Room.name == data.room)
        room = db.exec(room_stmt).first()
        if room:
            seminar.room_id = room.id
        else:
            # Create new room
            new_room = Room(name=data.room, location="")
            db.add(new_room)
            db.flush()
            seminar.room_id = new_room.id
    elif data.room is not None and data.room.strip() == '':
        # Clear the room if empty string is sent
        seminar.room_id = None
    
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
    if data.ticket_purchase_info is not None:
        try:
            setattr(details, 'ticket_purchase_info', data.ticket_purchase_info)
        except Exception:
            pass  # Column might not exist yet
    
    details.updated_at = datetime.utcnow()
    seminar.updated_at = datetime.utcnow()
    
    record_activity(
        db=db,
        event_type="SEMINAR_UPDATED",
        summary=f"Updated seminar details for '{seminar.title}'",
        entity_type="seminar",
        entity_id=seminar.id,
        actor=user.get("id"),
    )
    db.commit()
    db.refresh(seminar)
    db.refresh(details)
    refresh_fallback_mirror(db)
    
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
    record_activity(
        db=db,
        event_type="SEMESTER_PLAN_CREATED",
        summary=f"Created semester plan '{db_plan.name}'",
        semester_plan_id=None,
        entity_type="semester_plan",
        actor=user.get("id"),
    )
    db.commit()
    db.refresh(db_plan)
    refresh_fallback_mirror(db)
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
    record_activity(
        db=db,
        event_type="SEMESTER_PLAN_UPDATED",
        summary=f"Updated semester plan '{plan.name}'",
        semester_plan_id=plan.id,
        entity_type="semester_plan",
        entity_id=plan.id,
        actor=user.get("id"),
    )
    db.commit()
    db.refresh(plan)
    refresh_fallback_mirror(db)
    return plan

@app.delete("/api/v1/seminars/semester-plans/{plan_id}")
async def delete_semester_plan(plan_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    require_admin(user)
    result = delete_semester_plan_robust(plan_id, db)
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["error"])
    refresh_fallback_mirror(db)
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
    record_activity(
        db=db,
        event_type="SLOT_CREATED",
        summary=f"Added slot on {db_slot.date.isoformat()} at {db_slot.start_time}",
        semester_plan_id=plan_id,
        entity_type="slot",
        actor=user.get("id"),
    )
    db.commit()
    db.refresh(db_slot)
    refresh_fallback_mirror(db)
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
    refresh_fallback_mirror(db)
    return slot

@app.delete("/api/v1/seminars/slots/{slot_id}")
async def delete_slot(slot_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    require_admin(user)
    result = delete_slot_robust(slot_id, db)
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["error"])
    refresh_fallback_mirror(db)
    return result

@app.post("/api/v1/seminars/slots/{slot_id}/unassign")
async def unassign_slot(slot_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    slot = db.get(SeminarSlot, slot_id)
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")
    
    slot.assigned_seminar_id = None
    slot.status = "available"
    record_activity(
        db=db,
        event_type="SLOT_UNASSIGNED",
        summary=f"Unassigned seminar from slot {slot.date.isoformat()}",
        semester_plan_id=slot.semester_plan_id,
        entity_type="slot",
        entity_id=slot.id,
        actor=user.get("id"),
    )
    db.commit()
    refresh_fallback_mirror(db)
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
    db.flush()
    workflow = SpeakerWorkflow(suggestion_id=db_suggestion.id)
    db.add(workflow)
    record_activity(
        db=db,
        event_type="SPEAKER_SUGGESTED",
        summary=f"Suggested speaker {db_suggestion.speaker_name}",
        semester_plan_id=db_suggestion.semester_plan_id,
        entity_type="speaker_suggestion",
        entity_id=db_suggestion.id,
        actor=user.get("id"),
    )
    db.commit()
    db.refresh(db_suggestion)
    refresh_fallback_mirror(db)
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
    refresh_fallback_mirror(db)
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
    refresh_fallback_mirror(db)
    
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
    require_admin(user)
    result = delete_suggestion_robust(suggestion_id, db)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    refresh_fallback_mirror(db)
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
    workflow = get_or_create_workflow(db, suggestion_id)
    workflow.request_available_dates_sent = True
    workflow.updated_at = datetime.utcnow()
    db.add(workflow)
    record_activity(
        db=db,
        event_type="AVAILABILITY_LINK_CREATED",
        summary=f"Created availability link for {suggestion.speaker_name}",
        semester_plan_id=suggestion.semester_plan_id,
        entity_type="speaker_suggestion",
        entity_id=suggestion.id,
        actor=user.get("id"),
    )
    db.commit()
    refresh_fallback_mirror(db)
    
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
    
    if not suggestion_id and not seminar_id:
        logger.warning("Info token creation failed: seminar_id or suggestion_id is required")
        raise HTTPException(status_code=400, detail="seminar_id or suggestion_id is required")

    seminar = None
    if seminar_id:
        seminar = db.get(Seminar, seminar_id)
        if not seminar:
            logger.warning(f"Info token creation failed: Seminar {seminar_id} not found")
            raise HTTPException(status_code=404, detail="Seminar not found")

    suggestion = None
    if suggestion_id:
        suggestion = db.get(SpeakerSuggestion, suggestion_id)
        if not suggestion:
            logger.warning(f"Info token creation failed: Suggestion {suggestion_id} not found")
            raise HTTPException(status_code=404, detail="Suggestion not found")
    elif seminar_id:
        # 1) Prefer the suggestion explicitly assigned to the seminar's slot
        slot_stmt = select(SeminarSlot).where(SeminarSlot.assigned_seminar_id == seminar_id)
        slot = db.exec(slot_stmt).first()
        if slot and slot.assigned_suggestion_id:
            suggestion = db.get(SpeakerSuggestion, slot.assigned_suggestion_id)

        # 2) Otherwise, try to resolve by seminar speaker_id
        if not suggestion and seminar and seminar.speaker_id:
            suggestion_stmt = select(SpeakerSuggestion).where(
                SpeakerSuggestion.speaker_id == seminar.speaker_id
            ).order_by(SpeakerSuggestion.id.desc())
            suggestion = db.exec(suggestion_stmt).first()

        # 3) As a fallback for manually-created seminars, create a synthetic suggestion
        if not suggestion and seminar:
            speaker = db.get(Speaker, seminar.speaker_id)
            if not speaker:
                raise HTTPException(status_code=404, detail="Seminar speaker not found")

            synthetic = SpeakerSuggestion(
                suggested_by="System",
                speaker_id=speaker.id,
                speaker_name=speaker.name,
                speaker_email=speaker.email,
                speaker_affiliation=speaker.affiliation,
                suggested_topic=seminar.title,
                priority="medium",
                status="confirmed",
                semester_plan_id=slot.semester_plan_id if slot else None
            )
            db.add(synthetic)
            db.commit()
            db.refresh(synthetic)
            suggestion = synthetic

    if not suggestion:
        logger.warning(
            f"Info token creation failed: Unable to resolve suggestion for seminar_id={seminar_id}, suggestion_id={suggestion_id}"
        )
        raise HTTPException(status_code=400, detail="Could not resolve a speaker suggestion for this seminar")
    
    # Create token
    token = generate_token()
    expires_at = datetime.utcnow() + timedelta(days=30)
    
    db_token = SpeakerToken(
        token=token,
        suggestion_id=suggestion.id,
        seminar_id=seminar_id,
        token_type='info',
        expires_at=expires_at
    )
    db.add(db_token)
    workflow = get_or_create_workflow(db, suggestion.id)
    workflow.speaker_notified_of_date = True
    workflow.updated_at = datetime.utcnow()
    db.add(workflow)
    record_activity(
        db=db,
        event_type="INFO_LINK_CREATED",
        summary=f"Created seminar info link for {suggestion.speaker_name}",
        semester_plan_id=suggestion.semester_plan_id,
        entity_type="speaker_suggestion",
        entity_id=suggestion.id,
        actor=user.get("id"),
    )
    db.commit()
    refresh_fallback_mirror(db)
    
    logger.info(f"Info token created successfully: {token[:8]}... for suggestion {suggestion.id}")
    
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
    """Submit availability using a speaker token. Replaces existing availability (always updatable)."""
    statement = select(SpeakerToken).where(
        SpeakerToken.token == token,
        SpeakerToken.token_type == 'availability',
        SpeakerToken.expires_at > datetime.utcnow()
    )
    db_token = db.exec(statement).first()
    
    if not db_token:
        raise HTTPException(status_code=404, detail="Invalid or expired token")
    
    # Replace existing availability: delete old entries, add new ones
    suggestion = db.get(SpeakerSuggestion, db_token.suggestion_id)
    if suggestion:
        for avail in list(suggestion.availability):
            db.delete(avail)
    
    # Add new availability entries
    for avail in data.availabilities:
        db_avail = SpeakerAvailability(
            suggestion_id=db_token.suggestion_id,
            date=avail.date,
            preference=avail.preference
        )
        db.add(db_avail)
    
    # Do not set used_at - speakers can return and edit anytime
    workflow = get_or_create_workflow(db, db_token.suggestion_id)
    workflow.availability_dates_received = True
    workflow.updated_at = datetime.utcnow()
    db.add(workflow)
    if suggestion:
        record_activity(
            db=db,
            event_type="AVAILABILITY_SUBMITTED",
            summary=f"Availability submitted by {suggestion.speaker_name}",
            semester_plan_id=suggestion.semester_plan_id,
            entity_type="speaker_suggestion",
            entity_id=suggestion.id,
            actor=f"token:{token[:8]}",
        )
    db.commit()
    refresh_fallback_mirror(db)
    
    return {"success": True, "message": "Availability saved successfully"}

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
    suggestion = db.get(SpeakerSuggestion, db_token.suggestion_id)

    # Get or create seminar details
    seminar_id = db_token.seminar_id
    if not seminar_id:
        # If no seminar_id in token, try to find one from the suggestion
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
    workflow = get_or_create_workflow(db, db_token.suggestion_id)
    workflow.proposal_submitted = True
    workflow.updated_at = datetime.utcnow()
    db.add(workflow)
    record_activity(
        db=db,
        event_type="SPEAKER_INFO_SUBMITTED",
        summary=f"Seminar info submitted for {suggestion.speaker_name if suggestion else 'speaker'}",
        semester_plan_id=suggestion.semester_plan_id if suggestion else None,
        entity_type="speaker_suggestion",
        entity_id=suggestion.id if suggestion else None,
        actor=f"token:{token[:8]}",
    )
    db.commit()
    refresh_fallback_mirror(db)
    
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
        # If slot has an assigned seminar, get the speaker name and seminar room
        if s.assigned_seminar_id:
            seminar_stmt = select(Seminar).options(selectinload(Seminar.room)).where(Seminar.id == s.assigned_seminar_id)
            seminar = db.exec(seminar_stmt).first()
            if seminar:
                assigned_suggestion_id = s.assigned_suggestion_id  # Use stored value first
                
                # Use seminar's room if set, otherwise keep slot's room
                if seminar.room:
                    slot_data["room"] = seminar.room.name
                
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
                "suggested_by_email": s.suggested_by_email,
                "reason": s.reason,
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
    
    # Find or create Room from slot's room string
    room_id = None
    if slot.room:
        room_stmt = select(Room).where(Room.name == slot.room)
        existing_room = db.exec(room_stmt).first()
        if existing_room:
            room_id = existing_room.id
        else:
            # Create a new room from slot's room
            new_room = Room(name=slot.room)
            db.add(new_room)
            db.commit()
            db.refresh(new_room)
            room_id = new_room.id
    
    # Create a seminar from the suggestion
    seminar = Seminar(
        title=suggestion.suggested_topic or f"Seminar by {suggestion.speaker_name}",
        date=slot.date,
        start_time=slot.start_time,
        end_time=slot.end_time,
        speaker_id=speaker_id,
        room_id=room_id,
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
    workflow = get_or_create_workflow(db, suggestion.id)
    workflow.speaker_notified_of_date = True
    workflow.updated_at = datetime.utcnow()
    db.add(workflow)
    record_activity(
        db=db,
        event_type="SPEAKER_ASSIGNED",
        summary=f"Assigned {suggestion.speaker_name} to slot {slot.date.isoformat()}",
        semester_plan_id=slot.semester_plan_id,
        entity_type="slot",
        entity_id=slot.id,
        actor=user.get("id"),
        details={"suggestion_id": suggestion.id, "seminar_id": seminar.id},
    )
    
    db.commit()
    refresh_fallback_mirror(db)
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
    record_activity(
        db=db,
        event_type="SEMINAR_ASSIGNED",
        summary=f"Assigned seminar '{seminar.title}' to slot {slot.date.isoformat()}",
        semester_plan_id=slot.semester_plan_id,
        entity_type="slot",
        entity_id=slot.id,
        actor=user.get("id"),
        details={"seminar_id": seminar.id},
    )
    
    db.commit()
    refresh_fallback_mirror(db)
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
    suggestion = db.get(SpeakerSuggestion, db_token.suggestion_id)
    record_activity(
        db=db,
        event_type="FILE_UPLOADED",
        summary=f"File uploaded by speaker: {file.filename}",
        semester_plan_id=suggestion.semester_plan_id if suggestion else None,
        entity_type="file",
        entity_id=uploaded.id,
        actor=f"token:{token[:8]}",
        details={"filename": file.filename, "category": category},
    )
    db.commit()
    refresh_fallback_mirror(db)
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
    suggestion = db.get(SpeakerSuggestion, db_token.suggestion_id)
    record_activity(
        db=db,
        event_type="FILE_DELETED",
        summary=f"File deleted by speaker: {file_record.original_filename}",
        semester_plan_id=suggestion.semester_plan_id if suggestion else None,
        entity_type="file",
        entity_id=file_id,
        actor=f"token:{token[:8]}",
    )
    db.commit()
    refresh_fallback_mirror(db)
    
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
    slot = db.exec(select(SeminarSlot).where(SeminarSlot.assigned_seminar_id == seminar_id)).first()
    record_activity(
        db=db,
        event_type="FILE_UPLOADED",
        summary=f"File uploaded: {file.filename}",
        semester_plan_id=slot.semester_plan_id if slot else None,
        entity_type="file",
        entity_id=uploaded.id,
        actor=user.get("id"),
    )
    db.commit()
    refresh_fallback_mirror(db)
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
    slot = db.exec(select(SeminarSlot).where(SeminarSlot.assigned_seminar_id == seminar_id)).first()
    record_activity(
        db=db,
        event_type="FILE_UPLOADED",
        summary=f"File uploaded: {file.filename}",
        semester_plan_id=slot.semester_plan_id if slot else None,
        entity_type="file",
        entity_id=uploaded.id,
        actor=user.get("id"),
    )
    db.commit()
    refresh_fallback_mirror(db)
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
    require_admin(user)
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
    slot = db.exec(select(SeminarSlot).where(SeminarSlot.assigned_seminar_id == seminar_id)).first()
    record_activity(
        db=db,
        event_type="FILE_DELETED",
        summary=f"File deleted: {file_record.original_filename}",
        semester_plan_id=slot.semester_plan_id if slot else None,
        entity_type="file",
        entity_id=file_id,
        actor=user.get("id"),
    )
    db.commit()
    refresh_fallback_mirror(db)
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
# API Routes - Activity, Workflow, Faculty Form, and Speaker Status
# ============================================================================

@app.get("/api/v1/seminars/activity", response_model=List[ActivityEventResponse])
async def list_activity_events(
    plan_id: Optional[int] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    stmt = select(ActivityEvent)
    if plan_id is not None:
        stmt = stmt.where(ActivityEvent.semester_plan_id == plan_id)
    stmt = stmt.order_by(ActivityEvent.created_at.desc()).limit(limit)
    rows = db.exec(stmt).all()
    return [
        ActivityEventResponse(
            id=row.id,
            semester_plan_id=row.semester_plan_id,
            event_type=row.event_type,
            summary=row.summary,
            entity_type=row.entity_type,
            entity_id=row.entity_id,
            actor=row.actor,
            details=json.loads(row.details_json) if row.details_json else None,
            created_at=row.created_at,
        )
        for row in rows
    ]

@app.get("/api/v1/seminars/system/mode")
async def seminars_system_mode(user: dict = Depends(get_current_user)):
    return {
        "feature_semester_plan_v2": settings.feature_semester_plan_v2,
        "legacy_write_enabled": not settings.feature_semester_plan_v2,
    }

@app.get("/api/v1/seminars/semester-plans/{plan_id}/speaker-workflows")
async def list_speaker_workflows(
    plan_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    suggestions = db.exec(
        select(SpeakerSuggestion)
        .where(SpeakerSuggestion.semester_plan_id == plan_id)
        .order_by(SpeakerSuggestion.created_at.desc())
    ).all()
    items = []
    for suggestion in suggestions:
        workflow = get_or_create_workflow(db, suggestion.id)
        status_payload = build_speaker_status(workflow, suggestion)
        items.append(
            {
                "suggestion_id": suggestion.id,
                "speaker_name": suggestion.speaker_name,
                "speaker_affiliation": suggestion.speaker_affiliation,
                "speaker_email": suggestion.speaker_email,
                "status": suggestion.status,
                "workflow": {
                    "request_available_dates_sent": workflow.request_available_dates_sent,
                    "availability_dates_received": workflow.availability_dates_received,
                    "speaker_notified_of_date": workflow.speaker_notified_of_date,
                    "meal_ok": workflow.meal_ok,
                    "guesthouse_hotel_reserved": workflow.guesthouse_hotel_reserved,
                    "proposal_submitted": workflow.proposal_submitted,
                    "proposal_approved": workflow.proposal_approved,
                    "updated_at": workflow.updated_at.isoformat(),
                },
                "status_page": status_payload,
            }
        )
    return {"items": items}

@app.patch("/api/v1/seminars/speaker-suggestions/{suggestion_id}/workflow")
async def update_speaker_workflow(
    suggestion_id: int,
    data: SpeakerWorkflowUpdate,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    suggestion = db.get(SpeakerSuggestion, suggestion_id)
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    workflow = get_or_create_workflow(db, suggestion_id)
    for key, value in data.model_dump().items():
        if value is not None:
            setattr(workflow, key, value)
    workflow.updated_at = datetime.utcnow()
    db.add(workflow)
    record_activity(
        db=db,
        event_type="WORKFLOW_UPDATED",
        summary=f"Workflow updated for {suggestion.speaker_name}",
        semester_plan_id=suggestion.semester_plan_id,
        entity_type="speaker_suggestion",
        entity_id=suggestion.id,
        actor=user.get("id"),
        details=data.model_dump(),
    )
    db.commit()
    refresh_fallback_mirror(db)
    return {"success": True}

@app.post("/api/v1/seminars/speaker-tokens/status")
async def create_status_token(
    request: dict,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    suggestion_id = request.get("suggestion_id")
    if not suggestion_id:
        raise HTTPException(status_code=400, detail="suggestion_id is required")
    suggestion = db.get(SpeakerSuggestion, suggestion_id)
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    token = generate_token()
    expires_at = datetime.utcnow() + timedelta(days=90)
    db_token = SpeakerToken(
        token=token,
        suggestion_id=suggestion_id,
        token_type="status",
        expires_at=expires_at,
    )
    db.add(db_token)
    record_activity(
        db=db,
        event_type="STATUS_TOKEN_CREATED",
        summary=f"Created status link for {suggestion.speaker_name}",
        semester_plan_id=suggestion.semester_plan_id,
        entity_type="speaker_suggestion",
        entity_id=suggestion.id,
        actor=user.get("id"),
    )
    db.commit()
    refresh_fallback_mirror(db)
    return {"link": f"/speaker/status/{token}", "token": token}

@app.get("/speaker/status/{token}", response_class=HTMLResponse)
async def speaker_status_page(token: str, db: Session = Depends(get_db)):
    statement = select(SpeakerToken).where(
        SpeakerToken.token == token,
        SpeakerToken.token_type == "status",
        SpeakerToken.expires_at > datetime.utcnow(),
    )
    db_token = db.exec(statement).first()
    if not db_token:
        return HTMLResponse(content=get_invalid_token_html(), status_code=404)
    suggestion = db.get(SpeakerSuggestion, db_token.suggestion_id)
    if not suggestion:
        return HTMLResponse(content=get_invalid_token_html(), status_code=404)
    
    workflow_stmt = select(SpeakerWorkflow).where(SpeakerWorkflow.suggestion_id == suggestion.id)
    workflow = db.exec(workflow_stmt).first()
    status_payload = build_speaker_status(workflow, suggestion)
    
    # Get seminar details if assigned
    seminar = None
    seminar_details = None
    if suggestion.speaker_id:
        seminar_stmt = select(Seminar).where(Seminar.speaker_id == suggestion.speaker_id).order_by(Seminar.date.desc())
        seminar = db.exec(seminar_stmt).first()
        if seminar:
            details_stmt = select(SeminarDetails).where(SeminarDetails.seminar_id == seminar.id)
            seminar_details = db.exec(details_stmt).first()
    
    # Build status steps
    steps = [
        ("1. Waiting for Date Availability", status_payload['step'] >= 1, status_payload['step'] == 1),
        ("2. Date Assigned", status_payload['step'] >= 2, status_payload['step'] == 2),
        ("3. Information Submitted", status_payload['step'] >= 3, status_payload['step'] == 3),
        ("4. Proposal Approved", status_payload['step'] >= 4, status_payload['step'] == 4),
    ]
    
    steps_html = "".join(
        f"<div class='step {'completed' if completed else ''} {'active' if active else ''}'>{label}</div>"
        for label, completed, active in steps
    )
    
    # Warning box - only show if proposal not approved
    warning_box = ""
    if status_payload['step'] < 4:
        warning_box = """
        <div class='warning-box'>
            <div class='warning-title'>⚠️ IMPORTANT: Do Not Purchase Travel Tickets Yet</div>
            <p>Please do <strong>NOT</strong> buy your flight or train tickets until your proposal has been approved. 
            We will notify you once your proposal is approved and provide information about where you can purchase your tickets.</p>
        </div>
        """
    
    # Get tokens for action links
    availability_token = None
    info_token = None
    
    # Get availability token (for step 1)
    avail_stmt = select(SpeakerToken).where(
        SpeakerToken.suggestion_id == suggestion.id,
        SpeakerToken.token_type == "availability",
        SpeakerToken.expires_at > datetime.utcnow(),
    ).order_by(SpeakerToken.created_at.desc())
    avail_token = db.exec(avail_stmt).first()
    if avail_token:
        availability_token = avail_token.token
    
    # Get info token (for step 2)
    if seminar:
        info_stmt = select(SpeakerToken).where(
            SpeakerToken.suggestion_id == suggestion.id,
            SpeakerToken.token_type == "info",
            SpeakerToken.seminar_id == seminar.id,
            SpeakerToken.expires_at > datetime.utcnow(),
        ).order_by(SpeakerToken.created_at.desc())
        info_token_obj = db.exec(info_stmt).first()
        if info_token_obj:
            info_token = info_token_obj.token
    
    # Build action links based on current step
    action_links_html = ""
    
    if status_payload['step'] == 1:
        if availability_token:
            action_links_html = f"""
            <div class='action-section'>
                <h3>📝 Action Required</h3>
                <p>Please submit your available dates for the seminar:</p>
                <a href='/speaker/availability/{availability_token}' class='action-link primary'>Submit Availability</a>
            </div>
            """
        else:
            action_links_html = """
            <div class='action-section waiting'>
                <h3>⏳ Waiting for Availability Request</h3>
                <p>You will receive an email with a link to submit your available dates soon. If you have any questions, please contact the organizers.</p>
            </div>
            """
    elif status_payload['step'] == 2:
        if info_token:
            action_links_html = f"""
            <div class='action-section'>
                <h3>📝 Action Required</h3>
                <p>Please submit your seminar information and proposal:</p>
                <a href='/speaker/info/{info_token}' class='action-link primary'>Submit Information</a>
            </div>
            """
        else:
            action_links_html = """
            <div class='action-section waiting'>
                <h3>⏳ Waiting for Information Request</h3>
                <p>You will receive an email with a link to submit your seminar information soon. If you have any questions, please contact the organizers.</p>
            </div>
            """
    elif status_payload['step'] == 3:
        action_links_html = """
        <div class='action-section waiting'>
            <h3>⏳ Waiting for Review</h3>
            <p>Your proposal is being reviewed. You will be notified once it has been approved.</p>
        </div>
        """
    elif status_payload['step'] == 4:
        action_links_html = """
        <div class='action-section approved'>
            <h3>✅ Proposal Approved</h3>
            <p>Your proposal has been approved! You can now purchase your travel tickets.</p>
        </div>
        """
    
    # Ticket purchase info (only when approved)
    ticket_info_html = ""
    ticket_purchase_info = None
    try:
        if seminar_details:
            ticket_purchase_info = getattr(seminar_details, 'ticket_purchase_info', None)
    except Exception:
        pass  # Column might not exist yet
    
    if status_payload['step'] == 4 and ticket_purchase_info:
        ticket_info_html = f"""
        <div class='info-section approved'>
            <h3>✅ Travel Ticket Purchase Information</h3>
            <div class='ticket-info'>{ticket_purchase_info}</div>
        </div>
        """
    elif status_payload['step'] == 4:
        ticket_info_html = """
        <div class='info-section approved'>
            <h3>✅ Proposal Approved</h3>
            <p>You can now purchase your travel tickets. Contact the organizers for specific instructions on where to buy your tickets.</p>
        </div>
        """
    
    # Seminar info
    seminar_info_html = ""
    if seminar:
        seminar_info_html = f"""
        <div class='info-section'>
            <h3>📅 Seminar Information</h3>
            <div class='info-row'><span class='label'>Title:</span> <span class='value'>{seminar.title or 'TBD'}</span></div>
            <div class='info-row'><span class='label'>Date:</span> <span class='value'>{seminar.date}</span></div>
            <div class='info-row'><span class='label'>Time:</span> <span class='value'>{seminar.start_time or 'TBD'} - {seminar.end_time or 'TBD'}</span></div>
        </div>
        """
    
    # Speaker info
    speaker_info_html = f"""
    <div class='info-section'>
        <h3>👤 Speaker Information</h3>
        <div class='info-row'><span class='label'>Name:</span> <span class='value'>{suggestion.speaker_name}</span></div>
        <div class='info-row'><span class='label'>Affiliation:</span> <span class='value'>{suggestion.speaker_affiliation or 'TBD'}</span></div>
        <div class='info-row'><span class='label'>Topic:</span> <span class='value'>{suggestion.suggested_topic or 'TBD'}</span></div>
    </div>
    """
    
    header_html = get_external_header_with_logos()
    
    # Remove unused edit_link variable
    edit_link = ""
    
    return HTMLResponse(
        content=f"""<!doctype html>
<html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>Seminar Status - {suggestion.speaker_name}</title><style>
:root{{--primary:#003366;--success:#28a745;--warning:#ffc107;--danger:#dc3545;--gray-100:#f8f9fa;--gray-200:#e9ecef;--gray-600:#6c757d;}}
*{{box-sizing:border-box;}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#f4f6f8;padding:24px;margin:0;line-height:1.6;}}
.header{{background:var(--primary);color:white;padding:24px 20px;text-align:center;margin:-24px -24px 24px -24px;}}
.header-logos{{display:flex;flex-direction:column;align-items:center;gap:12px;}}
.header-logos-inner{{display:flex;align-items:center;justify-content:center;gap:24px;flex-wrap:wrap;}}
.header .logo-wrap{{background:white;padding:16px 28px;border-radius:12px;box-shadow:0 2px 8px rgba(0,0,0,0.15);}}
.header .logo{{height:72px;width:auto;object-fit:contain;display:block;}}
.header .logo-um{{max-height:80px;}}
.header .logo-econ{{max-height:72px;}}
.header h1{{font-size:26px;font-weight:600;margin:0;}}
.header .subtitle{{font-size:15px;opacity:.9;margin-top:6px;}}
.container{{max-width:800px;margin:0 auto;}}
.card{{background:#fff;border-radius:12px;padding:28px;box-shadow:0 2px 12px rgba(0,0,0,0.08);margin-bottom:24px;}}
.warning-box{{background:#fff3cd;border:2px solid #ffc107;border-radius:8px;padding:20px;margin-bottom:24px;}}
.warning-box .warning-title{{color:#856404;font-weight:bold;font-size:18px;margin-bottom:8px;}}
.warning-box p{{color:#856404;margin:0;}}
.status-steps{{display:flex;gap:8px;margin-bottom:24px;flex-wrap:wrap;}}
.step{{flex:1;min-width:140px;padding:16px 12px;background:var(--gray-200);border-radius:8px;text-align:center;font-size:14px;font-weight:500;color:var(--gray-600);}}
.step.completed{{background:#d4edda;color:#155724;}}
.step.active{{background:var(--primary);color:white;box-shadow:0 2px 8px rgba(0,51,102,0.3);}}
.status-message{{background:var(--gray-100);border-left:4px solid var(--primary);padding:16px 20px;border-radius:0 8px 8px 0;margin-bottom:24px;}}
.status-message h2{{margin:0 0 8px 0;font-size:20px;color:var(--primary);}}
.status-message p{{margin:0;color:var(--gray-600);}}
.info-section{{margin-bottom:24px;padding-bottom:24px;border-bottom:1px solid var(--gray-200);}}
.info-section:last-child{{border-bottom:none;margin-bottom:0;padding-bottom:0;}}
.info-section.approved{{background:#d4edda;border:1px solid #28a745;border-radius:8px;padding:20px;}}
.info-section h3{{margin:0 0 16px 0;font-size:16px;color:var(--primary);text-transform:uppercase;letter-spacing:0.5px;}}
.info-section.approved h3{{color:#155724;}}
.info-row{{display:flex;margin-bottom:12px;}}
.info-row:last-child{{margin-bottom:0;}}
.info-row .label{{width:120px;font-weight:600;color:var(--gray-600);flex-shrink:0;}}
.info-row .value{{flex:1;color:#333;}}
.ticket-info{{background:white;border:1px solid #28a745;border-radius:6px;padding:16px;font-size:15px;line-height:1.8;white-space:pre-wrap;}}
.action-section{{background:#e7f3ff;border:1px solid #0066cc;border-radius:8px;padding:20px;margin-bottom:24px;}}
.action-section.waiting{{background:#fff3cd;border-color:#ffc107;}}
.action-section.approved{{background:#d4edda;border-color:#28a745;}}
.action-section h3{{margin:0 0 12px 0;font-size:18px;color:#003366;}}
.action-section.waiting h3{{color:#856404;}}
.action-section.approved h3{{color:#155724;}}
.action-section p{{margin:0 0 16px 0;color:#333;}}
.action-link{{display:inline-block;background:var(--primary);color:white;padding:14px 28px;border-radius:8px;text-decoration:none;font-weight:600;font-size:16px;transition:all 0.2s;box-shadow:0 2px 4px rgba(0,51,102,0.2);}}
.action-link:hover{{background:#004080;transform:translateY(-1px);box-shadow:0 4px 8px rgba(0,51,102,0.3);}}
.action-link.primary{{background:#0066cc;}}
.action-link.primary:hover{{background:#0052a3;}}
.footer{{text-align:center;color:var(--gray-600);font-size:14px;margin-top:24px;}}
@media (max-width: 600px){{.step{{min-width:100%;}}.info-row{{flex-direction:column;}}.info-row .label{{width:auto;margin-bottom:4px;}}}}
</style></head>
<body>
<div class='header'>{header_html}</div>
<div class='container'>
    {warning_box}
    
    <div class='card'>
        <div class='status-steps'>
            {steps_html}
        </div>
        
        <div class='status-message'>
            <h2>{status_payload['title']}</h2>
            <p>{status_payload['message']}</p>
        </div>
    </div>
    
    {action_links_html}
    
    {ticket_info_html}
    
    <div class='card'>
        {speaker_info_html}
        {seminar_info_html}
    </div>
    
    <p class='footer'>This page updates automatically when your seminar status changes.<br>Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}</p>
</div>
</body></html>"""
    )

@app.get("/faculty/suggest-speaker/{plan_id}", response_class=HTMLResponse)
async def faculty_suggest_speaker_page(plan_id: int, db: Session = Depends(get_db)):
    plan = db.get(SemesterPlan, plan_id)
    if not plan:
        return HTMLResponse(content="<h1>Plan not found</h1>", status_code=404)
    header_html = get_external_header_with_logos()
    return HTMLResponse(
        content=f"""<!doctype html>
<html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>Suggest a Speaker - University of Macau</title><style>
:root{{--primary:#003366;--primary-light:#0066CC;--gray-100:#f8f9fa;--gray-200:#e9ecef;--gray-600:#6c757d;--gray-800:#343a40;}}
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:linear-gradient(135deg,#f5f7fa 0%,#c3cfe2 100%);min-height:100vh;padding:24px;line-height:1.6;}}
.header{{background:var(--primary);color:white;padding:24px 20px;text-align:center;margin:-24px -24px 24px -24px;}}
.header-logos{{display:flex;flex-direction:column;align-items:center;gap:12px;}}
.header-logos-inner{{display:flex;align-items:center;justify-content:center;gap:24px;flex-wrap:wrap;}}
.header .logo-wrap{{background:white;padding:16px 28px;border-radius:12px;box-shadow:0 2px 8px rgba(0,0,0,0.15);}}
.header .logo{{height:72px;width:auto;object-fit:contain;display:block;}}
.header .logo-um{{max-height:80px;}}
.header .logo-econ{{max-height:72px;}}
.header h1{{font-size:26px;font-weight:600;margin:0;}}
.header .subtitle{{font-size:15px;opacity:.9;margin-top:6px;}}
.container{{max-width:640px;margin:0 auto;}}
.card{{background:#fff;border-radius:12px;box-shadow:0 2px 12px rgba(0,0,0,0.08);overflow:hidden;}}
.card-header{{background:linear-gradient(135deg,var(--primary) 0%,var(--primary-light) 100%);color:white;padding:24px 28px;}}
.card-header h2{{font-size:22px;font-weight:600;margin:0;}}
.card-header p{{font-size:14px;opacity:0.95;margin-top:8px;}}
.card-body{{padding:28px;}}
.form-section{{margin-bottom:24px;}}
.form-section:last-of-type{{margin-bottom:0;}}
.form-section h3{{font-size:14px;font-weight:600;color:var(--gray-800);margin-bottom:12px;text-transform:uppercase;letter-spacing:0.5px;}}
.form-group{{margin-bottom:20px;}}
.form-group:last-child{{margin-bottom:0;}}
.form-label{{display:block;font-weight:500;color:var(--gray-800);margin-bottom:6px;font-size:14px;}}
.form-label .required{{color:#dc3545;margin-left:2px;}}
.form-input,.form-textarea{{width:100%;padding:12px 16px;border:2px solid var(--gray-200);border-radius:8px;font-size:16px;font-family:inherit;transition:border-color 0.2s;}}
.form-input:focus,.form-textarea:focus{{outline:none;border-color:var(--primary-light);box-shadow:0 0 0 3px rgba(0,102,204,0.1);}}
.form-textarea{{min-height:120px;resize:vertical;}}
.form-hint{{font-size:13px;color:var(--gray-600);margin-top:6px;}}
.form-row{{display:grid;grid-template-columns:1fr 1fr;gap:20px;}}
@media (max-width:600px){{.form-row{{grid-template-columns:1fr;}}}}
.btn-submit{{display:block;width:100%;padding:14px 24px;background:linear-gradient(135deg,var(--primary) 0%,var(--primary-light) 100%);color:white;border:none;border-radius:8px;font-size:16px;font-weight:600;cursor:pointer;transition:transform 0.15s,box-shadow 0.15s;margin-top:8px;}}
.btn-submit:hover{{transform:translateY(-1px);box-shadow:0 4px 12px rgba(0,51,102,0.3);}}
.btn-submit:active{{transform:translateY(0);}}
.plan-badge{{display:inline-block;background:rgba(255,255,255,0.2);padding:6px 12px;border-radius:6px;font-size:13px;margin-top:12px;}}
</style></head>
<body><div class='header'>{header_html}</div>
<div class='container'>
<div class='card'>
<div class='card-header'>
<h2>Suggest a Speaker</h2>
<p>Recommend a colleague or contact to present in our seminar series.</p>
<span class='plan-badge'>Plan: {plan.name}</span>
</div>
<div class='card-body'>
<form method='post' action='/faculty/suggest-speaker/{plan_id}'>
<div class='form-section'>
<h3>Your details</h3>
<div class='form-row'>
<div class='form-group'><label class='form-label'>Your name <span class='required'>*</span></label><input type='text' name='faculty_name' class='form-input' required placeholder='e.g. Jane Smith' /></div>
<div class='form-group'><label class='form-label'>Your email <span class='required'>*</span></label><input type='email' name='faculty_email' class='form-input' required placeholder='jane@um.edu.mo' /></div>
</div>
</div>
<div class='form-section'>
<h3>Speaker information</h3>
<div class='form-row'>
<div class='form-group'><label class='form-label'>Speaker name <span class='required'>*</span></label><input type='text' name='speaker_name' class='form-input' required placeholder='e.g. John Doe' /></div>
<div class='form-group'><label class='form-label'>Speaker email</label><input type='email' name='speaker_email' class='form-input' placeholder='john@university.edu' /></div>
</div>
<div class='form-group'><label class='form-label'>Speaker affiliation</label><input type='text' name='speaker_affiliation' class='form-input' placeholder='e.g. Harvard University' /></div>
<div class='form-group'><label class='form-label'>Suggested topic</label><input type='text' name='suggested_topic' class='form-input' placeholder='e.g. Machine Learning in Economics' /></div>
<div class='form-group'><label class='form-label'>Reason / context</label><textarea name='reason' class='form-textarea' rows='4' placeholder='Why do you recommend this speaker? Any relevant context...'></textarea></div>
</div>
<button type='submit' class='btn-submit'>Submit suggestion</button>
</form></div></div></div></body></html>"""
    )

@app.post("/api/v1/seminars/semester-plans/{plan_id}/faculty-suggestion-link")
async def create_faculty_suggestion_link(
    plan_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    plan = db.get(SemesterPlan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Semester plan not found")
    link = f"/faculty/suggest-speaker/{plan_id}"
    record_activity(
        db=db,
        event_type="FACULTY_FORM_LINK_ACCESSED",
        summary=f"Generated faculty suggestion form link for {plan.name}",
        semester_plan_id=plan_id,
        entity_type="semester_plan",
        entity_id=plan_id,
        actor=user.get("id"),
        details={"link": link},
    )
    db.commit()
    refresh_fallback_mirror(db)
    return {"link": link}

@app.post("/faculty/suggest-speaker/{plan_id}", response_class=HTMLResponse)
async def faculty_suggest_speaker_submit(
    plan_id: int,
    faculty_name: str = Form(...),
    faculty_email: str = Form(...),
    speaker_name: str = Form(...),
    speaker_email: Optional[str] = Form(None),
    speaker_affiliation: Optional[str] = Form(None),
    suggested_topic: Optional[str] = Form(None),
    reason: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    plan = db.get(SemesterPlan, plan_id)
    if not plan:
        return HTMLResponse(content="<h1>Plan not found</h1>", status_code=404)
    # Create a speaker for this plan suggestion flow (clean-start workflow)
    speaker = Speaker(name=speaker_name, email=speaker_email, affiliation=speaker_affiliation)
    db.add(speaker)
    db.commit()
    db.refresh(speaker)

    suggestion = SpeakerSuggestion(
        suggested_by=faculty_name,
        suggested_by_email=faculty_email,
        speaker_id=speaker.id,
        speaker_name=speaker_name,
        speaker_email=speaker_email,
        speaker_affiliation=speaker_affiliation,
        suggested_topic=suggested_topic,
        reason=reason,
        priority="medium",
        status="pending",
        semester_plan_id=plan_id,
    )
    db.add(suggestion)
    db.flush()
    workflow = SpeakerWorkflow(suggestion_id=suggestion.id)
    db.add(workflow)
    record_activity(
        db=db,
        event_type="FACULTY_SUGGESTION_SUBMITTED",
        summary=f"Faculty suggestion submitted for {speaker_name}",
        semester_plan_id=plan_id,
        entity_type="speaker_suggestion",
        entity_id=suggestion.id,
        actor=faculty_email,
    )
    db.commit()
    refresh_fallback_mirror(db)
    header_html = get_external_header_with_logos()
    return HTMLResponse(
        content=f"""<!doctype html>
<html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>Thank you - University of Macau</title><style>
:root{{--primary:#003366;--primary-light:#0066CC;--success:#28a745;}}
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:linear-gradient(135deg,#f5f7fa 0%,#c3cfe2 100%);min-height:100vh;padding:24px;line-height:1.6;}}
.header{{background:var(--primary);color:white;padding:24px 20px;text-align:center;margin:-24px -24px 24px -24px;}}
.header-logos{{display:flex;flex-direction:column;align-items:center;gap:12px;}}
.header-logos-inner{{display:flex;align-items:center;justify-content:center;gap:24px;flex-wrap:wrap;}}
.header .logo-wrap{{background:white;padding:16px 28px;border-radius:12px;box-shadow:0 2px 8px rgba(0,0,0,0.15);}}
.header .logo{{height:72px;width:auto;object-fit:contain;display:block;}}
.header .logo-um{{max-height:80px;}}
.header .logo-econ{{max-height:72px;}}
.header h1{{font-size:26px;font-weight:600;margin:0;}}
.header .subtitle{{font-size:15px;opacity:.9;margin-top:6px;}}
.container{{max-width:520px;margin:0 auto;}}
.card{{background:#fff;border-radius:12px;box-shadow:0 2px 12px rgba(0,0,0,0.08);padding:40px;text-align:center;}}
.success-icon{{font-size:48px;margin-bottom:16px;}}
.card h2{{font-size:24px;color:#155724;margin-bottom:12px;}}
.card p{{color:#6c757d;font-size:16px;margin-bottom:24px;}}
.btn-link{{display:inline-block;padding:12px 24px;background:var(--primary);color:white;border-radius:8px;text-decoration:none;font-weight:500;transition:background 0.2s;}}
.btn-link:hover{{background:var(--primary-light);color:white;}}
</style></head>
<body><div class='header'>{header_html}</div>
<div class='container'><div class='card'>
<div class='success-icon'>✓</div>
<h2>Thank you</h2>
<p>Your suggestion was submitted successfully. We will follow up with the speaker in due course.</p>
<a href='javascript:history.back()' class='btn-link'>Submit another suggestion</a>
</div></div></body></html>"""
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
# Admin / Backup Endpoints
# ============================================================================

@app.get("/api/admin/backup-status")
async def backup_status(secret: str):
    """
    Get latest backup status.
    Requires API_SECRET for authentication.
    """
    if secret != settings.api_secret:
        raise HTTPException(status_code=401, detail="Invalid secret")
    
    backup_dir = Path("/data/backups")
    
    if not backup_dir.exists():
        return {"backups": [], "latest": None}
    
    # Find all backup files
    backups = []
    for pattern in ["seminars_full_*.tar.gz", "seminars_mirror_*.tar.gz"]:
        for f in backup_dir.glob(pattern):
            backups.append({
                "filename": f.name,
                "size": f.stat().st_size,
                "created": datetime.fromtimestamp(f.stat().st_mtime).isoformat()
            })
    
    # Sort by creation time (newest first)
    backups.sort(key=lambda x: x["created"], reverse=True)
    
    return {
        "backups": backups[:10],  # Last 10 backups
        "latest": backups[0] if backups else None,
        "backup_dir": str(backup_dir)
    }


# ============================================================================
# Auth Helpers
# ============================================================================

def require_admin(user: dict) -> None:
    """Raise 403 if user is not an admin."""
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required for this operation")


# ============================================================================
# Auth Endpoints
# ============================================================================

class EditorLoginRequest(BaseModel):
    password: str


class AuthMeResponse(BaseModel):
    id: str
    role: str
    name: str


@app.post("/api/auth/login-editor")
async def login_editor(credentials: EditorLoginRequest):
    """Login with editor password to get editor token."""
    if not settings.editor_password:
        raise HTTPException(status_code=400, detail="Editor access not configured")
    
    if credentials.password != settings.editor_password:
        raise HTTPException(status_code=401, detail="Invalid password")
    
    # Return simple editor token
    token = create_editor_token()
    return {"token": token, "role": "editor", "name": "Editor User"}


class MasterLoginRequest(BaseModel):
    password: str


@app.post("/api/auth/login-admin")
async def login_admin(credentials: MasterLoginRequest):
    """Login with master password to get admin token."""
    if not settings.master_password:
        raise HTTPException(status_code=400, detail="Admin access not configured")
    
    if credentials.password != settings.master_password:
        raise HTTPException(status_code=401, detail="Invalid password")
    
    # Create admin token
    token = "admin_" + settings.master_password[:8]
    return {"token": token, "role": "admin", "name": "Admin User"}


@app.get("/api/auth/me", response_model=AuthMeResponse)
async def auth_me(user: dict = Depends(get_current_user)):
    """Get current user info."""
    return {
        "id": user.get("id", "unknown"),
        "role": user.get("role", "admin"),
        "name": user.get("name", "User")
    }


# ============================================================================
# Email Sending
# ============================================================================

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class SendEmailRequest(BaseModel):
    to: str
    subject: str
    body: str
    cc: Optional[str] = None

class SendEmailResponse(BaseModel):
    success: bool
    message: str

@app.post("/api/v1/seminars/send-email", response_model=SendEmailResponse)
async def send_email(request: SendEmailRequest, user: dict = Depends(get_current_user)):
    """Send an email to a speaker. Requires SMTP to be configured."""
    
    # Check if SMTP is configured
    if not settings.smtp_host or not settings.smtp_user or not settings.smtp_password:
        raise HTTPException(
            status_code=400, 
            detail="Email not configured. Please set SMTP_HOST, SMTP_USER, and SMTP_PASSWORD."
        )
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = f"{settings.smtp_from_name} <{settings.smtp_from or settings.smtp_user}>"
        msg['To'] = request.to
        msg['Subject'] = request.subject
        
        if request.cc:
            msg['Cc'] = request.cc
        
        # Attach body
        msg.attach(MIMEText(request.body, 'plain', 'utf-8'))
        
        # Connect to SMTP and send
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
            
            recipients = [request.to]
            if request.cc:
                recipients.extend(request.cc.split(','))
            
            server.sendmail(
                settings.smtp_from or settings.smtp_user,
                recipients,
                msg.as_string()
            )
        
        logger.info(f"Email sent successfully to {request.to} by {user.get('id')}")
        
        return {
            "success": True,
            "message": f"Email sent successfully to {request.to}"
        }
        
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")


# ============================================================================
# Recovery from Fallback Mirror
# ============================================================================

@app.post("/api/admin/recover-from-mirror")
async def recover_from_mirror(
    confirm: bool = False,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Recover seminar data from fallback mirror HTML file."""
    require_admin(user)
    
    if not confirm:
        raise HTTPException(status_code=400, detail="Must set confirm=true to proceed with recovery")
    
    import re
    from datetime import datetime
    
    mirror_path = Path("./fallback-mirror/recovery.html")
    if not mirror_path.exists():
        raise HTTPException(status_code=404, detail="Recovery file not found")
    
    with open(mirror_path, 'r') as f:
        html = f.read()
    
    recovered = {"speakers": 0, "seminars": 0, "rooms": 0}
    
    # Parse speakers
    speakers = []
    speaker_pattern = r'<h3>([^<]+)</h3>\s*<p><strong>Affiliation:</strong> ([^|]+) \| <strong>Email:</strong> ([^<]+)</p>'
    for match in re.finditer(speaker_pattern, html):
        name = match.group(1).strip()
        affiliation = match.group(2).strip()
        email = match.group(3).strip()
        speakers.append({
            'name': name,
            'affiliation': affiliation,
            'email': email
        })
    
    # Create speakers
    speaker_map = {}
    for s_data in speakers:
        stmt = select(Speaker).where(Speaker.email == s_data['email'])
        existing = db.exec(stmt).first()
        if existing:
            speaker_map[s_data['name']] = existing
        else:
            speaker = Speaker(**s_data)
            db.add(speaker)
            db.flush()
            speaker_map[s_data['name']] = speaker
            recovered["speakers"] += 1
    
    # Parse seminars
    seminar_blocks = re.findall(r'<div class="seminar-block">(.*?)</div>\s*</div>', html, re.DOTALL)
    
    for block in seminar_blocks:
        # Title
        title_match = re.search(r'<h2>([^<]+)</h2>', block)
        title = title_match.group(1) if title_match else 'Unknown'
        
        # Date, time, room, status
        meta_match = re.search(r'<strong>Date:</strong> ([^|]+) \| <strong>Time:</strong> ([^|]+) \| <strong>Room:</strong> ([^|]+) \| <strong>Status:</strong> ([^<]+)</p>', block)
        if not meta_match:
            continue
            
        date_str = meta_match.group(1).strip()
        time_range = meta_match.group(2).strip()
        room_name = meta_match.group(3).strip()
        status = meta_match.group(4).strip()
        
        # Speaker
        speaker_match = re.search(r'<strong>Speaker:</strong> ([^<]+) <([^>]+)>', block)
        speaker_name = speaker_match.group(1).strip() if speaker_match else 'Unknown'
        
        # Abstract
        abstract_match = re.search(r'<h3>Abstract</h3><p>([^<]+)</p>', block)
        abstract = abstract_match.group(1) if abstract_match else None
        
        # Parse time
        time_parts = time_range.split('-')
        start_time = time_parts[0].strip() if len(time_parts) > 0 else '14:00'
        end_time = time_parts[1].strip() if len(time_parts) > 1 else '15:30'
        
        # Parse date
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        except:
            continue
        
        # Create room if needed
        room = None
        if room_name and room_name != 'TBD':
            stmt = select(Room).where(Room.name == room_name)
            room = db.exec(stmt).first()
            if not room:
                room = Room(name=room_name, location="")
                db.add(room)
                db.flush()
                recovered["rooms"] += 1
        
        # Get speaker
        speaker = speaker_map.get(speaker_name)
        
        # Check if seminar already exists
        stmt = select(Seminar).where(
            Seminar.title == title,
            Seminar.date == date_obj
        )
        existing = db.exec(stmt).first()
        if not existing:
            seminar = Seminar(
                title=title,
                date=date_obj,
                start_time=start_time,
                end_time=end_time,
                speaker_id=speaker.id if speaker else None,
                room_id=room.id if room else None,
                abstract=abstract,
                status=status
            )
            db.add(seminar)
            recovered["seminars"] += 1
    
    db.commit()
    
    record_activity(
        db=db,
        event_type="DATA_RECOVERY",
        summary=f"Recovered data from mirror: {recovered}",
        entity_type="system",
        entity_id=0,
        actor=user.get("id"),
    )
    
    refresh_fallback_mirror(db)
    
    return {"success": True, "recovered": recovered}


@app.post("/api/admin/restore-database")
async def restore_database(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Restore database from uploaded SQLite backup file."""
    require_admin(user)
    
    # Get confirm from query params
    confirm = request.query_params.get('confirm', 'false')
    if confirm.lower() != "true":
        raise HTTPException(status_code=400, detail="Must set confirm=true to proceed with restore")
    
    import tempfile
    import shutil
    
    # Save uploaded file to temp location
    temp_dir = tempfile.mkdtemp()
    temp_path = Path(temp_dir) / "backup.db"
    
    try:
        with open(temp_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        
        # Connect to backup and inspect
        import sqlite3
        backup_conn = sqlite3.connect(str(temp_path))
        backup_cursor = backup_conn.cursor()
        
        # Check what's in the backup
        tables = ['semester_plans', 'seminar_slots', 'speaker_suggestions', 'speakers', 'seminars', 'rooms']
        backup_counts = {}
        for table in tables:
            try:
                backup_cursor.execute(f"SELECT COUNT(*) FROM {table}")
                backup_counts[table] = backup_cursor.fetchone()[0]
            except:
                backup_counts[table] = 0
        
        # Get semester plan details from backup
        backup_plans = []
        try:
            backup_cursor.execute("SELECT id, name, academic_year, semester, default_room, status FROM semester_plans")
            for row in backup_cursor.fetchall():
                backup_plans.append({
                    "id": row[0],
                    "name": row[1],
                    "academic_year": row[2],
                    "semester": row[3],
                    "default_room": row[4],
                    "status": row[5]
                })
        except Exception as e:
            return {"error": f"Failed to read semester_plans from backup: {e}", "backup_counts": backup_counts}
        
        # Get slots from backup
        backup_slots = []
        try:
            backup_cursor.execute("SELECT id, semester_plan_id, date, start_time, end_time, room, status FROM seminar_slots")
            for row in backup_cursor.fetchall():
                backup_slots.append({
                    "id": row[0],
                    "semester_plan_id": row[1],
                    "date": row[2],
                    "start_time": row[3],
                    "end_time": row[4],
                    "room": row[5],
                    "status": row[6]
                })
        except Exception as e:
            return {"error": f"Failed to read seminar_slots from backup: {e}", "backup_counts": backup_counts}
        
        # Get suggestions from backup
        backup_suggestions = []
        try:
            backup_cursor.execute("SELECT id, semester_plan_id, speaker_name, speaker_email, speaker_affiliation, suggested_topic, status FROM speaker_suggestions")
            for row in backup_cursor.fetchall():
                backup_suggestions.append({
                    "id": row[0],
                    "semester_plan_id": row[1],
                    "speaker_name": row[2],
                    "speaker_email": row[3],
                    "speaker_affiliation": row[4],
                    "suggested_topic": row[5],
                    "status": row[6]
                })
        except Exception as e:
            return {"error": f"Failed to read speaker_suggestions from backup: {e}", "backup_counts": backup_counts}
        
        backup_conn.close()
        
        # Now restore the data
        restored = {"semester_plans": 0, "slots": 0, "suggestions": 0, "speakers": 0, "seminars": 0, "rooms": 0}
        
        # Restore semester plans
        for plan_data in backup_plans:
            # Check if plan already exists
            stmt = select(SemesterPlan).where(SemesterPlan.name == plan_data["name"])
            existing = db.exec(stmt).first()
            if not existing:
                plan = SemesterPlan(
                    name=plan_data["name"],
                    academic_year=plan_data["academic_year"],
                    semester=plan_data["semester"],
                    default_room=plan_data["default_room"],
                    status=plan_data["status"]
                )
                db.add(plan)
                db.flush()
                restored["semester_plans"] += 1
        
        db.commit()
        
        # Build ID mapping for plans (backup_id -> new_id)
        plan_id_map = {}
        for plan_data in backup_plans:
            stmt = select(SemesterPlan).where(SemesterPlan.name == plan_data["name"])
            existing = db.exec(stmt).first()
            if existing:
                plan_id_map[plan_data["id"]] = existing.id
        
        # Restore slots
        for slot_data in backup_slots:
            new_plan_id = plan_id_map.get(slot_data["semester_plan_id"])
            if new_plan_id:
                # Check if slot already exists
                stmt = select(SeminarSlot).where(
                    SeminarSlot.semester_plan_id == new_plan_id,
                    SeminarSlot.date == slot_data["date"]
                )
                existing = db.exec(stmt).first()
                if not existing:
                    slot = SeminarSlot(
                        semester_plan_id=new_plan_id,
                        date=slot_data["date"],
                        start_time=slot_data["start_time"],
                        end_time=slot_data["end_time"],
                        room=slot_data["room"],
                        status=slot_data["status"]
                    )
                    db.add(slot)
                    restored["slots"] += 1
        
        db.commit()
        
        # Restore suggestions
        for sugg_data in backup_suggestions:
            new_plan_id = plan_id_map.get(sugg_data["semester_plan_id"])
            if new_plan_id:
                # Check if suggestion already exists
                stmt = select(SpeakerSuggestion).where(
                    SpeakerSuggestion.semester_plan_id == new_plan_id,
                    SpeakerSuggestion.speaker_name == sugg_data["speaker_name"]
                )
                existing = db.exec(stmt).first()
                if not existing:
                    suggestion = SpeakerSuggestion(
                        semester_plan_id=new_plan_id,
                        suggested_by=user.get("id", "admin"),
                        speaker_name=sugg_data["speaker_name"],
                        speaker_email=sugg_data["speaker_email"],
                        speaker_affiliation=sugg_data["speaker_affiliation"],
                        suggested_topic=sugg_data["suggested_topic"],
                        status=sugg_data["status"]
                    )
                    db.add(suggestion)
                    restored["suggestions"] += 1
        
        db.commit()
        
        # Restore speakers and seminars from backup
        backup_conn = sqlite3.connect(str(temp_path))
        backup_cursor = backup_conn.cursor()
        
        # Restore speakers with dynamic column detection
        try:
            # Get available columns in backup speakers table
            backup_cursor.execute("PRAGMA table_info(speakers)")
            speaker_cols_available = {row[1]: row[0] for row in backup_cursor.fetchall()}  # {col_name: col_index}
            
            # List of columns to try to restore
            speaker_columns = ['id', 'name', 'email', 'affiliation', 'website', 'bio', 'notes', 'cv_path', 'photo_path']
            cols_to_select = [col for col in speaker_columns if col in speaker_cols_available]
            select_sql = f"SELECT {', '.join(cols_to_select)} FROM speakers"
            
            logger.info(f"Restoring speakers with columns: {cols_to_select}")
            
            backup_cursor.execute(select_sql)
            for row in backup_cursor.fetchall():
                # Dynamic mapping: build a dict of column_name -> value
                row_dict = {cols_to_select[i]: row[i] for i in range(len(row))}
                
                # Check if speaker exists by email
                if row_dict.get('email'):
                    stmt = select(Speaker).where(Speaker.email == row_dict.get('email'))
                    existing = db.exec(stmt).first()
                    if not existing:
                        speaker = Speaker(
                            name=row_dict.get('name'),
                            email=row_dict.get('email'),
                            affiliation=row_dict.get('affiliation'),
                            website=row_dict.get('website'),
                            bio=row_dict.get('bio'),
                            notes=row_dict.get('notes'),
                            cv_path=row_dict.get('cv_path'),
                            photo_path=row_dict.get('photo_path')
                        )
                        db.add(speaker)
                        restored["speakers"] += 1
        except Exception as e:
            logger.error(f"Error restoring speakers: {e}")
            import traceback
            traceback.print_exc()
        
        db.commit()
        
        # Restore seminars with dynamic column detection
        try:
            # Get available columns in backup seminars table
            backup_cursor.execute("PRAGMA table_info(seminars)")
            available_cols = {row[1]: row[0] for row in backup_cursor.fetchall()}  # {col_name: col_index}
            
            # List of columns to try to restore, in preferred order
            seminar_columns = [
                'id', 'title', 'date', 'start_time', 'end_time', 'speaker_id', 'room_id',
                'abstract', 'paper_title', 'status', 'room_booked', 'announcement_sent',
                'calendar_invite_sent', 'website_updated', 'catering_ordered', 'notes'
            ]
            
            # Filter to only available columns
            cols_to_select = [col for col in seminar_columns if col in available_cols]
            select_sql = f"SELECT {', '.join(cols_to_select)} FROM seminars"
            
            logger.info(f"Restoring seminars with columns: {cols_to_select}")
            
            backup_cursor.execute(select_sql)
            for row in backup_cursor.fetchall():
                # Dynamic mapping: build a dict of column_name -> value
                row_dict = {cols_to_select[i]: row[i] for i in range(len(row))}
                
                # Check if seminar exists
                stmt = select(Seminar).where(
                    Seminar.title == row_dict.get('title'),
                    Seminar.date == row_dict.get('date')
                )
                existing = db.exec(stmt).first()
                if not existing:
                    # Parse date if it's a string
                    date_val = row_dict.get('date')
                    if date_val and isinstance(date_val, str):
                        try:
                            from datetime import datetime as dt
                            date_val = dt.strptime(date_val, '%Y-%m-%d').date()
                        except:
                            try:
                                # Try ISO format
                                date_val = dt.fromisoformat(date_val).date()
                            except:
                                logger.warning(f"Could not parse date: {date_val}")
                                continue
                    
                    # Create seminar with available data
                    seminar = Seminar(
                        title=row_dict.get('title'),
                        date=date_val,
                        start_time=row_dict.get('start_time', '14:00'),
                        end_time=row_dict.get('end_time'),
                        speaker_id=row_dict.get('speaker_id') or 1,
                        room_id=row_dict.get('room_id'),
                        abstract=row_dict.get('abstract'),
                        paper_title=row_dict.get('paper_title'),
                        status=row_dict.get('status', 'planned'),
                        room_booked=row_dict.get('room_booked', False) or False,
                        announcement_sent=row_dict.get('announcement_sent', False) or False,
                        calendar_invite_sent=row_dict.get('calendar_invite_sent', False) or False,
                        website_updated=row_dict.get('website_updated', False) or False,
                        catering_ordered=row_dict.get('catering_ordered', False) or False,
                        notes=row_dict.get('notes')
                    )
                    db.add(seminar)
                    restored["seminars"] += 1
        except Exception as e:
            logger.error(f"Error restoring seminars: {e}")
            import traceback
            traceback.print_exc()

        
        db.commit()
        backup_conn.close()
        
        record_activity(
            db=db,
            event_type="DATABASE_RESTORE",
            summary=f"Restored database from backup file: {restored}",
            entity_type="system",
            entity_id=0,
            actor=user.get("id"),
        )
        
        refresh_fallback_mirror(db)
        
        return {
            "success": True,
            "backup_counts": backup_counts,
            "restored": restored,
            "backup_plans_sample": backup_plans[:3],
            "backup_slots_sample": backup_slots[:3],
            "backup_suggestions_sample": backup_suggestions[:3]
        }
        
    finally:
        # Cleanup temp files
        shutil.rmtree(temp_dir, ignore_errors=True)


# ============================================================================
# Health Check
# ============================================================================

@app.get("/api/health")
async def health():
    return {"status": "ok"}


# ============================================================================
# Include Database Admin Router (imported here to avoid circular imports)
# ============================================================================

from app import admin_db
app.include_router(admin_db.router)
