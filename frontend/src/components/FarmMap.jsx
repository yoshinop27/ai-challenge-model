import { useEffect, useRef } from 'react'
import mapboxgl from 'mapbox-gl'
import 'mapbox-gl/dist/mapbox-gl.css'
import { SOIL_COLORS, MOISTURE_COLORS, FALLBACK_COLOR } from '../utils/constants'

mapboxgl.accessToken = import.meta.env.VITE_MAPBOX_TOKEN

function getSoilColor(label) {
  return SOIL_COLORS[label] ?? FALLBACK_COLOR
}

function farmSizeToZoom(acres) {
  const z = 16 - Math.log2(Math.max(1, acres)) * 0.7
  return Math.min(17, Math.max(8, z))
}

function makeMarkerEl(color) {
  const el = document.createElement('div')
  el.className = 'sample-marker'
  el.style.setProperty('--color', color)
  return el
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

function buildPopupHtml(sample, color) {
  const soil = sample.result.soil
  const moisture = sample.result.moisture

  const soilConf = (soil.confidence[soil.label] * 100).toFixed(1)
  const soilScores = Object.entries(soil.confidence)
    .sort(([, a], [, b]) => b - a)
    .map(
      ([label, score]) =>
        `<span class="popup-row"><span>${escapeHtml(label)}</span><span>${(score * 100).toFixed(1)}%</span></span>`
    )
    .join('')

  let moistureHtml = ''
  if (moisture) {
    const moistureColor = MOISTURE_COLORS[moisture.label] ?? FALLBACK_COLOR
    const moistureConf = (moisture.confidence[moisture.label] * 100).toFixed(1)
    const moistureScores = Object.entries(moisture.confidence)
      .sort(([, a], [, b]) => b - a)
      .map(
        ([label, score]) =>
          `<span class="popup-row"><span>${escapeHtml(label)}</span><span>${(score * 100).toFixed(1)}%</span></span>`
      )
      .join('')
    moistureHtml = `
      <span class="popup-section-title">Moisture</span>
      <span class="popup-label" style="color:${escapeHtml(moistureColor)}">${escapeHtml(moisture.label)}</span>
      <span class="popup-conf">${escapeHtml(moistureConf)}% confidence</span>
      <div class="popup-scores">${moistureScores}</div>`
  }

  const rec = sample.result.recommendations
  let recHtml = ''
  if (rec) {
    const cropsHtml = rec.mode === 'targeted'
      ? `<div class="popup-crop-analysis">
          ${rec.crop_analysis.map((item) => `
            <div class="popup-analysis-row">
              <span class="popup-analysis-indicator ${item.suitable ? 'good' : 'avoid'}">${item.suitable ? '✓' : '✗'}</span>
              <div class="popup-analysis-detail">
                <span class="popup-analysis-crop">${escapeHtml(item.crop)}</span>
                <span class="popup-analysis-reason">${escapeHtml(item.reason)}</span>
              </div>
            </div>`).join('')}
        </div>`
      : `<div class="popup-crops">
          <div class="popup-crop-col">
            <span class="popup-crop-title good">Good Crops</span>
            ${rec.good_crops.map((c) => `<span class="popup-crop-tag good">${escapeHtml(c)}</span>`).join('')}
          </div>
          <div class="popup-crop-col">
            <span class="popup-crop-title avoid">Avoid</span>
            ${rec.avoid_crops.map((c) => `<span class="popup-crop-tag avoid">${escapeHtml(c)}</span>`).join('')}
          </div>
        </div>`

    recHtml = `<div class="popup-section">
      <p class="popup-summary">${escapeHtml(rec.summary)}</p>
      ${cropsHtml}
      <p class="popup-tip">${escapeHtml(rec.tip)}</p>
    </div>`
  }

  return `<div class="marker-popup">
    <span class="popup-section-title">Soil Condition</span>
    <span class="popup-label" style="color:${escapeHtml(color)}">${escapeHtml(soil.label)}</span>
    <span class="popup-conf">${escapeHtml(soilConf)}% confidence</span>
    <div class="popup-scores">${soilScores}</div>
    ${moistureHtml}
    ${recHtml}
    <span class="popup-coords">${sample.lat.toFixed(5)}, ${sample.lng.toFixed(5)}</span>
  </div>`
}

export default function FarmMap({ farm, samples, onMapClick }) {
  const containerRef = useRef(null)
  const mapRef = useRef(null)
  const markersRef = useRef({})
  const openPopupRef = useRef(null)

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
      // Close any open popup first, then open the sample modal
      if (openPopupRef.current) {
        openPopupRef.current.remove()
        openPopupRef.current = null
      }
      onMapClick(e.lngLat.lat, e.lngLat.lng)
    })

    mapRef.current = map

    return () => {
      map.remove()
      mapRef.current = null
      markersRef.current = {}
      openPopupRef.current = null
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const map = mapRef.current
    if (!map) return

    samples.forEach((sample) => {
      if (markersRef.current[sample.id]) return

      const color = getSoilColor(sample.result.soil?.label)
      const el = makeMarkerEl(color)

      const popup = new mapboxgl.Popup({
        offset: 20,
        maxWidth: '280px',
        closeButton: false,
        closeOnClick: false,
      }).setHTML(buildPopupHtml(sample, color))

      const marker = new mapboxgl.Marker({ element: el })
        .setLngLat([sample.lng, sample.lat])
        .addTo(map)

      el.addEventListener('click', (e) => {
        e.stopPropagation() // don't fire map click / open modal
        if (openPopupRef.current === popup) return // already open
        openPopupRef.current?.remove()
        popup.addTo(map).setLngLat([sample.lng, sample.lat])
        openPopupRef.current = popup
      })

      markersRef.current[sample.id] = { marker }
    })
  }, [samples])

  return <div ref={containerRef} className="farm-map" />
}
