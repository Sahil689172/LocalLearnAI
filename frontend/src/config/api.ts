/**
 * API Configuration for LocalLearn AI Frontend
 * 
 * Single source of truth for backend API endpoint.
 */

// Backend API base URL
// Change this if backend runs on a different host/port
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// API endpoints
export const API_ENDPOINTS = {
  generateVideo: `${API_BASE_URL}/api/video/generate`,
  jobStatus: (jobId: string) => `${API_BASE_URL}/api/video/status/${jobId}`,
  downloadVideo: (jobId: string) => `${API_BASE_URL}/api/video/download/${jobId}`,
} as const;

// Polling interval for job status (milliseconds)
export const STATUS_POLL_INTERVAL = 2000; // 2 seconds
