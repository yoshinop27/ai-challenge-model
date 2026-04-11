import { useEffect, useRef } from 'react'
import mapboxgl from 'mapbox-gl'
import 'mapbox-gl/dist/mapbox-gl.css'

mapboxgl.accessToken = import.meta.env.VITE_MAPBOX_TOKEN

export const SOIL_COLORS = {
  'Alluvial soil': '#22d3ee',
  'Black Soil':    '#94a3b8',
  'Clay soil':     '#f59e0b',
  'Red soil':      '#ef4444',
}

function getSoilColor(label) {
  return SOIL_COLORS[label] ?? '#6366f1'
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

export default function FarmMap({ farm, samples, onMapClick }) {
  const containerRef = useRef(null)
  const mapRef = useRef(null)
  const markersRef = useRef({})

  // Init map once
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

  // Sync sample markers
  useEffect(() => {
    const map = mapRef.current
    if (!map) return

    // Clear existing markers
    Object.values(markersRef.current).forEach(({ marker }) => marker.remove())
    markersRef.current = {}

    // Add one marker per sample
    samples.forEach((sample) => {
      const color = getSoilColor(sample.result.label)
      const el = makeMarkerEl(color)

      // Stop map click from firing when user clicks a marker
      el.addEventListener('click', (e) => e.stopPropagation())

      const confidence = (sample.result.confidence[sample.result.label] * 100).toFixed(1)
      const allScores = Object.entries(sample.result.confidence)
        .sort(([, a], [, b]) => b - a)
        .map(([label, score]) => `<span class="popup-row"><span>${label}</span><span>${(score * 100).toFixed(1)}%</span></span>`)
        .join('')

      const popup = new mapboxgl.Popup({ offset: 20, maxWidth: '240px', closeButton: false, closeOnClick: false })
        .setHTML(`
          <div class="marker-popup">
            <span class="popup-label" style="color:${color}">${sample.result.label}</span>
            <span class="popup-conf">${confidence}% confidence</span>
            <div class="popup-scores">${allScores}</div>
            <span class="popup-coords">${sample.lat.toFixed(5)}, ${sample.lng.toFixed(5)}</span>
          </div>
        `)

      const marker = new mapboxgl.Marker({ element: el })
        .setLngLat([sample.lng, sample.lat])
        .addTo(map)

      el.addEventListener('mouseenter', () => popup.addTo(map).setLngLat([sample.lng, sample.lat]))
      el.addEventListener('mouseleave', () => popup.remove())

      markersRef.current[sample.id] = { marker }
    })
  }, [samples])

  return <div ref={containerRef} className="farm-map" />
}
