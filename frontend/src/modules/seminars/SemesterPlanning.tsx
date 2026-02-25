import { useState, useMemo, useCallback } from 'react';
import { fetchWithAuth } from '@/api/client';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '@/contexts/AuthContext';
import { 
  Plus, 
  Calendar, 
  Users, 
  X,
  ChevronRight,
  Clock,
  MapPin,
  ArrowRightLeft,
  Info,
  Trash2,
  UserPlus,
  UserX,
  Check,
  Mail,
  Copy,
  FileText,
  MessageSquare,
  Link as LinkIcon,
  ChevronDown,
  ChevronUp,
  Eye,
} from 'lucide-react';
import { cn, CHINA_TIMEZONE, formatDateToYMDChina } from '@/lib/utils';
import { CalendarPicker } from '@/components/CalendarPicker';
import { AddSpeakerModal } from './AddSpeakerModal';
import { AddAvailabilityModal } from './AddAvailabilityModal';
import { openSeminarDetails } from './SeminarsModule';
import { isWithinInterval, parseISO, isSameDay } from 'date-fns';
import type { Seminar } from '@/types';

// Types
interface SemesterPlan {
  id: number;
  name: string;
  default_room: string;
  status: string;
}

interface SeminarSlot {
  id: number;
  date: string;
  start_time: string;
  end_time: string;
  room: string;
  status: 'available' | 'reserved' | 'confirmed' | 'cancelled';
  assigned_seminar_id?: number;
  assigned_speaker_name?: string;
  assigned_seminar_title?: string;
  assigned_suggestion_id?: number;
}

interface SpeakerAvailability {
  id: number;
  date?: string;
  start_date?: string;
  end_date?: string;
  preference: string;
  earliest_time?: string;
  latest_time?: string;
  notes?: string;
}

function getAvailabilityRange(avail: SpeakerAvailability): { start: Date; end: Date } | null {
  const startRaw = avail.start_date || avail.date;
  const endRaw = avail.end_date || avail.date;
  if (!startRaw || !endRaw) return null;

  const start = parseISO(startRaw);
  const end = parseISO(endRaw);
  if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) return null;

  return { start, end };
}

interface SpeakerSuggestion {
  id: number;
  speaker_name: string;
  speaker_affiliation?: string;
  suggested_by: string;
  suggested_by_email?: string;
  reason?: string;
  suggested_topic?: string;
  priority: 'low' | 'medium' | 'high';
  status: string;
  availability?: SpeakerAvailability[];
}

// API functions
const fetchPlans = async (): Promise<SemesterPlan[]> => {
  const response = await fetchWithAuth('/api/v1/seminars/semester-plans');
  if (!response.ok) throw new Error('Failed to fetch plans');
  return response.json();
};

const deletePlan = async (planId: number) => {
  const response = await fetchWithAuth(`/api/v1/seminars/semester-plans/${planId}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    const error = await response.text();
    throw new Error(error || 'Failed to delete plan');
  }
  return response.json();
};

const deleteSuggestion = async (suggestionId: number) => {
  const response = await fetchWithAuth(`/api/v1/seminars/speaker-suggestions/${suggestionId}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    const error = await response.text();
    throw new Error(error || 'Failed to delete suggestion');
  }
  return response.json();
};

const fetchPlanningBoard = async (planId: number): Promise<{ plan: SemesterPlan; slots: SeminarSlot[]; suggestions: SpeakerSuggestion[] }> => {
  const response = await fetchWithAuth(`/api/v1/seminars/semester-plans/${planId}/planning-board`);
  if (!response.ok) throw new Error('Failed to fetch planning board');
  return response.json();
};

const assignSpeaker = async (suggestionId: number, slotId: number) => {
  const response = await fetchWithAuth('/api/v1/seminars/planning/assign', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ suggestion_id: suggestionId, slot_id: slotId }),
  });
  if (!response.ok) throw new Error('Failed to assign speaker');
  return response.json();
};

const unassignSpeaker = async (slotId: number) => {
  const response = await fetchWithAuth(`/api/v1/seminars/slots/${slotId}/unassign`, {
    method: 'POST',
  });
  if (!response.ok) throw new Error('Failed to unassign speaker');
  return response.json();
};

const addSlotToPlan = async (planId: number, slotData: { date: string; start_time: string; end_time: string; room: string }) => {
  const response = await fetchWithAuth(`/api/v1/seminars/semester-plans/${planId}/slots`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(slotData),
  });
  if (!response.ok) throw new Error('Failed to add slot');
  return response.json();
};

