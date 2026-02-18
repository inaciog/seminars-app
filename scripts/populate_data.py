#!/usr/bin/env python3
"""
Populate seminars database with synthetic data for testing.
Uses urllib instead of requests to avoid external dependencies.
"""

import urllib.request
import urllib.error
import json
from datetime import datetime, timedelta

BASE_URL = "https://seminars-app.fly.dev"

# Test JWT token (valid token for the inacio user)
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6ImluYWNpbyIsIm5hbWUiOiJJbmFjaW8iLCJyb2xlIjoib3duZXIiLCJleHAiOjE3NzE1MDYxNTZ9.dzUTeFOQPE3-UbLN_yPsSw6mxr7YSDgQB27llPORNOc"

def make_request(method, url, data=None):
    """Make HTTP request using urllib."""
    req = urllib.request.Request(url, method=method)
    req.add_header("Authorization", f"Bearer {TOKEN}")
    
    if data:
        req.add_header("Content-Type", "application/json")
        req.data = json.dumps(data).encode('utf-8')
    
    try:
        with urllib.request.urlopen(req) as response:
            return response.status, json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8')
    except Exception as e:
        return 0, str(e)

def create_semester_plan():
    """Create a semester plan for Spring 2025."""
    data = {
        "name": "Spring 2025 Seminar Series",
        "academic_year": "2024-2025",
        "semester": "Spring",
        "default_room": "E21-G010",
        "status": "active"
    }
    status, response = make_request("POST", f"{BASE_URL}/api/v1/seminars/semester-plans", data)
    if status == 200:
        print(f"✓ Created semester plan: {data['name']}")
        return response.get("id", 1)
    else:
        print(f"✗ Failed to create semester plan: {status} {response}")
        return 1

def create_slots(plan_id):
    """Create seminar slots for the semester."""
    slots = []
    # Create slots for Wednesdays in Spring 2025
    dates = [
        "2025-02-05", "2025-02-12", "2025-02-19", "2025-02-26",
        "2025-03-05", "2025-03-12", "2025-03-19", "2025-03-26",
        "2025-04-02", "2025-04-09", "2025-04-16", "2025-04-23", "2025-04-30",
        "2025-05-07", "2025-05-14"
    ]
    
    for date_str in dates:
        data = {
            "date": date_str,
            "start_time": "14:00",
            "end_time": "15:15",
            "room": "E21-G010",
            "status": "available"
        }
        status, response = make_request("POST", 
            f"{BASE_URL}/api/v1/seminars/semester-plans/{plan_id}/slots", data)
        if status == 200:
            slots.append(response)
            print(f"✓ Created slot: {date_str}")
        else:
            print(f"✗ Failed to create slot {date_str}: {status}")
    
    return slots

def create_speakers():
    """Create speaker records."""
    speakers = [
        {"name": "Dr. Sarah Chen", "email": "sarah.chen@stanford.edu", 
         "affiliation": "Stanford University", "title": "Associate Professor"},
        {"name": "Prof. Michael Rodriguez", "email": "m.rodriguez@mit.edu",
         "affiliation": "MIT", "title": "Professor"},
        {"name": "Dr. Lisa Wang", "email": "lisa.wang@caltech.edu",
         "affiliation": "Caltech", "title": "Assistant Professor"},
        {"name": "Prof. James Thompson", "email": "j.thompson@ox.ac.uk",
         "affiliation": "University of Oxford", "title": "Professor"},
        {"name": "Dr. Anna Kowalski", "email": "a.kowalski@uw.edu",
         "affiliation": "University of Washington", "title": "Research Scientist"},
        {"name": "Prof. David Kim", "email": "david.kim@berkeley.edu",
         "affiliation": "UC Berkeley", "title": "Professor"},
    ]
    
    created = []
    for speaker in speakers:
        status, response = make_request("POST", f"{BASE_URL}/api/speakers", speaker)
        if status in [200, 201]:
            created.append(response)
            print(f"✓ Created speaker: {speaker['name']}")
        else:
            print(f"✗ Failed to create speaker {speaker['name']}: {status}")
    
    return created

