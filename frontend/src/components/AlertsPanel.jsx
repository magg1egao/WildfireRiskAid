import { useState, useEffect } from 'react'

export default function AlertsPanel() {
  const [alerts, setAlerts] = useState([])

  useEffect(() => {
    fetch('/api/alerts')
      .then((r) => r.json())
      .then(setAlerts)
      .catch(() => {})
  }, [])

  return (
    <div className="panel panel-danger">
      <div className="panel-header">
        <div className="panel-title">
          <i className="fas fa-exclamation-triangle"></i>
          Critical Alerts
        </div>
        <div className="panel-actions">
          <span className="text-muted" style={{ fontSize: '0.8rem' }}>
            {alerts.length} active
          </span>
        </div>
      </div>
      <div className="panel-body">
        <div className="alert-list">
          {alerts.length === 0 && (
            <div className="text-muted" style={{ textAlign: 'center', padding: '1rem' }}>
              No active alerts
            </div>
          )}
          {alerts.map((alert) => (
            <div
              key={alert.name}
              className={`alert-item ${alert.severity}${alert.severity === 'critical' ? ' pulse' : ''}`}
            >
              <div className="alert-header">
                <div className="alert-title">
                  {alert.name}
                  <span className={`alert-severity ${alert.severity}`}>{alert.label}</span>
                </div>
                <div className="alert-actions">
                  <button className={`btn btn-sm ${alert.severity === 'critical' ? 'btn-danger' : 'btn-warning'}`}>
                    {alert.action}
                  </button>
                </div>
              </div>
              <div className="alert-details">{alert.details}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
