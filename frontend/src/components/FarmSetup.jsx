import { useState } from 'react'

function validate(fields) {
  const errors = {}
  const farmSize = Number(fields.farmSize)
  const lat = Number(fields.lat)
  const lng = Number(fields.lng)

  if (!fields.farmSize || Number.isNaN(farmSize) || farmSize <= 0)
    errors.farmSize = 'Enter a valid farm size (acres)'
  if (!fields.lat || Number.isNaN(lat) || Math.abs(lat) > 90)
    errors.lat = 'Enter a valid latitude (-90 to 90)'
  if (!fields.lng || Number.isNaN(lng) || Math.abs(lng) > 180)
    errors.lng = 'Enter a valid longitude (-180 to 180)'

  return errors
}

export default function FarmSetup({ onSubmit }) {
  const [fields, setFields] = useState({ farmSize: '', lat: '', lng: '' })
  const [errors, setErrors] = useState({})
  const [crops, setCrops] = useState([])
  const [cropInput, setCropInput] = useState('')

  const handleChange = (name) => (e) =>
    setFields((prev) => ({ ...prev, [name]: e.target.value }))

  const addCrop = () => {
    const val = cropInput.trim()
    if (!val || crops.includes(val)) { setCropInput(''); return }
    setCrops((prev) => [...prev, val])
    setCropInput('')
  }

  const removeCrop = (crop) => setCrops((prev) => prev.filter((c) => c !== crop))

  const handleCropKey = (e) => {
    if (e.key === 'Enter') { e.preventDefault(); addCrop() }
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    const errs = validate(fields)
    setErrors(errs)
    if (Object.keys(errs).length > 0) return
    onSubmit({
      lat: Number(fields.lat),
      lng: Number(fields.lng),
      farmSize: Number(fields.farmSize),
      crops,
    })
  }

  return (
    <div className="page">
      <div className="card">
        <h1 className="card-title">Your Farm</h1>
        <p className="card-subtitle">Enter your farm location to get started</p>

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
              onChange={handleChange('farmSize')}
            />
            {errors.farmSize && <p className="field-error">{errors.farmSize}</p>}
          </div>

          <div className="row">
            <div className="field">
              <label className="field-label" htmlFor="lat">Latitude</label>
              <input
                id="lat"
                className={`input${errors.lat ? ' error' : ''}`}
                type="number"
                step="any"
                placeholder="e.g. 41.8781"
                value={fields.lat}
                onChange={handleChange('lat')}
              />
              {errors.lat && <p className="field-error">{errors.lat}</p>}
            </div>
            <div className="field">
              <label className="field-label" htmlFor="lng">Longitude</label>
              <input
                id="lng"
                className={`input${errors.lng ? ' error' : ''}`}
                type="number"
                step="any"
                placeholder="e.g. -87.6298"
                value={fields.lng}
                onChange={handleChange('lng')}
              />
              {errors.lng && <p className="field-error">{errors.lng}</p>}
            </div>
          </div>

          <div className="field">
            <label className="field-label" htmlFor="setup-crop">Crops of Interest (optional)</label>
            <div className="crop-input-row">
              <input
                id="setup-crop"
                className="crop-input"
                placeholder="e.g. Cotton"
                value={cropInput}
                onChange={(e) => setCropInput(e.target.value)}
                onKeyDown={handleCropKey}
              />
              <button className="crop-add-btn" onClick={addCrop} type="button">+</button>
            </div>
            {crops.length > 0 && (
              <div className="crop-chips">
                {crops.map((c) => (
                  <span key={c} className="crop-chip">
                    {c}
                    <button className="crop-chip-remove" onClick={() => removeCrop(c)} type="button">×</button>
                  </span>
                ))}
              </div>
            )}
          </div>

          <button type="submit" className="submit-btn">View My Farm</button>
        </form>
      </div>
    </div>
  )
}
