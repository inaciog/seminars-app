# Seminars App Data Model Overhaul

## Current Problems
1. **Inconsistent speaker identification**: Matching by name instead of IDs
2. **Orphaned records**: Seminars with speakers not in suggestions
3. **Redundant data**: Speaker info stored in multiple places
4. **Weak relationships**: No foreign key constraints between slots/suggestions/seminars
5. **Frontend-dependent logic**: Business logic scattered between frontend and backend

## Proposed Robust Data Model

### Core Entities

#### 1. Speaker (Canonical source of speaker info)
```sql
CREATE TABLE speakers (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT,
    affiliation TEXT,
    website TEXT,
    bio TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 2. SemesterPlan
```sql
CREATE TABLE semester_plans (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    academic_year TEXT NOT NULL,
    semester TEXT NOT NULL,
    default_room TEXT,
    status TEXT DEFAULT 'draft', -- draft, active, archived
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 3. SeminarSlot (Time/place container)
```sql
CREATE TABLE seminar_slots (
    id INTEGER PRIMARY KEY,
    semester_plan_id INTEGER NOT NULL,
    date DATE NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    room TEXT NOT NULL,
    status TEXT DEFAULT 'available', -- available, reserved, confirmed, cancelled
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (semester_plan_id) REFERENCES semester_plans(id) ON DELETE CASCADE
);
```

#### 4. SpeakerSuggestion (Intent to invite)
```sql
CREATE TABLE speaker_suggestions (
    id INTEGER PRIMARY KEY,
    semester_plan_id INTEGER NOT NULL,
    speaker_id INTEGER, -- NULL until speaker is in system
    
    -- Denormalized for suggestion phase (copied from speaker when confirmed)
    suggested_speaker_name TEXT NOT NULL,
    suggested_speaker_email TEXT,
    suggested_speaker_affiliation TEXT,
    
    suggested_topic TEXT,
    suggested_by TEXT NOT NULL,
    priority TEXT DEFAULT 'medium',
    status TEXT DEFAULT 'pending', -- pending, contacted, checking_availability, availability_received, confirmed, declined
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (semester_plan_id) REFERENCES semester_plans(id) ON DELETE CASCADE,
    FOREIGN KEY (speaker_id) REFERENCES speakers(id) ON DELETE SET NULL
);
```

#### 5. Seminar (Actual scheduled event)
```sql
CREATE TABLE seminars (
    id INTEGER PRIMARY KEY,
    slot_id INTEGER UNIQUE, -- One seminar per slot, enforced at DB level
    speaker_id INTEGER NOT NULL,
    suggestion_id INTEGER, -- Link back to original suggestion
    
    title TEXT NOT NULL,
    abstract TEXT,
    date DATE NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    room TEXT NOT NULL,
    status TEXT DEFAULT 'planned',
    
    -- Bureaucracy tracking
    room_booked BOOLEAN DEFAULT FALSE,
    announcement_sent BOOLEAN DEFAULT FALSE,
    calendar_invite_sent BOOLEAN DEFAULT FALSE,
    website_updated BOOLEAN DEFAULT FALSE,
    catering_ordered BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (slot_id) REFERENCES seminar_slots(id) ON DELETE SET NULL,
    FOREIGN KEY (speaker_id) REFERENCES speakers(id) ON DELETE RESTRICT,
    FOREIGN KEY (suggestion_id) REFERENCES speaker_suggestions(id) ON DELETE SET NULL
);
```

#### 6. SpeakerAvailability (When speaker is available)
```sql
CREATE TABLE speaker_availabilities (
    id INTEGER PRIMARY KEY,
    suggestion_id INTEGER NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    preference TEXT DEFAULT 'available', -- available, preferred
    earliest_time TEXT,
    latest_time TEXT,
    notes TEXT,
    FOREIGN KEY (suggestion_id) REFERENCES speaker_suggestions(id) ON DELETE CASCADE
);
```

#### 7. SpeakerToken (For external speaker forms)
```sql
CREATE TABLE speaker_tokens (
    id INTEGER PRIMARY KEY,
    token TEXT UNIQUE NOT NULL,
    suggestion_id INTEGER NOT NULL,
    seminar_id INTEGER, -- Set once seminar is created
    token_type TEXT NOT NULL, -- availability, info
    expires_at TIMESTAMP NOT NULL,
    used_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (suggestion_id) REFERENCES speaker_suggestions(id) ON DELETE CASCADE,
    FOREIGN KEY (seminar_id) REFERENCES seminars(id) ON DELETE SET NULL
);
```

#### 8. SeminarDetails (Extended info submitted by speaker)
```sql
CREATE TABLE seminar_details (
    id INTEGER PRIMARY KEY,
    seminar_id INTEGER UNIQUE NOT NULL,
    
    -- Travel info
    passport_number TEXT,
    passport_country TEXT,
    departure_city TEXT,
    travel_method TEXT,
    needs_accommodation BOOLEAN DEFAULT FALSE,
    check_in_date DATE,
    check_out_date DATE,
    
    -- Payment info
    payment_email TEXT,
    beneficiary_name TEXT,
    bank_name TEXT,
    swift_code TEXT,
    bank_account_number TEXT,
    bank_address TEXT,
    currency TEXT,
    
    -- Talk requirements
    needs_projector BOOLEAN DEFAULT TRUE,
    needs_microphone BOOLEAN DEFAULT FALSE,
    special_requirements TEXT,
    
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (seminar_id) REFERENCES seminars(id) ON DELETE CASCADE
);
```

#### 9. UploadedFile
```sql
CREATE TABLE uploaded_files (
    id INTEGER PRIMARY KEY,
    seminar_id INTEGER NOT NULL,
    category TEXT NOT NULL, -- cv, photo, passport, abstract, other
    original_filename TEXT NOT NULL,
    storage_filename TEXT NOT NULL,
    file_size INTEGER,
    uploaded_by TEXT, -- 'speaker' or 'admin'
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (seminar_id) REFERENCES seminars(id) ON DELETE CASCADE
);
```

## Key Design Principles

### 1. Single Source of Truth
- **Speaker info**: `speakers` table is canonical
- **Seminar details**: `seminars` table + `seminar_details` extension
- **Scheduling**: `seminar_slots` defines time/place, `seminars` links to it

### 2. Immutable History
- Suggestions keep their original suggested_* fields even after linking to speaker
- This preserves the history of what was originally proposed

### 3. Strong Foreign Keys
- All relationships use foreign keys with appropriate ON DELETE actions
- No orphaned records possible

### 4. Clear Status Flow
```
Suggestion: pending → contacted → checking_availability → availability_received → confirmed → declined
Slot: available → reserved → confirmed → cancelled
Seminar: planned → confirmed → completed → cancelled
```

### 5. No Name-Based Matching
- All matching uses integer IDs
- Names are for display only, never for logic

## API Design Principles

### 1. Consistent Endpoints
```
GET    /api/v1/speakers
POST   /api/v1/speakers
GET    /api/v1/speakers/{id}
PUT    /api/v1/speakers/{id}
DELETE /api/v1/speakers/{id}

GET    /api/v1/semester-plans
POST   /api/v1/semester-plans
GET    /api/v1/semester-plans/{id}
PUT    /api/v1/semester-plans/{id}
DELETE /api/v1/semester-plans/{id}
GET    /api/v1/semester-plans/{id}/planning-board

GET    /api/v1/seminar-slots
POST   /api/v1/seminar-slots
GET    /api/v1/seminar-slots/{id}
PUT    /api/v1/seminar-slots/{id}
DELETE /api/v1/seminar-slots/{id}

GET    /api/v1/speaker-suggestions
POST   /api/v1/speaker-suggestions
GET    /api/v1/speaker-suggestions/{id}
PUT    /api/v1/speaker-suggestions/{id}
DELETE /api/v1/speaker-suggestions/{id}

GET    /api/v1/seminars
POST   /api/v1/seminars
GET    /api/v1/seminars/{id}
PUT    /api/v1/seminars/{id}
DELETE /api/v1/seminars/{id}
```

### 2. Atomic Operations
- Assign speaker to slot = create seminar + update slot + update suggestion (all in one transaction)
- No partial states possible

### 3. Validation at DB Level
- Check constraints prevent invalid states
- Triggers maintain consistency

## Migration Strategy

1. **Backup existing data**
2. **Create new tables** alongside old ones
3. **Migrate data** with validation
4. **Update API** to use new tables
5. **Test thoroughly**
6. **Drop old tables**

## Frontend Isolation

The frontend should:
- Only interact via well-defined API endpoints
- Never assume data relationships
- Handle all error states gracefully
- Not duplicate business logic

The backend should:
- Enforce all business rules
- Maintain data integrity
- Provide clear error messages
- Never trust frontend input
