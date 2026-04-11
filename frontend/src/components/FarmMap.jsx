import { useEffect, useRef } from 'react'
import mapboxgl from 'mapbox-gl'
import 'mapbox-gl/dist/mapbox-gl.css'

mapboxgl.accessToken = import.meta.env.VITE_MAPBOX_TOKEN

export default function FarmMap({ lat, lng }) {
  const containerRef = useRef(null)
  const mapRef = useRef(null)

  useEffect(() => {
    if (mapRef.current) {
      mapRef.current.setCenter([lng, lat])
      return
    }

    mapRef.current = new mapboxgl.Map({
      container: containerRef.current,
      style: 'mapbox://styles/mapbox/satellite-streets-v12',
      center: [lng, lat],
      zoom: 14,
    })

    new mapboxgl.Marker({ color: '#6366f1' })
      .setLngLat([lng, lat])
      .addTo(mapRef.current)

    return () => {
      mapRef.current?.remove()
      mapRef.current = null
    }
  }, [lat, lng])

  return <div ref={containerRef} className="farm-map" />
}
