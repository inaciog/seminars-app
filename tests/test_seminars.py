"""
Tests for seminars API.
"""

import pytest
from datetime import date, timedelta

from app.models import Seminar, SeminarStatus, Speaker


def test_list_seminars(client, auth_headers):
    """Test listing seminars."""
    response = client.get("/api/seminars", headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)


def test_create_seminar(client, auth_headers, db_session):
    """Test creating a seminar."""
    # Create speaker first
    speaker = Speaker(name="Test Speaker", email="test@example.com", affiliation="Test University")
    db_session.add(speaker)
    db_session.commit()
    
    seminar_data = {
        "title": "New Test Seminar",
        "date": (date.today() + timedelta(days=14)).isoformat(),
        "start_time": "14:00",
        "end_time": "15:30",
        "room": "B-202",
        "speaker_id": speaker.id,
        "status": "planned"
    }
    
    response = client.post("/api/seminars", json=seminar_data, headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["title"] == "New Test Seminar"
    assert "id" in data


def test_get_seminar(client, auth_headers, db_session):
    """Test getting a specific seminar."""
    # Create test seminar
    seminar = Seminar(
        title="Single Test Seminar",
        date=date.today() + timedelta(days=7),
        start_time="14:00",
        end_time="15:30",
        room="C-303",
        status=SeminarStatus.PLANNED
    )
    db_session.add(seminar)
    db_session.commit()
    
    response = client.get(f"/api/seminars/{seminar.id}", headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["title"] == "Single Test Seminar"


def test_update_seminar(client, auth_headers, db_session):
    """Test updating a seminar."""
    # Create test seminar
    seminar = Seminar(
        title="Update Test Seminar",
        date=date.today() + timedelta(days=7),
        start_time="14:00",
        end_time="15:30",
        room="D-404",
        status=SeminarStatus.PLANNED
    )
    db_session.add(seminar)
    db_session.commit()
    
    updates = {
        "title": "Updated Title",
        "room_booked": True
    }
    
    response = client.patch(f"/api/seminars/{seminar.id}", json=updates, headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["title"] == "Updated Title"


def test_delete_seminar(client, auth_headers, db_session):
    """Test deleting a seminar."""
    # Create test seminar
    seminar = Seminar(
        title="Delete Test Seminar",
        date=date.today() + timedelta(days=7),
        start_time="14:00",
        end_time="15:30",
        room="E-505",
        status=SeminarStatus.PLANNED
    )
    db_session.add(seminar)
    db_session.commit()
    
    response = client.delete(f"/api/seminars/{seminar.id}", headers=auth_headers)
    assert response.status_code == 200
    
    # Verify deletion
    deleted = db_session.get(Seminar, seminar.id)
    assert deleted is None
