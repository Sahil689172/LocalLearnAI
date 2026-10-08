import './LanguageSelector.css'

interface LanguageSelectorProps {
  value: string
  onChange: (value: string) => void
}

const languages = [
  { code: 'en', name: 'English' },
  { code: 'hi', name: 'Hindi' },
  { code: 'te', name: 'Telugu' },
]

function LanguageSelector({ value, onChange }: LanguageSelectorProps) {
  return (
    <div className="input-group">
      <label className="input-label">Language</label>
      <select
        className="language-select"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      >
        {languages.map((lang) => (
          <option key={lang.code} value={lang.code}>
            {lang.name}
          </option>
        ))}
      </select>
      <p className="input-hint">
        Choose the language for narration
      </p>
    </div>
  )
}

export default LanguageSelector
