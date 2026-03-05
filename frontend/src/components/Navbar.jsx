import { useState, useEffect } from 'react'
import { NavLink } from 'react-router-dom'

export default function Navbar() {
  const [stats, setStats] = useState(null)

  useEffect(() => {
    fetch('/api/dashboard-stats')
      .then((r) => r.json())
      .then(setStats)
      .catch(() => {})
  }, [])

  return (
    <nav className="top-navbar">
      <a href="/" className="navbar-brand">
        <svg className="brand-logo" viewBox="-1 -1 34 34" fill="none" xmlns="http://www.w3.org/2000/svg">
          {/* Hexagon container */}
          <path d="M4 10L16 2L28 10L28 22L16 30L4 22Z" fill="#1E293B" stroke="#F59E0B" strokeWidth="1.5"/>
          {/* Outer flame — amber */}
          <path d="M16 24C12 24 9.5 21 9.5 18C9.5 14.5 11.5 12 13.5 10C13.5 13 15 14.5 16 15C15 12 15.5 9 16 7C17 10 17.5 12.5 19 14C19.5 11.5 20 10 21 9C22.5 12 22.5 16 22.5 18C22.5 21.5 20 24 16 24Z" fill="#F59E0B"/>
          {/* Inner flame — red */}
          <path d="M16 22C14 22 12.5 20.5 12.5 19C12.5 17 14 15.5 15.5 15C15.5 17 16.5 18 17 18.5C16.5 16.5 17 15.5 18 14.5C19 16 20 18 20 19.5C20 21 18.5 22 16 22Z" fill="#DC2626"/>
          {/* Sight indicator — white ring, navy core */}
          <circle cx="16" cy="20.5" r="2" fill="white" opacity="0.9"/>
          <circle cx="16" cy="20.5" r="1" fill="#1E3A5F"/>
        </svg>
        <div className="brand-title">
          <h1>
            <span className="fire-text">Fire</span>
            <span className="sight-text">Sight</span>
          </h1>
        </div>
      </a>

      <ul className="nav-menu">
        <li>
          <NavLink to="/" end className={({ isActive }) => isActive ? 'active' : ''}>
            <i className="fas fa-chart-bar"></i>
            <span>Dashboard</span>
          </NavLink>
        </li>
        <li>
          <NavLink to="/upload" className={({ isActive }) => isActive ? 'active' : ''}>
            <i className="fas fa-upload"></i>
            <span>Upload Data</span>
          </NavLink>
        </li>
        <li>
          <NavLink to="/chat" className={({ isActive }) => isActive ? 'active' : ''}>
            <i className="fas fa-robot"></i>
            <span>AI Assistant</span>
          </NavLink>
        </li>
      </ul>

      <div className="system-info">
        <div className="status-indicator">
          <i className="fas fa-circle text-success"></i>
          <span>System Online</span>
        </div>
        <div className="status-indicator">
          <i className="fas fa-satellite text-info"></i>
          <span className="hide-mobile">Satellite Active</span>
        </div>
        {stats?.active_alerts > 0 && (
          <div className="status-indicator">
            <i className="fas fa-exclamation-triangle text-warning"></i>
            <span className="hide-mobile">{stats.active_alerts} Active Alert{stats.active_alerts !== 1 ? 's' : ''}</span>
          </div>
        )}
      </div>
    </nav>
  )
}
