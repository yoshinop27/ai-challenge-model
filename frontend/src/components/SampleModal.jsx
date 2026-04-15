import { useState, useRef } from 'react'
import { fetchWithTimeout } from '../utils/api'

export default function SampleModal({ point, crops = [], onResult, onClose }) {
  const cardRef = useRef(null)
  const [uploadType, setUploadType] = useState('image')
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (loading) return
    if (!file) { setError('Please select a file'); return }

    setLoading(true)
    setError(null)
    try {
      const body = new FormData()
      body.append('file', file)
      body.append('type', uploadType)
      if (crops.length > 0) body.append('crops', crops.join(','))
      const resp = await fetchWithTimeout('/api/predict', { method: 'POST', body })
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}))
        throw new Error(err.detail || `Server error: ${resp.status}`)
      }
      onResult(await resp.json())
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="modal-overlay" onClick={(e) => { if (!loading && cardRef.current && !cardRef.current.contains(e.target)) onClose() }}>
      <div className="modal-card" ref={cardRef}>
        <div className="modal-header">
          <div>
            <h2 className="modal-title">Add Soil Sample</h2>
            <p className="modal-coords">
              {point.lat.toFixed(5)}, {point.lng.toFixed(5)}
            </p>
            {crops.length > 0
              ? <p className="modal-crops-hint">Analyzing for: {crops.join(', ')}</p>
              : <p className="field-error">Add crops in the panel before analyzing</p>
            }
          </div>
          <button className="modal-close" onClick={onClose} disabled={loading}>×</button>
        </div>

        <form onSubmit={handleSubmit} noValidate>
          <div className="field">
            <span className="field-label">Upload Type</span>
            <div className="radio-group">
              <label className="radio-label">
                <input
                  type="radio"
                  name="modal-type"
                  value="image"
                  checked={uploadType === 'image'}
                  onChange={() => { setUploadType('image'); setFile(null); setError(null) }}
                />
                Soil Image
              </label>
              <label className="radio-label">
                <input
                  type="radio"
                  name="modal-type"
                  value="tabular"
                  checked={uploadType === 'tabular'}
                  onChange={() => { setUploadType('tabular'); setFile(null); setError(null) }}
                />
                Tabular (CSV)
              </label>
            </div>
          </div>

          <div className="field">
            <label className="field-label" htmlFor="modal-file">
              {uploadType === 'image' ? 'Soil Image' : 'CSV File'}
            </label>
            <input
              id="modal-file"
              className="input"
              type="file"
              accept={uploadType === 'image' ? 'image/*' : '.csv'}
              onChange={(e) => { setFile(e.target.files[0] || null); setError(null) }}
            />
          </div>

          {error && <p className="field-error">{error}</p>}

          <div className="modal-actions">
            <button type="button" className="cancel-btn" onClick={onClose} disabled={loading}>
              Cancel
            </button>
            <button type="submit" className="submit-btn modal-submit" disabled={loading || !file || crops.length === 0}>
              {loading ? 'Analyzing...' : 'Analyze'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
