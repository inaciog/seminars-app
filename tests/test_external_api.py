"""
Tests for external API (dashboard integration).
"""

import pytest
from datetime import date, timedelta

from app.main import Seminar, Speaker, Room, settings


def test_external_stats(client, db_session):
    """Test external stats endpoint."""
    speaker = Speaker(name="Test Speaker", email="test@example.com", affiliation="Test University")
    room = Room(name="A-101")
    db_session.add(speaker)
    db_session.add(room)
    db_session.commit()
    db_session.refresh(speaker)
    db_session.refresh(room)

    seminar = Seminar(
        title="Test Seminar",
        date=date.today() + timedelta(days=7),
        start_time="14:00",
        end_time="15:30",
        room_id=room.id,
        speaker_id=speaker.id,
        status="planned",
    )
    db_session.add(seminar)
    db_session.commit()

    response = client.get(f"/api/external/stats?secret={settings.api_secret}")
    assert response.status_code == 200

    data = response.json()
    assert data["upcoming_seminars"] == 1
    assert data["pending_tasks"] >= 0
    assert "total_speakers" in data


def test_external_upcoming(client, db_session):
    """Test external upcoming endpoint."""
    response = client.get(f"/api/external/upcoming?secret={settings.api_secret}&limit=5")
    assert response.status_code == 200

    data = response.json()
    assert "seminars" in data
    assert isinstance(data["seminars"], list)


def test_external_invalid_secret(client):
    """Test external endpoint with invalid secret returns 401."""
    response = client.get("/api/external/stats?secret=invalid-secret")
    assert response.status_code == 401
