#!/usr/bin/env python3
"""
Seed script for seminars-app test data.
Run this to populate the database with virtual data for testing.
"""

import os
import sys
from datetime import datetime, timedelta, date
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.main import (
    get_engine, Speaker, Room, Seminar, SemesterPlan, 
    SeminarSlot, SpeakerSuggestion, SpeakerAvailability,
    SeminarDetails, SQLModel, Session
)

def seed_data():
    """Populate database with test data."""
    
    engine = get_engine()
    
    # Create all tables
    print("📊 Creating database tables...")
    SQLModel.metadata.create_all(engine)
    print("  ✓ Tables created")
    
    with Session(engine) as db:
        print("🌱 Seeding database with test data...")
        
        # Create speakers
        print("  Creating speakers...")
        speakers_data = [
            {
                "name": "Dr. Jane Smith",
                "email": "jane.smith@stanford.edu",
                "affiliation": "Stanford University",
                "website": "https://janesmith.edu",
                "bio": "Expert in machine learning and artificial intelligence with 15 years of experience."
            },
            {
                "name": "Prof. Michael Chen",
                "email": "m.chen@mit.edu",
                "affiliation": "MIT",
                "website": "https://mchen.mit.edu",
                "bio": "Leading researcher in quantum computing and cryptography."
            },
            {
                "name": "Dr. Sarah Johnson",
                "email": "sarah.j@oxford.ac.uk",
                "affiliation": "University of Oxford",
                "bio": "Specializes in behavioral economics and game theory."
            },
            {
                "name": "Prof. David Williams",
                "email": "d.williams@cam.ac.uk",
                "affiliation": "Cambridge University",
                "website": "https://williams.cam.ac.uk",
                "bio": "Renowned physicist working on string theory and cosmology."
            },
            {
                "name": "Dr. Emily Brown",
                "email": "emily.brown@harvard.edu",
                "affiliation": "Harvard University",
                "bio": "Climate scientist focusing on ocean-atmosphere interactions."
            },
            {
                "name": "Prof. Robert Taylor",
                "email": "rtaylor@ethz.ch",
                "affiliation": "ETH Zurich",
                "bio": "Robotics and automation expert with industry experience."
            }
        ]
        
        speakers = []
        for data in speakers_data:
            speaker = Speaker(**data)
            db.add(speaker)
            speakers.append(speaker)
        
        db.commit()
        print(f"  ✓ Created {len(speakers)} speakers")
        
        # Create rooms
        print("  Creating rooms...")
        rooms_data = [
            {"name": "Main Auditorium", "capacity": 200, "location": "Building A", "equipment": '{"projector": true, "microphone": true, "recording": true}'},
            {"name": "Conference Room B", "capacity": 50, "location": "Building A", "equipment": '{"projector": true, "whiteboard": true}'},
            {"name": "Seminar Room 101", "capacity": 30, "location": "Building B", "equipment": '{"projector": true}'},
            {"name": "Lecture Hall C", "capacity": 150, "location": "Building C", "equipment": '{"projector": true, "microphone": true, "livestream": true}'},
            {"name": "Meeting Room 205", "capacity": 20, "location": "Building B", "equipment": '{"video_conf": true}'}
        ]
        
        rooms = []
        for data in rooms_data:
            room = Room(**data)
            db.add(room)
            rooms.append(room)
        
        db.commit()
        print(f"  ✓ Created {len(rooms)} rooms")
        
        # Create semester plan
        print("  Creating semester plan...")
        semester_plan = SemesterPlan(
            name="Spring 2025 Seminar Series",
            academic_year="2024-2025",
            semester="Spring",
            default_room="Main Auditorium",
            default_start_time="14:00",
            default_duration_minutes=90,
            status="active",
            notes="Weekly seminars on cutting-edge research topics"
        )
        db.add(semester_plan)
        db.commit()
        print(f"  ✓ Created semester plan: {semester_plan.name}")
        
        # Create seminar slots (use future dates so they appear as "upcoming")
        print("  Creating seminar slots...")
        slots = []
        today = date.today()
        base_date = today + timedelta(days=7)  # Start next week
        for i in range(12):  # 12 weeks
            slot_date = base_date + timedelta(weeks=i)
            slot = SeminarSlot(
                semester_plan_id=semester_plan.id,
                date=slot_date,
                start_time="14:00",
                end_time="15:30",
                room="Main Auditorium",
                status="available"
            )
            db.add(slot)
            slots.append(slot)
        
        db.commit()
        print(f"  ✓ Created {len(slots)} seminar slots")
        
        # Create seminars (dates relative to today so they appear as "upcoming")
        print("  Creating seminars...")
        seminar_base = today + timedelta(days=14)  # 2 weeks from now
        seminars_data = [
            {
                "title": "Advances in Machine Learning for Climate Modeling",
                "date": seminar_base,
                "start_time": "14:00",
                "end_time": "15:30",
                "speaker_id": speakers[4].id,  # Emily Brown
                "room_id": rooms[0].id,
                "abstract": "This talk explores how modern ML techniques are revolutionizing climate prediction models.",
                "status": "confirmed",
                "room_booked": True,
                "announcement_sent": True,
                "calendar_invite_sent": True
            },
            {
                "title": "Quantum Computing: From Theory to Practice",
                "date": seminar_base + timedelta(days=7),
                "start_time": "14:00",
                "end_time": "15:30",
                "speaker_id": speakers[1].id,  # Michael Chen
                "room_id": rooms[3].id,
                "abstract": "An overview of recent breakthroughs in quantum computing hardware and algorithms.",
                "status": "confirmed",
                "room_booked": True,
                "announcement_sent": True
            },
            {
                "title": "Behavioral Economics in the Digital Age",
                "date": seminar_base + timedelta(days=21),
                "start_time": "14:00",
                "end_time": "15:30",
                "speaker_id": speakers[2].id,  # Sarah Johnson
                "room_id": rooms[0].id,
                "abstract": "How digital platforms are changing our understanding of economic decision-making.",
                "status": "planned",
                "room_booked": True
            },
            {
                "title": "String Theory and the Multiverse",
                "date": seminar_base + timedelta(days=35),
                "start_time": "14:00",
                "end_time": "15:30",
                "speaker_id": speakers[3].id,  # David Williams
                "room_id": rooms[0].id,
                "abstract": "Exploring the implications of string theory for our understanding of the cosmos.",
                "status": "planned"
            },
            {
                "title": "Autonomous Robotics in Manufacturing",
                "date": seminar_base + timedelta(days=49),
                "start_time": "14:00",
                "end_time": "15:30",
                "speaker_id": speakers[5].id,  # Robert Taylor
                "room_id": rooms[3].id,
                "abstract": "Latest developments in industrial robotics and automation.",
                "status": "planned"
            },
            {
                "title": "Deep Learning for Natural Language Understanding",
                "date": seminar_base + timedelta(days=63),
                "start_time": "14:00",
                "end_time": "15:30",
                "speaker_id": speakers[0].id,  # Jane Smith
                "room_id": rooms[0].id,
                "abstract": "Recent advances in transformer architectures and their applications.",
                "status": "planned"
            }
        ]
        
        seminars = []
        for data in seminars_data:
            seminar = Seminar(**data)
            db.add(seminar)
            seminars.append(seminar)
        
        db.commit()
        print(f"  ✓ Created {len(seminars)} seminars")
        
        # Create seminar details for confirmed seminars
        print("  Creating seminar details...")
        for seminar in seminars[:2]:  # Add details to first 2
            details = SeminarDetails(
                seminar_id=seminar.id,
                check_in_date=seminar.date - timedelta(days=1),
                check_out_date=seminar.date + timedelta(days=1),
                departure_city="New York",
                travel_method="flight",
                estimated_travel_cost=800.00,
                needs_accommodation=True,
                accommodation_nights=2,
                estimated_hotel_cost=300.00,
                payment_email=seminar.speaker.email,
                beneficiary_name=seminar.speaker.name,
                currency="USD"
            )
            db.add(details)
        
        db.commit()
        print(f"  ✓ Created seminar details")
        
        # Create speaker suggestions
        print("  Creating speaker suggestions...")
        suggestions_data = [
            {
                "suggested_by": "Prof. Anderson",
                "suggested_by_email": "anderson@university.edu",
                "speaker_name": "Dr. Lisa Wang",
                "speaker_email": "lisa.wang@caltech.edu",
                "speaker_affiliation": "Caltech",
                "suggested_topic": "Neural Networks for Scientific Computing",
                "reason": "Leading expert in the field, highly recommended",
                "priority": "high",
                "status": "pending",
                "semester_plan_id": semester_plan.id
            },
            {
                "suggested_by": "Dr. Martinez",
                "suggested_by_email": "martinez@university.edu",
                "speaker_name": "Prof. James Wilson",
                "speaker_email": "jwilson@princeton.edu",
                "speaker_affiliation": "Princeton",
                "suggested_topic": "Economic Inequality and Policy",
                "reason": "Recent book on the topic is highly relevant",
                "priority": "medium",
                "status": "contacted",
                "semester_plan_id": semester_plan.id
            },
            {
                "suggested_by": "Prof. Thompson",
                "speaker_name": "Dr. Anna Kowalski",
                "speaker_email": "anna.k@mpg.de",
                "speaker_affiliation": "Max Planck Institute",
                "suggested_topic": "Molecular Biology of Aging",
                "priority": "medium",
                "status": "pending",
                "semester_plan_id": semester_plan.id
            },
            {
                "suggested_by": "Dr. Lee",
                "suggested_by_email": "lee@university.edu",
                "speaker_name": "Prof. Carlos Rodriguez",
                "speaker_email": "crodriguez@u-tokyo.ac.jp",
                "speaker_affiliation": "University of Tokyo",
                "suggested_topic": "Sustainable Urban Design",
                "reason": "Expert in smart city initiatives",
                "priority": "low",
                "status": "pending",
                "semester_plan_id": semester_plan.id
            }
        ]
        
        suggestions = []
        for data in suggestions_data:
            suggestion = SpeakerSuggestion(**data)
            db.add(suggestion)
            suggestions.append(suggestion)
        
        db.commit()
        print(f"  ✓ Created {len(suggestions)} speaker suggestions")
        
        # Add availability for one suggestion
        print("  Creating speaker availability...")
        availability_data = [
            {"date": today + timedelta(days=21), "preference": "preferred"},
            {"date": today + timedelta(days=28), "preference": "available"},
            {"date": today + timedelta(days=35), "preference": "available"},
            {"date": today + timedelta(days=42), "preference": "not_preferred"}
        ]
        
        for avail in availability_data:
            availability = SpeakerAvailability(
                suggestion_id=suggestions[0].id,
                date=avail["date"],
                preference=avail["preference"]
            )
            db.add(availability)
        
        db.commit()
        print(f"  ✓ Created availability entries")
        
        # Assign one seminar to a slot
        print("  Assigning seminars to slots...")
        slots[0].assigned_seminar_id = seminars[0].id
        slots[0].status = "confirmed"
        slots[1].assigned_seminar_id = seminars[1].id
        slots[1].status = "confirmed"
        
        db.commit()
        print(f"  ✓ Assigned seminars to slots")
        
        print("\n✅ Database seeded successfully!")
        print(f"\nSummary:")
        print(f"  - {len(speakers)} speakers")
        print(f"  - {len(rooms)} rooms")
        print(f"  - 1 semester plan with {len(slots)} slots")
        print(f"  - {len(seminars)} seminars")
        print(f"  - {len(suggestions)} speaker suggestions")
        print(f"\nYou can now log in and test the application.")

if __name__ == "__main__":
    seed_data()
