"""
Robust deletion handlers for seminars app.
Ensures data consistency when deleting entities.
"""

from sqlmodel import Session, select
from typing import Optional
import logging

logger = logging.getLogger(__name__)

def delete_speaker_robust(speaker_id: int, db: Session) -> dict:
    """
    Delete a speaker and handle all related data.
    
    Policy: Prevent deletion if speaker has seminars.
    This maintains data integrity - we don't want orphaned seminars.
    """
    from app.main import Speaker, Seminar, SpeakerSuggestion
    
    speaker = db.get(Speaker, speaker_id)
    if not speaker:
        return {"success": False, "error": "Speaker not found"}
    
    # Check for related seminars
    seminars_stmt = select(Seminar).where(Seminar.speaker_id == speaker_id)
    seminars = db.exec(seminars_stmt).all()
    if seminars:
        seminar_titles = [s.title for s in seminars[:3]]
        return {
            "success": False, 
            "error": f"Cannot delete speaker: they have {len(seminars)} seminar(s). Delete seminars first or reassign them.",
            "seminars": seminar_titles
        }
    
    # Clear speaker_id from suggestions (but keep suggestions)
    suggestions_stmt = select(SpeakerSuggestion).where(SpeakerSuggestion.speaker_id == speaker_id)
    suggestions = db.exec(suggestions_stmt).all()
    for sg in suggestions:
        sg.speaker_id = None
        logger.info(f"Cleared speaker_id from suggestion {sg.id}")
    
    db.delete(speaker)
    db.commit()
    
    return {
        "success": True, 
        "message": f"Speaker '{speaker.name}' deleted",
        "cleared_suggestions": len(suggestions)
    }

def delete_room_robust(room_id: int, db: Session) -> dict:
    """
    Delete a room and handle all related data.
    
    Policy: Clear room_id from seminars, don't delete them.
    """
    from app.main import Room, Seminar
    
    room = db.get(Room, room_id)
    if not room:
        return {"success": False, "error": "Room not found"}
    
    # Clear room_id from all seminars
    seminars_stmt = select(Seminar).where(Seminar.room_id == room_id)
    seminars = db.exec(seminars_stmt).all()
    for seminar in seminars:
        seminar.room_id = None
        logger.info(f"Cleared room_id from seminar {seminar.id}")
    
    db.delete(room)
    db.commit()
    
    return {
        "success": True,
        "message": f"Room '{room.name}' deleted",
        "cleared_seminars": len(seminars)
    }

def delete_seminar_robust(seminar_id: int, db: Session) -> dict:
    """
    Delete a seminar and handle all related data.
    
    Policy: 
    - Clear slot references
    - Delete uploaded files from disk
    - Delete seminar details
    - Keep speaker (they might have other seminars)
    """
    from app.main import Seminar, SeminarSlot, UploadedFile, SeminarDetails, Path, settings
    
    seminar = db.get(Seminar, seminar_id)
    if not seminar:
        return {"success": False, "error": "Seminar not found"}
    
    # Clear slot references
    slots_stmt = select(SeminarSlot).where(SeminarSlot.assigned_seminar_id == seminar_id)
    slots = db.exec(slots_stmt).all()
    for slot in slots:
        slot.assigned_seminar_id = None
        slot.assigned_suggestion_id = None
        slot.status = 'available'
        logger.info(f"Cleared seminar reference from slot {slot.id}")
    
    # Delete uploaded files from disk
    files_stmt = select(UploadedFile).where(UploadedFile.seminar_id == seminar_id)
    files = db.exec(files_stmt).all()
    deleted_files = 0
    for file in files:
        file_path = Path(settings.uploads_dir) / file.storage_filename
        if file_path.exists():
            file_path.unlink()
            deleted_files += 1
        db.delete(file)
    
    # Delete seminar details
    details_stmt = select(SeminarDetails).where(SeminarDetails.seminar_id == seminar_id)
    details = db.exec(details_stmt).first()
    if details:
        db.delete(details)
    
    title = seminar.title
    db.delete(seminar)
    db.commit()
    
    return {
        "success": True,
        "message": f"Seminar '{title}' deleted",
        "cleared_slots": len(slots),
        "deleted_files": deleted_files
    }

