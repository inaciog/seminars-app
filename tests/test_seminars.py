"""
Tests for seminars API.
"""

import pytest
from datetime import date, timedelta

from app.main import Seminar, Speaker, Room


def test_list_seminars(client, auth_headers):
    """Test listing seminars."""
    response = client.get("/api/seminars", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)


def test_create_seminar(client, auth_headers, db_session):
    """Test creating a seminar."""
    # Create speaker and room first
    speaker = Speaker(name="Test Speaker", email="test@example.com", affiliation="Test University")
    room = Room(name="B-202")
    db_session.add(speaker)
    db_session.add(room)
    db_session.commit()
    db_session.refresh(speaker)
    db_session.refresh(room)

    seminar_data = {
        "title": "New Test Seminar",
        "date": (date.today() + timedelta(days=14)).isoformat(),
        "start_time": "14:00",
        "end_time": "15:30",
        "room_id": room.id,
        "speaker_id": speaker.id,
    }

    response = client.post("/api/seminars", json=seminar_data, headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert data["title"] == "New Test Seminar"
    assert "id" in data


def test_get_seminar(client, auth_headers, db_session):
    """Test getting a specific seminar."""
    speaker = Speaker(name="Test Speaker", email="test@example.com", affiliation="Test University")
    room = Room(name="C-303")
    db_session.add(speaker)
    db_session.add(room)
    db_session.commit()
    db_session.refresh(speaker)
    db_session.refresh(room)

    seminar = Seminar(
        title="Single Test Seminar",
        date=date.today() + timedelta(days=7),
        start_time="14:00",
        end_time="15:30",
        room_id=room.id,
        speaker_id=speaker.id,
        status="planned",
    )
    db_session.add(seminar)
    db_session.commit()
    db_session.refresh(seminar)

    response = client.get(f"/api/seminars/{seminar.id}", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert data["title"] == "Single Test Seminar"


def test_update_seminar(client, auth_headers, db_session):
    """Test updating a seminar."""
    speaker = Speaker(name="Test Speaker", email="test@example.com", affiliation="Test University")
    room = Room(name="D-404")
    db_session.add(speaker)
    db_session.add(room)
    db_session.commit()
    db_session.refresh(speaker)
    db_session.refresh(room)

    seminar = Seminar(
        title="Update Test Seminar",
        date=date.today() + timedelta(days=7),
        start_time="14:00",
        end_time="15:30",
        room_id=room.id,
        speaker_id=speaker.id,
        status="planned",
    )
    db_session.add(seminar)
    db_session.commit()
    db_session.refresh(seminar)

    updates = {
        "title": "Updated Title",
        "room_booked": True,
    }

    response = client.put(f"/api/seminars/{seminar.id}", json=updates, headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert data["title"] == "Updated Title"


def test_delete_seminar(client, auth_headers, db_session):
    """Test deleting a seminar."""
    speaker = Speaker(name="Test Speaker", email="test@example.com", affiliation="Test University")
    room = Room(name="E-505")
    db_session.add(speaker)
    db_session.add(room)
    db_session.commit()
    db_session.refresh(speaker)
    db_session.refresh(room)

    seminar = Seminar(
        title="Delete Test Seminar",
        date=date.today() + timedelta(days=7),
        start_time="14:00",
        end_time="15:30",
        room_id=room.id,
        speaker_id=speaker.id,
        status="planned",
    )
    db_session.add(seminar)
    db_session.commit()
    db_session.refresh(seminar)
    seminar_id = seminar.id

    response = client.delete(f"/api/seminars/{seminar_id}", headers=auth_headers)
    assert response.status_code == 200

    # Verify deletion with fresh session
    db_session.expire_all()
    deleted = db_session.get(Seminar, seminar_id)
    assert deleted is None


def test_update_seminar_details_persists_internal_notes(client, auth_headers, db_session):
    """Internal notes and adjacent seminar details fields persist via details API."""
    speaker = Speaker(name="Details Speaker", email="details@example.com", affiliation="Test University")
    room = Room(name="F-606")
    db_session.add(speaker)
    db_session.add(room)
    db_session.commit()
    db_session.refresh(speaker)
    db_session.refresh(room)

    seminar = Seminar(
        title="Details Test Seminar",
        date=date.today() + timedelta(days=10),
        start_time="14:00",
        end_time="15:30",
        room_id=room.id,
        speaker_id=speaker.id,
        status="planned",
    )
    db_session.add(seminar)
    db_session.commit()
    db_session.refresh(seminar)

    # Ensure details record exists (endpoint auto-creates it)
    get_response = client.get(f"/api/v1/seminars/seminars/{seminar.id}/details", headers=auth_headers)
    assert get_response.status_code == 200

    update_payload = {
        "notes": "Internal scheduling note for organizer",
        "ticket_purchase_info": "Book refundable fare and keep receipt.",
    }
    update_response = client.put(
        f"/api/v1/seminars/seminars/{seminar.id}/details",
        json=update_payload,
        headers=auth_headers,
    )
    assert update_response.status_code == 200

    verify_response = client.get(f"/api/v1/seminars/seminars/{seminar.id}/details", headers=auth_headers)
    assert verify_response.status_code == 200
    body = verify_response.json()

    assert body["notes"] == "Internal scheduling note for organizer"
    assert body["info"]["ticket_purchase_info"] == "Book refundable fare and keep receipt."
