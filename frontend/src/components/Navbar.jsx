import { NavLink } from 'react-router-dom'

export default function Navbar() {
  return (
    <nav className="top-navbar">
      <a href="/" className="navbar-brand">
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
        <div className="status-indicator">
          <i className="fas fa-exclamation-triangle text-warning"></i>
          <span className="hide-mobile">3 Active Alerts</span>
        </div>
      </div>
    </nav>
  )
}
