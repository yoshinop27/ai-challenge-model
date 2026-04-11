import { useEffect, useRef } from 'react'
import mapboxgl from 'mapbox-gl'
import 'mapbox-gl/dist/mapbox-gl.css'
import { SOIL_COLORS, FALLBACK_COLOR } from '../utils/constants'

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
  const confidence = (sample.result.confidence[sample.result.label] * 100).toFixed(1)
  const allScores = Object.entries(sample.result.confidence)
    .sort(([, a], [, b]) => b - a)
    .map(
      ([label, score]) =>
        `<span class="popup-row"><span>${escapeHtml(label)}</span><span>${(score * 100).toFixed(1)}%</span></span>`
    )
    .join('')

  const rec = sample.result.recommendations
  const recHtml = rec
    ? `<div class="popup-section">
        <p class="popup-summary">${escapeHtml(rec.summary)}</p>
        <div class="popup-crops">
          <div class="popup-crop-col">
            <span class="popup-crop-title good">Good Crops</span>
            ${rec.good_crops.map((c) => `<span class="popup-crop-tag good">${escapeHtml(c)}</span>`).join('')}
          </div>
          <div class="popup-crop-col">
            <span class="popup-crop-title avoid">Avoid</span>
            ${rec.avoid_crops.map((c) => `<span class="popup-crop-tag avoid">${escapeHtml(c)}</span>`).join('')}
          </div>
        </div>
        <p class="popup-tip">${escapeHtml(rec.tip)}</p>
      </div>`
    : ''

  return `<div class="marker-popup">
    <span class="popup-label" style="color:${escapeHtml(color)}">${escapeHtml(sample.result.label)}</span>
    <span class="popup-conf">${escapeHtml(confidence)}% confidence</span>
    <div class="popup-scores">${allScores}</div>
    ${recHtml}
    <span class="popup-coords">${sample.lat.toFixed(5)}, ${sample.lng.toFixed(5)}</span>
  </div>`
}

export default function FarmMap({ farm, samples, onMapClick }) {
  const containerRef = useRef(null)
  const mapRef = useRef(null)
  const markersRef = useRef({})

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
      onMapClick(e.lngLat.lat, e.lngLat.lng)
    })

    mapRef.current = map

    return () => {
      map.remove()
      mapRef.current = null
      markersRef.current = {}
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const map = mapRef.current
    if (!map) return

    samples.forEach((sample) => {
      if (markersRef.current[sample.id]) return

      const color = getSoilColor(sample.result.label)
      const el = makeMarkerEl(color)

      el.addEventListener('click', (e) => e.stopPropagation())

      const popup = new mapboxgl.Popup({
        offset: 20,
        maxWidth: '280px',
        closeButton: false,
        closeOnClick: false,
      }).setHTML(buildPopupHtml(sample, color))

      const marker = new mapboxgl.Marker({ element: el })
        .setLngLat([sample.lng, sample.lat])
        .addTo(map)

      el.addEventListener('mouseenter', () =>
        popup.addTo(map).setLngLat([sample.lng, sample.lat])
      )
      el.addEventListener('mouseleave', () => popup.remove())

      markersRef.current[sample.id] = { marker }
    })
  }, [samples])

  return <div ref={containerRef} className="farm-map" />
}
