import { useState } from 'react'
import FarmSetup from './components/FarmSetup'
import FarmMap, { SOIL_COLORS } from './components/FarmMap'
import SampleModal from './components/SampleModal'

export default function App() {
  const [farm, setFarm] = useState(null)
  const [samples, setSamples] = useState([])
  const [pendingPoint, setPendingPoint] = useState(null)

  const handleMapClick = (lat, lng) => {
    setPendingPoint({ lat, lng })
  }

  const handleSampleResult = (result) => {
    setSamples((prev) => [
      ...prev,
      {
        id: `${Date.now()}`,
        lat: pendingPoint.lat,
        lng: pendingPoint.lng,
        result,
      },
    ])
    setPendingPoint(null)
  }

  const handleReset = () => {
    setFarm(null)
    setSamples([])
    setPendingPoint(null)
  }

  if (!farm) {
    return <FarmSetup onSubmit={setFarm} />
  }

  // Unique soil types found across all samples
  const foundTypes = [...new Set(samples.map((s) => s.result.label))]

  return (
    <div className="map-page">
      <div className="map-topbar">
        <div className="topbar-info">
          <span className="topbar-title">Your Farm</span>
          <span className="topbar-meta">
            {farm.farmSize} acres &middot; {farm.lat.toFixed(4)}, {farm.lng.toFixed(4)}
          </span>
        </div>
        <div className="topbar-right">
          {samples.length > 0 && (
            <span className="topbar-count">{samples.length} sample{samples.length !== 1 ? 's' : ''}</span>
          )}
          <button className="reset-btn" onClick={handleReset}>Change Farm</button>
        </div>
      </div>

      <div className="map-wrapper">
        <FarmMap farm={farm} samples={samples} onMapClick={handleMapClick} />
        {samples.length === 0 && (
          <div className="map-hint">Click anywhere on your farm to add a soil sample</div>
        )}
      </div>

      {foundTypes.length > 0 && (
        <div className="legend">
          {foundTypes.map((label) => (
            <div key={label} className="legend-item">
              <span className="legend-dot" style={{ background: SOIL_COLORS[label] ?? '#6366f1' }} />
              <span className="legend-label">{label}</span>
            </div>
          ))}
        </div>
      )}

      {pendingPoint && (
        <SampleModal
          point={pendingPoint}
          onResult={handleSampleResult}
          onClose={() => setPendingPoint(null)}
        />
      )}
    </div>
  )
}
