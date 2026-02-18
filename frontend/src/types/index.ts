// Module and Capability Types
export interface Module {
  name: string;
  description: string;
  version: string;
  capabilities: Capability[];
}

export interface Capability {
  name: string;
  description: string;
  parameters?: Record<string, any>;
}

// API Response Types
export interface ActionResult<T = any> {
  success: boolean;
  message: string;
  data: T;
  timestamp: string;
}

export interface SystemInfo {
  name: string;
  version: string;
  modules: string[];
}

// Chat Types
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  actions?: ActionResult[];
  timestamp: string;
}

// Seminars Module Types
export interface Speaker {
  id: number;
  name: string;
  email: string;
  affiliation: string;
  website?: string;
  bio?: string;
  notes?: string;
  created_at: string;
}

export interface Seminar {
  id: number;
  title: string;
  abstract?: string;
  date: string;
  start_time: string;
  end_time: string;
  room: string;
  building?: string;
  speaker_id?: number;
  speaker?: Speaker;
  status: 'planned' | 'confirmed' | 'cancelled' | 'completed';
  series?: string;
  organizer_notes?: string;
  room_booked: boolean;
  catering_ordered: boolean;
  announcement_sent: boolean;
  calendar_invite_sent: boolean;
  reimbursement_initiated: boolean;
}

export interface PendingTask {
  seminar_id: number;
  title: string;
  date: string;
  days_until: number;
  tasks: string[];
}

// Reimbursements Module Types
export interface Grant {
  id: number;
  name: string;
  grant_type: string;
  grant_number?: string;
  funding_body: string;
  start_date?: string;
  end_date?: string;
  total_budget?: number;
  max_flight_cost?: number;
  max_hotel_nightly_rate?: number;
  max_meal_daily_allowance?: number;
  requires_pre_approval: boolean;
  requires_boarding_pass: boolean;
  requires_original_receipts: boolean;
  currency: string;
  special_rules?: string;
  contact_email?: string;
  is_active: boolean;
}

export interface Expense {
  id: number;
  claim_id: number;
  category: string;
  description: string;
  amount: number;
  currency: string;
  expense_date: string;
  location?: string;
  has_receipt: boolean;
  has_boarding_pass: boolean;
  notes?: string;
}

export interface ReimbursementClaim {
  id: number;
  title: string;
  description?: string;
  purpose: string;
  grant_id: number;
  grant?: Grant;
  trip_start_date: string;
  trip_end_date: string;
  destination: string;
  status: string;
  total_amount: number;
  total_amount_eur: number;
  pre_approval_obtained: boolean;
  invitation_letter_received: boolean;
  submitted_date?: string;
  submission_reference?: string;
  expenses?: Expense[];
}

// Teaching Module Types
export interface Course {
  id: number;
  code: string;
  name: string;
  description?: string;
  level: string;
  credits: number;
  semester: string;
  academic_year: string;
  schedule?: string;
  room?: string;
  expected_students?: number;
  actual_students?: number;
  main_instructor: string;
  is_active: boolean;
}

export interface Assignment {
  id: number;
  course_id: number;
  name: string;
  assignment_type: string;
  description?: string;
  release_date: string;
  due_date: string;
  weight_percent: number;
  max_points: number;
  grades_published: boolean;
}

export interface Student {
  id: number;
  student_id: string;
  name: string;
  email: string;
  program?: string;
}

export interface Deadline {
  assignment_id: number;
  course_code: string;
  course_name: string;
  assignment_name: string;
  type: string;
  due_date: string;
  days_until: number;
  urgent: boolean;
}

// Navigation Types
export interface NavSection {
  id: string;
  name: string;
  icon: string;
  path: string;
  subsections?: NavSubsection[];
}

export interface NavSubsection {
  id: string;
  name: string;
  path: string;
}

// Semester Planning Types
export interface SemesterPlan {
  id: number;
  name: string;
  academic_year: string;
  semester: string;
  default_room: string;
  default_start_time: string;
  default_duration_minutes: number;
  status: 'draft' | 'active' | 'completed' | 'archived';
  notes?: string;
}

export interface SeminarSlot {
  id: number;
  semester_plan_id: number;
  date: string;
  start_time: string;
  end_time: string;
  room: string;
  status: 'available' | 'reserved' | 'confirmed' | 'cancelled';
  assigned_seminar_id?: number;
}

export interface SpeakerSuggestion {
  id: number;
  suggested_by: string;
  suggested_by_email?: string;
  speaker_id?: number;
  speaker_name: string;
  speaker_email?: string;
  speaker_affiliation?: string;
  suggested_topic?: string;
  reason?: string;
  priority: 'low' | 'medium' | 'high';
  status: string;
  semester_plan_id?: number;
  created_at: string;
  availability?: Array<{
    date: string;
    preference: string;
  }>;
}
