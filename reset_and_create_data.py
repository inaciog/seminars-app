"""
Reset and create fresh synthetic data using only API calls.
This ensures data integrity through proper API procedures.
"""

import requests
import json
import os
from datetime import datetime, timedelta

BASE_URL = "https://seminars-app.fly.dev"
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "i486983nacio:!")

# Get auth token via admin password
def get_auth_token():
    """Login with admin password to get auth token."""
    resp = requests.post(
        f"{BASE_URL}/api/auth/login-admin",
        json={"password": ADMIN_PASSWORD}
    )
    if resp.status_code == 200:
        return resp.json()["token"]
    raise Exception(f"Failed to authenticate: {resp.text}")

TOKEN = get_auth_token()

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

def api_get(endpoint):
    """Make GET request."""
    resp = requests.get(f"{BASE_URL}{endpoint}", headers=HEADERS)
    return resp.json() if resp.status_code == 200 else None

def api_post(endpoint, data):
    """Make POST request."""
    resp = requests.post(f"{BASE_URL}{endpoint}", headers=HEADERS, json=data)
    return resp.json() if resp.status_code in [200, 201] else None

def api_delete(endpoint):
    """Make DELETE request."""
    resp = requests.delete(f"{BASE_URL}{endpoint}", headers=HEADERS)
    return resp.status_code == 200

def clear_all_data():
    """Clear all existing data using API."""
    print("=" * 60)
    print("CLEARING ALL DATA")
    print("=" * 60)
    
    # Delete seminars first (they reference speakers and slots)
    seminars = api_get("/api/seminars") or []
    print(f"\n1. Deleting {len(seminars)} seminars...")
    for s in seminars:
        if api_delete(f"/api/seminars/{s['id']}"):
            print(f"   ✓ Deleted seminar: {s.get('title', s['id'])}")
    
    # Delete speaker suggestions
    suggestions = api_get("/api/v1/seminars/speaker-suggestions") or []
    print(f"\n2. Deleting {len(suggestions)} suggestions...")
    for sg in suggestions:
        if api_delete(f"/api/v1/seminars/speaker-suggestions/{sg['id']}"):
            print(f"   ✓ Deleted suggestion: {sg.get('speaker_name', sg['id'])}")
    
    # Delete speakers
    speakers = api_get("/api/speakers") or []
    print(f"\n3. Deleting {len(speakers)} speakers...")
    for sp in speakers:
        if api_delete(f"/api/speakers/{sp['id']}"):
            print(f"   ✓ Deleted speaker: {sp.get('name', sp['id'])}")
    
    # Delete semester plans (this should cascade to slots)
    plans = api_get("/api/v1/seminars/semester-plans") or []
    print(f"\n4. Deleting {len(plans)} semester plans...")
    for p in plans:
        if api_delete(f"/api/v1/seminars/semester-plans/{p['id']}"):
            print(f"   ✓ Deleted plan: {p.get('name', p['id'])}")
    
    print("\n✓ All data cleared")

def create_fresh_data():
    """Create fresh synthetic data using only API calls."""
    print("\n" + "=" * 60)
    print("CREATING FRESH SYNTHETIC DATA")
    print("=" * 60)
    
    # 1. Create speakers
    print("\n1. Creating speakers...")
    speakers_data = [
        {"name": "Dr. Sarah Chen", "email": "sarah.chen@stanford.edu", "affiliation": "Stanford University"},
        {"name": "Prof. Michael Rodriguez", "email": "m.rodriguez@mit.edu", "affiliation": "MIT"},
        {"name": "Dr. Lisa Wang", "email": "lisa.wang@caltech.edu", "affiliation": "Caltech"},
        {"name": "Prof. James Thompson", "email": "j.thompson@ox.ac.uk", "affiliation": "University of Oxford"},
        {"name": "Dr. Anna Kowalski", "email": "a.kowalski@uw.edu", "affiliation": "University of Washington"},
    ]
    
    speakers = []
    for sp_data in speakers_data:
        sp = api_post("/api/v1/seminars/speakers", sp_data)
        if sp:
            speakers.append(sp)
            print(f"   ✓ Created: {sp['name']}")
    
    # 2. Create semester plan
    print("\n2. Creating semester plan...")
    plan_data = {
        "name": "Spring 2025 Seminar Series",
        "academic_year": "2024-2025",
        "semester": "spring",
        "default_room": "E11-4047",
        "status": "active"
    }
    plan = api_post("/api/v1/seminars/semester-plans", plan_data)
    if plan:
        print(f"   ✓ Created plan: {plan['name']} (ID: {plan['id']})")
    
    # 3. Create seminar slots
    print("\n3. Creating seminar slots...")
    slots = []
    start_date = datetime(2025, 3, 4)
    for i in range(8):
        slot_date = start_date + timedelta(weeks=i)
        slot_data = {
            "semester_plan_id": plan['id'],
            "date": slot_date.strftime("%Y-%m-%d"),
            "start_time": "14:00",
            "end_time": "15:30",
            "room": "E11-4047"
        }
        slot = api_post(f"/api/v1/seminars/semester-plans/{plan['id']}/slots", slot_data)
        if slot:
            slots.append(slot)
            print(f"   ✓ Created slot: {slot['date']}")
    
    # 4. Create speaker suggestions
    print("\n4. Creating speaker suggestions...")
    topics = [
        "AI in Healthcare: Opportunities and Challenges",
        "Quantum Computing Applications",
        "Neural Networks for Scientific Computing",
        "Economic Policy in Developing Nations",
        "Climate Data Analysis and Modeling"
    ]
    
    suggestions = []
    for i, speaker in enumerate(speakers):
        sg_data = {
            "semester_plan_id": plan['id'],
            "speaker_id": speaker['id'],
            "speaker_name": speaker['name'],
            "speaker_email": speaker['email'],
            "speaker_affiliation": speaker['affiliation'],
            "suggested_topic": topics[i % len(topics)],
            "suggested_by": "Prof. Zhang",
            "priority": "medium",
            "status": "pending"
        }
        sg = api_post("/api/v1/seminars/speaker-suggestions", sg_data)
        if sg:
            suggestions.append(sg)
            print(f"   ✓ Created suggestion: {sg['speaker_name']} - {sg['suggested_topic']}")
    
    # 5. Assign speakers to slots (create seminars)
    print("\n5. Assigning speakers to slots...")
    for i, suggestion in enumerate(suggestions[:4]):  # Assign first 4
        if i < len(slots):
            result = api_post("/api/v1/seminars/planning/assign", {
                "suggestion_id": suggestion['id'],
                "slot_id": slots[i]['id']
            })
            if result:
                print(f"   ✓ Assigned: {suggestion['speaker_name']} to {slots[i]['date']}")
    
    print("\n" + "=" * 60)
    print("SYNTHETIC DATA CREATION COMPLETE")
    print("=" * 60)
    print(f"  Speakers: {len(speakers)}")
    print(f"  Slots: {len(slots)}")
    print(f"  Suggestions: {len(suggestions)}")
    print(f"  Assigned: {min(len(suggestions), len(slots))}")

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("DATA RESET AND SYNTHETIC DATA GENERATION")
    print("=" * 60)
    
    # Confirm
    print("\nThis will DELETE all existing data and create fresh synthetic data.")
    print("Proceeding in 3 seconds...")
    import time
    time.sleep(3)
    
    clear_all_data()
    create_fresh_data()
    
    print("\n✓ Done!")
