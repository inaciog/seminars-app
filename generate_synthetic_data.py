"""
Generate synthetic data for seminars app testing.
This creates a complete, realistic dataset with proper relationships.
"""

import requests
from datetime import datetime, timedelta
import random

BASE_URL = "https://seminars-app.fly.dev"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6ImluYWNpbyIsIm5hbWUiOiJJbmFjaW8iLCJyb2xlIjoib3duZXIiLCJpYXQiOjE3NzE1MDUyMzMsImV4cCI6MTc3NDA5NzIzM30.q1I_xwpKFZRPXHrLclwh_4nqYC1dqvPwLt4QL_Hd8Hk"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# Sample data
SPEAKERS_DATA = [
    {"name": "Dr. Sarah Chen", "email": "sarah.chen@stanford.edu", "affiliation": "Stanford University", "bio": "Expert in AI and machine learning"},
    {"name": "Prof. Michael Rodriguez", "email": "m.rodriguez@mit.edu", "affiliation": "MIT", "bio": "Quantum computing researcher"},
    {"name": "Dr. Lisa Wang", "email": "lisa.wang@caltech.edu", "affiliation": "Caltech", "bio": "Neural networks specialist"},
    {"name": "Prof. James Thompson", "email": "j.thompson@ox.ac.uk", "affiliation": "University of Oxford", "bio": "Economic policy expert"},
    {"name": "Dr. Anna Kowalski", "email": "a.kowalski@uw.edu", "affiliation": "University of Washington", "bio": "Climate data scientist"},
    {"name": "Prof. David Kim", "email": "david.kim@berkeley.edu", "affiliation": "UC Berkeley", "bio": "Computer systems researcher"},
    {"name": "Dr. Emily Johnson", "email": "emily.j@harvard.edu", "affiliation": "Harvard University", "bio": "Bioinformatics expert"},
    {"name": "Prof. Robert Brown", "email": "rbrown@cmu.edu", "affiliation": "Carnegie Mellon", "bio": "Robotics and automation"},
]

TOPICS = [
    "AI in Healthcare: Opportunities and Challenges",
    "Quantum Computing Applications in Chemistry",
    "Neural Networks for Scientific Computing",
    "Economic Policy in Developing Nations",
    "Climate Data Analysis and Modeling",
    "Distributed Systems at Scale",
    "Machine Learning for Drug Discovery",
    "Autonomous Systems and Safety",
    "Privacy-Preserving Machine Learning",
    "Sustainable Computing Infrastructure",
]

def create_speaker(speaker_data):
    """Create a speaker."""
    response = requests.post(
        f"{BASE_URL}/api/v1/seminars/speakers",
        headers=HEADERS,
        json=speaker_data
    )
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 409:
        # Speaker might exist, try to find by name
        speakers = requests.get(f"{BASE_URL}/api/speakers", headers=HEADERS).json()
        for s in speakers:
            if s['name'] == speaker_data['name']:
                return s
    print(f"Failed to create speaker {speaker_data['name']}: {response.status_code}")
    return None

def create_semester_plan():
    """Create a semester plan."""
    plan_data = {
        "name": "Spring 2025 Seminar Series",
        "academic_year": "2024-2025",
        "semester": "spring",
        "default_room": "E11-4047",
        "status": "active"
    }
    
    # Check if plan exists
    plans = requests.get(f"{BASE_URL}/api/v1/seminars/semester-plans", headers=HEADERS).json()
    for p in plans:
        if p['name'] == plan_data['name']:
            print(f"Plan already exists: {p['id']}")
            return p
    
    response = requests.post(
        f"{BASE_URL}/api/v1/seminars/semester-plans",
        headers=HEADERS,
        json=plan_data
    )
    if response.status_code == 200:
        plan = response.json()
        print(f"Created plan: {plan['id']}")
        return plan
    print(f"Failed to create plan: {response.status_code}")
    return None

def create_slots(plan_id):
    """Create seminar slots for the semester."""
    # Create slots for Tuesdays in March-May 2025
    slots = []
    start_date = datetime(2025, 3, 4)  # First Tuesday in March
    
    for i in range(12):  # 12 weeks
        slot_date = start_date + timedelta(weeks=i)
        
        slot_data = {
            "semester_plan_id": plan_id,
            "date": slot_date.strftime("%Y-%m-%d"),
            "start_time": "14:00",
            "end_time": "15:30",
            "room": "E11-4047",
            "status": "available"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/seminars/semester-plans/{plan_id}/slots",
            headers=HEADERS,
            json=slot_data
        )
        if response.status_code == 200:
            slots.append(response.json())
            print(f"Created slot: {slot_date.strftime('%Y-%m-%d')}")
        else:
            print(f"Failed to create slot: {response.status_code}")
    
    return slots

