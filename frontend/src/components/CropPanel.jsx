import { useState } from 'react'

export default function CropPanel({ crops, onChange }) {
  const [input, setInput] = useState('')

  const add = () => {
    const val = input.trim()
    if (!val || crops.includes(val)) { setInput(''); return }
    onChange([...crops, val])
    setInput('')
  }

  const remove = (crop) => onChange(crops.filter((c) => c !== crop))

  const handleKey = (e) => {
    if (e.key === 'Enter') { e.preventDefault(); add() }
  }

  return (
    <div className="crop-panel">
      <div className="crop-input-row">
        <input
          className="crop-input"
          placeholder="e.g. Cotton"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKey}
        />
        <button className="crop-add-btn" onClick={add} type="button">+</button>
      </div>
      {crops.length > 0 && (
        <div className="crop-chips">
          {crops.map((c) => (
            <span key={c} className="crop-chip">
              {c}
              <button className="crop-chip-remove" onClick={() => remove(c)} type="button">×</button>
            </span>
          ))}
        </div>
      )}
    </div>
  )
}
