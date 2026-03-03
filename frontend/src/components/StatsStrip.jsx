import { useState, useEffect } from 'react'

export default function StatsStrip() {
  const [stats, setStats] = useState(null)

  useEffect(() => {
    fetch('/api/dashboard-stats')
      .then((r) => r.json())
      .then(setStats)
      .catch(() => {})
  }, [])

  if (!stats) {
    return (
      <div className="stats-strip mb-md">
        <div className="stat-item">
          <div className="stat-label">Loading...</div>
        </div>
      </div>
    )
  }

  const riskClass =
    stats.risk_level === 'Critical' ? 'danger' :
    stats.risk_level === 'High'     ? 'warning' : ''

  return (
    <div className="stats-strip mb-md">
      <div className="stat-item">
        <div className="stat-label">Risk Level</div>
        <div className={`stat-value ${riskClass}`}>{stats.risk_level}</div>
      </div>
      <div className="stat-divider"></div>
      <div className="stat-item">
        <div className="stat-label">Active Alerts</div>
        <div className="stat-value">{stats.active_alerts}</div>
      </div>
      <div className="stat-divider"></div>
      <div className="stat-item">
        <div className="stat-label">Average NDVI</div>
        <div className="stat-value warning">{stats.avg_ndvi}</div>
      </div>
      <div className="stat-divider"></div>
      <div className="stat-item">
        <div className="stat-label">Current Wind</div>
        <div className="stat-value">{stats.wind_speed}</div>
      </div>
      <div className="stat-divider"></div>
      <div className="stat-item">
        <div className="stat-label">Last Updated</div>
        <div className="stat-value text-muted">{stats.last_updated}</div>
      </div>
    </div>
  )
}