def create_suggestion(plan_id, speaker, topic):
    """Create a speaker suggestion."""
    suggestion_data = {
        "semester_plan_id": plan_id,
        "speaker_id": speaker['id'],
        "speaker_name": speaker['name'],
        "speaker_email": speaker.get('email'),
        "speaker_affiliation": speaker.get('affiliation'),
        "suggested_topic": topic,
        "suggested_by": "Prof. Zhang",
        "priority": random.choice(['low', 'medium', 'high']),
        "status": "pending"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/seminars/speaker-suggestions",
        headers=HEADERS,
        json=suggestion_data
    )
    if response.status_code == 200:
        return response.json()
    print(f"Failed to create suggestion: {response.status_code}")
    return None

def add_availability(suggestion_id, plan_id):
    """Add availability for a suggestion."""
    # Get slots for this plan
    board = requests.get(
        f"{BASE_URL}/api/v1/seminars/semester-plans/{plan_id}/planning-board",
        headers=HEADERS
    ).json()
    
    slots = board.get('slots', [])
    if not slots:
        return
    
    # Pick 3-5 random slots as available
    available_slots = random.sample(slots, min(random.randint(3, 5), len(slots)))
    
    for slot in available_slots:
        avail_data = {
            "start_date": slot['date'],
            "end_date": slot['date'],
            "preference": random.choice(['available', 'preferred'])
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/seminars/speaker-suggestions/{suggestion_id}/availability",
            headers=HEADERS,
            json=avail_data
        )
        if response.status_code == 200:
            print(f"  Added availability: {slot['date']}")

def assign_to_slot(suggestion_id, slot_id):
    """Assign a suggestion to a slot."""
    response = requests.post(
        f"{BASE_URL}/api/v1/seminars/planning/assign",
        headers=HEADERS,
        json={"suggestion_id": suggestion_id, "slot_id": slot_id}
    )
    if response.status_code == 200:
        return response.json()
    print(f"Failed to assign: {response.status_code}")
    return None

def generate_synthetic_data():
    """Generate complete synthetic dataset."""
    print("=" * 60)
    print("Generating Synthetic Data for Seminars App")
    print("=" * 60)
    
    # Step 1: Create speakers
    print("\n1. Creating speakers...")
    speakers = []
    for speaker_data in SPEAKERS_DATA:
        speaker = create_speaker(speaker_data)
        if speaker:
            speakers.append(speaker)
            print(f"  ✓ {speaker['name']}")
    
    # Step 2: Create semester plan
    print("\n2. Creating semester plan...")
    plan = create_semester_plan()
    if not plan:
        print("Failed to create plan, exiting")
        return
    
    # Step 3: Create slots
    print("\n3. Creating seminar slots...")
    slots = create_slots(plan['id'])
    
    # Step 4: Create suggestions
    print("\n4. Creating speaker suggestions...")
    suggestions = []
    for i, speaker in enumerate(speakers):
        topic = TOPICS[i % len(TOPICS)]
        suggestion = create_suggestion(plan['id'], speaker, topic)
        if suggestion:
            suggestions.append(suggestion)
            print(f"  ✓ {speaker['name']} - {topic}")
            
            # Add availability
            add_availability(suggestion['id'], plan['id'])
    
    # Step 5: Assign some suggestions to slots
    print("\n5. Assigning speakers to slots...")
    assigned_count = 0
    for i, suggestion in enumerate(suggestions[:5]):  # Assign first 5
        if i < len(slots):
            result = assign_to_slot(suggestion['id'], slots[i]['id'])
            if result:
                assigned_count += 1
                print(f"  ✓ Assigned {suggestion['speaker_name']} to {slots[i]['date']}")
    
    print("\n" + "=" * 60)
    print("Synthetic data generation complete!")
    print(f"  Speakers: {len(speakers)}")
    print(f"  Slots: {len(slots)}")
    print(f"  Suggestions: {len(suggestions)}")
    print(f"  Assigned: {assigned_count}")
    print("=" * 60)

if __name__ == "__main__":
    generate_synthetic_data()
