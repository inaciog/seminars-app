#!/usr/bin/env python3
"""
Migration script to add ticket_purchase_info column to seminar_details table.
Run this after deployment to update the database schema.
"""

import sqlite3
import sys
from pathlib import Path

# Get database path from environment or use default
def get_db_path():
    import os
    db_url = os.environ.get('DATABASE_URL', '/data/seminars.db')
    if db_url.startswith('sqlite:///'):
        return db_url.replace('sqlite:///', '/')
    elif db_url.startswith('sqlite://'):
        return db_url.replace('sqlite://', '/')
    return db_url

def migrate():
    db_path = get_db_path()
    
    # Handle relative paths
    if not Path(db_path).is_absolute():
        db_path = str(Path(__file__).parent / db_path)
    
    print(f"Connecting to database: {db_path}")
    
    if not Path(db_path).exists():
        print(f"Database not found at {db_path}")
        sys.exit(1)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if column already exists
    cursor.execute("PRAGMA table_info(seminar_details)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'ticket_purchase_info' in columns:
        print("Column 'ticket_purchase_info' already exists. No migration needed.")
    else:
        print("Adding 'ticket_purchase_info' column to seminar_details table...")
        cursor.execute("ALTER TABLE seminar_details ADD COLUMN ticket_purchase_info TEXT")
        conn.commit()
        print("Migration completed successfully!")
    
    conn.close()

if __name__ == "__main__":
    migrate()
