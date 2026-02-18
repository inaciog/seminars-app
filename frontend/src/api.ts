import axios, { AxiosInstance } from 'axios';

// Get token from storage
const getToken = () => {
  return localStorage.getItem('token');
};

// Create axios instance
const api: AxiosInstance = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
    // Also add as query param for compatibility
    if (config.params) {
      config.params.token = token;
    } else {
      config.params = { token };
    }
  }
  return config;
});

// Error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.reload();
    }
    throw error;
  }
);

// Seminars API
export const seminarsApi = {
  listSeminars: () => api.get('/seminars').then(r => r.data),
  createSeminar: (data: any) => api.post('/seminars', data),
  updateSeminar: (id: number, data: any) => api.put(`/seminars/${id}`, data),
  deleteSeminar: (id: number) => api.delete(`/seminars/${id}`),
  getSeminar: (id: number) => api.get(`/seminars/${id}`).then(r => r.data),
  
  listSpeakers: () => api.get('/speakers').then(r => r.data),
  createSpeaker: (data: any) => api.post('/speakers', data),
  updateSpeaker: (id: number, data: any) => api.put(`/speakers/${id}`, data),
  deleteSpeaker: (id: number) => api.delete(`/speakers/${id}`),
  
  listRooms: () => api.get('/rooms').then(r => r.data),
  createRoom: (data: any) => api.post('/rooms', data),
  deleteRoom: (id: number) => api.delete(`/rooms/${id}`),
  
  listFiles: (seminarId: number) => api.get(`/seminars/${seminarId}/files`).then(r => r.data),
  uploadFile: (seminarId: number, formData: FormData) => 
    api.post(`/seminars/${seminarId}/files`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    }),
  downloadFile: (fileId: number) => api.get(`/files/${fileId}/download`),
};

export default api;
