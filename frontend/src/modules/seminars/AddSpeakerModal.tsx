import { useState, useMemo } from 'react';
import { fetchWithAuth } from '@/api/client';
import { useMutation, useQueryClient, useQuery } from '@tanstack/react-query';
import { X, Calendar, User, Mail, Building2, Lightbulb, Flag, Search, Plus, ChevronLeft } from 'lucide-react';
import { cn, CHINA_TIMEZONE } from '@/lib/utils';
import { CalendarPicker } from '@/components/CalendarPicker';

interface Speaker {
  id: number;
  name: string;
  email?: string;
  affiliation?: string;
  website?: string;
  bio?: string;
}

interface AddSpeakerModalProps {
  planId: number;
  onClose: () => void;
}

export function AddSpeakerModal({ planId, onClose }: AddSpeakerModalProps) {
  const queryClient = useQueryClient();
  const [step, setStep] = useState<'select' | 'info' | 'availability'>('select');
  const [selectedSpeakerId, setSelectedSpeakerId] = useState<number | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  
  // For new speaker
  const [isNewSpeaker, setIsNewSpeaker] = useState(false);
  const [formData, setFormData] = useState({
    speaker_name: '',
    speaker_email: '',
    speaker_affiliation: '',
    suggested_by: '',
    suggested_topic: '',
    priority: 'medium' as 'low' | 'medium' | 'high',
  });
  
  // Availability - now supports date ranges
  const [dateRanges, setDateRanges] = useState<{start: Date; end: Date}[]>([]);
  const [earliestTime, setEarliestTime] = useState('');
  const [latestTime, setLatestTime] = useState('');
  const [notes, setNotes] = useState('');

  // Fetch existing speakers
  const { data: speakers = [], isLoading: speakersLoading } = useQuery({
    queryKey: ['speakers'],
    queryFn: async () => {
      const response = await fetchWithAuth('/api/v1/seminars/speakers');
      if (!response.ok) throw new Error('Failed to fetch speakers');
      return response.json();
    },
  });

  const filteredSpeakers = useMemo(() => {
    if (!searchTerm) return speakers;
    const term = searchTerm.toLowerCase();
    return speakers.filter((s: Speaker) => 
      s.name.toLowerCase().includes(term) ||
      s.affiliation?.toLowerCase().includes(term) ||
      s.email?.toLowerCase().includes(term)
    );
  }, [speakers, searchTerm]);

  const createSpeakerMutation = useMutation({
    mutationFn: async (data: { name: string; email: string; affiliation: string }) => {
      const response = await fetchWithAuth('/api/v1/seminars/speakers', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      if (!response.ok) throw new Error('Failed to create speaker');
      return response.json();
    },
  });

  const createSuggestionMutation = useMutation({
    mutationFn: async () => {
      let speakerId = selectedSpeakerId;
      
      // Create new speaker if needed
      if (isNewSpeaker) {
        const newSpeaker = await createSpeakerMutation.mutateAsync({
          name: formData.speaker_name,
          email: formData.speaker_email,
          affiliation: formData.speaker_affiliation,
        });
        speakerId = newSpeaker.id;
      }

      const speaker = speakers.find((s: Speaker) => s.id === speakerId);
      
      // Create the suggestion
      const response = await fetchWithAuth('/api/v1/seminars/speaker-suggestions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          speaker_id: speakerId,
          speaker_name: speaker?.name || formData.speaker_name,
          speaker_email: speaker?.email || formData.speaker_email,
          speaker_affiliation: speaker?.affiliation || formData.speaker_affiliation,
          suggested_by: formData.suggested_by,
          suggested_topic: formData.suggested_topic,
          priority: formData.priority,
          semester_plan_id: planId,
          status: 'pending',
        }),
      });
      if (!response.ok) throw new Error('Failed to create suggestion');
      const suggestion = await response.json();
      
      // Add availability if date ranges are selected
      if (dateRanges.length > 0) {
        // Backend expects one availability item per date ({ date, preference }).
        const availabilities = dateRanges.flatMap((range) => {
          const dates: { date: string; preference: string }[] = [];
          const current = new Date(range.start);
          while (current <= range.end) {
            dates.push({
              date: current.toISOString().split('T')[0],
              preference: 'available',
            });
            current.setDate(current.getDate() + 1);
          }
          return dates;
        });
        
        await fetchWithAuth(`/api/v1/seminars/speaker-suggestions/${suggestion.id}/availability`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(availabilities),
        });
      }
      
      return suggestion;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['planning-board', planId] });
      queryClient.invalidateQueries({ queryKey: ['speakers'] });
      onClose();
    },
    onError: (error: Error) => {
      alert(`Error: ${error.message}`);
    },
  });

  const handleDateSelect = (dates: Date[]) => {
    if (dates.length === 0) return;
    
    // Sort dates
    const sorted = [...dates].sort((a, b) => a.getTime() - b.getTime());
    
    // Group consecutive dates into ranges
    const ranges: {start: Date; end: Date}[] = [];
    let rangeStart = sorted[0];
    let rangeEnd = sorted[0];
    
    for (let i = 1; i < sorted.length; i++) {
      const current = sorted[i];
      const prev = sorted[i - 1];
      const diffDays = (current.getTime() - prev.getTime()) / (1000 * 60 * 60 * 24);
      
      if (diffDays === 1) {
        // Consecutive, extend range
        rangeEnd = current;
      } else {
        // Gap, save current range and start new
        ranges.push({ start: rangeStart, end: rangeEnd });
        rangeStart = current;
        rangeEnd = current;
      }
    }
    ranges.push({ start: rangeStart, end: rangeEnd });
    
    setDateRanges(ranges);
  };

  // Flatten ranges for calendar display
  const selectedDates = useMemo(() => {
    const dates: Date[] = [];
    for (const range of dateRanges) {
      const current = new Date(range.start);
      while (current <= range.end) {
        dates.push(new Date(current));
        current.setDate(current.getDate() + 1);
      }
    }
    return dates;
  }, [dateRanges]);

  const formatDateRange = (start: Date, end: Date) => {
    const sameMonth = start.getMonth() === end.getMonth() && start.getFullYear() === end.getFullYear();
    const startStr = start.toLocaleDateString('en-US', { month: 'short', day: 'numeric', timeZone: CHINA_TIMEZONE });
    const endStr = end.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric', timeZone: CHINA_TIMEZONE });
    if (start.getTime() === end.getTime()) {
      return startStr + ', ' + start.getFullYear();
    }
    return sameMonth 
      ? `${startStr}-${end.getDate()}, ${end.getFullYear()}`
      : `${startStr} - ${endStr}`;
  };

  const priorityColors = {
    low: 'bg-gray-100 text-gray-700 border-gray-300',
    medium: 'bg-blue-100 text-blue-700 border-blue-300',
    high: 'bg-red-100 text-red-700 border-red-300',
  };

  // Step 1: Select Speaker
  if (step === 'select') {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div className="bg-white rounded-xl p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold">Select Speaker</h2>
            <button onClick={onClose} className="p-1 hover:bg-gray-100 rounded">
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Search */}
          <div className="relative mb-4">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search speakers..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
            />
          </div>

          {/* New Speaker Button */}
          <button
            onClick={() => {
              setIsNewSpeaker(true);
              setStep('info');
            }}
            className="w-full p-4 mb-4 border-2 border-dashed border-primary-300 rounded-lg text-primary-600 hover:bg-primary-50 flex items-center justify-center gap-2"
          >
            <Plus className="w-4 h-4" />
            Add New Speaker
          </button>

          {/* Speaker List */}
          {speakersLoading ? (
            <div className="text-center py-8">Loading speakers...</div>
          ) : filteredSpeakers.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              No speakers found. Add a new speaker above.
            </div>
          ) : (
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {filteredSpeakers.map((speaker: Speaker) => (
                <button
                  key={speaker.id}
                  onClick={() => {
                    setSelectedSpeakerId(speaker.id);
                    setIsNewSpeaker(false);
                    setFormData(prev => ({
                      ...prev,
                      speaker_name: speaker.name,
                      speaker_email: speaker.email || '',
                      speaker_affiliation: speaker.affiliation || '',
                    }));
                    setStep('info');
                  }}
                  className="w-full p-4 bg-gray-50 hover:bg-primary-50 rounded-lg text-left transition-colors"
                >
                  <div className="font-medium text-gray-900">{speaker.name}</div>
                  <div className="text-sm text-gray-600">{speaker.affiliation}</div>
                  {speaker.email && (
                    <div className="text-sm text-gray-500">{speaker.email}</div>
                  )}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  }

  // Step 2: Speaker Info
  if (step === 'info') {
    const canProceed = formData.speaker_name && formData.suggested_by;
    
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div className="bg-white rounded-xl p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-2">
              <button 
                onClick={() => setStep('select')}
                className="p-1 hover:bg-gray-100 rounded"
              >
                <ChevronLeft className="w-5 h-5" />
              </button>
              <h2 className="text-xl font-semibold">
                {isNewSpeaker ? 'Add New Speaker' : 'Speaker Details'}
              </h2>
            </div>
            <button onClick={onClose} className="p-1 hover:bg-gray-100 rounded">
              <X className="w-5 h-5" />
            </button>
          </div>

          <div className="space-y-4">
            {/* Speaker Info */}
            <div className="p-4 bg-gray-50 rounded-lg">
              <h3 className="font-medium text-gray-900 mb-3 flex items-center gap-2">
                <User className="w-4 h-4" />
                Speaker Information
              </h3>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Speaker Name *
                  </label>
                  <input
                    type="text"
                    value={formData.speaker_name}
                    onChange={(e) => setFormData(prev => ({ ...prev, speaker_name: e.target.value }))}
                    placeholder="e.g., Prof. Jane Smith"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                    disabled={!isNewSpeaker}
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1 flex items-center gap-1">
                    <Mail className="w-3 h-3" />
                    Email
                  </label>
                  <input
                    type="email"
                    value={formData.speaker_email}
                    onChange={(e) => setFormData(prev => ({ ...prev, speaker_email: e.target.value }))}
                    placeholder="speaker@university.edu"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                    disabled={!isNewSpeaker}
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1 flex items-center gap-1">
                    <Building2 className="w-3 h-3" />
                    Affiliation
                  </label>
                  <input
                    type="text"
                    value={formData.speaker_affiliation}
                    onChange={(e) => setFormData(prev => ({ ...prev, speaker_affiliation: e.target.value }))}
                    placeholder="e.g., MIT"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                    disabled={!isNewSpeaker}
                  />
                </div>
              </div>
            </div>

            {/* Suggestion Details */}
            <div className="p-4 bg-gray-50 rounded-lg">
              <h3 className="font-medium text-gray-900 mb-3 flex items-center gap-2">
                <Lightbulb className="w-4 h-4" />
                Suggestion Details
              </h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Suggested By *
                  </label>
                  <input
                    type="text"
                    value={formData.suggested_by}
                    onChange={(e) => setFormData(prev => ({ ...prev, suggested_by: e.target.value }))}
                    placeholder="Your name"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Suggested Topic
                  </label>
                  <input
                    type="text"
                    value={formData.suggested_topic}
                    onChange={(e) => setFormData(prev => ({ ...prev, suggested_topic: e.target.value }))}
                    placeholder="e.g., Monetary Policy in the Digital Age"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center gap-1">
                    <Flag className="w-3 h-3" />
                    Priority
                  </label>
                  <div className="flex gap-2">
                    {(['low', 'medium', 'high'] as const).map((p) => (
                      <button
                        key={p}
                        onClick={() => setFormData(prev => ({ ...prev, priority: p }))}
                        className={cn(
                          'px-4 py-2 rounded-lg border capitalize transition-all',
                          formData.priority === p
                            ? priorityColors[p]
                            : 'bg-white border-gray-300 text-gray-600 hover:bg-gray-50'
                        )}
                      >
                        {p}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => setStep('select')}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Back
              </button>
              <button
                onClick={() => setStep('availability')}
                disabled={!canProceed}
                className="flex-1 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
              >
                Next: Availability →
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Step 3: Availability with date ranges
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-2">
            <button 
              onClick={() => setStep('info')}
              className="p-1 hover:bg-gray-100 rounded"
            >
              <ChevronLeft className="w-5 h-5" />
            </button>
            <h2 className="text-xl font-semibold">Record Availability</h2>
          </div>
          <button onClick={onClose} className="p-1 hover:bg-gray-100 rounded">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="space-y-4">
          {/* Selected Date Ranges */}
          {dateRanges.length > 0 && (
            <div className="p-4 bg-green-50 rounded-lg border border-green-200">
              <h3 className="font-medium text-green-900 mb-3">
                Selected Date Ranges ({dateRanges.length})
              </h3>
              <div className="flex flex-wrap gap-2">
                {dateRanges.map((range, idx) => (
                  <span 
                    key={idx}
                    className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg text-sm bg-green-100 text-green-800"
                  >
                    {formatDateRange(range.start, range.end)}
                    <button
                      onClick={() => {
                        setDateRanges(prev => prev.filter((_, i) => i !== idx));
                      }}
                      className="ml-1 hover:text-green-900"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Calendar */}
          <div className="p-4 bg-gray-50 rounded-lg">
            <h3 className="font-medium text-gray-900 mb-3 flex items-center gap-2">
              <Calendar className="w-4 h-4" />
              Select Available Dates
            </h3>
            <p className="text-sm text-gray-600 mb-4">
              Click on dates to select ranges. Consecutive dates will be grouped automatically.
            </p>
            
            <CalendarPicker
              selectedDates={selectedDates}
              onChange={handleDateSelect}
              minDate={new Date()}
            />
          </div>

          {/* Time Constraints */}
          <div className="p-4 bg-gray-50 rounded-lg">
            <h3 className="font-medium text-gray-900 mb-3">Time Constraints (Optional)</h3>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Earliest Time
                </label>
                <input
                  type="time"
                  value={earliestTime}
                  onChange={(e) => setEarliestTime(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Latest Time
                </label>
                <input
                  type="time"
                  value={latestTime}
                  onChange={(e) => setLatestTime(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                />
              </div>
            </div>
            
            <div className="mt-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Additional Notes
              </label>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Any constraints or preferences..."
                rows={2}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
              />
            </div>
          </div>

          <div className="flex gap-3">
            <button
              onClick={() => setStep('info')}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              ← Back
            </button>
            <button
              onClick={() => createSuggestionMutation.mutate()}
              disabled={createSuggestionMutation.isPending}
              className="flex-1 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
            >
              {createSuggestionMutation.isPending 
                ? 'Adding...' 
                : dateRanges.length > 0 
                  ? `Add Speaker (${dateRanges.length} ranges, ${selectedDates.length} days)`
                  : 'Add Speaker (no availability)'
              }
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