export function SemesterPlanning() {
  const { isEditor } = useAuth();
  const [selectedPlanId, setSelectedPlanId] = useState<number | null>(null);
  const [selectedSuggestion, setSelectedSuggestion] = useState<SpeakerSuggestion | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showAddSpeakerModal, setShowAddSpeakerModal] = useState(false);
  const [showAddDateModal, setShowAddDateModal] = useState(false);
  const [editingSuggestion, setEditingSuggestion] = useState<SpeakerSuggestion | null>(null);
  const [expandedNotes, setExpandedNotes] = useState<Record<string, boolean>>({});
  const [unassignModal, setUnassignModal] = useState<{ slotId: number; seminarId: number; seminarTitle: string } | null>(null);
  const queryClient = useQueryClient();

  // Fetch all seminars for viewing details
  const { data: seminars = [] } = useQuery({
    queryKey: ['planning-seminars', selectedPlanId],
    queryFn: async () => {
      const r = await fetchWithAuth('/api/v1/seminars/seminars');
      if (!r.ok) throw new Error('Failed to fetch seminars');
      return r.json() as Promise<Seminar[]>;
    },
  });

  const seminarById = useMemo(() => {
    const map = new Map<number, Seminar>();
    seminars.forEach((s) => map.set(s.id, s));
    return map;
  }, [seminars]);

  const toggleNote = useCallback((id: string) => {
    setExpandedNotes(prev => ({ ...prev, [id]: !prev[id] }));
  }, []);

  const { data: plansRaw, isLoading: plansLoading } = useQuery({
    queryKey: ['semester-plans'],
    queryFn: fetchPlans,
  });

  // Deduplicate plans by id (safety against any duplicate API/db data)
  const plans = useMemo(() => {
    if (!plansRaw?.length) return plansRaw ?? [];
    const seen = new Set<number>();
    return plansRaw.filter((p: { id: number }) => {
      if (seen.has(p.id)) return false;
      seen.add(p.id);
      return true;
    });
  }, [plansRaw]);

  const { data: boardData, isLoading: boardLoading } = useQuery({
    queryKey: ['planning-board', selectedPlanId],
    queryFn: () => fetchPlanningBoard(selectedPlanId!),
    enabled: !!selectedPlanId,
  });

  // Get the selected plan from the plans list
  const selectedPlan = useMemo(() => {
    return plans.find((p: SemesterPlan) => p.id === selectedPlanId);
  }, [plans, selectedPlanId]);

  const assignMutation = useMutation({
    mutationFn: ({ suggestionId, slotId }: { suggestionId: number; slotId: number }) =>
      assignSpeaker(suggestionId, slotId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['planning-board', selectedPlanId] });
      queryClient.invalidateQueries({ queryKey: ['seminars'] });
      queryClient.invalidateQueries({ queryKey: ['bureaucracy'] });
      setSelectedSuggestion(null);
    },
  });

  const unassignMutation = useMutation({
    mutationFn: (slotId: number) => unassignSpeaker(slotId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['planning-board', selectedPlanId] });
      queryClient.invalidateQueries({ queryKey: ['seminars'] });
      queryClient.invalidateQueries({ queryKey: ['bureaucracy'] });
      queryClient.invalidateQueries({ queryKey: ['orphan-seminars'] });
      setUnassignModal(null);
    },
  });

  const deleteSeminarMutation = useMutation({
    mutationFn: (seminarId: number) => fetchWithAuth(`/api/v1/seminars/seminars/${seminarId}`, { method: 'DELETE' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['planning-board', selectedPlanId] });
      queryClient.invalidateQueries({ queryKey: ['seminars'] });
      queryClient.invalidateQueries({ queryKey: ['bureaucracy'] });
      queryClient.invalidateQueries({ queryKey: ['orphan-seminars'] });
      setUnassignModal(null);
    },
    onError: (err: Error) => alert(err.message),
  });

  const deleteSlotMutation = useMutation({
    mutationFn: async (slotId: number) => {
      const response = await fetchWithAuth(`/api/v1/seminars/slots/${slotId}`, {
        method: 'DELETE',
      });
      if (!response.ok) {
        const error = await response.text();
        throw new Error(error || 'Failed to delete slot');
      }
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['planning-board', selectedPlanId] });
      queryClient.invalidateQueries({ queryKey: ['seminars'] });
      queryClient.invalidateQueries({ queryKey: ['bureaucracy'] });
    },
    onError: (error: any) => {
      alert(`Failed to delete slot: ${error.message}`);
    },
  });

  const deletePlanMutation = useMutation({
    mutationFn: deletePlan,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['semester-plans'] });
      setSelectedPlanId(null);
    },
    onError: (error: any) => {
      alert(`Failed to delete plan: ${error.message}`);
    },
  });

  const deleteSuggestionMutation = useMutation({
    mutationFn: deleteSuggestion,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['planning-board', selectedPlanId] });
    },
    onError: (error: any) => {
      alert(`Failed to delete suggestion: ${error.message}`);
    },
  });

  // Group slots by month (using China timezone)
  const slotsByMonth = boardData?.slots?.reduce((acc: Record<string, SeminarSlot[]>, slot) => {
    const month = new Date(slot.date).toLocaleString('en-US', { month: 'long', year: 'numeric', timeZone: CHINA_TIMEZONE });
    if (!acc[month]) acc[month] = [];
    acc[month].push(slot);
    return acc;
  }, {});

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Plan Selector */}
      {!selectedPlanId ? (
        <>
          {/* Header - only shown in list view */}
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Semester Planning</h1>
              <p className="text-gray-600 mt-1">Plan and schedule seminars for the semester</p>
            </div>
            <button
              onClick={() => setShowCreateModal(true)}
              className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
            >
              <Plus className="w-4 h-4" />
              New Semester Plan
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {plansLoading ? (
              <div className="col-span-3 text-center py-12">Loading plans...</div>
            ) : plans?.length === 0 ? (
              <div className="col-span-3 text-center py-12 bg-gray-50 rounded-xl">
                <Calendar className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                <p className="text-gray-600">No semester plans yet</p>
                <button
                  onClick={() => setShowCreateModal(true)}
                  className="mt-4 text-primary-600 hover:underline"
                >
                  Create your first plan
                </button>
              </div>
            ) : (
              plans?.map((plan) => (
              <div
                key={plan.id}
                className="p-6 bg-white border border-gray-200 rounded-xl hover:border-primary-300 hover:shadow-md transition-all group"
              >
                <div className="flex items-start justify-between">
                  <div 
                    className="flex-1 cursor-pointer"
                    onClick={() => setSelectedPlanId(plan.id)}
                  >
                    <h3 className="font-semibold text-gray-900">{plan.name}</h3>
                    <p className="text-sm text-gray-500 mt-2">
                      Room: {plan.default_room}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={cn(
                      'px-2 py-1 text-xs rounded-full',
                      plan.status === 'active' ? 'bg-green-100 text-green-700' :
                      plan.status === 'draft' ? 'bg-amber-100 text-amber-700' :
                      'bg-gray-100 text-gray-700'
                    )}>
                      {plan.status}
                    </span>
                    {!isEditor && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          if (confirm(`Delete plan "${plan.name}"? This will also delete all associated slots.`)) {
                            deletePlanMutation.mutate(plan.id);
                          }
                        }}
                        className="p-1.5 text-red-400 hover:text-red-600 hover:bg-red-50 rounded-lg opacity-0 group-hover:opacity-100 transition-all"
                        title="Delete plan"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                </div>
                <ChevronRight 
                  className="w-5 h-5 text-gray-400 mt-4 ml-auto cursor-pointer" 
                  onClick={() => setSelectedPlanId(plan.id)}
                />
              </div>
            ))
          )}
        </div>
      </>
      ) : (
        /* Planning Board */
        <div className="space-y-6">
          {/* Board Header */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={() => setSelectedPlanId(null)}
                className="text-gray-600 hover:text-gray-900"
              >
                ← Back to Plans
              </button>
              <h2 className="text-xl font-semibold">
                {boardData?.plan?.name}
              </h2>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => window.open(`/faculty/suggest-speaker/${selectedPlanId}`, '_blank')}
                className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700"
              >
                Faculty Form
              </button>
              <button
                type="button"
                onClick={() => setShowAddDateModal(true)}
                className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
              >
                Add Date
              </button>
            </div>
          </div>

          {boardLoading ? (
            <div className="text-center py-12">Loading planning board...</div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Slots Column */}
              <div className="lg:col-span-2 space-y-6">
                {slotsByMonth && Object.entries(slotsByMonth).map(([month, slots]) => (
                  <div key={month} className="bg-white border border-gray-200 rounded-xl overflow-hidden">
                    <div className="px-4 py-3 bg-gray-50 border-b border-gray-200">
                      <h3 className="font-semibold text-gray-900">{month}</h3>
                    </div>
                    <div className="divide-y divide-gray-100">
                      {slots.map((slot) => (
                        <SlotCard
                          key={slot.id}
                          slot={slot}
                          isSelected={selectedSuggestion !== null && slot.status === 'available'}
                          selectedSuggestion={selectedSuggestion}
                          onClick={() => {
                            if (selectedSuggestion && slot.status === 'available') {
                              assignMutation.mutate({
                                suggestionId: selectedSuggestion.id,
                                slotId: slot.id,
                              });
                            }
                          }}
                          onUnassign={() => {
                            if (slot.assigned_seminar_id) {
                              setUnassignModal({
                                slotId: slot.id,
                                seminarId: slot.assigned_seminar_id,
                                seminarTitle: `${slot.assigned_speaker_name || 'Seminar'} on ${new Date(slot.date).toLocaleDateString('en-US', { timeZone: CHINA_TIMEZONE })}`,
                              });
                            }
                          }}
                          onDelete={!isEditor ? () => {
                            if (confirm(`Delete this slot on ${new Date(slot.date).toLocaleDateString('en-US', { timeZone: CHINA_TIMEZONE })}?`)) {
                              deleteSlotMutation.mutate(slot.id);
                            }
                          } : undefined}
                          onViewSeminar={() => {
                            if (slot.assigned_seminar_id) {
                              const seminar = seminarById.get(slot.assigned_seminar_id);
                              if (seminar) {
                                openSeminarDetails(seminar);
                              }
                            }
                          }}
                        />
                      ))}
                    </div>
                  </div>
                ))}
              </div>

              {/* Suggestions Column */}
              <div className="space-y-4">
                <div className="bg-white border border-gray-200 rounded-xl p-4">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="font-semibold text-gray-900 flex items-center gap-2">
                      <Users className="w-5 h-5" />
                      Suggested Speakers
                      {selectedSuggestion && (
                        <span className="text-sm font-normal text-primary-600">
                          (Select a slot)
                        </span>
                      )}
                    </h3>
                    <button
                      onClick={() => setShowAddSpeakerModal(true)}
                      className="flex items-center gap-1 px-3 py-1.5 text-sm bg-primary-100 text-primary-700 rounded-lg hover:bg-primary-200 transition-colors"
                    >
                      <UserPlus className="w-4 h-4" />
                      Add Speaker
                    </button>
                  </div>
                  
                  <div className="space-y-3">
                    {boardData?.suggestions?.map((suggestion) => (
                      <SuggestionCard
                        key={suggestion.id}
                        suggestion={suggestion}
                        isSelected={selectedSuggestion?.id === suggestion.id}
                        expandedNotes={expandedNotes}
                        onToggleNote={toggleNote}
                        onClick={() => setSelectedSuggestion(
                          selectedSuggestion?.id === suggestion.id ? null : suggestion
                        )}
                        onDelete={!isEditor ? () => {
                          if (confirm(`Delete suggestion for "${suggestion.speaker_name}"?`)) {
                            deleteSuggestionMutation.mutate(suggestion.id);
                          }
                        } : undefined}
                        onAddAvailability={() => setEditingSuggestion(suggestion)}
                      />
                    ))}
                    
                    {boardData?.suggestions?.length === 0 && (
                      <p className="text-center text-gray-500 py-4">
                        No speaker suggestions yet
                      </p>
                    )}
                  </div>
                </div>

                {/* Legend */}
                <div className="bg-gray-50 border border-gray-200 rounded-xl p-4">
                  <h4 className="text-sm font-medium text-gray-700 mb-3">Legend</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded-full bg-green-500" />
                      <span className="text-gray-600">Available</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded-full bg-amber-500" />
                      <span className="text-gray-600">Reserved</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded-full bg-blue-500" />
                      <span className="text-gray-600">Confirmed</span>
                    </div>
                    {selectedSuggestion && (
                      <div className="mt-3 pt-3 border-t border-gray-200">
                        <p className="text-primary-600 font-medium">
                          Click an available slot to assign {selectedSuggestion.speaker_name}
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Create Plan Modal */}
      {showCreateModal && (
        <CreatePlanModal onClose={() => setShowCreateModal(false)} />
      )}
      
      {/* Add Speaker Modal */}
      {showAddSpeakerModal && selectedPlanId && (
        <AddSpeakerModal 
          planId={selectedPlanId} 
          onClose={() => setShowAddSpeakerModal(false)} 
        />
      )}
      
      {/* Add Availability Modal */}
      {editingSuggestion && selectedPlanId && (
        <AddAvailabilityModal
          suggestionId={editingSuggestion.id}
          planId={selectedPlanId}
          speakerName={editingSuggestion.speaker_name}
          existingAvailability={editingSuggestion.availability || []}
          onClose={() => setEditingSuggestion(null)}
        />
      )}

      {/* Add Date Modal */}
      {showAddDateModal && selectedPlanId && selectedPlan && (
        <AddDateModal
          planId={selectedPlanId}
          defaultRoom={selectedPlan.default_room || 'TBD'}
          onClose={() => setShowAddDateModal(false)}
        />
      )}

      {/* Unassign choice modal */}
      {unassignModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Unassign speaker from slot</h3>
            <p className="text-gray-600 mb-4">
              What would you like to do with the seminar &quot;{unassignModal.seminarTitle}&quot;?
            </p>
            <div className="flex gap-3">
              {!isEditor && (
                <button
                  onClick={() => {
                    deleteSeminarMutation.mutate(unassignModal.seminarId);
                  }}
                  disabled={deleteSeminarMutation.isPending}
                  className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
                >
                  Delete seminar
                </button>
              )}
              <button
                onClick={() => unassignMutation.mutate(unassignModal.slotId)}
                disabled={unassignMutation.isPending}
                className="flex-1 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
              >
                Keep for reassignment
              </button>
              <button
                onClick={() => setUnassignModal(null)}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function SlotCard({ 
  slot, 
  isSelected,
  selectedSuggestion,
  onClick,
  onUnassign,
  onDelete,
  onViewSeminar,
}: { 
  slot: SeminarSlot; 
  isSelected: boolean;
  selectedSuggestion: SpeakerSuggestion | null;
  onClick: () => void;
  onUnassign?: () => void;
  onDelete?: () => void;
  onViewSeminar?: () => void;
}) {
  const statusColors = {
    available: 'bg-green-50 border-green-200 hover:border-green-300',
    reserved: 'bg-amber-50 border-amber-200',
    confirmed: 'bg-blue-50 border-blue-200',
    cancelled: 'bg-gray-50 border-gray-200 opacity-50',
  };

  // Check if slot date falls within selected speaker's availability ranges
  const isHighlighted = useMemo(() => {
    if (!selectedSuggestion?.availability || selectedSuggestion.availability.length === 0) {
      return false;
    }
    const slotDate = parseISO(slot.date);
    if (Number.isNaN(slotDate.getTime())) return false;
    return selectedSuggestion.availability.some(avail => {
      const range = getAvailabilityRange(avail);
      if (!range) return false;
      return isWithinInterval(slotDate, range) ||
             isSameDay(slotDate, range.start) ||
             isSameDay(slotDate, range.end);
    });
  }, [slot.date, selectedSuggestion]);

  return (
    <div
      onClick={onClick}
      className={cn(
        'p-4 flex items-center justify-between cursor-pointer transition-colors border-l-4',
        statusColors[slot.status],
        isSelected && 'ring-2 ring-primary-500 ring-offset-2',
        isHighlighted && 'bg-emerald-100 border-emerald-300'
      )}
    >
      <div className="flex items-center gap-4">
        <div className="text-center min-w-[60px]">
          <div className="text-2xl font-bold text-gray-900">
            {new Date(slot.date).getDate()}
          </div>
          <div className="text-xs text-gray-500 uppercase">
            {new Date(slot.date).toLocaleString('en-US', { weekday: 'short', timeZone: CHINA_TIMEZONE })}
          </div>
        </div>
        <div>
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <Clock className="w-4 h-4" />
            {slot.start_time} - {slot.end_time}
          </div>
          <div className="flex items-center gap-2 text-sm text-gray-600 mt-1">
            <MapPin className="w-4 h-4" />
            {slot.room}
          </div>
          {slot.assigned_seminar_id && (
            <div className="mt-1 space-y-0.5">
              <div className="flex items-center gap-2 text-sm font-medium text-gray-800">
                <UserPlus className="w-3 h-3 shrink-0" />
                {slot.assigned_speaker_name || 'Assigned'}
              </div>
              {slot.assigned_seminar_title && (
                <div className="text-xs text-gray-500 pl-5 line-clamp-1" title={slot.assigned_seminar_title}>
                  {slot.assigned_seminar_title}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
      <div className="flex items-center gap-2">
        {isHighlighted && (
          <span className="flex items-center gap-1 text-xs text-emerald-700 font-medium">
            <Check className="w-3 h-3" />
            Available
          </span>
        )}
        <span className={cn(
          'px-2 py-1 text-xs font-medium rounded-full',
          slot.status === 'available' ? 'bg-green-100 text-green-700' :
          slot.status === 'reserved' ? 'bg-amber-100 text-amber-700' :
          slot.status === 'confirmed' ? 'bg-blue-100 text-blue-700' :
          'bg-gray-100 text-gray-700'
        )}>
          {slot.status}
        </span>
        {slot.status === 'available' && isSelected && (
          <ArrowRightLeft className="w-5 h-5 text-primary-600" />
        )}
        {(slot.status === 'reserved' || slot.status === 'confirmed') && slot.assigned_seminar_id && (
          <div className="flex items-center gap-1">
            {onViewSeminar && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onViewSeminar();
                }}
                className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg"
                title="View seminar details"
              >
                <Eye className="w-4 h-4" />
              </button>
            )}
            {onUnassign && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onUnassign();
                }}
                className="p-1.5 text-gray-400 hover:text-amber-600 hover:bg-amber-50 rounded-lg"
                title="Unassign speaker"
              >
                <UserX className="w-4 h-4" />
              </button>
            )}
          </div>
        )}
        {onDelete && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onDelete();
            }}
            className="p-1.5 text-red-400 hover:text-red-600 hover:bg-red-50 rounded-lg"
            title="Delete slot"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  );
}

function SuggestionCard({ 
  suggestion, 
  isSelected,
  expandedNotes,
  onToggleNote,
  onClick,
  onDelete,
  onAddAvailability,
}: { 
  suggestion: SpeakerSuggestion; 
  isSelected: boolean;
  expandedNotes: Record<string, boolean>;
  onToggleNote: (id: string) => void;
  onClick: () => void;
  onDelete?: () => void;
  onAddAvailability?: () => void;
}) {
  const priorityColors = {
    low: 'bg-gray-100 text-gray-700',
    medium: 'bg-blue-100 text-blue-700',
    high: 'bg-red-100 text-red-700',
  };

  const statusColors: Record<string, string> = {
    pending: 'bg-gray-100 text-gray-700',
    contacted: 'bg-blue-100 text-blue-700',
    checking_availability: 'bg-amber-100 text-amber-700',
    availability_received: 'bg-purple-100 text-purple-700',
    confirmed: 'bg-green-100 text-green-700',
    declined: 'bg-red-100 text-red-700',
  };

  return (
    <div
      className={cn(
        'border rounded-lg transition-all',
        isSelected 
          ? 'border-primary-500 bg-primary-50 ring-1 ring-primary-500' 
          : 'border-gray-200 hover:border-gray-300 bg-white'
      )}
    >
      {/* Header with actions */}
      <div className="p-3 border-b border-gray-100">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0 flex-1">
            <h4 className="font-medium text-gray-900 truncate">{suggestion.speaker_name}</h4>
            <p className="text-sm text-gray-600 truncate">{suggestion.speaker_affiliation}</p>
          </div>
          <div className="flex items-center gap-1 shrink-0">
            <span className={cn('px-2 py-0.5 text-xs rounded', priorityColors[suggestion.priority])}>
              {suggestion.priority}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2 mt-2">
          <span
            className="text-xs text-gray-500 cursor-default"
            title={suggestion.reason ? `Reason / context: ${suggestion.reason}` : undefined}
          >
            by {suggestion.suggested_by}
            {suggestion.suggested_by_email && <> ({suggestion.suggested_by_email})</>}
          </span>
        </div>
      </div>

      {/* Content */}
      <div 
        className="p-3 cursor-pointer"
        onClick={onClick}
      >
        {suggestion.suggested_topic && (
          <p className="text-sm text-gray-700 mb-2 line-clamp-2">
            <Info className="w-3 h-3 inline mr-1" />
            {suggestion.suggested_topic}
          </p>
        )}
        
        {/* Availability preview */}
        {suggestion.availability && suggestion.availability.length > 0 && (
          <div className="mt-2 pt-2 border-t border-gray-100">
            <p className="text-xs text-gray-500 mb-1.5">
              Available ({suggestion.availability.length} {suggestion.availability.length === 1 ? 'range' : 'ranges'}):
            </p>
            <div className="space-y-1">
              {suggestion.availability.slice(0, 3).map((avail, i) => {
                const range = getAvailabilityRange(avail);
                if (!range) return null;
                const start = range.start;
                const end = range.end;
                const isRange = start.getTime() !== end.getTime();
                const sameMonth = start.getMonth() === end.getMonth() && start.getFullYear() === end.getFullYear();
                const hasNotes = avail.notes && avail.notes.trim().length > 0;
                const noteId = `${suggestion.id}-${avail.id || i}`;
                const isExpanded = expandedNotes[noteId];
                
                return (
                  <div 
                    key={i}
                    className={cn(
                      'text-xs rounded overflow-hidden',
                      avail.preference === 'preferred' ? 'bg-green-100 text-green-700' : 'bg-blue-50 text-blue-700'
                    )}
                  >
                    {/* Date row */}
                    <div 
                      className={cn(
                        'px-2 py-1 flex items-center gap-1.5',
                        hasNotes && 'cursor-pointer hover:opacity-80'
                      )}
                      onClick={(e) => {
                        if (hasNotes) {
                          e.stopPropagation();
                          onToggleNote(noteId);
                        }
                      }}
                    >
                      <Calendar className="w-3 h-3 flex-shrink-0" />
                      <span className="flex-1">
                        {isRange ? (
                          sameMonth ? (
                            <>
                              {start.toLocaleDateString('en-US', { month: 'short', day: 'numeric', timeZone: CHINA_TIMEZONE })} 
                              - {end.toLocaleDateString('en-US', { day: 'numeric', timeZone: CHINA_TIMEZONE })}, {end.toLocaleDateString('en-US', { year: 'numeric', timeZone: CHINA_TIMEZONE })}
                            </>
                          ) : (
                            <>
                              {start.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} 
                              {' - '}
                              {end.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                            </>
                          )
                        ) : (
                          start.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric', timeZone: CHINA_TIMEZONE })
                        )}
                      </span>
                      {hasNotes && (
                        <div className="flex items-center gap-0.5 text-[10px] opacity-70">
                          <MessageSquare className="w-3 h-3" />
                          {isExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                        </div>
                      )}
                    </div>
                    {/* Expandable notes */}
                    {hasNotes && isExpanded && (
                      <div 
                        className="px-2 pb-1.5 text-[10px] text-gray-600 bg-white/50 border-t border-white/30"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <span className="font-medium">Note:</span> {avail.notes}
                      </div>
                    )}
                  </div>
                );
              })}
              {suggestion.availability.length > 3 && (
                <span className="text-xs text-gray-500">
                  +{suggestion.availability.length - 3} more ranges
                </span>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Footer - Management Actions */}
      <div className="px-3 py-2 bg-gray-50 border-t border-gray-100 flex items-center justify-between">
        <span className="text-xs text-gray-400">
          Click card to select
        </span>
        <div className="flex items-center gap-1">
          {onAddAvailability && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onAddAvailability();
              }}
              className="flex items-center gap-1 px-2 py-1 text-xs text-gray-600 hover:text-primary-600 hover:bg-white rounded border border-transparent hover:border-gray-200"
              title="Add availability manually"
            >
              <Calendar className="w-3 h-3" />
              Add dates
            </button>
          )}
          {onDelete && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onDelete();
              }}
              className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg"
              title="Delete suggestion"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

function AddDateModal({ planId, defaultRoom, onClose }: { planId: number; defaultRoom: string; onClose: () => void }) {
  const queryClient = useQueryClient();
  const [selectedDates, setSelectedDates] = useState<Date[]>([]);
  const [startTime, setStartTime] = useState('14:00');
  const [endTime, setEndTime] = useState('15:30');
  const [room, setRoom] = useState(defaultRoom);

  const addSlotsMutation = useMutation({
    mutationFn: async () => {
      // Create slots for all selected dates
      for (const date of selectedDates) {
        await addSlotToPlan(planId, {
          date: formatDateToYMDChina(date),
          start_time: startTime,
          end_time: endTime,
          room: room,
        });
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['planning-board', planId] });
      onClose();
    },
    onError: (error: Error) => {
      alert(`Error: ${error.message}`);
    },
  });

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl p-6 w-full max-w-lg">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold">Add Dates to Plan</h2>
          <button onClick={onClose} className="p-1 hover:bg-gray-100 rounded">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Dates ({selectedDates.length} selected)
            </label>
            <div className="border border-gray-200 rounded-lg p-4">
              <CalendarPicker
                selectedDates={selectedDates}
                onChange={(dates) => setSelectedDates(dates)}
                minDate={new Date()}
              />
            </div>
            {selectedDates.length > 0 && (
              <p className="text-xs text-gray-500 mt-2">
                Selected: {selectedDates.map(d => formatDateToYMDChina(d)).join(', ')}
              </p>
            )}
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Start Time
              </label>
              <input
                type="time"
                value={startTime}
                onChange={(e) => setStartTime(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                End Time
              </label>
              <input
                type="time"
                value={endTime}
                onChange={(e) => setEndTime(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Room
            </label>
            <input
              type="text"
              value={room}
              onChange={(e) => setRoom(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
            />
          </div>

          <div className="flex gap-3 mt-6">
            <button
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              onClick={() => addSlotsMutation.mutate()}
              disabled={selectedDates.length === 0 || addSlotsMutation.isPending}
              className="flex-1 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
            >
              {addSlotsMutation.isPending ? 'Adding...' : `Add ${selectedDates.length} Date(s)`}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function CreatePlanModal({ onClose }: { onClose: () => void }) {
  const queryClient = useQueryClient();
  const [formData, setFormData] = useState({
    name: '',
    default_room: '',
  });
  const [selectedDates, setSelectedDates] = useState<Date[]>([]);

  const createMutation = useMutation({
    mutationFn: async () => {
      // First create the plan
      const planResponse = await fetchWithAuth('/api/v1/seminars/semester-plans', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: formData.name,
          default_room: formData.default_room,
          status: 'draft',
        }),
      });
      if (!planResponse.ok) {
        const errorText = await planResponse.text();
        throw new Error(`Failed to create plan: ${errorText}`);
      }
      const plan = await planResponse.json();
      
      // Then create slots for each selected date
      for (const date of selectedDates) {
        const dateStr = date.toISOString().split('T')[0];
        const slotResponse = await fetchWithAuth(`/api/v1/seminars/semester-plans/${plan.id}/slots`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            semester_plan_id: plan.id,
            date: dateStr,
            start_time: '14:00',
            end_time: '15:30',
            room: formData.default_room,
            status: 'available',
          }),
        });
        if (!slotResponse.ok) {
          const errorText = await slotResponse.text();
          throw new Error(`Failed to create slot for ${dateStr}: ${errorText}`);
        }
      }
      
      return plan;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['semester-plans'] });
      onClose();
    },
    onError: (error: Error) => {
      alert(`Error: ${error.message}`);
    },
  });

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold">Create Semester Plan</h2>
          <button onClick={onClose} className="p-1 hover:bg-gray-100 rounded">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Left Column - Basic Info */}
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Plan Name *
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                placeholder="e.g., Spring 2024 Seminar Series"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Default Room *
              </label>
              <input
                type="text"
                value={formData.default_room}
                onChange={(e) => setFormData(prev => ({ ...prev, default_room: e.target.value }))}
                placeholder="e.g., Room A-101"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
              />
            </div>

            {/* Selected Dates Preview */}
            <div className="p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700">
                  Selected Dates
                </span>
                <span className="text-lg font-bold text-primary-600">
                  {selectedDates.length}
                </span>
              </div>
              {selectedDates.length === 0 ? (
                <p className="text-sm text-gray-500">
                  Click dates in the calendar to select them
                </p>
              ) : (
                <p className="text-sm text-gray-600">
                  {selectedDates[0].toLocaleDateString('en-US', { timeZone: CHINA_TIMEZONE })} 
                  {selectedDates.length > 1 && ` - ${selectedDates[selectedDates.length - 1].toLocaleDateString('en-US', { timeZone: CHINA_TIMEZONE })}`}
                </p>
              )}
            </div>
          </div>

          {/* Right Column - Calendar */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Seminar Dates
            </label>
            <div className="border border-gray-200 rounded-lg p-4">
              <CalendarPicker
                selectedDates={selectedDates}
                onChange={setSelectedDates}
                minDate={new Date()}
              />
            </div>
          </div>
        </div>

        <div className="flex gap-3 mt-6">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            onClick={() => createMutation.mutate()}
            disabled={!formData.name || !formData.default_room || selectedDates.length === 0}
            className="flex-1 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
          >
            {createMutation.isPending ? 'Creating...' : `Create Plan (${selectedDates.length} dates)`}
          </button>
        </div>
      </div>
    </div>
  );
}

export function GeneratedLinkModal({ link, speakerName, linkType, onClose }: { link: string; speakerName: string; linkType: 'availability' | 'info' | 'status'; onClose: () => void }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(link);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const title = linkType === 'availability'
    ? 'Availability Link Generated'
    : linkType === 'info'
      ? 'Speaker Details Link Generated'
      : 'Speaker Status Link Generated';
  const description = linkType === 'availability'
    ? `Send this link to ${speakerName} so they can submit their availability:`
    : linkType === 'info'
      ? `Send this link to ${speakerName} so they can provide their talk details and travel information:`
      : `Send this link to ${speakerName} so they can check current seminar status anytime:`;
  const tip = linkType === 'availability'
    ? 'Include this link in your email to the speaker. The link is valid for 30 days and can be used multiple times if they need to update their availability.'
    : linkType === 'info'
      ? 'Include this link in your email to the speaker. The link is valid for 60 days and can be used multiple times if they need to update their information.'
      : 'Share this status link with the speaker for real-time workflow updates.';

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl p-6 w-full max-w-lg">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold">{title}</h2>
          <button onClick={onClose} className="p-1 hover:bg-gray-100 rounded">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="space-y-4">
          <p className="text-gray-600">
            {description}
          </p>
          
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
            <div className="flex items-center gap-2">
              <input
                type="text"
                value={link}
                readOnly
                className="flex-1 bg-transparent text-sm text-gray-700 outline-none"
              />
              <button
                onClick={handleCopy}
                className="flex items-center gap-1 px-3 py-1.5 bg-primary-100 text-primary-700 rounded-lg hover:bg-primary-200 transition-colors"
              >
                {copied ? (
                  <>
                    <Check className="w-4 h-4" />
                    Copied!
                  </>
                ) : (
                  <>
                    <Copy className="w-4 h-4" />
                    Copy
                  </>
                )}
              </button>
            </div>
          </div>

          <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
            <p className="text-sm text-amber-800">
              <strong>Tip:</strong> {tip}
            </p>
          </div>

          <div className="flex gap-3 mt-6">
            <button
              onClick={onClose}
              className="flex-1 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
            >
              Done
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// Email Draft Types - exported for SpeakersControlPanel
export interface EmailDraftData {
  type: 'availability_request' | 'date_confirmation' | 'info_request';
  speakerName: string;
  speakerEmail?: string;
  slotDate?: string;
  slotTime?: string;
  deadlineDate?: string;
  suggestedBy?: string;
  infoLink?: string;
  availabilityLink?: string;
  statusLink?: string;
  linkError?: string;
}

// Email Drafting Modal - exported for SpeakersControlPanel
export function EmailDraftModal({
  draft,
  onClose,
}: {
  draft: EmailDraftData;
  onClose: () => void;
}) {
  const [copiedField, setCopiedField] = useState<string | null>(null);
  const [isSending, setIsSending] = useState(false);
  const [sendStatus, setSendStatus] = useState<{type: 'success' | 'error', message: string} | null>(null);

  const handleCopy = async (text: string, field: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedField(field);
      setTimeout(() => setCopiedField(null), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const handleSendEmail = async () => {
    if (!draft.speakerEmail) {
      setSendStatus({ type: 'error', message: 'No speaker email address available' });
      return;
    }

    setIsSending(true);
    setSendStatus(null);

    try {
      const response = await fetch('/api/v1/seminars/send-email', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('seminars_token') || ''}`
        },
        body: JSON.stringify({
          to: draft.speakerEmail,
          subject: emailContent.subject,
          body: emailContent.body,
          cc: draft.suggestedBy,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to send email');
      }

      setSendStatus({ type: 'success', message: `Email sent successfully to ${draft.speakerEmail}` });
    } catch (err: any) {
      setSendStatus({ type: 'error', message: err.message || 'Failed to send email' });
    } finally {
      setIsSending(false);
    }
  };

  // Generate email content based on type
  const getEmailContent = () => {
    const semester = 'Spring/2026'; // This could be passed as a parameter
    
    switch (draft.type) {
      case 'availability_request':
        return {
          subject: `Seminar Invitation - ${draft.speakerName}`,
          body: `Dear ${draft.speakerName}${draft.suggestedBy ? ` (cc ${draft.suggestedBy})` : ''},

Greetings from the University of Macau!

This is Inácio Bó, the seminar organizer for the ${semester} term of the Department of Economics at the University of Macau.

Following a suggestion by my colleague${draft.suggestedBy ? ` ${draft.suggestedBy}` : ''}, we would like to know whether you would be interested and willing to come and give a talk.

We will be able to cover your travel and accommodation costs for your visit to us.

Our seminars take place, usually, on Wednesdays at 2:00 PM.

In order to find a date that would work for you and in our schedule, could you please fill the dates that you have available in the form below?

${draft.availabilityLink || '[AVAILABILITY_LINK]'}

Please note that, depending on the combination of constraints from all the speakers suggested, the invitation might not be able to be confirmed for the coming semester.

Please let me know if none of these dates work for you. We find an alternative. In the meantime, please also feel free to let me know if you have any other questions. I look forward to meeting you at the University of Macau soon.

Best regards,
Inácio Bó
Associate Professor
Department of Economics
University of Macau
http://www.inaciobo.com`,
        };

      case 'date_confirmation':
        return {
          subject: `Seminar Date Confirmation - ${draft.speakerName}`,
          body: `Dear ${draft.speakerName},

Thank you for letting me know the dates when you are available to come and give a talk at the Department of Economics at the University of Macau. The date below fits your requirements and our availability, and therefore this is our "save the date" e-mail so you can adjust your plans accordingly.

DATE: ${draft.slotDate || '[DATE]'}

(Please let me know ASAP if your availability changed and this date no longer works)

You can check the status of your visit preparation at any time using this link:

${draft.statusLink || '[STATUS_LINK]'}

I will soon send another e-mail asking for more details, but for the time being we are all set and looking forward to hosting you in Macau.

All the best,

Inácio Bó
Associate Professor
Department of Economics
University of Macau`,
        };

      case 'info_request':
        return {
          subject: `Seminar Details Required - ${draft.speakerName}`,
          body: `Dear ${draft.speakerName} (cc Bruna, and Tinsley),

Many thanks for agreeing to present in our seminar series. We very much look forward to welcoming you to the University of Macau.

Your seminar is scheduled for ${draft.slotDate || '[DATE]'}, from ${draft.slotTime || '14:00 to 15:15'}. Before and after the seminar, colleagues and PhD students may request individual meetings with you. These meetings are scheduled on a demand-driven basis, and the final schedule will be confirmed with you during the week preceding your visit. A complimentary dinner with colleagues is also planned for the evening.

We will cover your travel and accommodation expenses for the visit (subject to university regulations), and an honorarium of MOP 3,000 will be paid.

Please note that our reimbursement procedures may differ from those you are accustomed to. While we will do our utmost to minimize the administrative burden on your side, one point is crucial:

Please do not book any flight, train, or ferry tickets until we explicitly notify you that you may proceed.

In preparation for your visit, we require some information in order to arrange accommodation (if needed) and to promote your talk internally and publicly.

We therefore kindly ask you to complete the following form by ${draft.deadlineDate || '[DEADLINE]'}:

${draft.infoLink || '[INFO_FORM_LINK]'}

Although the form requests a substantial amount of information, all items are strictly required for our internal administrative procedures. It is very important that the form be completed carefully and in full, and that it be submitted as soon as possible, as the information feeds into a lengthy approval and booking process.

For reimbursement purposes, please retain all inbound tickets and boarding passes, which must be submitted to our administrative staff. For outbound tickets and boarding passes, clear photographs will suffice. The same applies to taxi receipts in Macau.

Should you have any questions in the meantime, please do not hesitate to contact me. I very much look forward to meeting you in Macau.

Best regards,

Inácio Bó
Associate Professor
Department of Economics
University of Macau
http://www.inaciobo.com`,
        };

      default:
        return { subject: '', body: '' };
    }
  };

  const emailContent = getEmailContent();

  const getTitle = () => {
    switch (draft.type) {
      case 'availability_request':
        return 'Draft Email: Availability Request';
      case 'date_confirmation':
        return 'Draft Email: Date Confirmation';
      case 'info_request':
        return 'Draft Email: Speaker Information Request';
      default:
        return 'Draft Email';
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl w-full max-w-3xl max-h-[90vh] overflow-hidden flex flex-col">
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold">{getTitle()}</h2>
          <button onClick={onClose} className="p-1 hover:bg-gray-100 rounded">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 overflow-y-auto space-y-4">
          {/* Subject Line */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Subject
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                value={emailContent.subject}
                readOnly
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg bg-gray-50 text-gray-700"
              />
              <button
                onClick={() => handleCopy(emailContent.subject, 'subject')}
                className="px-3 py-2 bg-primary-100 text-primary-700 rounded-lg hover:bg-primary-200 whitespace-nowrap"
              >
                {copiedField === 'subject' ? 'Copied!' : 'Copy'}
              </button>
            </div>
          </div>

          {/* Email Body */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Email Body
            </label>
            <div className="relative">
              <textarea
                value={emailContent.body}
                readOnly
                rows={20}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-50 text-gray-700 font-mono text-sm"
              />
              <button
                onClick={() => handleCopy(emailContent.body, 'body')}
                className="absolute top-2 right-2 px-3 py-1.5 bg-primary-100 text-primary-700 rounded-lg hover:bg-primary-200 text-sm"
              >
                {copiedField === 'body' ? 'Copied!' : 'Copy'}
              </button>
            </div>
          </div>

          {/* Instructions & Link Status */}
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 space-y-2">
            <p className="text-sm text-amber-800">
              <strong>Instructions:</strong> Copy the subject and body above, then paste them into your email client.
            </p>
            
            {/* Link Status */}
            {draft.type === 'info_request' && (
              <div className="flex items-center gap-2 text-sm">
                <span className="text-amber-700">Info form link:</span>
                {draft.infoLink ? (
                  <span className="flex items-center gap-1 text-green-700">
                    <Check className="w-4 h-4" />
                    Generated and included in email
                  </span>
                ) : draft.linkError ? (
                  <span className="text-red-600">Error: {draft.linkError}</span>
                ) : (
                  <span className="text-red-600">Failed to generate - please use "Link" button separately</span>
                )}
              </div>
            )}
            {draft.type === 'availability_request' && (
              <div className="flex items-center gap-2 text-sm">
                <span className="text-amber-700">Availability form link:</span>
                {draft.availabilityLink ? (
                  <span className="flex items-center gap-1 text-green-700">
                    <Check className="w-4 h-4" />
                    Generated and included in email
                  </span>
                ) : draft.linkError ? (
                  <span className="text-red-600">Error: {draft.linkError}</span>
                ) : (
                  <span className="text-red-600">Failed to generate - please use "Link" button separately</span>
                )}
              </div>
            )}
            {draft.type === 'date_confirmation' && (
              <div className="flex items-center gap-2 text-sm">
                <span className="text-amber-700">Status link:</span>
                {draft.statusLink ? (
                  <span className="flex items-center gap-1 text-green-700">
                    <Check className="w-4 h-4" />
                    Generated and included in email
                  </span>
                ) : draft.linkError ? (
                  <span className="text-red-600">Error: {draft.linkError}</span>
                ) : (
                  <span className="text-red-600">Failed to generate - please use "Status" button separately</span>
                )}
              </div>
            )}
          </div>
        </div>

        <div className="p-6 border-t border-gray-200 space-y-3">
          {/* Send Status */}
          {sendStatus && (
            <div className={`p-3 rounded-lg text-sm ${
              sendStatus.type === 'success' 
                ? 'bg-green-50 text-green-700 border border-green-200' 
                : 'bg-red-50 text-red-700 border border-red-200'
            }`}>
              {sendStatus.message}
            </div>
          )}
          
          {/* Action Buttons */}
          <div className="flex gap-3">
            <button
              onClick={handleSendEmail}
              disabled={isSending || !draft.speakerEmail}
              className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {isSending ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Sending...
                </>
              ) : (
                <>
                  <Mail className="w-4 h-4" />
                  Send Email
                </>
              )}
            </button>
            <button
              onClick={onClose}
              className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
            >
              Close
            </button>
          </div>
          
          {!draft.speakerEmail && (
            <p className="text-xs text-amber-600 text-center">
              Cannot send: No email address for this speaker
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
