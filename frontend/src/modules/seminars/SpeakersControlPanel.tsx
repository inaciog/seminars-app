import { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchWithAuth } from '@/api/client';
import {
  Users,
  Mail,
  Link as LinkIcon,
  Calendar,
  Trash2,
  FileText,
  Eye,
} from 'lucide-react';
import { AddAvailabilityModal } from './AddAvailabilityModal';
import { GeneratedLinkModal, EmailDraftModal, type EmailDraftData } from './SemesterPlanning';
import { openSeminarDetails } from './SeminarsModule';
import type { Seminar } from '@/types';

interface SpeakerSuggestion {
  id: number;
  speaker_name: string;
  speaker_affiliation?: string;
  speaker_email?: string;
  suggested_by: string;
  suggested_by_email?: string;
  reason?: string;
  suggested_topic?: string;
  priority: string;
  status: string;
  semester_plan_id?: number;
  availability?: { date?: string; start_date?: string; end_date?: string; preference: string }[];
}

interface WorkflowItem {
  suggestion_id: number;
  speaker_name: string;
  workflow: {
    request_available_dates_sent: boolean;
    availability_dates_received: boolean;
    speaker_notified_of_date: boolean;
    meal_ok: boolean;
    guesthouse_hotel_reserved: boolean;
    proposal_submitted: boolean;
    proposal_approved: boolean;
  };
}

interface Plan {
  id: number;
  name: string;
}

const WORKFLOW_LABELS: [string, string][] = [
  ['request_available_dates_sent', 'Request dates sent'],
  ['availability_dates_received', 'Availability received'],
  ['speaker_notified_of_date', 'Date notified'],
  ['meal_ok', 'Meal OK'],
  ['guesthouse_hotel_reserved', 'Hotel reserved'],
  ['proposal_submitted', 'Proposal submitted'],
  ['proposal_approved', 'Proposal approved'],
];

