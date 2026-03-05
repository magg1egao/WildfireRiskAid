import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import StatsStrip from '../components/StatsStrip'
import RiskMap from '../components/RiskMap'
import AlertsPanel from '../components/AlertsPanel'
import IndicesChart from '../components/IndicesChart'
import Footer from '../components/Footer'

export default function Dashboard() {
  const [hasData, setHasData] = useState(null)
  const navigate = useNavigate()

  function checkData() {
    fetch('/api/has-data')
      .then((r) => r.json())
      .then((d) => setHasData(d.has_data))
      .catch(() => setHasData(false))
  }

  useEffect(() => { checkData() }, [])

  async function loadDemo() {
    await fetch('/api/load-demo', { method: 'POST' })
    checkData()
  }

  if (hasData === null) return null

  if (!hasData) {
    return (
      <div className="content">
        <div className="dashboard-empty">
          <div className="dashboard-empty-icon">
            <i className="fas fa-layer-group"></i>
          </div>
          <h2>No Data Loaded</h2>
          <p>Upload a CSV dataset to populate the risk map, alerts, and indices chart.</p>
          <div className="dashboard-empty-actions">
            <button className="btn btn-primary" onClick={() => navigate('/upload')}>
              <i className="fas fa-upload"></i>
              Upload Data
            </button>
            <button className="btn btn-outline" onClick={loadDemo}>
              <i className="fas fa-database"></i>
              Load Demo Data
            </button>
          </div>
        </div>
        <Footer />
      </div>
    )
  }

  return (
    <div className="content">
      <StatsStrip />

      <div className="dashboard-grid">
        <div className="panel panel-main">
          <div className="panel-header">
            <div className="panel-title">
              <i className="fas fa-map-marked-alt"></i>
              Risk Assessment Map
            </div>
            <div className="panel-actions">
              <select className="form-select compact">
                <option value="risk">Risk Assessment</option>
                <option value="ndvi">NDVI (Vegetation)</option>
                <option value="nbr">NBR (Burn Ratio)</option>
                <option value="terrain">Terrain</option>
              </select>
            </div>
          </div>
          <div className="panel-body no-padding">
            <RiskMap />
          </div>
        </div>

        <AlertsPanel />

        <IndicesChart />
      </div>
      <Footer />
    </div>
  )
}
