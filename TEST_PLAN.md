# Test Plan for Data Model Overhaul

## Pre-Migration Tests (Run on current data)

### 1. Data Integrity Check
```sql
-- Count records
SELECT 'speakers' as table_name, COUNT(*) as count FROM speakers
UNION ALL SELECT 'seminars', COUNT(*) FROM seminars
UNION ALL SELECT 'seminar_slots', COUNT(*) FROM seminar_slots
UNION ALL SELECT 'speaker_suggestions', COUNT(*) FROM speaker_suggestions
UNION ALL SELECT 'speaker_tokens', COUNT(*) FROM speaker_tokens;

-- Find seminars without speakers
SELECT s.id, s.title FROM seminars s
LEFT JOIN speakers sp ON s.speaker_id = sp.id
WHERE sp.id IS NULL;

-- Find slots with assigned_seminar_id but seminar doesn't exist
SELECT sl.id, sl.assigned_seminar_id 
FROM seminar_slots sl
LEFT JOIN seminars s ON sl.assigned_seminar_id = s.id
WHERE sl.assigned_seminar_id IS NOT NULL AND s.id IS NULL;

-- Find suggestions with speaker_id but speaker doesn't exist
SELECT ss.id, ss.speaker_name 
FROM speaker_suggestions ss
LEFT JOIN speakers sp ON ss.speaker_id = sp.id
WHERE ss.speaker_id IS NOT NULL AND sp.id IS NULL;
```

### 2. Relationship Check
```sql
-- Slots with seminars (should match)
SELECT COUNT(*) FROM seminar_slots WHERE assigned_seminar_id IS NOT NULL;
SELECT COUNT(*) FROM seminars WHERE EXISTS (
    SELECT 1 FROM seminar_slots WHERE assigned_seminar_id = seminars.id
);

-- Suggestions with speakers
SELECT COUNT(*) FROM speaker_suggestions WHERE speaker_id IS NOT NULL;
```

## Migration Steps

### Step 1: Backup
```bash
cp /data/seminars.db /data/seminars.db.backup.$(date +%Y%m%d_%H%M%S)
```

### Step 2: Run Migration Script
```bash
cd /root/.openclaw/workspace/seminars-app
python3 safe_migration.py /data/seminars.db
```

Expected output:
```
Phase 1: Adding missing columns...
  ✓ Added seminars.slot_id (or already exists)
  ✓ Added seminars.suggestion_id (or already exists)
  ✓ Added seminar_slots.assigned_suggestion_id (or already exists)
Phase 1 complete!

Phase 2: Migrating data...
  ✓ Updated X seminars with slot_id/suggestion_id
  ✓ Matched Y additional seminars to suggestions
Phase 2 complete!

Phase 3: Verifying data integrity...
  Seminars with slot_id: X/Y
  Seminars with suggestion_id: X/Y
  Slots with assigned seminar: Z
  ✓ No slot/seminar mismatches
Phase 3 complete!
```

### Step 3: Deploy Updated Backend
```bash
fly deploy --app seminars-app
```

## Post-Migration Tests

### 1. Planning Board Loads
- Navigate to semester planning
- Select a plan
- Verify slots, suggestions, and assigned speakers display correctly

### 2. Assign Speaker to Slot
- Click "Add Speaker" to create suggestion
- Select a slot
- Click to assign
- Verify:
  - Slot shows as "confirmed"
  - Speaker name appears
  - Seminar is created
  - Can generate info link

### 3. Generate Info Link
- Click "Info" button on assigned slot
- Verify link is generated
- Verify no "Speaker not found" error

### 4. Speaker Info Form
- Open generated link
- Fill form
- Submit
- Verify data is saved

### 5. Token-Based Operations
- Create availability token
- Submit availability
- Create info token
- Submit info

## Rollback Plan

If issues occur:

1. **Immediate rollback**:
   ```bash
   # Restore from backup
   cp /data/seminars.db.backup.XXXX /data/seminars.db
   # Redeploy previous version
   git checkout HEAD~1
   fly deploy --app seminars-app
   ```

2. **Debug without rollback**:
   - Check logs: `fly logs --app seminars-app`
   - Check migration output
   - Verify database state

## Success Criteria

- [ ] Planning board loads without errors
- [ ] All existing data is preserved
- [ ] Can assign speaker to slot
- [ ] Can generate info/availability links
- [ ] Speaker forms work correctly
- [ ] No "Speaker not found" errors
- [ ] No database constraint violations
