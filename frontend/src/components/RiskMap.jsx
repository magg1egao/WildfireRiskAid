import { useState, useEffect } from 'react'
import { MapContainer, TileLayer, Polygon, Popup, useMap } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'

function MapInvalidator() {
  const map = useMap()
  useEffect(() => {
    const container = map.getContainer()
    const ro = new ResizeObserver(() => map.invalidateSize())
    ro.observe(container)
    return () => ro.disconnect()
  }, [map])
  return null
}

function MapFitter({ zones }) {
  const map = useMap()
  useEffect(() => {
    const coords = zones
      .filter((z) => Array.isArray(z.coordinates) && z.coordinates.length >= 3)
      .flatMap((z) => z.coordinates)
    if (coords.length === 0) return
    map.fitBounds(coords, { padding: [30, 30] })
  }, [zones, map])
  return null
}

const RISK_COLORS = {
  critical: '#DC2626',
  high:     '#F59E0B',
  medium:   '#FBC02D',
  low:      '#22C55E',
}

export default function RiskMap() {
  const [zones, setZones] = useState([])

  useEffect(() => {
    fetch('/api/zones')
      .then((r) => r.json())
      .then(setZones)
      .catch(() => {})
  }, [])

  return (
    <div className="map-container" style={{ position: 'relative' }}>
      <MapContainer
        center={[34.1, -118.3]}
        zoom={10}
        style={{ height: '100%', minHeight: '400px', width: '100%' }}
      >
        <MapInvalidator />
        <MapFitter zones={zones} />
        <TileLayer
          attribution="&copy; OpenStreetMap contributors"
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {zones.filter((zone) => Array.isArray(zone.coordinates) && zone.coordinates.length >= 3).map((zone) => (
          <Polygon
            key={zone.zone_id}
            positions={zone.coordinates}
            pathOptions={{
              color:       RISK_COLORS[zone.risk_level] || '#8BC34A',
              fillColor:   RISK_COLORS[zone.risk_level] || '#8BC34A',
              fillOpacity: 0.7,
              weight:      2,
            }}
          >
            <Popup>
              <div className="map-popup">
                <div className="popup-title">{zone.name}</div>
                <div className={`popup-risk ${zone.risk_level}`}>
                  Risk: {zone.risk_level} ({zone.risk_score?.toFixed(0)}%)
                </div>
                <div className="popup-details">
                  <div className="popup-detail"><span>NDVI:</span><span>{zone.ndvi?.toFixed(2)}</span></div>
                  <div className="popup-detail"><span>NBR:</span><span>{zone.nbr?.toFixed(2)}</span></div>
                  <div className="popup-detail"><span>NDWI:</span><span>{zone.ndwi?.toFixed(2)}</span></div>
                  <div className="popup-detail"><span>Terrain:</span><span>{zone.terrain}</span></div>
                  <div className="popup-detail"><span>Vegetation:</span><span>{zone.vegetation}</span></div>
                </div>
              </div>
            </Popup>
          </Polygon>
        ))}
      </MapContainer>

      <div className="map-legend">
        <div className="legend-title">Risk Levels</div>
        <div className="legend-items">
          {[
            { risk: 'critical', label: 'Critical (>80%)' },
            { risk: 'high',     label: 'High (60–80%)' },
            { risk: 'medium',   label: 'Medium (40–60%)' },
            { risk: 'low',      label: 'Low (<40%)' },
          ].map(({ risk, label }) => (
            <div className="legend-item" key={risk}>
              <div className="legend-color" style={{ backgroundColor: RISK_COLORS[risk] }}></div>
              <div className="legend-label">{label}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
