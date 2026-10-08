/**
 * WorkflowStatus Component
 * 
 * Displays the real-time workflow phase of video generation.
 * Shows which actual backend stage is currently running.
 * 
 * NO FAKE PROGRESS. Only real backend phases.
 */

import React from 'react';
import './WorkflowStatus.css';

export interface WorkflowPhase {
  id: string;
  label: string;
  status: 'completed' | 'active' | 'pending' | 'failed';
  message?: string;
  details?: string;
}

interface WorkflowStatusProps {
  mode: 'topic' | 'custom_script';
  currentPhase: string;
  phaseLabel: string;
  message: string;
  status: 'queued' | 'running' | 'completed' | 'failed';
  error?: string | null;
  
  // Additional metadata from backend
  beatCount?: number;
  audioSegments?: number;
  audioDuration?: number;
}

// Define workflow phases for each mode
const TOPIC_MODE_PHASES = [
  { id: 'lesson_planning', label: 'Lesson Planning (Ollama)' },
  { id: 'voice_generation', label: 'Voice Generation (Piper TTS)' },
  { id: 'audio_timing', label: 'Audio Timing' },
  { id: 'scene_generation', label: 'Scene Generation' },
  { id: 'rendering', label: 'Manim Rendering' },
  { id: 'muxing', label: 'Audio + Video Muxing' },
  { id: 'complete', label: 'Complete' },
];

const CUSTOM_SCRIPT_PHASES = [
  { id: 'preparing_script', label: 'Preparing Script' },
  { id: 'rendering', label: 'ManimGL Rendering' },
  { id: 'voice_generation', label: 'Voice Generation (Piper TTS)' },
  { id: 'audio_timing', label: 'Audio Timing' },
  { id: 'muxing', label: 'Audio + Video Muxing' },
  { id: 'complete', label: 'Complete' },
];

export const WorkflowStatus: React.FC<WorkflowStatusProps> = ({
  mode,
  currentPhase,
  phaseLabel,
  message,
  status,
  error,
  beatCount,
  audioSegments,
  audioDuration,
}) => {
  const phases = mode === 'topic' ? TOPIC_MODE_PHASES : CUSTOM_SCRIPT_PHASES;
  
  // Determine phase status
  const getPhaseStatus = (phaseId: string): 'completed' | 'active' | 'pending' | 'failed' => {
    if (status === 'failed' && currentPhase === phaseId) {
      return 'failed';
    }
    
    if (currentPhase === phaseId) {
      return 'active';
    }
    
    // Check if this phase comes before current phase (completed)
    const currentIndex = phases.findIndex(p => p.id === currentPhase);
    const phaseIndex = phases.findIndex(p => p.id === phaseId);
    
    if (phaseIndex < currentIndex) {
      return 'completed';
    }
    
    return 'pending';
  };
  
  // Get phase icon
  const getPhaseIcon = (phaseStatus: string): string => {
    switch (phaseStatus) {
      case 'completed':
        return '✓';
      case 'active':
        return '●';
      case 'failed':
        return '✕';
      default:
        return '○';
    }
  };
  
  // Format details for current phase
  const getPhaseDetails = (phaseId: string): string | undefined => {
    if (currentPhase !== phaseId) return undefined;
    
    switch (phaseId) {
      case 'voice_generation':
        if (audioSegments) {
          return `${audioSegments} audio segments`;
        }
        break;
      case 'audio_timing':
        if (audioDuration) {
          return `${audioDuration.toFixed(2)}s narration`;
        }
        break;
      case 'scene_generation':
        if (beatCount) {
          return `${beatCount} beats`;
        }
        break;
    }
    
    return undefined;
  };
  
  return (
    <div className="workflow-status">
      <div className="workflow-status-header">
        <h3>
          {status === 'completed' ? 'Video Generation Complete' : 'Generating Your Video'}
        </h3>
        {status === 'failed' && (
          <div className="workflow-error">
            <strong>Generation Failed</strong>
            {error && <p>{error}</p>}
          </div>
        )}
      </div>
      
      <div className="workflow-phases">
        {phases.map((phase) => {
          const phaseStatus = getPhaseStatus(phase.id);
          const phaseDetails = getPhaseDetails(phase.id);
          
          return (
            <div
              key={phase.id}
              className={`workflow-phase workflow-phase-${phaseStatus}`}
            >
              <div className="workflow-phase-icon">
                {getPhaseIcon(phaseStatus)}
              </div>
              <div className="workflow-phase-content">
                <div className="workflow-phase-label">{phase.label}</div>
                {phaseStatus === 'active' && (
                  <div className="workflow-phase-message">{message}</div>
                )}
                {phaseDetails && (
                  <div className="workflow-phase-details">{phaseDetails}</div>
                )}
              </div>
            </div>
          );
        })}
      </div>
      
      {status === 'running' && (
        <div className="workflow-current-status">
          <div className="workflow-spinner" />
          <span>{phaseLabel}: {message}</span>
        </div>
      )}
    </div>
  );
};
