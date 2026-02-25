import StatsStrip from '../components/StatsStrip'
import RiskMap from '../components/RiskMap'
import AlertsPanel from '../components/AlertsPanel'
import IndicesChart from '../components/IndicesChart'

export default function Dashboard() {
  return (
    <div className="content">
      <header>
        <h2>Wildfire Risk Command Center</h2>
      </header>

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
    </div>
  )
}
