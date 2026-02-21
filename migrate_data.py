"""
Migration script to overhaul seminars app data model.
This creates a new, robust schema with proper foreign keys and relationships.
"""

import sqlite3
import sys
from pathlib import Path

def migrate_database(db_path: str):
    """Migrate database to new robust schema."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Starting database migration...")
    
    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON")
    
    # Create backup of old tables
    print("Creating backups...")
    cursor.execute("ALTER TABLE speakers RENAME TO speakers_old")
    cursor.execute("ALTER TABLE semester_plans RENAME TO semester_plans_old")
    cursor.execute("ALTER TABLE seminar_slots RENAME TO seminar_slots_old")
    cursor.execute("ALTER TABLE speaker_suggestions RENAME TO speaker_suggestions_old")
    cursor.execute("ALTER TABLE seminars RENAME TO seminars_old")
    cursor.execute("ALTER TABLE speaker_availabilities RENAME TO speaker_availabilities_old")
    cursor.execute("ALTER TABLE speaker_tokens RENAME TO speaker_tokens_old")
    cursor.execute("ALTER TABLE seminar_details RENAME TO seminar_details_old")
    cursor.execute("ALTER TABLE uploaded_files RENAME TO uploaded_files_old")
    
    # Create new speakers table
    print("Creating speakers table...")
    cursor.execute("""
        CREATE TABLE speakers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT,
            affiliation TEXT,
            website TEXT,
            bio TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Migrate speakers
    cursor.execute("""
        INSERT INTO speakers (id, name, email, affiliation, website, bio, notes)
        SELECT id, name, email, affiliation, website, bio, notes
        FROM speakers_old
        WHERE name IS NOT NULL AND name != ''
    """)
    
    # Create semester_plans table
    print("Creating semester_plans table...")
    cursor.execute("""
        CREATE TABLE semester_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            academic_year TEXT NOT NULL,
            semester TEXT NOT NULL,
            default_room TEXT,
            status TEXT DEFAULT 'draft',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Migrate semester plans
    cursor.execute("""
        INSERT INTO semester_plans (id, name, academic_year, semester, default_room, status)
        SELECT id, name, academic_year, semester, default_room, status
        FROM semester_plans_old
    """)
    
    # Create seminar_slots table
    print("Creating seminar_slots table...")
    cursor.execute("""
        CREATE TABLE seminar_slots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            semester_plan_id INTEGER NOT NULL,
            date DATE NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            room TEXT NOT NULL,
            status TEXT DEFAULT 'available',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (semester_plan_id) REFERENCES semester_plans(id) ON DELETE CASCADE
        )
    """)
    
    # Migrate seminar slots
    cursor.execute("""
        INSERT INTO seminar_slots (id, semester_plan_id, date, start_time, end_time, room, status)
        SELECT id, semester_plan_id, date, start_time, end_time, room, status
        FROM seminar_slots_old
    """)
    
    # Create speaker_suggestions table
    print("Creating speaker_suggestions table...")
    cursor.execute("""
        CREATE TABLE speaker_suggestions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            semester_plan_id INTEGER NOT NULL,
            speaker_id INTEGER,
            suggested_speaker_name TEXT NOT NULL,
            suggested_speaker_email TEXT,
            suggested_speaker_affiliation TEXT,
            suggested_topic TEXT,
            suggested_by TEXT NOT NULL,
            priority TEXT DEFAULT 'medium',
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (semester_plan_id) REFERENCES semester_plans(id) ON DELETE CASCADE,
            FOREIGN KEY (speaker_id) REFERENCES speakers(id) ON DELETE SET NULL
        )
    """)
    
    # Migrate speaker suggestions
    cursor.execute("""
        INSERT INTO speaker_suggestions (
            id, semester_plan_id, speaker_id, suggested_speaker_name,
            suggested_speaker_email, suggested_speaker_affiliation,
            suggested_topic, suggested_by, priority, status
        )
        SELECT 
            id, semester_plan_id, speaker_id, speaker_name,
            speaker_email, speaker_affiliation,
            suggested_topic, suggested_by, priority, status
        FROM speaker_suggestions_old
    """)
    
    # Create seminars table with proper foreign keys
    print("Creating seminars table...")
    cursor.execute("""
        CREATE TABLE seminars (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slot_id INTEGER UNIQUE,
            speaker_id INTEGER NOT NULL,
            suggestion_id INTEGER,
            title TEXT NOT NULL,
            abstract TEXT,
            date DATE NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            room TEXT NOT NULL,
            status TEXT DEFAULT 'planned',
            room_booked BOOLEAN DEFAULT FALSE,
            announcement_sent BOOLEAN DEFAULT FALSE,
            calendar_invite_sent BOOLEAN DEFAULT FALSE,
            website_updated BOOLEAN DEFAULT FALSE,
            catering_ordered BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (slot_id) REFERENCES seminar_slots(id) ON DELETE SET NULL,
            FOREIGN KEY (speaker_id) REFERENCES speakers(id) ON DELETE RESTRICT,
            FOREIGN KEY (suggestion_id) REFERENCES speaker_suggestions(id) ON DELETE SET NULL
        )
    """)
    
    # Migrate seminars - only those with valid speakers
    cursor.execute("""
        INSERT INTO seminars (
            id, slot_id, speaker_id, title, abstract, date,
            start_time, end_time, room, status,
            room_booked, announcement_sent, calendar_invite_sent,
            website_updated, catering_ordered
        )
        SELECT 
            s.id, 
            (SELECT id FROM seminar_slots WHERE id = s.id),  -- Try to find matching slot
            s.speaker_id,
            s.title, s.abstract, s.date,
            s.start_time, s.end_time, s.room, s.status,
            s.room_booked, s.announcement_sent, s.calendar_invite_sent,
            s.website_updated, s.catering_ordered
        FROM seminars_old s
        WHERE s.speaker_id IN (SELECT id FROM speakers)
    """)
    
    # Update slot statuses based on seminars
    cursor.execute("""
        UPDATE seminar_slots 
        SET status = 'confirmed'
        WHERE id IN (SELECT slot_id FROM seminars WHERE slot_id IS NOT NULL)
    """)
    
    # Link seminars to suggestions
    cursor.execute("""
        UPDATE seminars
        SET suggestion_id = (
            SELECT ss.id 
            FROM speaker_suggestions ss
            WHERE ss.speaker_id = seminars.speaker_id
            AND ss.semester_plan_id = (
                SELECT semester_plan_id 
                FROM seminar_slots 
                WHERE id = seminars.slot_id
            )
            LIMIT 1
        )
        WHERE slot_id IS NOT NULL
    """)
    
    # Create speaker_availabilities table
    print("Creating speaker_availabilities table...")
    cursor.execute("""
        CREATE TABLE speaker_availabilities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            suggestion_id INTEGER NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            preference TEXT DEFAULT 'available',
            earliest_time TEXT,
            latest_time TEXT,
            notes TEXT,
            FOREIGN KEY (suggestion_id) REFERENCES speaker_suggestions(id) ON DELETE CASCADE
        )
    """)
    
    # Migrate availabilities
    cursor.execute("""
        INSERT INTO speaker_availabilities (
            id, suggestion_id, start_date, end_date, preference, earliest_time, latest_time, notes
        )
        SELECT 
            id, suggestion_id, start_date, end_date, preference, earliest_time, latest_time, notes
        FROM speaker_availabilities_old
        WHERE suggestion_id IN (SELECT id FROM speaker_suggestions)
    """)
    
    # Create speaker_tokens table
    print("Creating speaker_tokens table...")
    cursor.execute("""
        CREATE TABLE speaker_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token TEXT UNIQUE NOT NULL,
            suggestion_id INTEGER NOT NULL,
            seminar_id INTEGER,
            token_type TEXT NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            used_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (suggestion_id) REFERENCES speaker_suggestions(id) ON DELETE CASCADE,
            FOREIGN KEY (seminar_id) REFERENCES seminars(id) ON DELETE SET NULL
        )
    """)
    
    # Migrate tokens
    cursor.execute("""
        INSERT INTO speaker_tokens (
            id, token, suggestion_id, seminar_id, token_type, expires_at, used_at
        )
        SELECT 
            id, token, suggestion_id, seminar_id, token_type, expires_at, used_at
        FROM speaker_tokens_old
        WHERE suggestion_id IN (SELECT id FROM speaker_suggestions)
    """)
    
    # Create seminar_details table
    print("Creating seminar_details table...")
    cursor.execute("""
        CREATE TABLE seminar_details (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            seminar_id INTEGER UNIQUE NOT NULL,
            passport_number TEXT,
            passport_country TEXT,
            departure_city TEXT,
            travel_method TEXT,
            needs_accommodation BOOLEAN DEFAULT FALSE,
            check_in_date DATE,
            check_out_date DATE,
            payment_email TEXT,
            beneficiary_name TEXT,
            bank_name TEXT,
            swift_code TEXT,
            bank_account_number TEXT,
            bank_address TEXT,
            currency TEXT,
            needs_projector BOOLEAN DEFAULT TRUE,
            needs_microphone BOOLEAN DEFAULT FALSE,
            special_requirements TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (seminar_id) REFERENCES seminars(id) ON DELETE CASCADE
        )
    """)
    
    # Migrate seminar details
    cursor.execute("""
        INSERT INTO seminar_details (
            id, seminar_id, passport_number, passport_country, departure_city,
            travel_method, needs_accommodation, check_in_date, check_out_date,
            payment_email, beneficiary_name, bank_name, swift_code,
            bank_account_number, bank_address, currency,
            needs_projector, needs_microphone, special_requirements
        )
        SELECT 
            id, seminar_id, passport_number, passport_country, departure_city,
            travel_method, needs_accommodation, check_in_date, check_out_date,
            payment_email, beneficiary_name, bank_name, swift_code,
            bank_account_number, bank_address, currency,
            needs_projector, needs_microphone, special_requirements
        FROM seminar_details_old
        WHERE seminar_id IN (SELECT id FROM seminars)
    """)
    
    # Create uploaded_files table
    print("Creating uploaded_files table...")
    cursor.execute("""
        CREATE TABLE uploaded_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            seminar_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            original_filename TEXT NOT NULL,
            storage_filename TEXT NOT NULL,
            file_size INTEGER,
            uploaded_by TEXT,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (seminar_id) REFERENCES seminars(id) ON DELETE CASCADE
        )
    """)
    
    # Migrate uploaded files
    cursor.execute("""
        INSERT INTO uploaded_files (
            id, seminar_id, category, original_filename, storage_filename, file_size, uploaded_by, uploaded_at
        )
        SELECT 
            id, seminar_id, category, original_filename, storage_filename, file_size, uploaded_by, uploaded_at
        FROM uploaded_files_old
        WHERE seminar_id IN (SELECT id FROM seminars)
    """)
    
    # Create indexes for performance
    print("Creating indexes...")
    cursor.execute("CREATE INDEX idx_speakers_name ON speakers(name)")
    cursor.execute("CREATE INDEX idx_suggestions_plan ON speaker_suggestions(semester_plan_id)")
    cursor.execute("CREATE INDEX idx_suggestions_speaker ON speaker_suggestions(speaker_id)")
    cursor.execute("CREATE INDEX idx_suggestions_status ON speaker_suggestions(status)")
    cursor.execute("CREATE INDEX idx_slots_plan ON seminar_slots(semester_plan_id)")
    cursor.execute("CREATE INDEX idx_slots_date ON seminar_slots(date)")
    cursor.execute("CREATE INDEX idx_seminars_slot ON seminars(slot_id)")
    cursor.execute("CREATE INDEX idx_seminars_speaker ON seminars(speaker_id)")
    cursor.execute("CREATE INDEX idx_seminars_suggestion ON seminars(suggestion_id)")
    cursor.execute("CREATE INDEX idx_seminars_date ON seminars(date)")
    cursor.execute("CREATE INDEX idx_tokens_token ON speaker_tokens(token)")
    cursor.execute("CREATE INDEX idx_tokens_suggestion ON speaker_tokens(suggestion_id)")
    cursor.execute("CREATE INDEX idx_availabilities_suggestion ON speaker_availabilities(suggestion_id)")
    cursor.execute("CREATE INDEX idx_files_seminar ON uploaded_files(seminar_id)")
    
    conn.commit()
    print("Migration completed successfully!")
    
    # Print summary
    cursor.execute("SELECT COUNT(*) FROM speakers")
    speaker_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM semester_plans")
    plan_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM seminar_slots")
    slot_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM speaker_suggestions")
    suggestion_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM seminars")
    seminar_count = cursor.fetchone()[0]
    
    print(f"\nMigrated data:")
    print(f"  Speakers: {speaker_count}")
    print(f"  Semester plans: {plan_count}")
    print(f"  Seminar slots: {slot_count}")
    print(f"  Speaker suggestions: {suggestion_count}")
    print(f"  Seminars: {seminar_count}")
    
    conn.close()

def cleanup_old_tables(db_path: str):
    """Remove old tables after migration is verified."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Cleaning up old tables...")
    tables = [
        'speakers_old', 'semester_plans_old', 'seminar_slots_old',
        'speaker_suggestions_old', 'seminars_old', 'speaker_availabilities_old',
        'speaker_tokens_old', 'seminar_details_old', 'uploaded_files_old'
    ]
    
    for table in tables:
        try:
            cursor.execute(f"DROP TABLE {table}")
            print(f"  Dropped {table}")
        except sqlite3.OperationalError:
            print(f"  {table} already removed")
    
    conn.commit()
    conn.close()
    print("Cleanup completed!")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python migrate_data.py <database_path> [--cleanup]")
        sys.exit(1)
    
    db_path = sys.argv[1]
    cleanup = '--cleanup' in sys.argv
    
    if cleanup:
        cleanup_old_tables(db_path)
    else:
        migrate_database(db_path)
