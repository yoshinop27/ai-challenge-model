import { useState } from 'react'

function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 ** 2) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 ** 2).toFixed(1)} MB`
}

function validate(fields, file, uploadType) {
  const errors = {}
  const farmSize = Number(fields.farmSize)
  const lat = Number(fields.lat)
  const lng = Number(fields.lng)

  if (!fields.farmSize || Number.isNaN(farmSize) || farmSize <= 0) {
    errors.farmSize = 'Enter a valid farm size (acres)'
  }
  if (!fields.lat || Number.isNaN(lat) || Math.abs(lat) > 90) {
    errors.lat = 'Enter a valid latitude (-90 to 90)'
  }
  if (!fields.lng || Number.isNaN(lng) || Math.abs(lng) > 180) {
    errors.lng = 'Enter a valid longitude (-180 to 180)'
  }
  if (!file) {
    errors.file = uploadType === 'tabular' ? 'Upload a CSV file' : 'Upload a soil image'
  }

  return errors
}

export default function App() {
  const [fields, setFields] = useState({ farmSize: '', lat: '', lng: '' })
  const [file, setFile] = useState(null)
  const [uploadType, setUploadType] = useState('image')
  const [errors, setErrors] = useState({})
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  const handleFieldChange = (name) => (event) => {
    setFields((current) => ({ ...current, [name]: event.target.value }))
  }

  const handleTypeChange = (event) => {
    setUploadType(event.target.value)
    setFile(null)
    setResult(null)
    setErrors({})
  }

  const handleFileChange = (event) => {
    setFile(event.target.files[0] || null)
    setResult(null)
  }

  const removeFile = () => {
    setFile(null)
    setResult(null)
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    const nextErrors = validate(fields, file, uploadType)
    setErrors(nextErrors)
    if (Object.keys(nextErrors).length > 0) return

    setLoading(true)
    setResult(null)
    try {
      const body = new FormData()
      body.append('file', file)
      body.append('type', uploadType)
      const response = await fetch('http://localhost:8000/predict', { method: 'POST', body })
      if (!response.ok) {
        const err = await response.json().catch(() => ({}))
        throw new Error(err.detail || `Server error: ${response.status}`)
      }
      setResult(await response.json())
    } catch (err) {
      setErrors({ submit: err.message })
    } finally {
      setLoading(false)
    }
  }

  const fileAccept = uploadType === 'tabular' ? '.csv' : 'image/*'
  const fileLabel = uploadType === 'tabular' ? 'Tabular Data (CSV)' : 'Soil Image'

  return (
    <div className="page">
      <div className="card">
        <h1 className="card-title">Farm Submission</h1>
        <p className="card-subtitle">Provide your farm details and upload a soil file</p>

        <form onSubmit={handleSubmit} noValidate>
          <div className="field">
            <label className="field-label" htmlFor="farm-size">Farm Size (acres)</label>
            <input
              id="farm-size"
              className={`input${errors.farmSize ? ' error' : ''}`}
              type="number"
              min="0"
              step="any"
              placeholder="e.g. 250"
              value={fields.farmSize}
              onChange={handleFieldChange('farmSize')}
              aria-invalid={Boolean(errors.farmSize)}
              aria-describedby={errors.farmSize ? 'farm-size-error' : undefined}
            />
            {errors.farmSize && <p id="farm-size-error" className="field-error">{errors.farmSize}</p>}
          </div>

          <div className="row">
            <div className="field">
              <label className="field-label" htmlFor="latitude">Latitude</label>
              <input
                id="latitude"
                className={`input${errors.lat ? ' error' : ''}`}
                type="number"
                step="any"
                placeholder="e.g. 41.8781"
                value={fields.lat}
                onChange={handleFieldChange('lat')}
                aria-invalid={Boolean(errors.lat)}
                aria-describedby={errors.lat ? 'latitude-error' : undefined}
              />
              {errors.lat && <p id="latitude-error" className="field-error">{errors.lat}</p>}
            </div>
            <div className="field">
              <label className="field-label" htmlFor="longitude">Longitude</label>
              <input
                id="longitude"
                className={`input${errors.lng ? ' error' : ''}`}
                type="number"
                step="any"
                placeholder="e.g. -87.6298"
                value={fields.lng}
                onChange={handleFieldChange('lng')}
                aria-invalid={Boolean(errors.lng)}
                aria-describedby={errors.lng ? 'longitude-error' : undefined}
              />
              {errors.lng && <p id="longitude-error" className="field-error">{errors.lng}</p>}
            </div>
          </div>

          <div className="field">
            <span className="field-label">Upload Type</span>
            <div className="radio-group">
              <label className="radio-label">
                <input
                  type="radio"
                  name="uploadType"
                  value="image"
                  checked={uploadType === 'image'}
                  onChange={handleTypeChange}
                />
                Image
              </label>
              <label className="radio-label">
                <input
                  type="radio"
                  name="uploadType"
                  value="tabular"
                  checked={uploadType === 'tabular'}
                  onChange={handleTypeChange}
                />
                Tabular Data (CSV)
              </label>
            </div>
          </div>

          <div className="field">
            <label className="field-label" htmlFor="file">{fileLabel}</label>
            <input
              id="file"
              className={`input${errors.file ? ' error' : ''}`}
              type="file"
              accept={fileAccept}
              onChange={handleFileChange}
              aria-invalid={Boolean(errors.file)}
              aria-describedby={errors.file ? 'file-error' : undefined}
            />
            {errors.file && <p id="file-error" className="field-error">{errors.file}</p>}
          </div>

          {file && (
            <ul className="file-list">
              <li className="file-item">
                <span className="file-name">{file.name}</span>
                <span className="file-size">{formatSize(file.size)}</span>
                <button className="file-remove" type="button" title="Remove" onClick={removeFile}>x</button>
              </li>
            </ul>
          )}

          {errors.submit && <p className="field-error">{errors.submit}</p>}

          <button type="submit" className="submit-btn" disabled={loading}>
            {loading ? 'Analyzing...' : 'Submit'}
          </button>
        </form>

        {result && (
          <div className="result">
            <h2 className="result-label">Soil Type: <strong>{result.label.toUpperCase()}</strong></h2>
            <ul className="confidence-list">
              {Object.entries(result.confidence).map(([label, score]) => (
                <li key={label} className="confidence-item">
                  <span className="confidence-label">{label}</span>
                  <div className="confidence-bar-track">
                    <div className="confidence-bar-fill" style={{ width: `${(score * 100).toFixed(1)}%` }} />
                  </div>
                  <span className="confidence-score">{(score * 100).toFixed(1)}%</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  )
}