export function SpeakersControlPanel() {
  const queryClient = useQueryClient();
  const [generatedLink, setGeneratedLink] = useState<{ link: string; speaker_name: string; linkType: 'availability' | 'info' | 'status' } | null>(null);
  const [emailDraft, setEmailDraft] = useState<EmailDraftData | null>(null);
  const [editingSuggestion, setEditingSuggestion] = useState<SpeakerSuggestion | null>(null);
  const [planFilter, setPlanFilter] = useState<number | ''>('');

  // Fetch all seminars to find assigned ones
  const { data: seminars = [] } = useQuery({
    queryKey: ['speakers-panel-seminars'],
    queryFn: async () => {
      const r = await fetchWithAuth('/api/v1/seminars/seminars');
      if (!r.ok) throw new Error('Failed to fetch seminars');
      return r.json() as Promise<Seminar[]>;
    },
  });

  // Create a map of seminar_id -> seminar for quick lookup
  const seminarById = useMemo(() => {
    const map = new Map<number, Seminar>();
    seminars.forEach((s) => map.set(s.id, s));
    return map;
  }, [seminars]);

  const { data: suggestions = [], isLoading: suggestionsLoading } = useQuery({
    queryKey: ['speaker-suggestions-all', planFilter],
    queryFn: async () => {
      const url = planFilter ? `/api/v1/seminars/speaker-suggestions?plan_id=${planFilter}` : '/api/v1/seminars/speaker-suggestions';
      const r = await fetchWithAuth(url);
      if (!r.ok) throw new Error('Failed to fetch suggestions');
      return r.json();
    },
  });

  const { data: plans = [] } = useQuery({
    queryKey: ['semester-plans'],
    queryFn: async () => {
      const r = await fetchWithAuth('/api/v1/seminars/semester-plans');
      if (!r.ok) throw new Error('Failed to fetch plans');
      return r.json();
    },
  });

  const planIds = useMemo(() => {
    const ids = new Set<number>();
    suggestions.forEach((s: SpeakerSuggestion) => {
      if (s.semester_plan_id) ids.add(s.semester_plan_id);
    });
    return Array.from(ids);
  }, [suggestions]);

  const { data: workflowsByPlan } = useQuery({
    queryKey: ['speaker-workflows-bulk', planIds],
    queryFn: async () => {
      const results: Record<number, { items: WorkflowItem[] }> = {};
      for (const planId of planIds) {
        const r = await fetchWithAuth(`/api/v1/seminars/semester-plans/${planId}/speaker-workflows`);
        if (r.ok) results[planId] = await r.json();
      }
      return results;
    },
    enabled: planIds.length > 0,
  });

  const workflowBySuggestion = useMemo(() => {
    const map = new Map<number, WorkflowItem['workflow']>();
    if (!workflowsByPlan) return map;
    Object.values(workflowsByPlan).forEach((data) => {
      data?.items?.forEach((item) => {
        map.set(item.suggestion_id, item.workflow);
      });
    });
    return map;
  }, [workflowsByPlan]);

  const planById = useMemo(() => {
    const m = new Map<number, Plan>();
    plans.forEach((p: Plan) => m.set(p.id, p));
    return m;
  }, [plans]);

  // Fetch assignment info (suggestion -> seminar, slot) from planning boards
  const { data: assignmentsBySuggestion } = useQuery({
    queryKey: ['suggestion-assignments', planIds],
    queryFn: async () => {
      const map: Record<number, { seminarId: number; slotDate: string; startTime: string; endTime: string }> = {};
      for (const planId of planIds) {
        const r = await fetchWithAuth(`/api/v1/seminars/semester-plans/${planId}/planning-board`);
        if (r.ok) {
          const data = await r.json();
          for (const slot of data.slots || []) {
            if (slot.assigned_suggestion_id && slot.assigned_seminar_id) {
              map[slot.assigned_suggestion_id] = {
                seminarId: slot.assigned_seminar_id,
                slotDate: slot.date,
                startTime: slot.start_time,
                endTime: slot.end_time,
              };
            }
          }
        }
      }
      return map;
    },
    enabled: planIds.length > 0,
  });

  const updateWorkflowMutation = useMutation({
    mutationFn: async ({ suggestionId, patch }: { suggestionId: number; patch: Record<string, boolean> }) => {
      const r = await fetchWithAuth(`/api/v1/seminars/speaker-suggestions/${suggestionId}/workflow`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(patch),
      });
      if (!r.ok) {
        const err = await r.text();
        throw new Error(err || 'Failed to update workflow');
      }
      return r.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['speaker-workflows-bulk'] });
      queryClient.invalidateQueries({ queryKey: ['recent-activity'] });
    },
    onError: (e: Error) => alert(e.message),
  });

  const generateAvailabilityLinkMutation = useMutation({
    mutationFn: async (suggestionId: number) => {
      const r = await fetchWithAuth('/api/v1/seminars/speaker-tokens/availability', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ suggestion_id: suggestionId }),
      });
      if (!r.ok) throw new Error('Failed to generate link');
      return r.json();
    },
    onSuccess: (data, suggestionId) => {
      const s = suggestions.find((x: SpeakerSuggestion) => x.id === suggestionId);
      setGeneratedLink({
        link: `${window.location.origin}${data.link}`,
        speaker_name: s?.speaker_name || '',
        linkType: 'availability',
      });
    },
    onError: (e: Error) => alert(e.message),
  });

  const generateStatusLinkMutation = useMutation({
    mutationFn: async (suggestionId: number) => {
      const r = await fetchWithAuth('/api/v1/seminars/speaker-tokens/status', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ suggestion_id: suggestionId }),
      });
      if (!r.ok) {
        const err = await r.text();
        throw new Error(err || 'Failed to generate status link');
      }
      return r.json();
    },
    onSuccess: (data, suggestionId) => {
      const s = suggestions.find((x: SpeakerSuggestion) => x.id === suggestionId);
      setGeneratedLink({
        link: `${window.location.origin}${data.link}`,
        speaker_name: s?.speaker_name || '',
        linkType: 'status',
      });
    },
    onError: (e: Error) => alert(e.message),
  });

  const generateInfoLinkMutation = useMutation({
    mutationFn: async ({ seminarId, suggestionId }: { seminarId: number; suggestionId: number }) => {
      const r = await fetchWithAuth('/api/v1/seminars/speaker-tokens/info', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ seminar_id: seminarId, suggestion_id: suggestionId }),
      });
      if (!r.ok) {
        const err = await r.text();
        throw new Error(err || 'Failed to generate info link');
      }
      return r.json();
    },
    onSuccess: (data, variables) => {
      const s = suggestions.find((x: SpeakerSuggestion) => x.id === variables.suggestionId);
      setGeneratedLink({
        link: `${window.location.origin}${data.link}`,
        speaker_name: s?.speaker_name || '',
        linkType: 'info',
      });
    },
    onError: (e: Error) => alert(e.message),
  });

  const deleteSuggestionMutation = useMutation({
    mutationFn: async (suggestionId: number) => {
      const r = await fetchWithAuth(`/api/v1/seminars/speaker-suggestions/${suggestionId}`, { method: 'DELETE' });
      if (!r.ok) {
        const err = await r.text();
        throw new Error(err || 'Failed to delete');
      }
      return r.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['speaker-suggestions-all'] });
      queryClient.invalidateQueries({ queryKey: ['speaker-workflows-bulk'] });
      queryClient.invalidateQueries({ queryKey: ['planning-board'] });
    },
    onError: (e: Error) => alert(e.message),
  });

  const handleDraftEmail = async (
    suggestion: SpeakerSuggestion,
    type: 'availability_request' | 'date_confirmation' | 'info_request',
    assignment?: { seminarId: number; slotDate: string; startTime: string; endTime: string }
  ) => {
    if (type === 'availability_request') {
      let availabilityLink = '';
      try {
        const r = await fetchWithAuth('/api/v1/seminars/speaker-tokens/availability', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ suggestion_id: suggestion.id }),
        });
        if (r.ok) {
          const data = await r.json();
          availabilityLink = `${window.location.origin}${data.link}`;
        }
      } catch {
        // ignore
      }
      setEmailDraft({
        type,
        speakerName: suggestion.speaker_name,
        suggestedBy: suggestion.suggested_by,
        availabilityLink,
      });
      return;
    }
    if (type === 'date_confirmation' || type === 'info_request') {
      if (!assignment) return;
      const talkDate = new Date(assignment.slotDate);
      const today = new Date();
      const deadline = new Date(talkDate);
      deadline.setDate(deadline.getDate() - 45);
      if (deadline < today) {
        deadline.setTime(today.getTime() + 3 * 24 * 60 * 60 * 1000);
      }
      let infoLink = '';
      let statusLink = '';
      let linkError = '';
      if (type === 'info_request') {
        try {
          const r = await fetchWithAuth('/api/v1/seminars/speaker-tokens/info', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ seminar_id: assignment.seminarId, suggestion_id: suggestion.id }),
          });
          if (r.ok) {
            const data = await r.json();
            infoLink = `${window.location.origin}${data.link}`;
          } else {
            const errorText = await r.text();
            linkError = `Failed: ${r.status} - ${errorText}`;
          }
        } catch (err) {
          linkError = 'Network error generating link';
        }
      }
      if (type === 'date_confirmation') {
        try {
          const r = await fetchWithAuth('/api/v1/seminars/speaker-tokens/status', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ suggestion_id: suggestion.id }),
          });
          if (r.ok) {
            const data = await r.json();
            statusLink = `${window.location.origin}${data.link}`;
          } else {
            const errorText = await r.text();
            linkError = `Failed: ${r.status} - ${errorText}`;
          }
        } catch (err) {
          linkError = linkError || 'Network error generating status link';
        }
      }
      setEmailDraft({
        type,
        speakerName: suggestion.speaker_name,
        slotDate: talkDate.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' }),
        slotTime: `${assignment.startTime} - ${assignment.endTime}`,
        deadlineDate: deadline.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' }),
        suggestedBy: suggestion.suggested_by,
        infoLink,
        statusLink,
        linkError,
      });
    }
  };

  if (suggestionsLoading) {
    return (
      <div className="text-center py-12 text-gray-500">
        Loading suggested speakers...
      </div>
    );
  }

  if (suggestions.length === 0) {
    return (
      <div className="text-center py-16 px-6 bg-gray-50 rounded-xl border border-gray-100">
        <Users className="w-14 h-14 mx-auto mb-4 text-gray-300" />
        <p className="text-lg font-medium text-gray-600">No suggested speakers yet</p>
        <p className="text-sm text-gray-500 mt-1">Add speakers from the Semester Planning tab</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <label className="text-sm font-medium text-gray-700">Filter by plan:</label>
          <select
            value={planFilter}
            onChange={(e) => setPlanFilter(e.target.value ? Number(e.target.value) : '')}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
          >
            <option value="">All plans</option>
            {plans.map((p: Plan) => (
              <option key={p.id} value={p.id}>{p.name}</option>
            ))}
          </select>
        </div>
        <p className="text-sm text-gray-500">
          {suggestions.length} speaker{suggestions.length !== 1 ? 's' : ''}
        </p>
      </div>

      <div className="space-y-4">
        {suggestions.map((suggestion: SpeakerSuggestion) => {
          const workflow = workflowBySuggestion.get(suggestion.id);
          const planName = suggestion.semester_plan_id ? planById.get(suggestion.semester_plan_id)?.name : null;
          return (
            <div
              key={suggestion.id}
              className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h3 className="font-semibold text-gray-900">{suggestion.speaker_name}</h3>
                  {suggestion.speaker_affiliation && (
                    <p className="text-sm text-gray-600 mt-0.5">{suggestion.speaker_affiliation}</p>
                  )}
                  {suggestion.suggested_topic && (
                    <p className="text-sm text-gray-700 mt-1 line-clamp-2">{suggestion.suggested_topic}</p>
                  )}
                  <p
                    className="text-xs text-gray-500 mt-2 cursor-default"
                    title={suggestion.reason ? `Reason / context: ${suggestion.reason}` : undefined}
                  >
                    Suggested by {suggestion.suggested_by}
                    {suggestion.suggested_by_email && (
                      <> ({suggestion.suggested_by_email})</>
                    )}
                  </p>
                  {planName && (
                    <span className="inline-block mt-2 px-2 py-0.5 text-xs bg-gray-100 text-gray-700 rounded">
                      {planName}
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-2 shrink-0 flex-wrap">
                  {suggestion.status === 'pending' && (
                    <button
                      onClick={() => handleDraftEmail(suggestion, 'availability_request')}
                      className="flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-white bg-indigo-500 hover:bg-indigo-600 rounded-lg"
                      title="Draft availability request email"
                    >
                      <Mail className="w-3 h-3" />
                      Email
                    </button>
                  )}
                  <button
                    onClick={() => generateAvailabilityLinkMutation.mutate(suggestion.id)}
                    disabled={generateAvailabilityLinkMutation.isPending}
                    className="flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-green-700 bg-green-100 hover:bg-green-200 rounded-lg"
                    title="Generate availability form link"
                  >
                    <LinkIcon className="w-3 h-3" />
                    Availability
                  </button>
                  <button
                    onClick={() => generateStatusLinkMutation.mutate(suggestion.id)}
                    disabled={generateStatusLinkMutation.isPending}
                    className="flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-purple-700 bg-purple-100 hover:bg-purple-200 rounded-lg"
                    title="Generate status link"
                  >
                    <LinkIcon className="w-3 h-3" />
                    Status
                  </button>
                  {assignmentsBySuggestion?.[suggestion.id] && (
                    <>
                      <button
                        onClick={() => {
                          const seminar = seminarById.get(assignmentsBySuggestion[suggestion.id].seminarId);
                          if (seminar) {
                            openSeminarDetails(seminar);
                          }
                        }}
                        disabled={!seminarById.has(assignmentsBySuggestion[suggestion.id].seminarId)}
                        className="flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg"
                        title="View seminar details"
                      >
                        <Eye className="w-3 h-3" />
                        View
                      </button>
                      <button
                        onClick={() => generateInfoLinkMutation.mutate({
                          seminarId: assignmentsBySuggestion[suggestion.id].seminarId,
                          suggestionId: suggestion.id,
                        })}
                        disabled={generateInfoLinkMutation.isPending}
                        className="flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-indigo-700 bg-indigo-100 hover:bg-indigo-200 rounded-lg"
                        title="Generate info form link"
                      >
                        <LinkIcon className="w-3 h-3" />
                        Info
                      </button>
                      <button
                        onClick={() => handleDraftEmail(suggestion, 'date_confirmation', assignmentsBySuggestion[suggestion.id])}
                        className="flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-white bg-indigo-500 hover:bg-indigo-600 rounded-lg"
                        title="Draft date confirmation email"
                      >
                        <Mail className="w-3 h-3" />
                        Confirm
                      </button>
                      <button
                        onClick={() => handleDraftEmail(suggestion, 'info_request', assignmentsBySuggestion[suggestion.id])}
                        className="flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-white bg-blue-500 hover:bg-blue-600 rounded-lg"
                        title="Draft info request email"
                      >
                        <FileText className="w-3 h-3" />
                        Info
                      </button>
                    </>
                  )}
                  {suggestion.semester_plan_id && (
                    <button
                      onClick={() => setEditingSuggestion(suggestion)}
                      className="flex items-center gap-1 px-3 py-1.5 text-xs text-gray-600 hover:text-primary-600 hover:bg-gray-100 rounded-lg"
                      title="Add availability"
                    >
                      <Calendar className="w-3 h-3" />
                      Dates
                    </button>
                  )}
                  <button
                    onClick={() => {
                      if (confirm(`Delete suggestion for "${suggestion.speaker_name}"?`)) {
                        deleteSuggestionMutation.mutate(suggestion.id);
                      }
                    }}
                    className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg"
                    title="Delete"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {workflow && (
                <div className="mt-4 pt-4 border-t border-gray-100">
                  <h4 className="text-xs font-medium text-gray-500 mb-2">Workflow checklist</h4>
                  <div className="flex flex-wrap gap-x-6 gap-y-2">
                    {WORKFLOW_LABELS.map(([key, label]) => {
                      const checked = Boolean((workflow as Record<string, boolean>)[key]);
                      return (
                        <label key={key} className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={checked}
                            onChange={(e) => {
                              updateWorkflowMutation.mutate({
                                suggestionId: suggestion.id,
                                patch: { [key]: e.target.checked },
                              });
                            }}
                            className="rounded border-gray-300"
                          />
                          <span>{label}</span>
                        </label>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {generatedLink && (
        <GeneratedLinkModal
          link={generatedLink.link}
          speakerName={generatedLink.speaker_name}
          linkType={generatedLink.linkType}
          onClose={() => setGeneratedLink(null)}
        />
      )}

      {emailDraft && (
        <EmailDraftModal draft={emailDraft} onClose={() => setEmailDraft(null)} />
      )}

      {editingSuggestion && editingSuggestion.semester_plan_id && (
        <AddAvailabilityModal
          suggestionId={editingSuggestion.id}
          planId={editingSuggestion.semester_plan_id}
          speakerName={editingSuggestion.speaker_name}
          existingAvailability={editingSuggestion.availability || []}
          onClose={() => setEditingSuggestion(null)}
        />
      )}
    </div>
  );
}
