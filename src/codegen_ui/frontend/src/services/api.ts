import axios from 'axios';
import { createContext, useContext } from 'react';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// System API
export const systemApi = {
  getSystemInfo: () => api.get('/system-info'),
  scanProjects: (data: { base_path?: string }) => api.post('/scan-projects', data),
  initialize: (data: { path: string; language?: string }) => api.post('/initialize', data),
};

// Project API
export const projectApi = {
  listProjects: () => api.get('/projects'),
  getProject: (id: string) => api.get(`/projects/${id}`),
  createProject: (data: { path: string; language?: string; auto_init?: boolean }) => api.post('/projects', data),
  commitChanges: (projectId: string) => api.post(`/projects/${projectId}/commit`),
  resetCodebase: (projectId: string) => api.post(`/projects/${projectId}/reset`),
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
  createDirectory: (projectId: string, data: { path: string }) => 
    api.post(`/projects/${projectId}/directories`, data),
};

// Symbol API
export const symbolApi = {
  listSymbols: (projectId: string) => api.get(`/projects/${projectId}/symbols`),
  listClasses: (projectId: string) => api.get(`/projects/${projectId}/classes`),
  listFunctions: (projectId: string) => api.get(`/projects/${projectId}/functions`),
  getDependencies: (projectId: string) => api.get(`/projects/${projectId}/dependencies`),
  getImports: (projectId: string) => api.get(`/projects/${projectId}/imports`),
  getSymbolUsages: (projectId: string, symbolName: string) => 
    api.get(`/projects/${projectId}/symbols/${encodeURIComponent(symbolName)}/usages`),
};

// Search API
export const searchApi = {
  search: (projectId: string, data: { query: string; file_pattern?: string }) => 
    api.post(`/projects/${projectId}/search`, data),
  regexSearch: (projectId: string, data: { pattern: string; file_pattern?: string }) => 
    api.post(`/projects/${projectId}/regex-search`, data),
};

// Transform API
export const transformApi = {
  transform: (projectId: string, data: { operation: string; params: any }) => 
    api.post(`/projects/${projectId}/transform`, data),
  batchOperation: (projectId: string, data: { operation: string; files: string[]; params: any }) => 
    api.post(`/projects/${projectId}/batch`, data),
};

// Analysis API
export const analysisApi = {
  analyze: (projectId: string, data: { type: string; target?: string; params?: any }) => 
    api.post(`/projects/${projectId}/analysis`, data),
};

// Git API
export const gitApi = {
  gitOperation: (projectId: string, data: { operation: string; params: any }) => 
    api.post(`/projects/${projectId}/git`, data),
};

// Advanced Features API
export const advancedFeaturesApi = {
  // Code Quality Analysis
  getCodeQuality: (projectId: string, filePath?: string) => 
    api.get(`/projects/${projectId}/code-quality`, { params: filePath ? { file_path: filePath } : {} }),
  
  // Refactoring Suggestions
  getRefactoringSuggestions: (projectId: string, filePath?: string) => 
    api.get(`/projects/${projectId}/refactoring-suggestions`, { params: filePath ? { file_path: filePath } : {} }),
  
  // Test Generation
  getTestGeneration: (projectId: string, filePath?: string) => 
    api.get(`/projects/${projectId}/test-generation`, { params: filePath ? { file_path: filePath } : {} }),
  
  // Documentation Generation
  getDocumentation: (projectId: string, filePath?: string) => 
    api.get(`/projects/${projectId}/documentation`, { params: filePath ? { file_path: filePath } : {} }),
  
  // Visualizations
  getVisualizations: (projectId: string, filePath?: string) => 
    api.get(`/projects/${projectId}/visualizations`, { params: filePath ? { file_path: filePath } : {} }),
};

// WebSocket API
export const createWebSocketConnection = (projectId: string) => {
  const WS_BASE_URL = process.env.REACT_APP_WS_BASE_URL || 'ws://localhost:8000';
  return new WebSocket(`${WS_BASE_URL}/ws/${projectId}`);
};

// Simple API wrapper for components
export const ApiContext = createContext({
  get: (url: string) => api.get(url).then(res => res.data),
  post: (url: string, data?: any) => api.post(url, data).then(res => res.data),
  put: (url: string, data?: any) => api.put(url, data).then(res => res.data),
  delete: (url: string) => api.delete(url).then(res => res.data),
});

export const useApi = () => useContext(ApiContext);

export default {
  systemApi,
  projectApi,
  fileApi,
  symbolApi,
  searchApi,
  transformApi,
  analysisApi,
  gitApi,
  advancedFeaturesApi,
  createWebSocketConnection,
};