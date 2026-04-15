import { useState } from 'react'
import CropPanel from './CropPanel'

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
  const [cropError, setCropError] = useState(null)

  const handleChange = (name) => (e) =>
    setFields((prev) => ({ ...prev, [name]: e.target.value }))

  const handleSubmit = (e) => {
    e.preventDefault()
    const errs = validate(fields)
    setErrors(errs)
    const cropErr = crops.length === 0 ? 'Add at least one crop of interest' : null
    setCropError(cropErr)
    if (Object.keys(errs).length > 0 || cropErr) return
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
            <label className="field-label">Crops of Interest</label>
            <CropPanel crops={crops} onChange={(c) => { setCrops(c); if (c.length > 0) setCropError(null) }} />
            {cropError && <p className="field-error">{cropError}</p>}
          </div>

          <button type="submit" className="submit-btn">View My Farm</button>
        </form>
      </div>
    </div>
  )
}
