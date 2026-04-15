import { useEffect, useRef, useState } from 'react'
import mapboxgl from 'mapbox-gl'
import 'mapbox-gl/dist/mapbox-gl.css'
import { SOIL_COLORS, MOISTURE_COLORS, FALLBACK_COLOR } from '../utils/constants'

mapboxgl.accessToken = import.meta.env.VITE_MAPBOX_TOKEN

function farmSizeToZoom(acres) {
  const z = 16 - Math.log2(Math.max(1, acres)) * 0.7
  return Math.min(17, Math.max(8, z))
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

function buildScoresHtml(confidence) {
  const e = escapeHtml
  return Object.entries(confidence)
    .sort(([, a], [, b]) => b - a)
    .map(([label, score]) =>
      `<span class="popup-row"><span>${e(label)}</span><span>${(score * 100).toFixed(1)}%</span></span>`
    )
    .join('')
}

function buildPopupHtml(sample, color) {
  const e = escapeHtml
  const result = sample.result

  // Tabular CSV result — flat {label, confidence} shape
  if (!result.soil) {
    const qualityColors = { good: '#4ade80', average: '#fbbf24', bad: '#f87171' }
    const labelColor = qualityColors[result.label] ?? color
    return `<div class="marker-popup">
      <span class="popup-section-title">Soil Quality (CSV)</span>
      <span class="popup-label" style="color:${e(labelColor)}">${e(result.label)}</span>
      <div class="popup-scores">${buildScoresHtml(result.confidence)}</div>
      <span class="popup-coords">${sample.lat.toFixed(5)}, ${sample.lng.toFixed(5)}</span>
    </div>`
  }

  // Image result — {soil, moisture, recommendations} shape
  const soil = result.soil
  const moisture = result.moisture
  const soilConf = (soil.confidence[soil.label] * 100).toFixed(1)

  const moistureHtml = moisture ? (() => {
    const moistureColor = MOISTURE_COLORS[moisture.label] ?? FALLBACK_COLOR
    const moistureConf = (moisture.confidence[moisture.label] * 100).toFixed(1)
    return `
      <span class="popup-section-title">Moisture</span>
      <span class="popup-label" style="color:${e(moistureColor)}">${e(moisture.label)}</span>
      <span class="popup-conf">${e(moistureConf)}% confidence</span>
      <div class="popup-scores">${buildScoresHtml(moisture.confidence)}</div>`
  })() : ''

  const rec = result.recommendations
  const recHtml = rec?.mode === 'targeted' && rec.crop_analysis?.length
    ? `<div class="popup-section">
      <p class="popup-summary">${e(rec.summary)}</p>
      <div class="popup-crop-analysis">${rec.crop_analysis.map((item) => `
      <div class="popup-analysis-row">
        <span class="popup-analysis-indicator ${item.suitable ? 'good' : 'avoid'}">${item.suitable ? '✓' : '✗'}</span>
        <div class="popup-analysis-detail">
          <span class="popup-analysis-crop">${e(item.crop)}</span>
          <span class="popup-analysis-reason">${e(item.reason)}</span>
        </div>
      </div>`).join('')}</div>
      <p class="popup-tip">${e(rec.tip)}</p>
    </div>`
    : ''

  return `<div class="marker-popup">
    <span class="popup-section-title">Soil Condition</span>
    <span class="popup-label" style="color:${e(color)}">${e(soil.label)}</span>
    <span class="popup-conf">${e(soilConf)}% confidence</span>
    <div class="popup-scores">${buildScoresHtml(soil.confidence)}</div>
    ${moistureHtml}
    ${recHtml}
    <span class="popup-coords">${sample.lat.toFixed(5)}, ${sample.lng.toFixed(5)}</span>
  </div>`
}

function getScoreAtPoint(lat, lng, cropData) {
  const { scores, coordinates } = cropData
  if (!scores || !coordinates) return null
  const lng_min = coordinates[0][0], lat_max = coordinates[0][1]
  const lng_max = coordinates[1][0], lat_min = coordinates[2][1]
  const n = scores.length
  const row = Math.round(((lat - lat_min) / (lat_max - lat_min)) * (n - 1))
  const col = Math.round(((lng - lng_min) / (lng_max - lng_min)) * (n - 1))
  const r = Math.max(0, Math.min(n - 1, row))
  const c = Math.max(0, Math.min(n - 1, col))
  return scores[r][c]
}

function buildSuitabilityHtml(crop, score, cropData, lat, lng) {
  const e = escapeHtml
  const pct = Math.round(score)
  const tier = pct >= 65 ? 'good' : pct >= 35 ? 'moderate' : 'poor'
  const tierColor = tier === 'good' ? '#4ade80' : tier === 'moderate' ? '#fbbf24' : '#f87171'
  const tierLabel = tier === 'good' ? 'Good Zone' : tier === 'moderate' ? 'Moderate Zone' : 'Poor Zone'
  const reason = tier === 'poor'
    ? (cropData.poor_reason || cropData.summary || '')
    : (cropData.good_reason || cropData.summary || '')
  return `<div class="suit-popup">
    <div class="suit-popup-head">
      <span class="suit-crop">${e(crop)}</span>
      <span class="suit-tier" style="color:${e(tierColor)}">${e(tierLabel)}</span>
    </div>
    <div class="suit-score-bar">
      <div class="suit-score-fill" style="width:${pct}%;background:${e(tierColor)}"></div>
    </div>
    <div class="suit-score-label">${pct}/100 suitability</div>
    ${reason ? `<p class="suit-reason">${e(reason)}</p>` : ''}
    <button class="suit-add-btn" id="suit-add-sample">+ Add Sample Here</button>
  </div>`
}

export default function FarmMap({ farm, samples, farmAnalysis, onMapClick, onMapReady }) {
  const containerRef = useRef(null)
  const mapRef = useRef(null)
  const markersRef = useRef({})
  const openPopupRef = useRef(null)
  const mapReadyRef = useRef(false)
  const farmAnalysisRef = useRef(null)
  const activeCropsRef = useRef({})
  const pendingClickRef = useRef(null)
  const [activeCrops, setActiveCrops] = useState({})

  useEffect(() => {
    const map = new mapboxgl.Map({
      container: containerRef.current,
      style: 'mapbox://styles/mapbox/satellite-streets-v12',
      center: [farm.lng, farm.lat],
      zoom: farmSizeToZoom(farm.farmSize),
    })

    map.addControl(new mapboxgl.NavigationControl(), 'top-right')
    map.getCanvas().style.cursor = 'crosshair'

    map.on('click', (e) => {
      const { lat, lng } = e.lngLat
      if (openPopupRef.current) { openPopupRef.current.remove(); openPopupRef.current = null }

      const analysis = farmAnalysisRef.current
      const crops = activeCropsRef.current
      const activeCrop = analysis && Object.entries(crops).find(([, v]) => v)?.[0]
      const cropData = activeCrop && analysis[activeCrop]

      if (cropData?.scores) {
        const score = getScoreAtPoint(lat, lng, cropData)
        if (score !== null) {
          const popup = new mapboxgl.Popup({ offset: 12, maxWidth: '260px', closeButton: false, closeOnClick: false })
            .setHTML(buildSuitabilityHtml(activeCrop, score, cropData, lat, lng))
            .setLngLat([lng, lat])
            .addTo(map)
          openPopupRef.current = popup

          // Wire up "Add Sample Here" button after DOM renders
          requestAnimationFrame(() => {
            const btn = popup.getElement()?.querySelector('#suit-add-sample')
            if (btn) {
              btn.addEventListener('click', () => {
                popup.remove()
                openPopupRef.current = null
                onMapClick(lat, lng)
              })
            }
          })
          return
        }
      }

      onMapClick(lat, lng)
    })

    map.on('load', () => {
      mapReadyRef.current = true
      onMapReady?.(() => {
        const b = map.getBounds()
        return { west: b.getWest(), south: b.getSouth(), east: b.getEast(), north: b.getNorth() }
      })
    })
    mapRef.current = map

    return () => {
      mapReadyRef.current = false
      map.remove()
      mapRef.current = null
      markersRef.current = {}
      openPopupRef.current = null
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // Keep refs in sync with props/state so the one-time click handler can read current values
  useEffect(() => { farmAnalysisRef.current = farmAnalysis }, [farmAnalysis])
  useEffect(() => { activeCropsRef.current = activeCrops }, [activeCrops])

  useEffect(() => {
    const map = mapRef.current
    if (!map) return
    samples.forEach((sample) => {
      if (markersRef.current[sample.id]) return
      const color = SOIL_COLORS[sample.result.soil?.label] ?? FALLBACK_COLOR
      const el = document.createElement('div')
      el.className = 'sample-marker'
      el.style.setProperty('--color', color)
      const popup = new mapboxgl.Popup({ offset: 20, maxWidth: '280px', closeButton: false, closeOnClick: false })
        .setHTML(buildPopupHtml(sample, color))
      new mapboxgl.Marker({ element: el }).setLngLat([sample.lng, sample.lat]).addTo(map)
      el.addEventListener('click', (e) => {
        e.stopPropagation()
        if (openPopupRef.current === popup) return
        openPopupRef.current?.remove()
        popup.addTo(map).setLngLat([sample.lng, sample.lat])
        openPopupRef.current = popup
      })
      markersRef.current[sample.id] = true
    })
  }, [samples])

  useEffect(() => {
    const map = mapRef.current
    if (!map || !farmAnalysis) return

    const applyRasters = () => {
      Object.entries(farmAnalysis).forEach(([crop, data]) => {
        const sourceId = `contour-img-${crop}`
        const layerId = `contour-raster-${crop}`
        const imageUrl = `data:image/png;base64,${data.image}`

        if (map.getSource(sourceId)) {
          map.getSource(sourceId).updateImage({ url: imageUrl, coordinates: data.coordinates })
        } else {
          map.addSource(sourceId, { type: 'image', url: imageUrl, coordinates: data.coordinates })
          map.addLayer({ id: layerId, type: 'raster', source: sourceId, paint: { 'raster-opacity': 1.0 } })
          setActiveCrops((prev) => {
            if (crop in prev) return prev
            const makeActive = Object.values(prev).every((v) => !v)
            return { ...Object.fromEntries(Object.keys(prev).map((k) => [k, false])), [crop]: makeActive }
          })
        }
      })
    }

    if (mapReadyRef.current) applyRasters()
    else map.once('load', applyRasters)
  }, [farmAnalysis])

  useEffect(() => {
    const map = mapRef.current
    if (!map || !mapReadyRef.current) return
    Object.entries(activeCrops).forEach(([crop, visible]) => {
      const rasterLayerId = `contour-raster-${crop}`
      if (map.getLayer(rasterLayerId)) {
        map.setLayoutProperty(rasterLayerId, 'visibility', visible ? 'visible' : 'none')
      }
    })
  }, [activeCrops])

  const toggleCrop = (crop) => setActiveCrops((prev) =>
    Object.fromEntries(Object.keys(prev).map((k) => [k, k === crop]))
  )

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%' }}>
      <div ref={containerRef} className="farm-map" />
      {Object.keys(activeCrops).length > 0 && (
        <div className="crop-toggle-panel">
          <p className="crop-panel-label">Crop Layers</p>
          <div className="crop-toggle-btns">
            {Object.keys(activeCrops).map((crop) => (
              <button
                key={crop}
                className={`contour-toggle-btn${activeCrops[crop] !== false ? ' active' : ''}`}
                onClick={() => toggleCrop(crop)}
                type="button"
              >
                {crop}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
