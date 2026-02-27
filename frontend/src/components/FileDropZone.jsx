import { useState } from 'react'
import { formatSize } from '../utils/formatSize'

export default function FileDropZone({ files, onChange }) {
  const [dragging, setDragging] = useState(false)

  const addFiles = (incoming) => {
    const list = Array.from(incoming)
    onChange((prev) => [
      ...prev,
      ...list.filter((f) => !prev.some((p) => p.name === f.name && p.size === f.size)),
    ])
  }

  const onDrop = (e) => {
    e.preventDefault()
    setDragging(false)
    addFiles(e.dataTransfer.files)
  }

  const removeFile = (index) =>
    onChange((prev) => prev.filter((_, i) => i !== index))

  return (
    <div>
      <label
        className={`dropzone${dragging ? ' dragging' : ''}`}
        onDrop={onDrop}
        onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
      >
        <input type="file" multiple style={{ display: 'none' }} onChange={(e) => addFiles(e.target.files)} />
        <svg className="dropzone-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
          <path strokeLinecap="round" strokeLinejoin="round"
            d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
        </svg>
        <p className="dropzone-text">{dragging ? 'Release to drop' : 'Drop files here or click to browse'}</p>
        <p className="dropzone-hint">Any file type accepted</p>
      </label>

      {files.length > 0 && (
        <ul className="file-list">
          {files.map((file, i) => (
            <li key={i} className="file-item">
              <span className="file-name">{file.name}</span>
              <span className="file-size">{formatSize(file.size)}</span>
              <button className="file-remove" type="button" title="Remove" onClick={() => removeFile(i)}>✕</button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
