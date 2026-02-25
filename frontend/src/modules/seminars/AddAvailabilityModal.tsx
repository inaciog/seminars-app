import { useState, useMemo } from 'react';
import { fetchWithAuth } from '@/api/client';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { X, Calendar, Clock, CheckCircle } from 'lucide-react';
import { CalendarPicker } from '@/components/CalendarPicker';
import { CHINA_TIMEZONE } from '@/lib/utils';

interface Availability {
  id?: number;
  date?: string;
  start_date?: string;
  end_date?: string;
  preference: string;
  earliest_time?: string;
  latest_time?: string;
  notes?: string;
}

interface AddAvailabilityModalProps {
  suggestionId: number;
  planId: number;
  speakerName: string;
  existingAvailability?: Availability[];
  onClose: () => void;
}

export function AddAvailabilityModal({ 
  suggestionId, 
  planId, 
  speakerName,
  existingAvailability = [],
  onClose 
}: AddAvailabilityModalProps) {
  const queryClient = useQueryClient();
  const [dateRanges, setDateRanges] = useState<{start: Date; end: Date}[]>([]);
  const [earliestTime, setEarliestTime] = useState('');
  const [latestTime, setLatestTime] = useState('');
  const [notes, setNotes] = useState('');

  const addAvailabilityMutation = useMutation({
    mutationFn: async () => {
      if (dateRanges.length === 0) return;
      
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
      
      const response = await fetchWithAuth(`/api/v1/seminars/speaker-suggestions/${suggestionId}/availability`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(availabilities),
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Failed to add availability: ${errorText}`);
      }
      
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['planning-board', planId] });
      onClose();
    },
    onError: (error: Error) => {
      alert(`Error: ${error.message}`);
    },
  });

  const handleDateSelect = (dates: Date[]) => {
    if (dates.length === 0) {
      setDateRanges([]);
      return;
    }
    
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
        rangeEnd = current;
      } else {
        ranges.push({ start: rangeStart, end: rangeEnd });
        rangeStart = current;
        rangeEnd = current;
      }
    }
    ranges.push({ start: rangeStart, end: rangeEnd });
    
    setDateRanges(ranges);
  };

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

  const formatAvailabilityDisplay = (avail: Availability): string => {
    const startStr = avail.start_date ?? avail.date;
    const endStr = avail.end_date ?? avail.date;
    if (!startStr || !endStr) return '—';
    const start = new Date(startStr);
    const end = new Date(endStr);
    if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) return '—';
    const sameMonth = start.getMonth() === end.getMonth() && start.getFullYear() === end.getFullYear();
    const startFmt = start.toLocaleDateString('en-US', { month: 'short', day: 'numeric', timeZone: CHINA_TIMEZONE });
    const endFmt = end.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric', timeZone: CHINA_TIMEZONE });
    if (startStr === endStr) return startFmt + ', ' + start.getFullYear();
    return sameMonth
      ? `${startFmt}-${end.getDate()}, ${end.getFullYear()}`
      : `${startFmt} - ${endFmt}`;
  };

  // Calculate total days in existing availability (supports { date } or { start_date, end_date })
  const existingDays = useMemo(() => {
    let days = 0;
    for (const avail of existingAvailability) {
      const startStr = avail.start_date ?? avail.date;
      const endStr = avail.end_date ?? avail.date;
      if (!startStr || !endStr) continue;
      const start = new Date(startStr);
      const end = new Date(endStr);
      if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) continue;
      days += Math.floor((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24)) + 1;
    }
    return days;
  }, [existingAvailability]);

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl p-6 w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold">
            Availability for {speakerName}
          </h2>
          <button onClick={onClose} className="p-1 hover:bg-gray-100 rounded">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="space-y-4">
          {/* Existing Availability */}
          {existingAvailability.length > 0 && (
            <div className="p-4 bg-green-50 rounded-lg border border-green-200">
              <h3 className="font-medium text-green-900 mb-3 flex items-center gap-2">
                <CheckCircle className="w-4 h-4" />
                Already Available ({existingAvailability.length} entries, {existingDays} days)
              </h3>
              <div className="flex flex-wrap gap-2">
                {existingAvailability.map((avail, idx) => (
                  <span 
                    key={idx}
                    className="inline-flex items-center px-2.5 py-1 rounded-full text-sm bg-green-100 text-green-800"
                  >
                    {formatAvailabilityDisplay(avail)}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* New Date Ranges */}
          {dateRanges.length > 0 && (
            <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
              <h3 className="font-medium text-blue-900 mb-3">
                New Ranges to Add ({dateRanges.length})
              </h3>
              <div className="flex flex-wrap gap-2">
                {dateRanges.map((range, idx) => (
                  <span 
                    key={idx}
                    className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-sm bg-blue-100 text-blue-800"
                  >
                    {range.start.toLocaleDateString('en-US', { month: 'short', day: 'numeric', timeZone: CHINA_TIMEZONE })}
                    {range.start.getTime() !== range.end.getTime() && (
                      <> - {range.end.toLocaleDateString('en-US', { month: 'short', day: 'numeric', timeZone: CHINA_TIMEZONE })}</>
                    )}
                    <button
                      onClick={() => {
                        setDateRanges(prev => prev.filter((_, i) => i !== idx));
                      }}
                      className="ml-1 hover:text-blue-900"
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
              Add More Available Dates
            </h3>
            <p className="text-sm text-gray-600 mb-4">
              Select dates. Consecutive dates will be grouped into ranges.
            </p>
            <CalendarPicker
              selectedDates={selectedDates}
              onChange={handleDateSelect}
              minDate={new Date()}
              existingAvailability={existingAvailability}
            />
          </div>

          {/* Time Constraints */}
          <div className="p-4 bg-gray-50 rounded-lg">
            <h3 className="font-medium text-gray-900 mb-3 flex items-center gap-2">
              <Clock className="w-4 h-4" />
              Time Constraints (Optional)
            </h3>
            
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
                Notes
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
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              onClick={() => addAvailabilityMutation.mutate()}
              disabled={dateRanges.length === 0 || addAvailabilityMutation.isPending}
              className="flex-1 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
            >
              {addAvailabilityMutation.isPending 
                ? 'Adding...' 
                : `Add ${dateRanges.length} Range(s)`
              }
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
