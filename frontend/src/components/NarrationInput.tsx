/**
 * NarrationInput Component
 * 
 * Text area for entering narration text for custom scripts.
 * Narration is synthesized using Piper TTS and synchronized with video.
 */

import './NarrationInput.css'

interface NarrationInputProps {
  value: string
  onChange: (value: string) => void
}

function NarrationInput({ value, onChange }: NarrationInputProps) {
  return (
    <div className="narration-input-group">
      <label className="input-label">
        Narration (Optional)
      </label>
      <textarea
        className="narration-input"
        placeholder="Enter narration text to be spoken during your animation (optional)&#10;&#10;Example:&#10;Linear search is a simple algorithm that checks each element sequentially. It starts at the beginning and compares each element with the target value until a match is found."
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
      <p className="input-hint">
        💡 Leave empty for silent video, or add narration to be synthesized with Piper TTS
      </p>
    </div>
  )
}

export default NarrationInput
