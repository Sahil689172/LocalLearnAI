/**
 * API Service for LocalLearn AI
 * 
 * Handles all communication with the backend API.
 */

import { API_ENDPOINTS } from '../config/api';

// Request types
export interface GenerateVideoRequest {
  mode: 'topic' | 'custom_script';
  topic?: string;
  script?: string;
  narration?: string;
  language: string;
}

// Response types
export interface GenerateVideoResponse {
  success: boolean;
  job_id: string;
  status: string;
  message: string;
}

export interface JobStatusResponse {
  job_id: string;
  status: 'queued' | 'running' | 'completed' | 'failed';
  phase: string;
  phase_label: string;
  message: string;
  video_url: string | null;
  duration: number | null;
  error: string | null;
  beat_count?: number;
  audio_segments?: number;
  audio_duration?: number;
}

/**
 * Submit a video generation request
 */
export async function generateVideo(request: GenerateVideoRequest): Promise<GenerateVideoResponse> {
  const response = await fetch(API_ENDPOINTS.generateVideo, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || 'Failed to start video generation');
  }

  return response.json();
}

/**
 * Get the current status of a job
 */
export async function getJobStatus(jobId: string): Promise<JobStatusResponse> {
  const response = await fetch(API_ENDPOINTS.jobStatus(jobId));

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || 'Failed to get job status');
  }

  return response.json();
}

/**
 * Get the video download URL
 */
export function getVideoDownloadUrl(jobId: string): string {
  return API_ENDPOINTS.downloadVideo(jobId);
}
