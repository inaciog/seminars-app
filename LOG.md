# Changelog

## 2026 — Expressive Recent Activity with Before/After Diffs

### Change
Recent Activity now shows structured, field-level change details so edits are explicit:
- what field changed,
- what it was before,
- what it is after,
- and whether a value was added or removed.

### Backend
- Added safe, reusable activity diff helpers in [app/main.py](app/main.py) to normalize values and build `changes` payloads.
- Enriched activity events for key operations (seminar updates, seminar details updates, semester plan create/update, slot create/update, workflow updates).
- Extended expressive details to additional flows: slot unassign, speaker suggestion create/update, availability submissions, speaker info submissions, assignment flows, file upload/delete flows, and all speaker-token link creation events.
- Kept storage fully backward-compatible by using existing `activity_events.details_json` (no schema migration, no destructive changes).

### Frontend
- Updated [frontend/src/modules/seminars/SeminarsModule.tsx](frontend/src/modules/seminars/SeminarsModule.tsx) to render structured activity changes in each Recent Activity card.
- Added support for new `SLOT_UPDATED` event label.
- Preserved compatibility with older activity entries that have no `changes` payload.

### Safety
- No data model changes and no deletions.
- Existing activity rows remain valid and readable.
- Verified with backend tests and frontend production build.

## 2026 — Status Page Always Shows Availability/Info Action Buttons

### Change
On external speaker status page:
- Step 1 now always shows a **Submit Availability** button.
- Step 2 now always shows a **Submit Information** button.

### Implementation
- If an unexpired token is missing, the page now auto-generates the required token (`availability` or `info`) and renders the button link immediately.
- Removed passive “Waiting for Availability Request” and “Waiting for Information Request” boxes.

---

## 2026 — Clarified Speaker Status Messaging (Confirmed Seminar vs Ticket Timing)

### Change
Updated external speaker status page wording to make clear that, before proposal approval, the seminar is still confirmed and can be planned normally.

### Wording Adjustments
- Updated pre-approval warning box text.
- Updated Step 2 (Date Assigned) message.
- Updated Step 3 (Information Received / Waiting for Review) message.

### Clarification
Only ticket purchase timing is restricted (must be after proposal approval) for bureaucratic reimbursement reasons.

---

## 2026 — External Speaker Status Fully Checkbox-Driven

### Change
Speaker external status page now derives status strictly from internal workflow checkboxes.

### Status Criteria (checkbox only)
- Step 1 (Waiting for Date Availability): default when later-step checkboxes are not checked
- Step 2 (Date Assigned): `speaker_notified_of_date`
- Step 3 (Information Received): `proposal_submitted` (renamed label in UI to “Information received”)
- Step 4 (Proposal Approved): `proposal_approved`

### Important Behavior Change
- External availability submission no longer auto-checks workflow status checkboxes.
- External info submission no longer auto-checks workflow status checkboxes.
- Internal checkboxes are now the only criterion for status progression.

---

## 2026 — Fix Missing Ticket Instructions on Approved Status Page

### Issue
Approved external status page sometimes did not show ticket purchase instructions even when `ticket_purchase_info` was filled in seminar details.

### Root Cause
Status page selected seminar by `speaker_id` only, which can point to a different seminar than the one linked to the current suggestion/token.

### Fix
Updated seminar resolution order in speaker status page:
1. Most recent info token seminar for the suggestion
2. Slot assignment via `assigned_suggestion_id`
3. Fallback by speaker_id

This ensures `ticket_purchase_info` is read from the correct seminar details record.

---

## 2026 — Speaker Status Page (Approved State) Simplification

### Change
When proposal status is approved on the external speaker status page, it now shows a single green approval box only.

### Details
- The approved box states that the proposal is approved and that travel tickets can be purchased.
- The same approved box now includes the content from `ticket_purchase_info` (Ticket Purchase Instructions) from seminar details when provided.
- Removed the duplicate second approved green box.

---

## 2026 — Replace Success Popups with Inline Status

