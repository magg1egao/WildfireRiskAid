const alerts = [
  {
    name: 'Northridge Canyon',
    severity: 'critical',
    label: 'Critical (89%)',
    details: 'Extreme dry conditions, increasing winds, and declining vegetation health (NDVI: 0.37)',
    action: 'Deploy Resources',
    btnClass: 'btn-danger',
    pulse: true,
  },
  {
    name: 'Eastern Foothills',
    severity: 'high',
    label: 'High (72%)',
    details: 'Decreasing moisture levels, temperatures expected to rise to 92°F today',
    action: 'Monitor',
    btnClass: 'btn-warning',
    pulse: false,
  },
  {
    name: 'Pine Ridge Forest',
    severity: 'high',
    label: 'High (68%)',
    details: 'Limited access routes, dense vegetation with declining moisture content',
    action: 'Monitor',
    btnClass: 'btn-warning',
    pulse: false,
  },
]

export default function AlertsPanel() {
  return (
    <div className="panel panel-danger">
      <div className="panel-header">
        <div className="panel-title">
          <i className="fas fa-exclamation-triangle"></i>
          Critical Alerts
        </div>
        <div className="panel-actions">
          <button className="btn btn-text">View All</button>
        </div>
      </div>
      <div className="panel-body">
        <div className="alert-list">
          {alerts.map((alert) => (
            <div key={alert.name} className={`alert-item ${alert.severity}${alert.pulse ? ' pulse' : ''}`}>
              <div className="alert-header">
                <div className="alert-title">
                  {alert.name}
                  <span className={`alert-severity ${alert.severity}`}>{alert.label}</span>
                </div>
                <div className="alert-actions">
                  <button className={`btn btn-sm ${alert.btnClass}`}>{alert.action}</button>
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
