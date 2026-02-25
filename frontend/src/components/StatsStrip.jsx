export default function StatsStrip() {
  return (
    <div className="stats-strip mb-md">
      <div className="stat-item">
        <div className="stat-label">Risk Level</div>
        <div className="stat-value danger">High</div>
      </div>
      <div className="stat-divider"></div>
      <div className="stat-item">
        <div className="stat-label">Active Alerts</div>
        <div className="stat-value">3</div>
      </div>
      <div className="stat-divider"></div>
      <div className="stat-item">
        <div className="stat-label">Average NDVI</div>
        <div className="stat-value warning">0.52</div>
      </div>
      <div className="stat-divider"></div>
      <div className="stat-item">
        <div className="stat-label">Current Wind</div>
        <div className="stat-value">12 mph</div>
      </div>
      <div className="stat-divider"></div>
      <div className="stat-item">
        <div className="stat-label">Last Updated</div>
        <div className="stat-value text-muted">March 22, 08:45 AM</div>
      </div>
    </div>
  )
}