def create_suggestions(plan_id, speakers):
    """Create speaker suggestions."""
    suggestions = [
        {"speaker_name": "Dr. Sarah Chen", "speaker_email": "sarah.chen@stanford.edu",
         "speaker_affiliation": "Stanford University", "suggested_topic": "AI in Healthcare",
         "suggested_by": "Prof. Zhang", "priority": "high", "semester_plan_id": plan_id},
        {"speaker_name": "Prof. Michael Rodriguez", "speaker_email": "m.rodriguez@mit.edu",
         "speaker_affiliation": "MIT", "suggested_topic": "Quantum Computing Applications",
         "suggested_by": "Dr. Liu", "priority": "medium", "semester_plan_id": plan_id},
        {"speaker_name": "Dr. Lisa Wang", "speaker_email": "lisa.wang@caltech.edu",
         "speaker_affiliation": "Caltech", "suggested_topic": "Neural Networks for Scientific Computing",
         "suggested_by": "Prof. Chen", "priority": "high", "semester_plan_id": plan_id},
        {"speaker_name": "Prof. James Thompson", "speaker_email": "j.thompson@ox.ac.uk",
         "speaker_affiliation": "University of Oxford", "suggested_topic": "Economic Policy in Developing Nations",
         "suggested_by": "Dr. Wang", "priority": "medium", "semester_plan_id": plan_id},
        {"speaker_name": "Dr. Anna Kowalski", "speaker_email": "a.kowalski@uw.edu",
         "speaker_affiliation": "University of Washington", "suggested_topic": "Climate Data Analysis",
         "suggested_by": "Prof. Li", "priority": "low", "semester_plan_id": plan_id},
    ]
    
    created = []
    for suggestion in suggestions:
        status, response = make_request("POST", 
            f"{BASE_URL}/api/v1/seminars/speaker-suggestions", suggestion)
        if status == 200:
            created.append(response)
            print(f"✓ Created suggestion: {suggestion['speaker_name']}")
        else:
            print(f"✗ Failed to create suggestion {suggestion['speaker_name']}: {status}")
    
    return created

def create_rooms():
    """Create room records."""
    rooms = [
        {"name": "E21-G010", "capacity": 50, "building": "E21", "floor": "G", "has_projector": True},
        {"name": "E21-1001", "capacity": 30, "building": "E21", "floor": "1", "has_projector": True},
        {"name": "N21-G014", "capacity": 40, "building": "N21", "floor": "G", "has_projector": True},
    ]
    
    for room in rooms:
        status, response = make_request("POST", f"{BASE_URL}/api/rooms", room)
        if status in [200, 201]:
            print(f"✓ Created room: {room['name']}")
        else:
            print(f"✗ Failed to create room {room['name']}: {status}")

def main():
    print("=" * 60)
    print("Populating Seminars Database with Synthetic Data")
    print("=" * 60)
    
    # Create rooms
    print("\n--- Creating Rooms ---")
    create_rooms()
    
    # Create semester plan
    print("\n--- Creating Semester Plan ---")
    plan_id = create_semester_plan()
    
    # Create slots
    print("\n--- Creating Seminar Slots ---")
    slots = create_slots(plan_id)
    
    # Create speakers
    print("\n--- Creating Speakers ---")
    speakers = create_speakers()
    
    # Create suggestions
    print("\n--- Creating Speaker Suggestions ---")
    suggestions = create_suggestions(plan_id, speakers)
    
    print("\n" + "=" * 60)
    print(f"Data population complete!")
    print(f"- Plan ID: {plan_id}")
    print(f"- Slots created: {len(slots)}")
    print(f"- Speakers created: {len(speakers)}")
    print(f"- Suggestions created: {len(suggestions)}")
    print("=" * 60)

if __name__ == "__main__":
    main()
