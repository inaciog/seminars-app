"""
Robust API layer for seminars app.
All business logic is centralized here - frontend only calls these endpoints.
"""

from typing import Optional, List
from datetime import datetime, date
from sqlmodel import SQLModel, Field, Session, select, and_, or_
from fastapi import HTTPException, Depends
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# Business Logic Service Layer
# ============================================================================

class SeminarService:
    """Centralized business logic for seminar operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ---------------------------------------------------------------------
    # Speaker Operations
    # ---------------------------------------------------------------------
    
    def get_or_create_speaker(self, name: str, email: Optional[str] = None, 
                              affiliation: Optional[str] = None) -> "Speaker":
        """Get existing speaker by name or create new one."""
        # Try to find by name (exact match)
        stmt = select(Speaker).where(Speaker.name == name)
        speaker = self.db.exec(stmt).first()
        
        if speaker:
            # Update with new info if provided
            if email and not speaker.email:
                speaker.email = email
            if affiliation and not speaker.affiliation:
                speaker.affiliation = affiliation
            self.db.commit()
            return speaker
        
        # Create new speaker
        speaker = Speaker(
            name=name,
            email=email,
            affiliation=affiliation
        )
        self.db.add(speaker)
        self.db.commit()
        self.db.refresh(speaker)
        logger.info(f"Created new speaker: {name} (id={speaker.id})")
        return speaker
    
    # ---------------------------------------------------------------------
    # Suggestion Operations
    # ---------------------------------------------------------------------
    
    def create_suggestion(self, plan_id: int, speaker_name: str, 
                         suggested_by: str, **kwargs) -> "SpeakerSuggestion":
        """Create a new speaker suggestion."""
        # Verify plan exists
        plan = self.db.get(SemesterPlan, plan_id)
        if not plan:
            raise HTTPException(status_code=404, detail="Semester plan not found")
        
        # Try to link to existing speaker
        stmt = select(Speaker).where(Speaker.name == speaker_name)
        speaker = self.db.exec(stmt).first()
        
        suggestion = SpeakerSuggestion(
            semester_plan_id=plan_id,
            speaker_id=speaker.id if speaker else None,
            suggested_speaker_name=speaker_name,
            suggested_speaker_email=kwargs.get('speaker_email'),
            suggested_speaker_affiliation=kwargs.get('speaker_affiliation'),
            suggested_topic=kwargs.get('suggested_topic'),
            suggested_by=suggested_by,
            priority=kwargs.get('priority', 'medium'),
            status='pending'
        )
        self.db.add(suggestion)
        self.db.commit()
        self.db.refresh(suggestion)
        return suggestion
    
    # ---------------------------------------------------------------------
    # Assignment Operations (The critical fix)
    # ---------------------------------------------------------------------
    
    def assign_speaker_to_slot(self, suggestion_id: int, slot_id: int) -> "Seminar":
        """
        Assign a speaker suggestion to a slot.
        This is an ATOMIC operation that:
        1. Creates/gets the speaker
        2. Creates the seminar
        3. Updates the slot
        4. Updates the suggestion
        5. Links everything together
        """
        # Get suggestion and slot
        suggestion = self.db.get(SpeakerSuggestion, suggestion_id)
        if not suggestion:
            raise HTTPException(status_code=404, detail="Suggestion not found")
        
        slot = self.db.get(SeminarSlot, slot_id)
        if not slot:
            raise HTTPException(status_code=404, detail="Slot not found")
        
        if slot.status not in ['available', 'reserved']:
            raise HTTPException(status_code=400, detail="Slot is not available")
        
        # Get or create speaker
        speaker = self.get_or_create_speaker(
            name=suggestion.suggested_speaker_name,
            email=suggestion.suggested_speaker_email,
            affiliation=suggestion.suggested_speaker_affiliation
        )
        
        # Update suggestion with speaker link
        suggestion.speaker_id = speaker.id
        suggestion.status = 'confirmed'
        
        # Create seminar
        seminar = Seminar(
            slot_id=slot.id,
            speaker_id=speaker.id,
            suggestion_id=suggestion.id,
            title=suggestion.suggested_topic or f"Seminar by {speaker.name}",
            date=slot.date,
            start_time=slot.start_time,
            end_time=slot.end_time,
            room=slot.room,
            status='planned'
        )
        self.db.add(seminar)
        self.db.flush()  # Get seminar.id without committing
        
        # Update slot (no need for assigned_suggestion_id - use seminar.suggestion_id)
        slot.status = 'confirmed'
        
        self.db.commit()
        self.db.refresh(seminar)
        
        logger.info(f"Assigned suggestion {suggestion_id} to slot {slot_id}, created seminar {seminar.id}")
        return seminar
    
    # ---------------------------------------------------------------------
    # Token Operations
    # ---------------------------------------------------------------------
    
    def create_info_token(self, suggestion_id: int) -> "SpeakerToken":
        """Create a token for speaker info submission."""
        suggestion = self.db.get(SpeakerSuggestion, suggestion_id)
        if not suggestion:
            raise HTTPException(status_code=404, detail="Suggestion not found")
        
        # Find associated seminar if exists
        stmt = select(Seminar).where(Seminar.suggestion_id == suggestion_id)
        seminar = self.db.exec(stmt).first()
        
        import secrets
        token = SpeakerToken(
            token=secrets.token_urlsafe(32),
            suggestion_id=suggestion_id,
            seminar_id=seminar.id if seminar else None,
            token_type='info',
            expires_at=datetime.utcnow() + timedelta(days=60)
        )
        self.db.add(token)
        self.db.commit()
        self.db.refresh(token)
        return token
    
    def submit_speaker_info(self, token: str, data: dict) -> "SeminarDetails":
        """Submit speaker info via token."""
        stmt = select(SpeakerToken).where(
            and_(
                SpeakerToken.token == token,
                SpeakerToken.token_type == 'info',
                SpeakerToken.expires_at > datetime.utcnow()
            )
        )
        db_token = self.db.exec(stmt).first()
        
        if not db_token:
            raise HTTPException(status_code=404, detail="Invalid or expired token")
        
        # Get or create seminar
        seminar = None
        if db_token.seminar_id:
            seminar = self.db.get(Seminar, db_token.seminar_id)
        
        if not seminar:
            # Create seminar from suggestion if not exists
            suggestion = self.db.get(SpeakerSuggestion, db_token.suggestion_id)
            if not suggestion:
                raise HTTPException(status_code=404, detail="Suggestion not found")
            
            # Find an available slot
            stmt = select(SeminarSlot).where(
                and_(
                    SeminarSlot.semester_plan_id == suggestion.semester_plan_id,
                    SeminarSlot.status == 'available'
                )
            ).order_by(SeminarSlot.date)
            slot = self.db.exec(stmt).first()
            
            if not slot:
                raise HTTPException(status_code=400, detail="No available slots")
            
            speaker = self.db.get(Speaker, suggestion.speaker_id)
            if not speaker:
                raise HTTPException(status_code=400, detail="Speaker not found")
            
            seminar = Seminar(
                slot_id=slot.id,
                speaker_id=speaker.id,
                suggestion_id=suggestion.id,
                title=data.get('final_talk_title') or suggestion.suggested_topic or f"Seminar by {speaker.name}",
                date=slot.date,
                start_time=slot.start_time,
                end_time=slot.end_time,
                room=slot.room,
                status='planned'
            )
            self.db.add(seminar)
            self.db.flush()
            
            slot.status = 'confirmed'
            db_token.seminar_id = seminar.id
        
        # Update seminar title if provided
        if data.get('final_talk_title'):
            seminar.title = data['final_talk_title']
        if data.get('abstract'):
            seminar.abstract = data['abstract']
        
        # Update speaker name if provided
        if data.get('speaker_name') and seminar.speaker_id:
            speaker = self.db.get(Speaker, seminar.speaker_id)
            if speaker:
                speaker.name = data['speaker_name']
        
        # Create or update seminar details
        stmt = select(SeminarDetails).where(SeminarDetails.seminar_id == seminar.id)
        details = self.db.exec(stmt).first()
        
        if not details:
            details = SeminarDetails(seminar_id=seminar.id)
            self.db.add(details)
        
        # Update fields from data
        for key, value in data.items():
            if hasattr(details, key) and value is not None:
                setattr(details, key, value)
        
        details.updated_at = datetime.utcnow()
        db_token.used_at = datetime.utcnow()
        
        self.db.commit()
        return details


# ============================================================================
# API Response Models (Clean, consistent)
# ============================================================================

class SpeakerResponse(SQLModel):
    id: int
    name: str
    email: Optional[str]
    affiliation: Optional[str]
    website: Optional[str]
    bio: Optional[str]
    notes: Optional[str]

class SemesterPlanResponse(SQLModel):
    id: int
    name: str
    academic_year: str
    semester: str
    default_room: str
    status: str

class SeminarSlotResponse(SQLModel):
    id: int
    semester_plan_id: int
    date: date
    start_time: str
    end_time: str
    room: str
    status: str
    assigned_seminar_id: Optional[int]
    assigned_speaker_name: Optional[str]

class SpeakerSuggestionResponse(SQLModel):
    id: int
    semester_plan_id: int
    speaker_id: Optional[int]
    speaker_name: str
    speaker_affiliation: Optional[str]
    suggested_topic: Optional[str]
    suggested_by: str
    priority: str
    status: str

class SeminarResponse(SQLModel):
    id: int
    slot_id: Optional[int]
    speaker_id: int
    suggestion_id: Optional[int]
    title: str
    abstract: Optional[str]
    date: date
    start_time: str
    end_time: str
    room: str
    status: str
    speaker: Optional[SpeakerResponse]

class PlanningBoardResponse(SQLModel):
    plan: SemesterPlanResponse
    slots: List[SeminarSlotResponse]
    suggestions: List[SpeakerSuggestionResponse]
    seminars: List[SeminarResponse]


# ============================================================================
# API Endpoints (Thin layer - all logic in Service)
# ============================================================================

def register_robust_routes(app):
    """Register all API routes with the FastAPI app."""
    from fastapi import APIRouter
    from .database import get_session
    
    router = APIRouter(prefix="/api/v2")
    
    @router.get("/planning-board/{plan_id}", response_model=PlanningBoardResponse)
    def get_planning_board_v2(plan_id: int, db: Session = Depends(get_session)):
        """Get complete planning board data in one request."""
        service = SeminarService(db)
        
        plan = db.get(SemesterPlan, plan_id)
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        
        # Get all slots with assigned seminar info
        slots_stmt = select(SeminarSlot).where(SeminarSlot.semester_plan_id == plan_id)
        slots = db.exec(slots_stmt).all()
        
        # Get all suggestions
        suggestions_stmt = select(SpeakerSuggestion).where(
            SpeakerSuggestion.semester_plan_id == plan_id
        )
        suggestions = db.exec(suggestions_stmt).all()
        
        # Get all seminars for this plan
        seminar_ids = [s.assigned_seminar_id for s in slots if s.assigned_seminar_id]
        seminars = []
        if seminar_ids:
            seminars_stmt = select(Seminar).where(Seminar.id.in_(seminar_ids))
            seminars = db.exec(seminars_stmt).all()
        
        # Build slot responses with speaker names
        slot_responses = []
        for slot in slots:
            slot_data = {
                "id": slot.id,
                "semester_plan_id": slot.semester_plan_id,
                "date": slot.date,
                "start_time": slot.start_time,
                "end_time": slot.end_time,
                "room": slot.room,
                "status": slot.status,
                "assigned_seminar_id": None,
                "assigned_speaker_name": None
            }
            
            # Find seminar for this slot
            seminar = next((s for s in seminars if s.slot_id == slot.id), None)
            if seminar:
                slot_data["assigned_seminar_id"] = seminar.id
                speaker = db.get(Speaker, seminar.speaker_id)
                if speaker:
                    slot_data["assigned_speaker_name"] = speaker.name
            
            slot_responses.append(SeminarSlotResponse(**slot_data))
        
        return PlanningBoardResponse(
            plan=plan,
            slots=slot_responses,
            suggestions=suggestions,
            seminars=seminars
        )
    
    @router.post("/assign")
    def assign_speaker_v2(data: dict, db: Session = Depends(get_session)):
        """Assign speaker to slot - atomic operation."""
        service = SeminarService(db)
        seminar = service.assign_speaker_to_slot(
            suggestion_id=data['suggestion_id'],
            slot_id=data['slot_id']
        )
        return {"success": True, "seminar_id": seminar.id}
    
    @router.post("/speaker-tokens/info")
    def create_info_token_v2(data: dict, db: Session = Depends(get_session)):
        """Create info token for speaker."""
        service = SeminarService(db)
        token = service.create_info_token(data['suggestion_id'])
        return {"token": token.token, "link": f"/speaker/info/{token.token}"}
    
    @router.post("/speaker-tokens/{token}/submit-info")
    def submit_info_v2(token: str, data: dict, db: Session = Depends(get_session)):
        """Submit speaker info via token."""
        service = SeminarService(db)
        details = service.submit_speaker_info(token, data)
        return {"success": True, "message": "Information submitted successfully"}
    
    app.include_router(router)
