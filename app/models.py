"""
Database models for seminars-app.
"""

from datetime import datetime, date, time
from typing import Optional
from enum import Enum

from sqlmodel import SQLModel, Field, Relationship


class SeminarStatus(str, Enum):
    PLANNED = "planned"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class Speaker(SQLModel, table=True):
    """A speaker who presents at seminars."""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    email: str
    affiliation: str
    website: Optional[str] = None
    bio: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    seminars: list["Seminar"] = Relationship(back_populates="speaker")


class Seminar(SQLModel, table=True):
    """A seminar event."""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    abstract: Optional[str] = None
    
    # Date and time
    date: date
    start_time: time
    end_time: time
    
    # Location
    room: str
    building: Optional[str] = None
    
    # Speaker (can be null if TBD)
    speaker_id: Optional[int] = Field(default=None, foreign_key="speaker.id")
    speaker: Optional[Speaker] = Relationship(back_populates="seminars")
    
    # Status
    status: SeminarStatus = Field(default=SeminarStatus.PLANNED)
    
    # Organization
    series: Optional[str] = None  # e.g., "Macro Workshop", "Job Market"
    organizer_notes: Optional[str] = None
    
    # Bureaucracy tracking
    room_booked: bool = False
    catering_ordered: bool = False
    announcement_sent: bool = False
    calendar_invite_sent: bool = False
    reimbursement_initiated: bool = False
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class SeminarTemplate(SQLModel, table=True):
    """Templates for common seminar types (for quick creation)."""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    
    # Default values
    default_room: Optional[str] = None
    default_building: Optional[str] = None
    default_duration_minutes: int = 90
    default_series: Optional[str] = None
    
    # Checklist items (stored as JSON list)
    checklist_items: str = "[]"  # JSON array of strings


# Planning models

class SemesterPlanStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class SemesterPlan(SQLModel, table=True):
    """A semester's seminar schedule plan."""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)  # e.g., "Spring 2024"
    academic_year: str  # e.g., "2023-2024"
    semester: str  # "fall" or "spring"
    
    # Default settings for this semester
    default_room: str
    default_start_time: str = "14:00"  # HH:MM format
    default_duration_minutes: int = 90
    
    # Planning status
    status: SemesterPlanStatus = Field(default=SemesterPlanStatus.DRAFT)
    
    # Notes
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class SeminarSlot(SQLModel, table=True):
    """A specific slot in a semester plan."""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    semester_plan_id: int = Field(foreign_key="semesterplan.id")
    
    # Slot details
    date: date
    start_time: str  # HH:MM format
    end_time: str    # HH:MM format
    room: str
    
    # Assignment
    status: str = "available"  # available, reserved, confirmed, cancelled
    assigned_seminar_id: Optional[int] = Field(default=None, foreign_key="seminar.id")
    
    # Notes
    notes: Optional[str] = None


class SpeakerSuggestionStatus(str, Enum):
    PENDING = "pending"
    CONTACTED = "contacted"
    CHECKING_AVAILABILITY = "checking_availability"
    AVAILABILITY_RECEIVED = "availability_received"
    CONFIRMED = "confirmed"
    DECLINED = "declined"
    COMPLETED = "completed"


class SpeakerSuggestion(SQLModel, table=True):
    """A speaker suggestion by a faculty member."""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Who suggested
    suggested_by: str  # Faculty member name
    suggested_by_email: Optional[str] = None
    
    # Speaker info (can link to existing speaker or be new)
    speaker_id: Optional[int] = Field(default=None, foreign_key="speaker.id")
    speaker_name: str
    speaker_email: Optional[str] = None
    speaker_affiliation: Optional[str] = None
    
    # Suggestion details
    suggested_topic: Optional[str] = None
    reason: Optional[str] = None
    priority: str = "medium"  # low, medium, high
    
    # Status tracking
    status: SpeakerSuggestionStatus = Field(default=SpeakerSuggestionStatus.PENDING)
    semester_plan_id: Optional[int] = Field(default=None, foreign_key="semesterplan.id")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    contacted_at: Optional[datetime] = None
    confirmed_at: Optional[datetime] = None


class SpeakerAvailability(SQLModel, table=True):
    """Date ranges when a speaker is available."""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    suggestion_id: int = Field(foreign_key="speakersuggestion.id")
    
    # Available date range (inclusive)
    start_date: date
    end_date: date
    preference: str = "available"  # preferred, available, not_preferred
    
    # Constraints
    earliest_time: Optional[str] = None  # HH:MM
    latest_time: Optional[str] = None    # HH:MM
    notes: Optional[str] = None


class SpeakerInfo(SQLModel, table=True):
    """Comprehensive information collected from speakers."""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    suggestion_id: int = Field(foreign_key="speakersuggestion.id")
    
    # Talk information
    talk_title: Optional[str] = None
    abstract: Optional[str] = None
    
    # Technical requirements
    needs_projector: bool = True
    needs_microphone: bool = False
    special_requirements: Optional[str] = None
    
    # Guesthouse accommodation dates
    check_in_date: Optional[date] = None
    check_out_date: Optional[date] = None
    
    # Travel information (for budgeting)
    departure_city: Optional[str] = None
    estimated_travel_cost: Optional[float] = None
    needs_accommodation: bool = True
    accommodation_nights: Optional[int] = None
    estimated_hotel_cost: Optional[float] = None
    travel_method: Optional[str] = None
    
    # Passport information
    passport_number: Optional[str] = None
    passport_country: Optional[str] = None
    
    # Payment information
    payment_email: Optional[str] = None
    beneficiary_name: Optional[str] = None
    bank_account_number: Optional[str] = None
    bank_name: Optional[str] = None
    bank_address: Optional[str] = None
    swift_code: Optional[str] = None
    currency: Optional[str] = None
    beneficiary_address: Optional[str] = None
    
    # Documents
    cv_file_path: Optional[str] = None
    photo_file_path: Optional[str] = None
    passport_file_path: Optional[str] = None
    flight_booking_file_path: Optional[str] = None
    has_been_informed_of_budget: bool = False
    
    # Status
    info_complete: bool = False
    submitted_at: Optional[datetime] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class UploadedFile(SQLModel, table=True):
    """Generic file upload tracking with safe storage naming."""
    
    __tablename__ = "uploaded_files"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Reference to what this file belongs to
    entity_type: str = Field(index=True)
    entity_id: int = Field(index=True)
    
    # File categorization
    file_category: Optional[str] = None
    
    # Original file info
    original_filename: str
    original_extension: Optional[str] = None
    content_type: Optional[str] = None
    file_size: Optional[int] = None
    
    # Safe storage info
    storage_filename: str
    storage_path: str
    
    # Upload metadata
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    uploaded_by: Optional[str] = None
    
    # Optional description
    description: Optional[str] = None


class Activity(SQLModel, table=True):
    """Activity log for audit trail."""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Actor (from JWT)
    actor_user_id: Optional[str] = None
    actor_role: Optional[str] = None
    
    # Activity details
    activity_type: str
    target_type: str
    target_id: Optional[int] = None
    target_name: Optional[str] = None
    title: str
    description: Optional[str] = None
    
    # Timestamp
    created_at: datetime = Field(default_factory=datetime.utcnow)
