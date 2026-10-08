import './GenerateButton.css'

interface GenerateButtonProps {
  onClick: () => void
  disabled: boolean
  label: string
}

function GenerateButton({ onClick, disabled, label }: GenerateButtonProps) {
  return (
    <div className="generate-section">
      <button
        className="generate-button"
        onClick={onClick}
        disabled={disabled}
      >
        <span className="button-icon">🎬</span>
        <span className="button-text">{label}</span>
      </button>
      {disabled && (
        <p className="button-hint">
          Please fill in all required fields
        </p>
      )}
    </div>
  )
}

export default GenerateButton