def delete_semester_plan_robust(plan_id: int, db: Session) -> dict:
    """
    Delete a semester plan and ALL related data.
    
    Policy: Cascade delete everything related to this plan.
    This is a destructive operation.
    """
    from app.main import SemesterPlan, SeminarSlot, SpeakerSuggestion, SpeakerToken, Seminar, ActivityEvent, SpeakerWorkflow, SpeakerAvailability
    
    plan = db.get(SemesterPlan, plan_id)
    if not plan:
        return {"success": False, "error": "Plan not found"}
    
    # Get all slots for this plan
    slots_stmt = select(SeminarSlot).where(SeminarSlot.semester_plan_id == plan_id)
    slots = db.exec(slots_stmt).all()
    
    # Get all suggestions for this plan
    suggestions_stmt = select(SpeakerSuggestion).where(SpeakerSuggestion.semester_plan_id == plan_id)
    suggestions = db.exec(suggestions_stmt).all()
    suggestion_ids = [sg.id for sg in suggestions]
    
    # Delete tokens for these suggestions
    if suggestion_ids:
        tokens_stmt = select(SpeakerToken).where(SpeakerToken.suggestion_id.in_(suggestion_ids))
        tokens = db.exec(tokens_stmt).all()
        for token in tokens:
            db.delete(token)
        logger.info(f"Deleted {len(tokens)} tokens")
    
    # Delete seminars that were created from these suggestions
    # (seminars that have their slot in this plan)
    slot_ids = [s.id for s in slots]
    if slot_ids:
        seminars_stmt = select(Seminar).where(Seminar.slot_id.in_(slot_ids))
        seminars = db.exec(seminars_stmt).all()
        for seminar in seminars:
            # Use robust delete to clean up files, details, etc.
            delete_seminar_robust(seminar.id, db)
        logger.info(f"Deleted {len(seminars)} seminars")
    
    # Delete activity events for this plan
    events_stmt = select(ActivityEvent).where(ActivityEvent.semester_plan_id == plan_id)
    for evt in db.exec(events_stmt).all():
        db.delete(evt)
    
    # Delete speaker workflows for these suggestions
    if suggestion_ids:
        workflows_stmt = select(SpeakerWorkflow).where(SpeakerWorkflow.suggestion_id.in_(suggestion_ids))
        for wf in db.exec(workflows_stmt).all():
            db.delete(wf)
    
    # Delete speaker availability for these suggestions
    if suggestion_ids:
        avail_stmt = select(SpeakerAvailability).where(SpeakerAvailability.suggestion_id.in_(suggestion_ids))
        for av in db.exec(avail_stmt).all():
            db.delete(av)
    
    # Delete slots
    for slot in slots:
        db.delete(slot)
    
    # Delete suggestions
    for suggestion in suggestions:
        db.delete(suggestion)
    
    # Delete plan
    plan_name = plan.name
    db.delete(plan)
    db.commit()
    
    return {
        "success": True,
        "message": f"Plan '{plan_name}' and all related data deleted",
        "deleted_slots": len(slots),
        "deleted_suggestions": len(suggestions)
    }

def delete_slot_robust(slot_id: int, db: Session) -> dict:
    """
    Delete a slot and handle related data.
    
    Policy: If slot has an assigned seminar, unassign it first (don't delete the seminar).
    """
    from app.main import SeminarSlot, Seminar
    
    slot = db.get(SeminarSlot, slot_id)
    if not slot:
        return {"success": False, "error": "Slot not found"}
    
    # If there's an assigned seminar, just clear the reference (don't delete seminar)
    if slot.assigned_seminar_id:
        seminar = db.get(Seminar, slot.assigned_seminar_id)
        if seminar:
            # Clear the slot_id from seminar
            seminar.slot_id = None
            logger.info(f"Cleared slot_id from seminar {seminar.id}")
    
    date_str = slot.date.isoformat()
    db.delete(slot)
    db.commit()
    
    return {
        "success": True,
        "message": f"Slot for {date_str} deleted"
    }

def delete_suggestion_robust(suggestion_id: int, db: Session) -> dict:
    """
    Delete a speaker suggestion and related data.
    
    Policy: 
    - Delete associated tokens
    - If suggestion is assigned to a slot, clear the slot
    - Don't delete the speaker (they might exist independently)
    """
    from app.main import SpeakerSuggestion, SpeakerToken, SeminarSlot
    
    suggestion = db.get(SpeakerSuggestion, suggestion_id)
    if not suggestion:
        return {"success": False, "error": "Suggestion not found"}
    
    # Delete tokens
    tokens_stmt = select(SpeakerToken).where(SpeakerToken.suggestion_id == suggestion_id)
    tokens = db.exec(tokens_stmt).all()
    for token in tokens:
        db.delete(token)
    
    # Clear slot if assigned
    slots_stmt = select(SeminarSlot).where(SeminarSlot.assigned_suggestion_id == suggestion_id)
    slots = db.exec(slots_stmt).all()
    for slot in slots:
        slot.assigned_suggestion_id = None
        slot.assigned_seminar_id = None
        slot.status = 'available'
        logger.info(f"Cleared assignment from slot {slot.id}")
    
    speaker_name = suggestion.speaker_name
    db.delete(suggestion)
    db.commit()
    
    return {
        "success": True,
        "message": f"Suggestion for '{speaker_name}' deleted",
        "deleted_tokens": len(tokens),
        "cleared_slots": len(slots)
    }
