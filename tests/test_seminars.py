"""
Tests for seminars API.
"""

import pytest
from datetime import date, timedelta
from uuid import uuid4

from app.main import Seminar, Speaker, Room


def _current_and_other_term_dates() -> tuple[date, date]:
    today = date.today()
    if today.month <= 6:
        return date(today.year, 4, 10), date(today.year, 9, 10)
    return date(today.year, 10, 10), date(today.year, 3, 10)


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


def test_public_page_shows_subscription_links(client, db_session):
    """Public seminar page exposes live subscription links without auth."""
    current_term_date, other_term_date = _current_and_other_term_dates()
    suffix = uuid4().hex[:8]

    speaker = Speaker(name=f"Public Speaker {suffix}", email=f"public-{suffix}@example.com", affiliation="University of Macau")
    room = Room(name=f"Room {suffix}", location="E22")
    db_session.add(speaker)
    db_session.add(room)
    db_session.commit()
    db_session.refresh(speaker)
    db_session.refresh(room)

    current_title = f"Public Calendar Current {suffix}"
    other_title = f"Public Calendar Other {suffix}"
    db_session.add(
        Seminar(
            title=current_title,
            date=current_term_date,
            start_time="14:00",
            end_time="15:30",
            room_id=room.id,
            speaker_id=speaker.id,
            status="planned",
        )
    )
    db_session.add(
        Seminar(
            title=other_title,
            date=other_term_date,
            start_time="16:00",
            end_time="17:00",
            room_id=room.id,
            speaker_id=speaker.id,
            status="planned",
        )
    )
    db_session.commit()

    response = client.get("/public")
    assert response.status_code == 200
    assert current_title in response.text
    assert other_title not in response.text
    assert "Google Calendar" in response.text
    assert "Apple Calendar / iCal" in response.text
    assert "Asia/Macau" in response.text
    assert "https://calendar.google.com/calendar/u/0/r/settings/addbyurl" in response.text
    assert "/public/calendar.ics" in response.text


def test_public_calendar_feed_is_public_and_current_term_only(client, db_session):
    """Public ICS feed stays limited to the same term shown on /public."""
    current_term_date, other_term_date = _current_and_other_term_dates()
    suffix = uuid4().hex[:8]

    speaker = Speaker(name=f"Calendar Feed Speaker {suffix}", email=f"feed-{suffix}@example.com", affiliation="University of Macau")
    room = Room(name=f"Calendar Room {suffix}", location="E4")
    db_session.add(speaker)
    db_session.add(room)
    db_session.commit()
    db_session.refresh(speaker)
    db_session.refresh(room)

    current_title = f"Calendar Feed Current {suffix}"
    other_title = f"Calendar Feed Other {suffix}"
    seminar = Seminar(
        title=current_title,
        date=current_term_date,
        start_time="14:00",
        end_time="15:30",
        room_id=room.id,
        speaker_id=speaker.id,
        status="planned",
    )
    db_session.add(seminar)
    db_session.add(
        Seminar(
            title=other_title,
            date=other_term_date,
            start_time="16:00",
            end_time="17:00",
            room_id=room.id,
            speaker_id=speaker.id,
            status="planned",
        )
    )
    db_session.commit()
    db_session.refresh(seminar)

    response = client.get("/public/calendar.ics")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/calendar")
    assert "BEGIN:VCALENDAR" in response.text
    assert "X-WR-TIMEZONE:Asia/Macau" in response.text
    assert "TZID:Asia/Macau" in response.text
    assert current_title in response.text
    assert other_title not in response.text
    assert f"UID:seminar-{seminar.id}@" in response.text
    assert "DTSTART;TZID=Asia/Macau:" in response.text
    assert "STATUS:CONFIRMED" in response.text
