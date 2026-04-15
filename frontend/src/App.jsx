import { useState, useRef } from 'react'
import LandingPage from './components/LandingPage'
import FarmSetup from './components/FarmSetup'
import FarmMap from './components/FarmMap'
import SampleModal from './components/SampleModal'
import FarmTimelineModal from './components/FarmTimelineModal'
import { SOIL_COLORS, MOISTURE_COLORS, FALLBACK_COLOR } from './utils/constants'
import { fetchWithTimeout } from './utils/api'

const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN

async function fetchSatelliteBase64(bounds) {
  const { west, south, east, north } = bounds
  const bbox = `[${west},${south},${east},${north}]`
  const url = `https://api.mapbox.com/styles/v1/mapbox/satellite-v9/static/${bbox}/600x600?access_token=${MAPBOX_TOKEN}`
  const resp = await fetch(url)
  if (!resp.ok) return null
  const blob = await resp.blob()
  return new Promise((resolve) => {
    const reader = new FileReader()
    reader.onloadend = () => resolve(reader.result.split(',')[1])
    reader.readAsDataURL(blob)
  })
}

export default function App() {
  const [showLanding, setShowLanding] = useState(true)
  const [farm, setFarm] = useState(null)
  const [samples, setSamples] = useState([])
  const [pendingPoint, setPendingPoint] = useState(null)
  const [crops, setCrops] = useState([])
  const [farmAnalysis, setFarmAnalysis] = useState(null)
  const [farmTimeline, setFarmTimeline] = useState(null)
  const [showTimeline, setShowTimeline] = useState(false)
  const [analyzingFarm, setAnalyzingFarm] = useState(false)
  const [analysisError, setAnalysisError] = useState(null)
  const getBoundsRef = useRef(null)

  const handleSampleResult = (result) => {
    setSamples((prev) => [
      ...prev,
      { id: `${Date.now()}`, lat: pendingPoint.lat, lng: pendingPoint.lng, result },
    ])
    setPendingPoint(null)
  }

  const handleReset = () => {
    setFarm(null)
    setSamples([])
    setPendingPoint(null)
    setCrops([])
    setFarmAnalysis(null)
    setFarmTimeline(null)
    setShowTimeline(false)
    setAnalysisError(null)
  }

  const handleAnalyzeFarm = async () => {
    if (analyzingFarm) return

    setAnalyzingFarm(true)
    setAnalysisError(null)
    try {
      const bounds = getBoundsRef.current?.()
      const satellite_b64 = bounds ? await fetchSatelliteBase64(bounds) : null
      const resp = await fetchWithTimeout('/analyze-farm', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ farm, samples, crops, satellite_b64, bounds }),
      })
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}))
        throw new Error(err.detail || `Server error: ${resp.status}`)
      }
      const data = await resp.json()
      const timeline = data['__timeline__'] ?? null
      const { '__timeline__': _tl, ...cropAnalysis } = data
      setFarmTimeline(timeline)
      setFarmAnalysis(cropAnalysis)
    } catch (err) {
      setAnalysisError(err.message)
    } finally {
      setAnalyzingFarm(false)
    }
  }

  if (showLanding) {
    return <LandingPage onEnter={() => setShowLanding(false)} />
  }

  if (!farm) {
    return (
      <FarmSetup
        onSubmit={(data) => {
          const { crops: initialCrops = [], ...farmData } = data
          setCrops(initialCrops)
          setFarm(farmData)
        }}
      />
    )
  }

  const foundSoilTypes = [...new Set(samples.map((s) => s.result.soil?.label).filter(Boolean))]
  const foundMoistureTypes = [...new Set(samples.map((s) => s.result.moisture?.label).filter(Boolean))]

  const renderLegendGroup = (groupLabel, labels, colors, prefix) =>
    labels.length > 0 && (
      <>
        <span className="legend-group-label">{groupLabel}</span>
        {labels.map((label) => (
          <div key={`${prefix}-${label}`} className="legend-item">
            <span className="legend-dot" style={{ background: colors[label] ?? FALLBACK_COLOR }} />
            <span className="legend-label">{label}</span>
          </div>
        ))}
      </>
    )

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
          {farmTimeline && (
            <button className="timeline-btn" onClick={() => setShowTimeline(true)}>
              📅 Farm Timeline
            </button>
          )}
          {samples.length >= 3 && (
            <button
              className="analyze-btn"
              onClick={handleAnalyzeFarm}
              disabled={analyzingFarm}
            >
              {analyzingFarm ? 'Analyzing…' : farmAnalysis ? 'Re-analyze Farm' : 'Analyze Farm'}
            </button>
          )}
          <button className="reset-btn" onClick={handleReset}>Change Farm</button>
        </div>
      </div>

      <div className="map-wrapper">
        <FarmMap farm={farm} samples={samples} farmAnalysis={farmAnalysis} onMapClick={(lat, lng) => setPendingPoint({ lat, lng })} onMapReady={(fn) => { getBoundsRef.current = fn }} />
        {samples.length === 0 && (
          <div className="map-hint">Click anywhere on your farm to add a soil sample</div>
        )}
        {analysisError && (
          <div className="map-hint" style={{ color: '#ef4444' }}>Analysis failed: {analysisError}</div>
        )}
      </div>

      {(foundSoilTypes.length > 0 || foundMoistureTypes.length > 0) && (
        <div className="legend">
          {renderLegendGroup('Condition:', foundSoilTypes, SOIL_COLORS, 'soil')}
          {renderLegendGroup('Moisture:', foundMoistureTypes, MOISTURE_COLORS, 'moisture')}
        </div>
      )}

      {pendingPoint && (
        <SampleModal
          point={pendingPoint}
          crops={crops}
          onResult={handleSampleResult}
          onClose={() => setPendingPoint(null)}
        />
      )}

      {showTimeline && (
        <FarmTimelineModal
          timeline={farmTimeline}
          onClose={() => setShowTimeline(false)}
        />
      )}
    </div>
  )
}
