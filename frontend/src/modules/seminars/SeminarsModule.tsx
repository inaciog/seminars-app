import { useState, useEffect, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  Plus, 
  Calendar, 
  Users, 
  MapPin, 
  CheckCircle,
  XCircle,
  LayoutGrid,
  Trash2,
  Edit,
  X,
  Mail,
  Building2,
  Globe,
  FileText,
  MoreHorizontal,
  ExternalLink,
  Clock3,
  UserPlus,
  Link as LinkIcon,
  FileUp,
  FileDown,
  Send,
  ClipboardList,
  Database
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { seminarsApi, fetchWithAuth } from '@/api/client';
import { formatDate, formatTime, cn } from '@/lib/utils';
import { SemesterPlanning } from './SemesterPlanning';
import { SpeakersControlPanel } from './SpeakersControlPanel';
import { SeminarDetailsModal } from './SeminarDetailsModal';
import { SeminarViewPage } from './SeminarViewPage';
import { DatabaseAdmin } from './DatabaseAdmin';
import type { Seminar, Speaker } from '@/types';

// Helper to open seminar details from any component
export function openSeminarDetails(seminar: Seminar) {
  window.dispatchEvent(new CustomEvent('open-seminar-details', { detail: seminar }));
}

// Activity event type -> friendly label and icon
const ACTIVITY_EVENT_CONFIG: Record<string, { label: string; icon: React.ComponentType<{ className?: string }>; color: string }> = {
  SEMESTER_PLAN_CREATED: { label: 'Plan created', icon: LayoutGrid, color: 'text-blue-600 bg-blue-50' },
  SEMESTER_PLAN_UPDATED: { label: 'Plan updated', icon: LayoutGrid, color: 'text-blue-600 bg-blue-50' },
  SLOT_CREATED: { label: 'Date added', icon: Calendar, color: 'text-emerald-600 bg-emerald-50' },
  SLOT_UNASSIGNED: { label: 'Slot freed', icon: Calendar, color: 'text-amber-600 bg-amber-50' },
  SPEAKER_SUGGESTED: { label: 'Speaker suggested', icon: UserPlus, color: 'text-indigo-600 bg-indigo-50' },
  AVAILABILITY_LINK_CREATED: { label: 'Availability link sent', icon: LinkIcon, color: 'text-purple-600 bg-purple-50' },
  INFO_LINK_CREATED: { label: 'Info link created', icon: LinkIcon, color: 'text-purple-600 bg-purple-50' },
  AVAILABILITY_SUBMITTED: { label: 'Availability received', icon: CheckCircle, color: 'text-green-600 bg-green-50' },
  SPEAKER_INFO_SUBMITTED: { label: 'Speaker info submitted', icon: FileText, color: 'text-green-600 bg-green-50' },
  SPEAKER_ASSIGNED: { label: 'Speaker assigned', icon: Users, color: 'text-teal-600 bg-teal-50' },
  SEMINAR_ASSIGNED: { label: 'Seminar scheduled', icon: Calendar, color: 'text-teal-600 bg-teal-50' },
  FILE_UPLOADED: { label: 'File uploaded', icon: FileUp, color: 'text-slate-600 bg-slate-50' },
  FILE_DELETED: { label: 'File removed', icon: FileDown, color: 'text-slate-600 bg-slate-50' },
  WORKFLOW_UPDATED: { label: 'Workflow updated', icon: ClipboardList, color: 'text-amber-600 bg-amber-50' },
  STATUS_TOKEN_CREATED: { label: 'Status link created', icon: LinkIcon, color: 'text-purple-600 bg-purple-50' },
  FACULTY_FORM_LINK_ACCESSED: { label: 'Faculty form shared', icon: Send, color: 'text-indigo-600 bg-indigo-50' },
  FACULTY_SUGGESTION_SUBMITTED: { label: 'Faculty suggestion received', icon: UserPlus, color: 'text-indigo-600 bg-indigo-50' },
};

function getActivityConfig(eventType: string) {
  return ACTIVITY_EVENT_CONFIG[eventType] ?? {
    label: eventType.replace(/_/g, ' ').toLowerCase(),
    icon: Clock3,
    color: 'text-gray-600 bg-gray-50',
  };
}

// Speaker Modal Component
interface SpeakerModalProps {
  speaker?: Speaker | null;
  onClose: () => void;
  onSave: (data: Partial<Speaker>) => void;
  isLoading?: boolean;
}

function SpeakerModal({ speaker, onClose, onSave, isLoading }: SpeakerModalProps) {
  const isEditing = !!speaker;
  const [formData, setFormData] = useState({
    name: speaker?.name || '',
    email: speaker?.email || '',
    affiliation: speaker?.affiliation || '',
    website: speaker?.website || '',
    bio: speaker?.bio || '',
    notes: speaker?.notes || '',
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave(formData);
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl p-6 w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold">
            {isEditing ? 'Edit Speaker' : 'Add New Speaker'}
          </h2>
          <button onClick={onClose} className="p-1 hover:bg-gray-100 rounded">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Name *
            </label>
            <input
              type="text"
              required
              value={formData.name}
              onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
              placeholder="e.g., Prof. Jane Smith"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1 flex items-center gap-1">
                <Mail className="w-3 h-3" />
                Email
              </label>
              <input
                type="email"
                value={formData.email}
                onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
                placeholder="speaker@university.edu"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1 flex items-center gap-1">
                <Building2 className="w-3 h-3" />
                Affiliation
              </label>
              <input
                type="text"
                value={formData.affiliation}
                onChange={(e) => setFormData(prev => ({ ...prev, affiliation: e.target.value }))}
                placeholder="e.g., MIT"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1 flex items-center gap-1">
              <Globe className="w-3 h-3" />
              Website
            </label>
            <input
              type="url"
              value={formData.website}
              onChange={(e) => setFormData(prev => ({ ...prev, website: e.target.value }))}
              placeholder="https://..."
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1 flex items-center gap-1">
              <FileText className="w-3 h-3" />
              Bio
            </label>
            <textarea
              value={formData.bio}
              onChange={(e) => setFormData(prev => ({ ...prev, bio: e.target.value }))}
              placeholder="Brief biography..."
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Notes
            </label>
            <textarea
              value={formData.notes}
              onChange={(e) => setFormData(prev => ({ ...prev, notes: e.target.value }))}
              placeholder="Internal notes..."
              rows={2}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
            />
          </div>

          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading || !formData.name.trim()}
              className="flex-1 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
            >
              {isLoading ? 'Saving...' : (isEditing ? 'Save Changes' : 'Add Speaker')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export function SeminarsModule() {
  const [activeTab, setActiveTab] = useState<'activity' | 'upcoming' | 'speakers' | 'planning' | 'other'>('activity');
  const [speakerModalOpen, setSpeakerModalOpen] = useState(false);
  const [editingSpeaker, setEditingSpeaker] = useState<Speaker | null>(null);
  const [detailsSeminar, setDetailsSeminar] = useState<Seminar | null>(null);
  const [viewPageSeminar, setViewPageSeminar] = useState<Seminar | null>(null);
  const queryClient = useQueryClient();

  // Listen for custom event to open seminar details from child components
  useEffect(() => {
    const handleOpenSeminarDetails = (event: Event) => {
      const customEvent = event as CustomEvent<Seminar>;
      if (customEvent.detail) {
        setDetailsSeminar(customEvent.detail);
      }
    };
    
    window.addEventListener('open-seminar-details', handleOpenSeminarDetails);
    return () => {
      window.removeEventListener('open-seminar-details', handleOpenSeminarDetails);
    };
  }, []);

  const { data: seminarsRaw, isLoading: seminarsLoading } = useQuery({
    queryKey: ['seminars'],
    queryFn: () => seminarsApi.listSeminars({ upcoming: true }),
  });

  // Filter seminars to include today onwards (API may return only future dates)
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const seminars = useMemo(() => {
    if (!seminarsRaw) return [];
    return seminarsRaw.filter((s: Seminar) => new Date(s.date) >= today);
  }, [seminarsRaw]);

  const { data: speakers, isLoading: speakersLoading } = useQuery({
    queryKey: ['speakers'],
    queryFn: seminarsApi.listSpeakers,
  });

  const { data: activities = [], isLoading: activitiesLoading } = useQuery({
    queryKey: ['recent-activity'],
    queryFn: async () => {
      const response = await fetchWithAuth('/api/v1/seminars/activity?limit=100');
      if (!response.ok) throw new Error('Failed to fetch activity');
      return response.json();
    },
  });

  const updateStatusMutation = useMutation({
    mutationFn: ({ id, updates }: { id: number; updates: any }) =>
      seminarsApi.updateSeminar(id, updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['seminars'] });
    },
  });

  const deleteSpeakerMutation = useMutation({
    mutationFn: (id: number) => fetchWithAuth(`/api/v1/seminars/speakers/${id}`, { method: 'DELETE' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['speakers'] });
    },
    onError: (error: any) => {
      alert(`Failed to delete speaker: ${error.message}`);
    },
  });

  const deleteSeminarMutation = useMutation({
    mutationFn: (id: number) => fetchWithAuth(`/api/v1/seminars/seminars/${id}`, { method: 'DELETE' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['seminars'] });
      queryClient.invalidateQueries({ queryKey: ['planning-board'] });
      queryClient.invalidateQueries({ queryKey: ['orphan-seminars'] });
    },
    onError: (error: any) => {
      alert(`Failed to delete seminar: ${error.message}`);
    },
  });

  const saveSpeakerMutation = useMutation({
    mutationFn: async ({ speaker, data }: { speaker?: Speaker | null; data: Partial<Speaker> }) => {
      if (speaker) {
        // Update existing
        const response = await fetchWithAuth(`/api/v1/seminars/speakers/${speaker.id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data),
        });
        if (!response.ok) throw new Error('Failed to update speaker');
        return response.json();
      } else {
        // Create new
        const response = await fetchWithAuth('/api/v1/seminars/speakers', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data),
        });
        if (!response.ok) throw new Error('Failed to create speaker');
        return response.json();
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['speakers'] });
      setSpeakerModalOpen(false);
      setEditingSpeaker(null);
    },
  });

  const handleAddSpeaker = () => {
    setEditingSpeaker(null);
    setSpeakerModalOpen(true);
  };

  const handleEditSpeaker = (speaker: Speaker) => {
    setEditingSpeaker(speaker);
    setSpeakerModalOpen(true);
  };

  const handleSaveSpeaker = (data: Partial<Speaker>) => {
    saveSpeakerMutation.mutate({ speaker: editingSpeaker, data });
  };

  return (
    <div className="p-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Seminars</h1>
        <p className="text-gray-600 mt-2">Manage your seminar series and speakers</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6 border-b border-gray-200">
        {[
          { id: 'activity', label: 'Recent Activity', icon: Clock3 },
          { id: 'upcoming', label: 'Upcoming Seminars', icon: Calendar },
          { id: 'speakers', label: 'Speakers', icon: Users },
          { id: 'planning', label: 'Semester Planning', icon: LayoutGrid },
          { id: 'admin', label: 'Database', icon: Database },
          { id: 'other', label: 'Other', icon: MoreHorizontal },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={cn(
              'flex items-center gap-2 px-4 py-3 border-b-2 transition-colors',
              activeTab === tab.id
                ? 'border-primary-600 text-primary-600'
                : 'border-transparent text-gray-600 hover:text-gray-900'
            )}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content */}
      {activeTab === 'activity' && (
        <div className="space-y-3">
          {activitiesLoading ? (
            <div className="text-center py-12 text-gray-500">Loading activity...</div>
          ) : activities.length === 0 ? (
            <div className="text-center py-16 px-6 bg-gray-50 rounded-xl border border-gray-100">
              <Clock3 className="w-14 h-14 mx-auto mb-4 text-gray-300" />
              <p className="text-lg font-medium text-gray-600">No recent activity yet</p>
              <p className="text-sm text-gray-500 mt-1">Actions you take will appear here</p>
            </div>
          ) : (
            activities.map((evt: any) => {
              const config = getActivityConfig(evt.event_type);
              const Icon = config.icon;
              const createdAt = new Date(evt.created_at);
              return (
                <div
                  key={evt.id}
                  className="p-4 bg-white border border-gray-200 rounded-xl shadow-sm hover:shadow-md transition-shadow"
                >
                  <div className="flex gap-4">
                    <div className={cn('flex-shrink-0 w-10 h-10 rounded-lg flex items-center justify-center', config.color)}>
                      <Icon className="w-5 h-5" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-gray-900">{evt.summary}</p>
                      <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mt-1.5 text-sm text-gray-500">
                        <span className="flex items-center gap-1">
                          <span className={cn('px-1.5 py-0.5 rounded text-xs font-medium', config.color)}>
                            {config.label}
                          </span>
                        </span>
                        {evt.semester_plan_id && (
                          <span>Plan {evt.semester_plan_id}</span>
                        )}
                        <span title={createdAt.toLocaleString()}>
                          {formatDistanceToNow(createdAt, { addSuffix: true })}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>
      )}

      {activeTab === 'upcoming' && (
        <div className="space-y-4">
          {seminarsLoading ? (
            <div className="text-center py-12">Loading seminars...</div>
          ) : seminars?.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <Calendar className="w-12 h-12 mx-auto mb-4 text-gray-300" />
              <p>No upcoming seminars</p>
              <button
                onClick={() => {}}
                className="mt-4 text-primary-600 hover:underline"
              >
                Add your first seminar
              </button>
            </div>
          ) : (
            seminars?.map((seminar: Seminar) => (
              <SeminarCard 
                key={seminar.id} 
                seminar={seminar}
                onUpdateStatus={(updates) => 
                  updateStatusMutation.mutate({ id: seminar.id, updates })
                }
                onDelete={() => {
                  if (confirm(`Delete seminar "${seminar.title}"?`)) {
                    deleteSeminarMutation.mutate(seminar.id);
                  }
                }}
                onViewDetails={() => setDetailsSeminar(seminar)}
                onViewFullPage={() => setViewPageSeminar(seminar)}
              />
            ))
          )}
        </div>
      )}

      {activeTab === 'speakers' && (
        <div>
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold text-gray-900">Speaker Control Panel</h2>
            <button
              onClick={handleAddSpeaker}
              className="flex items-center gap-2 px-4 py-2 text-sm text-gray-600 hover:text-gray-900 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <Plus className="w-4 h-4" />
              Add to contacts
            </button>
          </div>
          <SpeakersControlPanel />
        </div>
      )}

      {activeTab === 'planning' && <SemesterPlanning />}

      {activeTab === 'admin' && <DatabaseAdmin />}

      {activeTab === 'other' && (
        <OtherTab
          onViewDetails={setDetailsSeminar}
          deleteSeminarMutation={deleteSeminarMutation}
          queryClient={queryClient}
        />
      )}

      {/* Speaker Modal */}
      {speakerModalOpen && (
        <SpeakerModal
          speaker={editingSpeaker}
          onClose={() => {
            setSpeakerModalOpen(false);
            setEditingSpeaker(null);
          }}
          onSave={handleSaveSpeaker}
          isLoading={saveSpeakerMutation.isPending}
        />
      )}

      {/* Seminar Details Modal */}
      {detailsSeminar && (
        <SeminarDetailsModal
          seminarId={detailsSeminar.id}
          speakerName={detailsSeminar.speaker?.name || 'TBD'}
          onClose={() => setDetailsSeminar(null)}
        />
      )}

      {/* Seminar View Page (full info + files) */}
      {viewPageSeminar && (
        <SeminarViewPage
          seminarId={viewPageSeminar.id}
          seminarTitle={viewPageSeminar.title}
          onClose={() => setViewPageSeminar(null)}
        />
      )}
    </div>
  );
}

// Other tab - orphan seminars and future misc items
function OtherTab({ 
  onViewDetails, 
  deleteSeminarMutation, 
  queryClient 
}: { 
  onViewDetails: (s: Seminar) => void; 
  deleteSeminarMutation: { mutate: (id: number) => void };
  queryClient: ReturnType<typeof useQueryClient>;
}) {
  const [assigningOrphan, setAssigningOrphan] = useState<Seminar | null>(null);
  
  const { data: orphans = [], isLoading } = useQuery({
    queryKey: ['orphan-seminars'],
    queryFn: seminarsApi.listOrphanSeminars,
  });

  const assignMutation = useMutation({
    mutationFn: ({ seminarId, slotId }: { seminarId: number; slotId: number }) =>
      seminarsApi.assignSeminarToSlot(seminarId, slotId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['orphan-seminars'] });
      queryClient.invalidateQueries({ queryKey: ['seminars'] });
      queryClient.invalidateQueries({ queryKey: ['planning-board'] });
      queryClient.invalidateQueries({ queryKey: ['bureaucracy'] });
      setAssigningOrphan(null);
    },
    onError: (err: Error) => alert(err.message),
  });

  return (
    <div className="space-y-8">
      {/* Orphaned Seminars */}
      <section>
        <h2 className="text-lg font-semibold text-gray-900 mb-3">Orphaned Seminars</h2>
        <p className="text-sm text-gray-600 mb-4">
          Seminars not assigned to any slot. You can reassign them to a slot or delete them.
        </p>
        {isLoading ? (
          <div className="text-center py-8 text-gray-500">Loading...</div>
        ) : orphans.length === 0 ? (
          <div className="p-6 bg-gray-50 rounded-xl text-center text-gray-500">
            <p>No orphaned seminars</p>
          </div>
        ) : (
          <div className="space-y-3">
            {orphans.map((seminar: Seminar) => (
              <div
                key={seminar.id}
                className="p-4 bg-white border border-gray-200 rounded-lg flex items-center justify-between hover:shadow-sm transition-shadow group"
              >
                <div 
                  className="flex-1 cursor-pointer min-w-0"
                  onClick={() => onViewDetails(seminar)}
                >
                  <h3 className="font-medium text-gray-900 truncate">{seminar.title}</h3>
                  <p className="text-sm text-gray-600 mt-0.5">
                    {seminar.speaker?.name || 'Unknown'} • {formatDate(seminar.date)} {seminar.start_time && `• ${formatTime(seminar.start_time)}`}
                  </p>
                </div>
                <div className="flex gap-2 ml-4 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button
                    onClick={() => setAssigningOrphan(seminar)}
                    className="px-3 py-1.5 text-sm font-medium text-primary-600 hover:bg-primary-50 rounded-lg"
                  >
                    Assign to slot
                  </button>
                  <button
                    onClick={() => {
                      if (confirm(`Delete "${seminar.title}"?`)) {
                        deleteSeminarMutation.mutate(seminar.id);
                      }
                    }}
                    className="px-3 py-1.5 text-sm font-medium text-red-600 hover:bg-red-50 rounded-lg"
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {assigningOrphan && (
        <AssignToSlotModal
          seminar={assigningOrphan}
          onClose={() => setAssigningOrphan(null)}
          onAssign={(slotId) => assignMutation.mutate({ seminarId: assigningOrphan.id, slotId })}
          isAssigning={assignMutation.isPending}
        />
      )}
    </div>
  );
}

function AssignToSlotModal({ 
  seminar, 
  onClose, 
  onAssign, 
  isAssigning 
}: { 
  seminar: Seminar; 
  onClose: () => void; 
  onAssign: (slotId: number) => void;
  isAssigning: boolean;
}) {
  const [selectedPlanId, setSelectedPlanId] = useState<number | null>(null);
  
  const { data: plans = [] } = useQuery({
    queryKey: ['semester-plans'],
    queryFn: async () => {
      const r = await fetchWithAuth('/api/v1/seminars/semester-plans');
      if (!r.ok) throw new Error('Failed to fetch plans');
      return r.json();
    },
  });

  const { data: boardData } = useQuery({
    queryKey: ['planning-board', selectedPlanId],
    queryFn: async () => {
      if (!selectedPlanId) return null;
      const r = await fetchWithAuth(`/api/v1/seminars/semester-plans/${selectedPlanId}/planning-board`);
      if (!r.ok) throw new Error('Failed to fetch board');
      return r.json();
    },
    enabled: !!selectedPlanId,
  });

  const availableSlots = (boardData?.slots || []).filter(
    (s: { assigned_seminar_id?: number }) => !s.assigned_seminar_id
  );

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl p-6 w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h2 className="text-xl font-semibold">Assign to Slot</h2>
            <p className="text-sm text-gray-600 mt-1">{seminar.title}</p>
          </div>
          <button onClick={onClose} className="p-1 hover:bg-gray-100 rounded">
            <X className="w-5 h-5" />
          </button>
        </div>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Select plan</label>
            <select
              value={selectedPlanId ?? ''}
              onChange={(e) => setSelectedPlanId(e.target.value ? Number(e.target.value) : null)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
            >
              <option value="">Choose a plan...</option>
              {plans.map((p: { id: number; name: string }) => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          </div>
          {selectedPlanId && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Available slots</label>
              {availableSlots.length === 0 ? (
                <p className="text-sm text-gray-500">No available slots in this plan</p>
              ) : (
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {availableSlots.map((slot: { id: number; date: string; start_time: string; end_time: string; room: string }) => (
                    <button
                      key={slot.id}
                      onClick={() => onAssign(slot.id)}
                      disabled={isAssigning}
                      className="w-full text-left px-4 py-2 border border-gray-200 rounded-lg hover:bg-primary-50 hover:border-primary-200 flex items-center gap-2"
                    >
                      <Calendar className="w-4 h-4 text-gray-500" />
                      <span>{formatDate(slot.date)}</span>
                      <span className="text-gray-500">•</span>
                      <span>{slot.start_time}–{slot.end_time}</span>
                      <span className="text-gray-500">•</span>
                      <span>{slot.room}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function SeminarCard({ 
  seminar, 
  onUpdateStatus,
  onDelete,
  onViewDetails,
  onViewFullPage
}: { 
  seminar: Seminar; 
  onUpdateStatus: (updates: any) => void;
  onDelete?: () => void;
  onViewDetails?: () => void;
  onViewFullPage?: () => void;
}) {
  return (
    <div className="p-6 bg-white border border-gray-200 rounded-xl shadow-sm hover:shadow-md transition-shadow group relative">
      {/* Action buttons */}
      <div className="absolute top-4 right-4 flex gap-1 opacity-0 group-hover:opacity-100 transition-all z-10">
        {onViewFullPage && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onViewFullPage();
            }}
            className="p-1.5 text-green-600 hover:text-green-700 hover:bg-green-50 rounded-lg"
            title="View full info & files"
          >
            <ExternalLink className="w-4 h-4" />
          </button>
        )}
        {onViewDetails && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onViewDetails();
            }}
            className="p-1.5 text-blue-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg"
            title="Edit details"
          >
            <FileText className="w-4 h-4" />
          </button>
        )}
        {onDelete && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onDelete();
            }}
            className="p-1.5 text-red-400 hover:text-red-600 hover:bg-red-50 rounded-lg"
            title="Delete seminar"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        )}
      </div>
      
      {/* Main content */}
      <div 
        className={cn(
          'flex items-start justify-between pr-16',
          onViewDetails && 'cursor-pointer'
        )}
        onClick={onViewDetails}
      >
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900">{seminar.title}</h3>
          
          {seminar.speaker && (
            <p className="text-sm text-gray-600 mt-1">
              <Users className="w-4 h-4 inline mr-1" />
              {seminar.speaker.name} • {seminar.speaker.affiliation}
            </p>
          )}
          
          <div className="flex items-center gap-4 mt-3 text-sm text-gray-500">
            <span className="flex items-center gap-1">
              <Calendar className="w-4 h-4" />
              {formatDate(seminar.date)}
            </span>
            <span>{formatTime(seminar.start_time)} - {formatTime(seminar.end_time)}</span>
            <span className="flex items-center gap-1">
              <MapPin className="w-4 h-4" />
              {seminar.room}
            </span>
          </div>
        </div>
        
        <span className={cn(
          'px-3 py-1 text-xs font-medium rounded-full',
          seminar.status === 'confirmed' ? 'bg-green-100 text-green-800' :
          seminar.status === 'cancelled' ? 'bg-red-100 text-red-800' :
          'bg-amber-100 text-amber-800'
        )}>
          {seminar.status}
        </span>
      </div>

      {/* Checklist */}
      <div className="mt-4 pt-4 border-t border-gray-100">
        <div className="flex flex-wrap gap-2">
          <StatusBadge 
            checked={seminar.room_booked} 
            label="Room Booked"
            onClick={() => onUpdateStatus({ room_booked: !seminar.room_booked })}
          />
          <StatusBadge 
            checked={seminar.announcement_sent} 
            label="Announcement"
            onClick={() => onUpdateStatus({ announcement_sent: !seminar.announcement_sent })}
          />
          <StatusBadge 
            checked={seminar.calendar_invite_sent} 
            label="Calendar Invite"
            onClick={() => onUpdateStatus({ calendar_invite_sent: !seminar.calendar_invite_sent })}
          />
          <StatusBadge 
            checked={seminar.catering_ordered} 
            label="Catering"
            onClick={() => onUpdateStatus({ catering_ordered: !seminar.catering_ordered })}
          />
        </div>
      </div>
    </div>
  );
}

function StatusBadge({ 
  checked, 
  label,
  onClick 
}: { 
  checked: boolean; 
  label: string;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        'flex items-center gap-1 px-3 py-1.5 text-sm rounded-lg transition-colors',
        checked 
          ? 'bg-green-100 text-green-700 hover:bg-green-200' 
          : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
      )}
    >
      {checked ? (
        <CheckCircle className="w-4 h-4" />
      ) : (
        <XCircle className="w-4 h-4" />
      )}
      {label}
    </button>
  );
}

function SpeakerCard({ speaker, upcomingSeminar, onEdit, onDelete }: { speaker: Speaker; upcomingSeminar?: Seminar; onEdit?: () => void; onDelete?: () => void }) {
  return (
    <div className="p-4 bg-white border border-gray-200 rounded-lg shadow-sm group relative hover:shadow-md transition-shadow">
      {/* Action buttons */}
      <div className="absolute top-2 right-2 flex gap-1 opacity-0 group-hover:opacity-100 transition-all">
        {onEdit && (
          <button
            onClick={onEdit}
            className="p-1.5 text-blue-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg"
            title="Edit speaker"
          >
            <Edit className="w-4 h-4" />
          </button>
        )}
        {onDelete && (
          <button
            onClick={onDelete}
            className="p-1.5 text-red-400 hover:text-red-600 hover:bg-red-50 rounded-lg"
            title="Delete speaker"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        )}
      </div>
      
      <h3 className="font-semibold text-gray-900 pr-16">{speaker.name}</h3>
      <p className="text-sm text-primary-600">{speaker.affiliation}</p>
      <p className="text-sm text-gray-500 mt-2">{speaker.email}</p>
      
      {upcomingSeminar && (
        <div className="mt-3 p-2 bg-green-50 rounded-lg border border-green-100">
          <p className="text-xs text-green-700 font-medium">Upcoming Seminar</p>
          <p className="text-sm text-green-900 font-medium truncate">{upcomingSeminar.title}</p>
          <p className="text-xs text-green-700">
            <Calendar className="w-3 h-3 inline mr-1" />
            {formatDate(upcomingSeminar.date)} • {formatTime(upcomingSeminar.start_time)}
          </p>
        </div>
      )}
      
      {speaker.bio && (
        <p className="text-sm text-gray-600 mt-3 line-clamp-2">{speaker.bio}</p>
      )}
      
      {speaker.website && (
        <a 
          href={speaker.website}
          target="_blank"
          rel="noopener noreferrer"
          className="text-sm text-primary-600 hover:underline mt-2 block"
        >
          Website
        </a>
      )}
    </div>
  );
}
