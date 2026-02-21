import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  Plus, 
  Calendar, 
  Users, 
  MapPin, 
  CheckCircle,
  XCircle,
  AlertCircle,
  LayoutGrid,
  Trash2,
  Edit,
  X,
  Mail,
  Building2,
  Globe,
  FileText
} from 'lucide-react';
import { seminarsApi, fetchWithAuth } from '@/api/client';
import { formatDate, formatTime, cn } from '@/lib/utils';
import { SemesterPlanning } from './SemesterPlanning';
import { SeminarDetailsModal } from './SeminarDetailsModal';
import type { Seminar, Speaker } from '@/types';

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
  const [activeTab, setActiveTab] = useState<'upcoming' | 'speakers' | 'tasks' | 'planning'>('upcoming');
  const [speakerModalOpen, setSpeakerModalOpen] = useState(false);
  const [editingSpeaker, setEditingSpeaker] = useState<Speaker | null>(null);
  const [detailsSeminar, setDetailsSeminar] = useState<Seminar | null>(null);
  const queryClient = useQueryClient();

  const { data: seminars, isLoading: seminarsLoading } = useQuery({
    queryKey: ['seminars'],
    queryFn: seminarsApi.listSeminars,
  });

  const { data: speakers, isLoading: speakersLoading } = useQuery({
    queryKey: ['speakers'],
    queryFn: seminarsApi.listSpeakers,
  });

  const { data: bureaucracy } = useQuery({
    queryKey: ['bureaucracy'],
    queryFn: seminarsApi.checkBureaucracy,
  });

  const updateStatusMutation = useMutation({
    mutationFn: ({ id, updates }: { id: number; updates: any }) =>
      seminarsApi.updateSeminar(id, updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['seminars'] });
      queryClient.invalidateQueries({ queryKey: ['bureaucracy'] });
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
      queryClient.invalidateQueries({ queryKey: ['bureaucracy'] });
      // Invalidate all planning-board queries to refresh slot assignments
      queryClient.invalidateQueries({ queryKey: ['planning-board'] });
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
          { id: 'upcoming', label: 'Upcoming Seminars', icon: Calendar },
          { id: 'speakers', label: 'Speakers', icon: Users },
          { id: 'tasks', label: 'Pending Tasks', icon: AlertCircle },
          { id: 'planning', label: 'Semester Planning', icon: LayoutGrid },
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
              />
            ))
          )}
        </div>
      )}

      {activeTab === 'speakers' && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <p className="text-gray-600">
              {speakers?.length || 0} speaker{speakers?.length !== 1 ? 's' : ''} in database
            </p>
            <button
              onClick={handleAddSpeaker}
              className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
            >
              <Plus className="w-4 h-4" />
              Add Speaker
            </button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {speakersLoading ? (
              <div className="col-span-full text-center py-12">Loading speakers...</div>
            ) : speakers?.length === 0 ? (
              <div className="col-span-full text-center py-12 text-gray-500">
                <Users className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                <p>No speakers yet</p>
                <button
                  onClick={handleAddSpeaker}
                  className="mt-4 text-primary-600 hover:underline"
                >
                  Add your first speaker
                </button>
              </div>
            ) : (
              speakers?.map((speaker: Speaker) => {
                // Find upcoming seminar for this speaker
                const upcomingSeminar = seminars?.find((s: Seminar) => 
                  s.speaker?.id === speaker.id && 
                  new Date(s.date) >= new Date()
                );
                return (
                  <SpeakerCard 
                    key={speaker.id} 
                    speaker={speaker} 
                    upcomingSeminar={upcomingSeminar}
                    onEdit={() => handleEditSpeaker(speaker)}
                    onDelete={() => {
                      if (confirm(`Delete speaker "${speaker.name}"?`)) {
                        deleteSpeakerMutation.mutate(speaker.id);
                      }
                    }}
                  />
                );
              })
            )}
          </div>
        </div>
      )}

      {activeTab === 'tasks' && (
        <div className="space-y-4">
          {bureaucracy?.data?.pending_tasks?.length === 0 ? (
            <div className="text-center py-12 text-green-600">
              <CheckCircle className="w-12 h-12 mx-auto mb-4" />
              <p className="font-medium">All tasks completed!</p>
              <p className="text-sm text-gray-500 mt-1">No pending bureaucracy tasks</p>
            </div>
          ) : (
            bureaucracy?.data?.pending_tasks?.map((task: any) => (
              <div 
                key={task.seminar_id}
                className="p-4 bg-white border border-amber-200 rounded-lg shadow-sm"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="font-semibold text-gray-900">{task.title}</h3>
                    <p className="text-sm text-gray-600">
                      {formatDate(task.date)} • {task.days_until} days away
                    </p>
                  </div>
                  <span className="px-3 py-1 text-sm font-medium bg-amber-100 text-amber-800 rounded-full">
                    {task.tasks.length} pending
                  </span>
                </div>
                <ul className="mt-3 space-y-2">
                  {task.tasks.map((t: string, i: number) => (
                    <li key={i} className="flex items-center gap-2 text-sm text-gray-700">
                      <AlertCircle className="w-4 h-4 text-amber-500" />
                      {t}
                    </li>
                  ))}
                </ul>
              </div>
            ))
          )}
        </div>
      )}

      {activeTab === 'planning' && <SemesterPlanning />}

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
    </div>
  );
}

function SeminarCard({ 
  seminar, 
  onUpdateStatus,
  onDelete,
  onViewDetails
}: { 
  seminar: Seminar; 
  onUpdateStatus: (updates: any) => void;
  onDelete?: () => void;
  onViewDetails?: () => void;
}) {
  return (
    <div className="p-6 bg-white border border-gray-200 rounded-xl shadow-sm hover:shadow-md transition-shadow group relative">
      {/* Action buttons */}
      <div className="absolute top-4 right-4 flex gap-1 opacity-0 group-hover:opacity-100 transition-all z-10">
        {onViewDetails && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onViewDetails();
            }}
            className="p-1.5 text-blue-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg"
            title="View details"
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
