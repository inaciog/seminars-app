"""
Tests for external API.
"""

import pytest
from datetime import date, timedelta

from app.models import Seminar, SeminarStatus, Speaker


def test_external_stats(client, db_session):
    """Test external stats endpoint."""
    settings = get_settings()
    
    # Create test data
    speaker = Speaker(name="Test Speaker", email="test@example.com", affiliation="Test University")
    db_session.add(speaker)
    db_session.commit()
    
    seminar = Seminar(
        title="Test Seminar",
        date=date.today() + timedelta(days=7),
        start_time="14:00",
        end_time="15:30",
        room="A-101",
        speaker_id=speaker.id,
        status=SeminarStatus.PLANNED
    )
    db_session.add(seminar)
    db_session.commit()
    
    # Test stats endpoint
    response = client.get(f"/api/external/stats?secret={settings.api_secret}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["total_upcoming"] == 1
    assert data["pending_tasks"] >= 2  # room_booked and announcement_sent


def test_external_upcoming(client, db_session):
    """Test external upcoming endpoint."""
    settings = get_settings()
    
    response = client.get(f"/api/external/upcoming?secret={settings.api_secret}&limit=5")
    assert response.status_code == 200
    
    data = response.json()
    assert "seminars" in data
    assert "count" in data


def test_external_invalid_secret(client):
    """Test external endpoint with invalid secret."""
    response = client.get("/api/external/stats?secret=invalid-secret")
    assert response.status_code == 403
