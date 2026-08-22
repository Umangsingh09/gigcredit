function Topbar({ currentPage, onLogout, profile }) {
  const pageTitles = {
    dashboard: "Overview",
    applications: "Applications",
    analytics: "Analytics",
    settings: "Settings",
    "worker-profile": "Worker Profile",
  };
  const pageTitle = pageTitles[currentPage] || "Overview";
  const lenderName = profile?.full_name || "Umang Raj";
  const initials = lenderName.split(" ").map((part) => part[0]).join("").slice(0, 2).toUpperCase();

  return (
    <header className="topbar">
      <div>
        <p className="topbar-label">LENDER DASHBOARD</p>
        <h1>{pageTitle}</h1>
      </div>

      <div className="topbar-right">
        <div className="notification">
          <span>♢</span>
        </div>

        <div className="lender-profile">
          <div className="profile-avatar">{initials}</div>

          <div className="profile-info">
            <strong>{lenderName}</strong>
            <span>Lender</span>
          </div>
        </div>

        <button className="logout-button" onClick={onLogout}>
          Logout
        </button>
      </div>
    </header>
  );
}

export default Topbar;