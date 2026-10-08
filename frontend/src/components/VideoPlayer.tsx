/**
 * VideoPlayer Component
 * 
 * Displays the completed video with metadata.
 */

import React from 'react';
import './VideoPlayer.css';
import { getVideoDownloadUrl } from '../services/api';

interface VideoPlayerProps {
  jobId: string;
  mode: 'topic' | 'custom_script';
  duration?: number | null;
  language: string;
}

const LANGUAGE_NAMES: Record<string, string> = {
  en: 'English',
  hi: 'Hindi',
  te: 'Telugu',
};

export const VideoPlayer: React.FC<VideoPlayerProps> = ({
  jobId,
  mode,
  duration,
  language,
}) => {
  const videoUrl = getVideoDownloadUrl(jobId);
  const modeLabel = mode === 'topic' ? 'Topic Mode' : 'Custom Script';
  const languageName = LANGUAGE_NAMES[language] || language;

  return (
    <div className="video-player">
      <div className="video-player-header">
        <h3>Generated Video</h3>
      </div>

      <div className="video-player-container">
        <video controls className="video-player-element">
          <source src={videoUrl} type="video/mp4" />
          Your browser does not support the video tag.
        </video>
      </div>

      <div className="video-player-metadata">
        <div className="video-metadata-item">
          <span className="video-metadata-label">Status:</span>
          <span className="video-metadata-value">Complete</span>
        </div>
        <div className="video-metadata-item">
          <span className="video-metadata-label">Mode:</span>
          <span className="video-metadata-value">{modeLabel}</span>
        </div>
        <div className="video-metadata-item">
          <span className="video-metadata-label">Language:</span>
          <span className="video-metadata-value">{languageName}</span>
        </div>
        {duration && (
          <div className="video-metadata-item">
            <span className="video-metadata-label">Duration:</span>
            <span className="video-metadata-value">{duration.toFixed(1)}s</span>
          </div>
        )}
      </div>

      <div className="video-player-actions">
        <a
          href={videoUrl}
          download={`locallearn_${mode}_${jobId.slice(0, 8)}.mp4`}
          className="video-download-button"
        >
          Download Video
        </a>
      </div>
    </div>
  );
};
