# Database Restore Function Schema Mismatch Fix

## Issue
After adding new fields to the `Seminar` model (specifically `notes`, `created_at`, `updated_at` columns), database restores from older backups that didn't include these columns would fail with error: **"Restore failed: The string did not match the expected pattern"**

### Root Cause
The restore functions in both `app/main.py` and `app/admin_db.py` were using hardcoded column indices when reading data from the backup database:
```python
# OLD APPROACH - FRAGILE
backup_cursor.execute("SELECT id, title, date, start_time, end_time, speaker_id, room_id, abstract, paper_title, status, room_booked, announcement_sent, calendar_invite_sent, website_updated, catering_ordered FROM seminars")
for row in backup_cursor.fetchall():
    seminar = Seminar(
        title=row[1],      # brittle row indexing
        date=row[2],
        # ... etc
    )
```

**Problems:**
1. If the backup database schema is different (missing columns), the SELECT fails or returns wrong data
2. No handling for missing columns with proper defaults
3. Date parsing could fail if format is unexpected
4. No logging of schema differences

## Solution

### 1. Dynamic Schema Detection (app/main.py - restore_database endpoint)
Modified the restore functions to:
- Detect which columns actually exist in the backup database using `PRAGMA table_info()`
- Dynamically build the SELECT query with only available columns
- Map data by column name instead of rigid indices
- Provide defaults for missing columns
- Handle date string parsing with fallback formats

```python
# NEW APPROACH - ROBUST
backup_cursor.execute("PRAGMA table_info(seminars)")
available_cols = {row[1]: row[0] for row in backup_cursor.fetchall()}

seminar_columns = ['id', 'title', 'date', 'start_time', ...  'notes']
cols_to_select = [col for col in seminar_columns if col in available_cols]

for row in backup_cursor.fetchall():
    row_dict = {cols_to_select[i]: row[i] for i in range(len(row))}
    # Safe access with defaults
    title = row_dict.get('title')
    date_val = row_dict.get('date')
    notes = row_dict.get('notes')  # Will be None if column missing
```

### 2. Schema Migration (app/admin_db.py - confirm_restore endpoint)
Added automatic schema migration after database restore:
- Function `_get_backup_schema()`: Detects all tables and their columns
- Function `_migrate_backup_schema()`: Adds missing columns with appropriate defaults using `ALTER TABLE`
- Handles both column additions and data type migrations
- Logs schema differences for debugging

**Key improvements:**
- Missing `notes` columns get `TEXT DEFAULT NULL`
- Missing timestamp columns get `DATETIME DEFAULT CURRENT_TIMESTAMP`
- Non-fatal migration errors logged as warnings
- Backup schema information included in audit logs

## Changes Made

### Files Modified
1. **app/main.py** (lines 4510-4575)
   - Fixed `restore_database()` endpoint for seminars restoration
   - Fixed speaker restoration with dynamic schema detection
   - Added date parsing with multiple format support
   - Added comprehensive error logging

2. **app/admin_db.py** (lines ~170-650)
   - Added `_get_backup_schema()` function
   - Added `_migrate_backup_schema()` function
   - Enhanced `confirm_restore()` with schema migration
   - Return backup schema information for debugging

### Testing
- Verified dynamic column selection works with old schemas
- Confirmed date parsing handles ISO and standard formats
- All existing seminar tests pass
- Schema migration handles missing columns gracefully

## Impact
- **Backward Compatibility**: Old backups can now be restored successfully
- **Forward Compatibility**: New backups include all current columns
- **Schema Evolution**: Future schema changes won't break old backups
- **Debugging**: Audit logs include backup schema for troubleshooting

## How to Use
1. Upload a backup database file (even old schema)
2. The system will detect the schema differences
3. Missing columns are added with sensible defaults
4. Data is restored preserving integrity
5. Check audit logs for detailed migration information

## Next Steps
- Consider adding a schema version field to backups for future compatibility
- May want to add a manual schema repair endpoint if needed
- Consider deprecating the old restore endpoint in favor of admin_db.py version
