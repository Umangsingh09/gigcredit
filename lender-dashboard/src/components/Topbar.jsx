function Topbar({ currentPage }) {
  const pageTitle =
    currentPage === "applications"
      ? "Applications"
      : "Overview";

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
          <div className="profile-avatar">A</div>

          <div className="profile-info">
            <strong>Aditya Kumar</strong>
            <span>Lender</span>
          </div>
        </div>

        <button className="logout-button">
          Logout
        </button>
      </div>
    </header>
  );
}

export default Topbar;