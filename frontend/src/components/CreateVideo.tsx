import { useState, useEffect, useRef } from 'react'
import './CreateVideo.css'
import ModeSelector from './ModeSelector'
import TopicInput from './TopicInput'
import ScriptEditor from './ScriptEditor'
import NarrationInput from './NarrationInput'
import LanguageSelector from './LanguageSelector'
import GenerateButton from './GenerateButton'
import { WorkflowStatus } from './WorkflowStatus'
import { VideoPlayer } from './VideoPlayer'
import { generateVideo, getJobStatus, type JobStatusResponse } from '../services/api'
import { STATUS_POLL_INTERVAL } from '../config/api'

type Mode = 'topic' | 'script' | null

function CreateVideo() {
  const [mode, setMode] = useState<Mode>(null)
  const [topic, setTopic] = useState('')
  const [script, setScript] = useState('')
  const [narration, setNarration] = useState('')
  const [language, setLanguage] = useState('en')
  
  // Generation state
  const [isGenerating, setIsGenerating] = useState(false)
  const [jobId, setJobId] = useState<string | null>(null)
  const [jobStatus, setJobStatus] = useState<JobStatusResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  
  const pollIntervalRef = useRef<number | null>(null)

  // Poll job status
  useEffect(() => {
    if (!jobId || !isGenerating) return

    const poll = async () => {
      try {
        const status = await getJobStatus(jobId)
        setJobStatus(status)
        
        // Stop polling when complete or failed
        if (status.status === 'completed' || status.status === 'failed') {
          setIsGenerating(false)
          if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current)
            pollIntervalRef.current = null
          }
          
          if (status.status === 'failed') {
            setError(status.error || 'Video generation failed')
          }
        }
      } catch (err) {
        console.error('Failed to poll job status:', err)
        setError(err instanceof Error ? err.message : 'Failed to get job status')
        setIsGenerating(false)
        if (pollIntervalRef.current) {
          clearInterval(pollIntervalRef.current)
          pollIntervalRef.current = null
        }
      }
    }

    // Poll immediately and then on interval
    poll()
    pollIntervalRef.current = window.setInterval(poll, STATUS_POLL_INTERVAL)

    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current)
        pollIntervalRef.current = null
      }
    }
  }, [jobId, isGenerating])

  const handleGenerate = async () => {
    setError(null)
    setJobStatus(null)
    setIsGenerating(true)
    
    try {
      const request = mode === 'topic'
        ? { mode: 'topic' as const, topic, language }
        : { mode: 'custom_script' as const, script, narration, language }
      
      const response = await generateVideo(request)
      setJobId(response.job_id)
    } catch (err) {
      console.error('Failed to start video generation:', err)
      setError(err instanceof Error ? err.message : 'Failed to start video generation')
      setIsGenerating(false)
    }
  }

  const handleReset = () => {
    setMode(null)
    setTopic('')
    setScript('')
    setNarration('')
    setLanguage('en')
    setIsGenerating(false)
    setJobId(null)
    setJobStatus(null)
    setError(null)
    
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current)
      pollIntervalRef.current = null
    }
  }

  const canGenerate = mode === 'topic' ? topic.trim().length > 0 : script.trim().length > 0

  return (
    <div className="create-video">
      <header className="hero">
        <h1 className="title">LocalLearn AI</h1>
        <p className="subtitle">Create educational videos with AI + Manim</p>
      </header>

      {!mode ? (
        <ModeSelector onSelectMode={setMode} />
      ) : (
        <>
          <div className="video-form">
            <button 
              className="back-button" 
              onClick={handleReset}
              disabled={isGenerating}
            >
              ← {jobStatus?.status === 'completed' ? 'Create Another Video' : 'Change Mode'}
            </button>

            {mode === 'topic' && !isGenerating && !jobStatus && (
              <>
                <TopicInput value={topic} onChange={setTopic} />
                <LanguageSelector value={language} onChange={setLanguage} />
                <GenerateButton 
                  onClick={handleGenerate} 
                  disabled={!canGenerate || isGenerating}
                  label="Generate Video"
                />
              </>
            )}

            {mode === 'script' && !isGenerating && !jobStatus && (
              <>
                <ScriptEditor value={script} onChange={setScript} />
                <NarrationInput value={narration} onChange={setNarration} />
                <LanguageSelector value={language} onChange={setLanguage} />
                <GenerateButton 
                  onClick={handleGenerate} 
                  disabled={!canGenerate || isGenerating}
                  label="Render Video"
                />
              </>
            )}
            
            {error && !jobStatus && (
              <div className="error-message">
                <strong>Error:</strong> {error}
              </div>
            )}
          </div>

          {jobStatus && (
            <WorkflowStatus
              mode={mode === 'topic' ? 'topic' : 'custom_script'}
              currentPhase={jobStatus.phase}
              phaseLabel={jobStatus.phase_label}
              message={jobStatus.message}
              status={jobStatus.status}
              error={jobStatus.error}
              beatCount={jobStatus.beat_count}
              audioSegments={jobStatus.audio_segments}
              audioDuration={jobStatus.audio_duration}
            />
          )}

          {jobStatus?.status === 'completed' && jobId && (
            <VideoPlayer
              jobId={jobId}
              mode={mode === 'topic' ? 'topic' : 'custom_script'}
              duration={jobStatus.duration}
              language={language}
            />
          )}
        </>
      )}
    </div>
  )
}

export default CreateVideo
