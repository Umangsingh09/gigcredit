function Sidebar({ currentPage, onNavigate }) {
  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="logo-mark">G</div>

        <div>
          <h2>GigCredit</h2>
          <span>Lender Portal</span>
        </div>
      </div>

      <nav className="sidebar-nav">
        <p className="nav-label">MAIN</p>

        <button
          className={`nav-item ${
            currentPage === "dashboard" ? "active" : ""
          }`}
          onClick={() => onNavigate("dashboard")}
        >
          <span className="nav-icon">⌂</span>
          Dashboard
        </button>

        <button
          className={`nav-item ${
            currentPage === "applications" ? "active" : ""
          }`}
          onClick={() => onNavigate("applications")}
        >
          <span className="nav-icon">▣</span>
          Applications
        </button>

        <p className="nav-label">MANAGEMENT</p>

        <button
          className={`nav-item ${currentPage === "analytics" ? "active" : ""}`}
          onClick={() => onNavigate("analytics")}
        >
          <span className="nav-icon">◉</span>
          Analytics
        </button>

        <button
          className={`nav-item ${currentPage === "settings" ? "active" : ""}`}
          onClick={() => onNavigate("settings")}
        >
          <span className="nav-icon">⚙</span>
          Settings
        </button>
      </nav>

      <div className="sidebar-footer">
        <div className="security-badge">
          <span>✓</span>

          <div>
            <strong>Secure Portal</strong>
            <small>Protected access</small>
          </div>
        </div>
      </div>
    </aside>
  );
}

export default Sidebar;