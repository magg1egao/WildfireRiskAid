import { MapContainer, TileLayer, Polygon, Popup } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'

const RISK_COLORS = {
  critical: '#D32F2F',
  high: '#FF9800',
  medium: '#FFC107',
  low: '#8BC34A',
}

const zones = [
  {
    name: 'Northridge Canyon',
    coords: [[34.2, -118.5], [34.3, -118.5], [34.3, -118.4], [34.2, -118.4]],
    risk: 'critical',
    ndvi: '0.37',
    terrain: 'Canyon',
    vegetation: 'Dense',
  },
  {
    name: 'Eastern Foothills',
    coords: [[34.1, -118.2], [34.2, -118.2], [34.2, -118.1], [34.1, -118.1]],
    risk: 'high',
    ndvi: '0.52',
    terrain: 'Foothills',
    vegetation: 'Moderate',
  },
  {
    name: 'Pine Ridge Forest',
    coords: [[34.0, -118.3], [34.1, -118.3], [34.1, -118.2], [34.0, -118.2]],
    risk: 'high',
    ndvi: '0.48',
    terrain: 'Ridge',
    vegetation: 'Dense',
  },
  {
    name: 'Valley Grasslands',
    coords: [[33.9, -118.4], [34.0, -118.4], [34.0, -118.3], [33.9, -118.3]],
    risk: 'medium',
    ndvi: '0.61',
    terrain: 'Valley',
    vegetation: 'Sparse',
  },
]

export default function RiskMap() {
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
            key={zone.name}
            positions={zone.coords}
            pathOptions={{
              color: RISK_COLORS[zone.risk],
              fillColor: RISK_COLORS[zone.risk],
              fillOpacity: 0.7,
              weight: 2,
            }}
          >
            <Popup>
              <div className="map-popup">
                <div className="popup-title">{zone.name}</div>
                <div className={`popup-risk ${zone.risk}`}>Risk: {zone.risk}</div>
                <div className="popup-details">
                  <div className="popup-detail">
                    <span>NDVI:</span>
                    <span>{zone.ndvi}</span>
                  </div>
                  <div className="popup-detail">
                    <span>Terrain:</span>
                    <span>{zone.terrain}</span>
                  </div>
                  <div className="popup-detail">
                    <span>Vegetation:</span>
                    <span>{zone.vegetation}</span>
                  </div>
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
            { risk: 'high', label: 'High (60–80%)' },
            { risk: 'medium', label: 'Medium (40–60%)' },
            { risk: 'low', label: 'Low (<40%)' },
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
