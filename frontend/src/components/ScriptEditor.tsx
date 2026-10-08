import './ScriptEditor.css'

interface ScriptEditorProps {
  value: string
  onChange: (value: string) => void
}

function ScriptEditor({ value, onChange }: ScriptEditorProps) {
  const placeholder = `from manimlib import *

class LinearSearch(Scene):
    def construct(self):
        # Your animation code here
        title = Text("Linear Search")
        self.play(Write(title))
        self.wait(2)
        self.play(FadeOut(title))
`

  return (
    <div className="script-editor-group">
      <label className="input-label">Paste your ManimGL Python Script</label>
      <textarea
        className="script-editor"
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        spellCheck={false}
      />
      <p className="editor-hint">
        ⚠️ Your script must be valid ManimGL Python code with a Scene class
      </p>
    </div>
  )
}

export default ScriptEditor
