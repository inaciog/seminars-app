import axios, { AxiosInstance, AxiosError } from 'axios';
import type { ActionResult } from '@/types';

// Get token from URL or localStorage
const getToken = (): string | null => {
  if (typeof window === 'undefined') return null;
  
  // Check URL first
  const params = new URLSearchParams(window.location.search);
  const urlToken = params.get('token');
  if (urlToken) {
    localStorage.setItem('seminars_token', urlToken);
    // Clean URL
    window.history.replaceState({}, '', window.location.pathname);
    return urlToken;
  }
  
  // Then check localStorage
  return localStorage.getItem('seminars_token');
};

// Create axios instance
const api: AxiosInstance = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Error handling interceptor
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    console.error('API Error:', error.response?.data || error.message);
    
    // Handle 401 Unauthorized - redirect to login
    if (error.response?.status === 401) {
      localStorage.removeItem('seminars_token');
      const currentUrl = window.location.href;
      window.location.href = `https://inacio-auth.fly.dev/login?returnTo=${encodeURIComponent(currentUrl)}`;
    }
    
    throw error;
  }
);

// Helper for fetch with auth
export const fetchWithAuth = async (url: string, options: RequestInit = {}): Promise<Response> => {
  const token = getToken();
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string> || {}),
  };
  
  // Only set Content-Type if it's not FormData (browser will set it with boundary)
  const isFormData = options.body instanceof FormData;
  if (!isFormData && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }
  
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  
  const response = await fetch(url, {
    ...options,
    headers,
  });
  
  // Handle 401 - redirect to login
  if (response.status === 401) {
    localStorage.removeItem('seminars_token');
    const currentUrl = window.location.href;
    window.location.href = `https://inacio-auth.fly.dev/login?returnTo=${encodeURIComponent(currentUrl)}`;
  }
  
  return response;
};

// Seminars API - adapted for standalone seminars backend
export const seminarsApi = {
  listSeminars: (params?: { upcoming?: boolean; in_plan_only?: boolean; orphaned?: boolean }) =>
    api.get('/seminars', { params: { upcoming: true, ...params } }).then(r => r.data),
  listOrphanSeminars: async () => {
    const r = await fetchWithAuth('/api/v1/seminars/seminars?orphaned=true');
    if (!r.ok) throw new Error('Failed to fetch orphan seminars');
    return r.json();
  },
  assignSeminarToSlot: async (seminarId: number, slotId: number) => {
    const r = await fetchWithAuth('/api/v1/seminars/planning/assign-seminar', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ seminar_id: seminarId, slot_id: slotId }),
    });
    if (!r.ok) {
      const err = await r.text();
      throw new Error(err || 'Failed to assign seminar');
    }
    return r.json();
  },
  listSpeakers: () => api.get('/speakers').then(r => r.data),
  createSeminar: (data: any) => api.post('/seminars', data),
  updateSeminar: (id: number, data: any) => api.put(`/seminars/${id}`, data),
  getSeminarDetails: (id: number) => api.get(`/seminars/${id}`).then(r => r.data),
  deleteSeminar: (id: number) => api.delete(`/seminars/${id}`),
  
  // Speakers
  createSpeaker: (data: any) => api.post('/speakers', data),
  updateSpeaker: (id: number, data: any) => api.put(`/speakers/${id}`, data),
  deleteSpeaker: (id: number) => api.delete(`/speakers/${id}`),
  
  // Rooms
  listRooms: () => api.get('/rooms').then(r => r.data),
  createRoom: (data: any) => api.post('/rooms', data),
  deleteRoom: (id: number) => api.delete(`/rooms/${id}`),
  
  // Semester Plans - these need to be implemented in backend
  listSemesterPlans: () => Promise.resolve([]),
  getSemesterPlan: (id: number) => Promise.resolve(null),
  createSemesterPlan: (data: any) => Promise.resolve({}),
  createSemesterSlot: (planId: number, data: any) => Promise.resolve({}),
  getPlanningBoard: (planId: number) => Promise.resolve({ slots: [], suggestions: [] }),
  
  // Speaker Suggestions - stubbed for now
  listSpeakerSuggestions: (planId?: number) => Promise.resolve([]),
  createSpeakerSuggestion: (data: any) => Promise.resolve({}),
  addSpeakerAvailability: (suggestionId: number, availabilities: any[]) => Promise.resolve({}),
  assignSpeakerToSlot: (suggestionId: number, slotId: number) => Promise.resolve({}),
  
  // Bureaucracy check - simplified (uses same seminar list as upcoming tab)
  checkBureaucracy: () => api.get('/seminars', { params: { upcoming: true } }).then(r => {
    const seminars = r.data || [];
    const today = new Date();
    const pendingTasks = [];
    
    for (const seminar of seminars) {
      const seminarDate = new Date(seminar.date);
      const daysUntil = Math.ceil((seminarDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
      
      if (daysUntil >= 0 && daysUntil <= 7) {
        const tasks = [];
        if (!seminar.room_booked) tasks.push('Book room');
        if (!seminar.announcement_sent) tasks.push('Send announcement');
        if (!seminar.calendar_invite_sent) tasks.push('Send calendar invite');
        
        if (tasks.length > 0) {
          pendingTasks.push({
            seminar_id: seminar.id,
            title: seminar.title,
            date: seminar.date,
            days_until: daysUntil,
            tasks
          });
        }
      }
    }
    
    return {
      data: {
        pending_tasks: pendingTasks
      }
    };
  }),
  
  // Activities
  getRecentActivities: async (limit: number = 100, planId?: number) => {
    const qs = new URLSearchParams();
    qs.set('limit', String(limit));
    if (planId != null) qs.set('plan_id', String(planId));
    const r = await fetchWithAuth(`/api/v1/seminars/activity?${qs.toString()}`);
    if (!r.ok) throw new Error('Failed to fetch activity');
    return r.json();
  },
};

// Legacy helper for compatibility
export const getAccessCode = (): string | null => {
  return getToken();
};

export default api;
