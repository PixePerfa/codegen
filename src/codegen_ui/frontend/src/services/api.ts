import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Project API
export const projectApi = {
  listProjects: () => api.get('/projects'),
  getProject: (id: string) => api.get(`/projects/${id}`),
  createProject: (data: { path: string; language?: string }) => api.post('/projects', data),
};

// File API
export const fileApi = {
  listFiles: (projectId: string) => api.get(`/projects/${projectId}/files`),
  getFile: (projectId: string, path: string) => api.get(`/projects/${projectId}/files/${path}`),
  createFile: (projectId: string, data: { path: string; content: string }) => 
    api.post(`/projects/${projectId}/files`, data),
  updateFile: (projectId: string, path: string, data: { path: string; content: string }) => 
    api.put(`/projects/${projectId}/files/${path}`, data),
  deleteFile: (projectId: string, path: string) => 
    api.delete(`/projects/${projectId}/files/${path}`),
};

// Symbol API
export const symbolApi = {
  listSymbols: (projectId: string) => api.get(`/projects/${projectId}/symbols`),
  listClasses: (projectId: string) => api.get(`/projects/${projectId}/classes`),
  listFunctions: (projectId: string) => api.get(`/projects/${projectId}/functions`),
};

// Search API
export const searchApi = {
  search: (projectId: string, data: { query: string; file_pattern?: string }) => 
    api.post(`/projects/${projectId}/search`, data),
};

// Transform API
export const transformApi = {
  transform: (projectId: string, data: { operation: string; params: any }) => 
    api.post(`/projects/${projectId}/transform`, data),
};

// WebSocket API
export const createWebSocketConnection = (projectId: string) => {
  const WS_BASE_URL = process.env.REACT_APP_WS_BASE_URL || 'ws://localhost:8000';
  return new WebSocket(`${WS_BASE_URL}/ws/${projectId}`);
};

export default {
  projectApi,
  fileApi,
  symbolApi,
  searchApi,
  transformApi,
  createWebSocketConnection,
};