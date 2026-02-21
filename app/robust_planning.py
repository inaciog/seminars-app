"""
Updated planning board endpoint that uses new seminar.slot_id and seminar.suggestion_id
to properly link slots, seminars, and suggestions.
"""

from typing import Optional, List
from datetime import datetime, date as date_type
from sqlmodel import SQLModel, Field, Session, select, and_, or_
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# Updated Planning Board Endpoint (Backward Compatible)
# ============================================================================

async def get_planning_board_robust(plan_id: int, db: Session) -> dict:
    """
    Get planning board data with proper ID-based relationships.
    
    Returns slots with:
    - assigned_seminar_id: from slot.assigned_seminar_id (or via seminar.slot_id)
    - assigned_suggestion_id: from seminar.suggestion_id
    - assigned_speaker_name: from seminar.speaker.name
    """
    from app.main import SemesterPlan, SeminarSlot, SpeakerSuggestion, Seminar, Speaker
    
    plan = db.get(SemesterPlan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Semester plan not found")
    
    # Get all slots for this plan
    slots_stmt = select(SeminarSlot).where(SeminarSlot.semester_plan_id == plan_id).order_by(SeminarSlot.date)
    slots = db.exec(slots_stmt).all()
    
    # Get all suggestions for this plan
    suggestions_stmt = select(SpeakerSuggestion).where(SpeakerSuggestion.semester_plan_id == plan_id)
    suggestions = db.exec(suggestions_stmt).all()
    
    # Get all seminars linked to these slots (via slot_id or assigned_seminar_id)
    slot_ids = [s.id for s in slots]
    assigned_seminar_ids = [s.assigned_seminar_id for s in slots if s.assigned_seminar_id]
    
    # Find seminars by slot_id (new way) or by id in assigned_seminar_ids (old way)
    seminars_stmt = select(Seminar).where(
        or_(
            Seminar.slot_id.in_(slot_ids),
            Seminar.id.in_(assigned_seminar_ids) if assigned_seminar_ids else False
        )
    )
    seminars = db.exec(seminars_stmt).all()
    
    # Build lookup dicts
    seminar_by_id = {s.id: s for s in seminars}
    seminar_by_slot_id = {s.slot_id: s for s in seminars if s.slot_id}
    suggestion_by_id = {s.id: s for s in suggestions}
    
    # Build slots response
    slots_response = []
    for slot in slots:
        slot_data = {
            "id": slot.id,
            "date": slot.date.isoformat(),
            "start_time": slot.start_time,
            "end_time": slot.end_time,
            "room": slot.room,
            "status": slot.status,
            "assigned_seminar_id": None,
            "assigned_suggestion_id": None,
            "assigned_speaker_name": None
        }
        
        # Find seminar for this slot
        seminar = None
        
        # First try: seminar.slot_id (new proper relationship)
        if slot.id in seminar_by_slot_id:
            seminar = seminar_by_slot_id[slot.id]
        
        # Second try: slot.assigned_seminar_id (old relationship)
        elif slot.assigned_seminar_id and slot.assigned_seminar_id in seminar_by_id:
            seminar = seminar_by_id[slot.assigned_seminar_id]
        
        if seminar:
            slot_data["assigned_seminar_id"] = seminar.id
            
            # Get suggestion_id from seminar (new way) or slot (old way)
            suggestion_id = seminar.suggestion_id or slot.assigned_suggestion_id
            if suggestion_id and suggestion_id in suggestion_by_id:
                slot_data["assigned_suggestion_id"] = suggestion_id
            
            # Get speaker name
            speaker = db.get(Speaker, seminar.speaker_id)
            if speaker:
                slot_data["assigned_speaker_name"] = speaker.name
        
        slots_response.append(slot_data)
    
    return {
        "plan": {
            "id": plan.id,
            "name": plan.name,
            "academic_year": plan.academic_year,
            "semester": plan.semester,
            "default_room": plan.default_room,
            "status": plan.status
        },
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
                "availability": [
                    {"id": a.id, "date": a.date.isoformat(), "preference": a.preference}
                    for a in s.availability
                ]
            }
            for s in suggestions
        ]
    }


