import { useState, useEffect } from 'react'
import { MapContainer, TileLayer, Polygon, Popup } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'

const RISK_COLORS = {
  critical: '#D32F2F',
  high:     '#FF9800',
  medium:   '#FFC107',
  low:      '#8BC34A',
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
        <TileLayer
          attribution="&copy; OpenStreetMap contributors"
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {zones.map((zone) => (
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
