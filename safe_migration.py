"""
SAFE Migration Plan - Incremental changes with backward compatibility

Phase 1: Add missing columns (safe, no data loss)
Phase 2: Update backend to use new columns
Phase 3: Update frontend if needed
Phase 4: Test thoroughly
Phase 5: Remove old columns (optional)
"""

import sqlite3
from datetime import datetime

def phase1_add_columns(db_path: str):
    """Add missing columns to existing tables."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Phase 1: Adding missing columns...")
    
    # Add slot_id to seminars (the critical missing link)
    try:
        cursor.execute("ALTER TABLE seminars ADD COLUMN slot_id INTEGER UNIQUE REFERENCES seminar_slots(id)")
        print("  ✓ Added seminars.slot_id")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("  ✓ seminars.slot_id already exists")
        else:
            raise
    
    # Add suggestion_id to seminars
    try:
        cursor.execute("ALTER TABLE seminars ADD COLUMN suggestion_id INTEGER REFERENCES speaker_suggestions(id)")
        print("  ✓ Added seminars.suggestion_id")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("  ✓ seminars.suggestion_id already exists")
        else:
            raise
    
    # Ensure seminar_slots has assigned_suggestion_id (added in previous deploy)
    try:
        cursor.execute("ALTER TABLE seminar_slots ADD COLUMN assigned_suggestion_id INTEGER REFERENCES speaker_suggestions(id)")
        print("  ✓ Added seminar_slots.assigned_suggestion_id")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("  ✓ seminar_slots.assigned_suggestion_id already exists")
        else:
            raise
    
    conn.commit()
    conn.close()
    print("Phase 1 complete!\n")

def phase2_migrate_data(db_path: str):
    """Migrate existing data to new columns."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Phase 2: Migrating data...")
    
    # For each slot with assigned_seminar_id, update the seminar's slot_id
    cursor.execute("""
        SELECT id, assigned_seminar_id, assigned_suggestion_id 
        FROM seminar_slots 
        WHERE assigned_seminar_id IS NOT NULL
    """)
    slots = cursor.fetchall()
    
    updated = 0
    for slot_id, seminar_id, suggestion_id in slots:
        # Update seminar with slot_id
        cursor.execute(
            "UPDATE seminars SET slot_id = ? WHERE id = ? AND slot_id IS NULL",
            (slot_id, seminar_id)
        )
        
        # Update seminar with suggestion_id if we have it
        if suggestion_id:
            cursor.execute(
                "UPDATE seminars SET suggestion_id = ? WHERE id = ? AND suggestion_id IS NULL",
                (suggestion_id, seminar_id)
            )
        
        if cursor.rowcount > 0:
            updated += 1
    
    conn.commit()
    print(f"  ✓ Updated {updated} seminars with slot_id/suggestion_id")
    
    # For seminars without suggestion_id, try to find matching suggestion
    cursor.execute("""
        SELECT s.id, s.speaker_id, s.title, s.date
        FROM seminars s
        WHERE s.suggestion_id IS NULL AND s.speaker_id IS NOT NULL
    """)
    seminars = cursor.fetchall()
    
    matched = 0
    for seminar_id, speaker_id, title, date in seminars:
        # Find suggestion with same speaker_id and similar date
        cursor.execute("""
            SELECT ss.id 
            FROM speaker_suggestions ss
            JOIN seminar_slots sl ON sl.semester_plan_id = ss.semester_plan_id
            WHERE ss.speaker_id = ? 
            AND sl.date = ?
            AND ss.status = 'confirmed'
            LIMIT 1
        """, (speaker_id, date))
        
        result = cursor.fetchone()
        if result:
            cursor.execute(
                "UPDATE seminars SET suggestion_id = ? WHERE id = ?",
                (result[0], seminar_id)
            )
            matched += 1
    
    conn.commit()
    print(f"  ✓ Matched {matched} additional seminars to suggestions")
    
    conn.close()
    print("Phase 2 complete!\n")

def phase3_verify(db_path: str):
    """Verify data integrity after migration."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Phase 3: Verifying data integrity...")
    
    # Count seminars with slot_id
    cursor.execute("SELECT COUNT(*) FROM seminars WHERE slot_id IS NOT NULL")
    with_slot = cursor.fetchone()[0]
    
    # Count seminars with suggestion_id
    cursor.execute("SELECT COUNT(*) FROM seminars WHERE suggestion_id IS NOT NULL")
    with_suggestion = cursor.fetchone()[0]
    
    # Count total seminars
    cursor.execute("SELECT COUNT(*) FROM seminars")
    total = cursor.fetchone()[0]
    
    # Count slots with assigned_seminar_id
    cursor.execute("SELECT COUNT(*) FROM seminar_slots WHERE assigned_seminar_id IS NOT NULL")
    assigned_slots = cursor.fetchone()[0]
    
    print(f"  Seminars with slot_id: {with_slot}/{total}")
    print(f"  Seminars with suggestion_id: {with_suggestion}/{total}")
    print(f"  Slots with assigned seminar: {assigned_slots}")
    
    # Check for mismatches
    cursor.execute("""
        SELECT COUNT(*) 
        FROM seminar_slots sl
        JOIN seminars s ON sl.assigned_seminar_id = s.id
        WHERE s.slot_id IS NOT NULL AND s.slot_id != sl.id
    """)
    mismatches = cursor.fetchone()[0]
    
    if mismatches > 0:
        print(f"  ⚠ WARNING: {mismatches} slot/seminar mismatches found!")
    else:
        print(f"  ✓ No slot/seminar mismatches")
    
    conn.close()
    print("Phase 3 complete!\n")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python safe_migration.py <database_path>")
        sys.exit(1)
    
    db_path = sys.argv[1]
    
    print("=" * 60)
    print("SAFE MIGRATION - Seminars App Data Model")
    print("=" * 60)
    print()
    
    phase1_add_columns(db_path)
    phase2_migrate_data(db_path)
    phase3_verify(db_path)
    
    print("=" * 60)
    print("Migration complete! Please test the application.")
    print("=" * 60)