# ============================================================================
# Updated Assignment Function (Atomic)
# ============================================================================

def assign_speaker_to_slot_robust(suggestion_id: int, slot_id: int, db: Session) -> "Seminar":
    """
    Atomically assign a speaker suggestion to a slot.
    Creates seminar with proper slot_id and suggestion_id links.
    """
    from app.main import SpeakerSuggestion, SeminarSlot, Seminar, Speaker
    
    # Get suggestion and slot
    suggestion = db.get(SpeakerSuggestion, suggestion_id)
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    
    slot = db.get(SeminarSlot, slot_id)
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")
    
    if slot.status not in ['available', 'reserved']:
        raise HTTPException(status_code=400, detail="Slot is not available")
    
    # Get or create speaker
    speaker = None
    if suggestion.speaker_id:
        speaker = db.get(Speaker, suggestion.speaker_id)
    
    if not speaker:
        # Create speaker from suggestion data
        speaker = Speaker(
            name=suggestion.speaker_name,
            email=suggestion.speaker_email,
            affiliation=suggestion.speaker_affiliation
        )
        db.add(speaker)
        db.flush()  # Get speaker.id
        
        # Update suggestion with speaker link
        suggestion.speaker_id = speaker.id
    
    # Create seminar with proper links
    seminar = Seminar(
        slot_id=slot.id,  # NEW: proper link to slot
        suggestion_id=suggestion.id,  # NEW: proper link to suggestion
        speaker_id=speaker.id,
        title=suggestion.suggested_topic or f"Seminar by {speaker.name}",
        date=slot.date,
        start_time=slot.start_time,
        end_time=slot.end_time,
        room=slot.room,
        status='planned'
    )
    db.add(seminar)
    db.flush()  # Get seminar.id
    
    # Update slot (backward compatible)
    slot.assigned_seminar_id = seminar.id
    slot.assigned_suggestion_id = suggestion.id  # Also store here for quick lookup
    slot.status = 'confirmed'
    
    # Update suggestion
    suggestion.status = 'confirmed'
    
    db.commit()
    db.refresh(seminar)
    
    logger.info(f"Assigned suggestion {suggestion_id} to slot {slot_id}, created seminar {seminar.id}")
    return seminar


# ============================================================================
# Updated Info Token Creation
# ============================================================================

def create_info_token_robust(suggestion_id: int, db: Session) -> "SpeakerToken":
    """
    Create info token that works whether or not seminar exists yet.
    """
    from app.main import SpeakerSuggestion, Seminar, SpeakerToken
    import secrets
    
    suggestion = db.get(SpeakerSuggestion, suggestion_id)
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    
    # Find associated seminar if exists
    # Try by suggestion_id first (new way), then by speaker+date matching
    seminar_stmt = select(Seminar).where(Seminar.suggestion_id == suggestion_id)
    seminar = db.exec(seminar_stmt).first()
    
    if not seminar and suggestion.speaker_id:
        # Fallback: find by speaker and date from slot
        from app.main import SeminarSlot
        slot_stmt = select(SeminarSlot).where(
            SeminarSlot.assigned_suggestion_id == suggestion_id
        )
        slot = db.exec(slot_stmt).first()
        
        if slot:
            seminar_stmt = select(Seminar).where(
                and_(
                    Seminar.speaker_id == suggestion.speaker_id,
                    Seminar.date == slot.date
                )
            )
            seminar = db.exec(seminar_stmt).first()
    
    token = SpeakerToken(
        token=secrets.token_urlsafe(32),
        suggestion_id=suggestion_id,
        seminar_id=seminar.id if seminar else None,
        token_type='info',
        expires_at=datetime.utcnow() + timedelta(days=60)
    )
    db.add(token)
    db.commit()
    db.refresh(token)
    
    return token
