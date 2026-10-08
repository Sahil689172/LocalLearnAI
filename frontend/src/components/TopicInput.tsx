import './TopicInput.css'

interface TopicInputProps {
  value: string
  onChange: (value: string) => void
}

function TopicInput({ value, onChange }: TopicInputProps) {
  return (
    <div className="input-group">
      <label className="input-label">Topic</label>
      <input
        type="text"
        className="topic-input"
        placeholder='Enter your topic... (e.g., "Linear Search")'
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
      <p className="input-hint">
        Examples: "Binary Search", "Insertion Sort", "Quick Sort"
      </p>
    </div>
  )
}

export default TopicInput
