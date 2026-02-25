"""
Database Models for Seminars App

All SQLModel models defined here to avoid circular imports.
"""

from datetime import datetime, date as date_type
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship


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
    assigned_slot: Optional["SeminarSlot"] = Relationship(sa_relationship_kwargs={"primaryjoin": "Seminar.id == SeminarSlot.assigned_seminar_id", "remote_side": "SeminarSlot.assigned_seminar_id", "uselist": False})


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
    assigned_seminar: Optional[Seminar] = Relationship(sa_relationship_kwargs={"overlaps": "assigned_slot"})


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
    token_type: str  # 'availability', 'info', or 'status'
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
    
    # Ticket purchase info (shown when proposal is approved)
    ticket_purchase_info: Optional[str] = None
    
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    seminar: Seminar = Relationship()


class SpeakerWorkflow(SQLModel, table=True):
    __tablename__ = "speaker_workflows"

    id: Optional[int] = Field(default=None, primary_key=True)
    suggestion_id: int = Field(foreign_key="speaker_suggestions.id", unique=True, index=True)
    request_available_dates_sent: bool = Field(default=False)
    availability_dates_received: bool = Field(default=False)
    speaker_notified_of_date: bool = Field(default=False)
    meal_ok: bool = Field(default=False)
    guesthouse_hotel_reserved: bool = Field(default=False)
    proposal_submitted: bool = Field(default=False)
    proposal_approved: bool = Field(default=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ActivityEvent(SQLModel, table=True):
    __tablename__ = "activity_events"

    id: Optional[int] = Field(default=None, primary_key=True)
    semester_plan_id: Optional[int] = Field(default=None, foreign_key="semester_plans.id", index=True)
    event_type: str = Field(index=True)
    summary: str
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    actor: Optional[str] = None
    details_json: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