### Change
Removed blocking success popup dialogs in seminar details modal and replaced them with inline status messages shown in the modal footer.

### Updated Flows
- Save changes
- File upload success
- File delete success

### Notes
- Error dialogs were left unchanged in this pass.

---

## 2026 — Speaker Availability Limited to Semester Plan Slot Dates

### Issue
External speaker availability form allowed selecting any date within the semester range, including dates that were not actual seminar slot dates in the plan.

### Fix
- Updated availability page generation to pass explicit `allowed_slot_dates` from the semester plan (all slot dates in the plan).
- Calendar UI now enables selection only for those allowed dates; all other dates are disabled.
- Shift-range selection also respects allowed dates.
- Added server-side validation in `submit-availability` to reject dates outside plan slot dates.
- Included `allowed_slot_dates` in token availability API response for consistency.

### Safety
- Restriction is enforced both client-side and server-side.
- Existing old backup/restore compatibility remains unchanged.

---

## 2026 — Payment Details Expansion (Internal + External Forms)

### Requested Change
Add payment-section fields and region-specific bank requirements:
- Contact Number
- Europe: SWIFT + IBAN
- USA: ABA Routing Number + SWIFT
- Australia: BSB Number + SWIFT
- Elsewhere: SWIFT

### What Was Updated
- Extended `SeminarDetails` schema with:
    - `contact_number`
    - `bank_region`
    - `iban`
    - `aba_routing_number`
    - `bsb_number`
- Updated API request/response models and handlers for:
    - Internal seminar details edit/view endpoints
    - External speaker token info read/submit endpoints
- Updated internal UI (`SeminarDetailsModal`, `SeminarViewPage`) to capture and display the new fields.
- Updated external speaker form (`speaker_info_v6`) with dynamic bank-field visibility by region and autosave payload support.

### Backward Compatibility / Restore Safety
- Added schema compatibility migrations for old databases to create missing `seminar_details` columns automatically.
- Included new `seminar_details` columns in two-step restore schema migration (`admin_db`).
- Existing/old backups remain restorable (missing new columns are added with `ALTER TABLE`).

---

## 2026 — Restore Slot Assignment Relinking Fix

### Issue
After restoring a backup database, semester planning slots were present but did not show linked seminar details (speaker name and talk title) in the date slots.

### Root Cause
The restore endpoint copied `seminar_slots` without restoring assignment fields (`assigned_seminar_id`, `assigned_suggestion_id`), and did not remap backup IDs to current database IDs for related tables (`speakers`, `rooms`, `seminars`, `speaker_suggestions`).

### Fix
- Restored `seminar_slots` with dynamic column detection including assignment fields
- Added ID remapping maps for plans, slots, suggestions, speakers, rooms, and seminars
- Restored rooms explicitly (with mapping) before seminar restore
- Remapped seminar `speaker_id` and `room_id` during seminar import
- Re-applied slot assignments in a dedicated relinking pass after seminars/suggestions are restored

---

## 2025 — Planning Board Speaker Name Fix

### Issue
The semester planning board's list of dates was not showing the speaker names for slots that had been assigned a speaker.

### Root Cause
Two bugs in `get_planning_board` (`app/main.py`):
1. The seminar query used `selectinload(Seminar.room)` but NOT `selectinload(Seminar.speaker)`. The speaker relationship relied on lazy loading wrapped in a bare `try/except`, which could silently skip the speaker name if any issue occurred.
2. The API response never included the `plan` object, even though the frontend expected `boardData.plan.name` for the board header.
3. The `availability` list for suggestions was missing the `id` field.

### Fix
- Changed seminar query to eagerly load both room and speaker: `.options(selectinload(Seminar.room), selectinload(Seminar.speaker))`
- Cleaned up the speaker-name resolution to a simple `if seminar.speaker / elif seminar.speaker_id` fallback (no bare try/except swallowing errors)
- Added `plan` object to the planning-board response
- Added `id` to each availability item in the suggestions list

---

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
