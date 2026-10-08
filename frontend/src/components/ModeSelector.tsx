import './ModeSelector.css'

type Mode = 'topic' | 'script'

interface ModeSelectorProps {
  onSelectMode: (mode: Mode) => void
}

function ModeSelector({ onSelectMode }: ModeSelectorProps) {
  return (
    <div className="mode-selector">
      <div className="mode-cards">
        <button 
          className="mode-card"
          onClick={() => onSelectMode('topic')}
        >
          <div className="mode-icon">✨</div>
          <h2 className="mode-title">Enter Topic</h2>
          <p className="mode-description">
            Let LocalLearn AI create the lesson and animation
          </p>
          <div className="mode-example">
            Example: "Linear Search"
          </div>
        </button>

        <button 
          className="mode-card"
          onClick={() => onSelectMode('script')}
        >
          <div className="mode-icon">📝</div>
          <h2 className="mode-title">Custom Python Script</h2>
          <p className="mode-description">
            Paste your own ManimGL animation script
          </p>
          <div className="mode-example">
            Use your own Python code
          </div>
        </button>
      </div>
    </div>
  )
}

export default ModeSelector
