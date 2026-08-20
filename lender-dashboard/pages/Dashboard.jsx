function Dashboard({ onNavigate }) {
  return (
    <section className="dashboard-page">
      <div className="welcome-section">
        <div>
          <p className="eyebrow">GOOD EVENING, ADITYA</p>

          <h2>Welcome to GigCredit</h2>

          <p>
            Review applications and make informed lending decisions
            using alternative credit intelligence.
          </p>
        </div>

        <button
          className="primary-button"
          onClick={() => onNavigate("applications")}
        >
          View Applications
        </button>
      </div>

      <div className="dashboard-grid">
        <div className="dashboard-card">
          <span className="card-icon">▣</span>
          <p>Total Applications</p>
          <h3>24</h3>
          <span className="card-change">+8% this month</span>
        </div>

        <div className="dashboard-card">
          <span className="card-icon">✓</span>
          <p>Approved</p>
          <h3>16</h3>
          <span className="card-change">67% approval rate</span>
        </div>

        <div className="dashboard-card">
          <span className="card-icon">◷</span>
          <p>Pending Review</p>
          <h3>5</h3>
          <span className="card-change">Needs attention</span>
        </div>

        <div className="dashboard-card">
          <span className="card-icon">₹</span>
          <p>Total Loan Value</p>
          <h3>₹5.8L</h3>
          <span className="card-change">Across applications</span>
        </div>
      </div>

      <div className="dashboard-lower-grid">
        <div className="analytics-panel">
          <div className="section-heading">
            <div>
              <p className="eyebrow">PORTFOLIO MOMENTUM</p>
              <h3>Application flow</h3>
            </div>

            <span className="period-pill">Last 6 months <span>⌄</span></span>
          </div>

          <div className="chart-summary">
            <strong>24</strong>
            <span><b>+18.4%</b> vs previous period</span>
          </div>

          <div className="bar-chart" aria-label="Application flow over the last six months">
            <div className="chart-y-axis"><span>30</span><span>20</span><span>10</span><span>0</span></div>
            <div className="chart-bars">
              <div className="chart-column"><i style={{ height: "42%" }} /><span>Mar</span></div>
              <div className="chart-column"><i style={{ height: "58%" }} /><span>Apr</span></div>
              <div className="chart-column"><i style={{ height: "48%" }} /><span>May</span></div>
              <div className="chart-column"><i style={{ height: "72%" }} /><span>Jun</span></div>
              <div className="chart-column"><i style={{ height: "66%" }} /><span>Jul</span></div>
              <div className="chart-column current"><i style={{ height: "88%" }} /><span>Aug</span></div>
            </div>
          </div>
        </div>

        <div className="health-panel">
          <div className="section-heading">
            <div>
              <p className="eyebrow">PORTFOLIO HEALTH</p>
              <h3>Decision mix</h3>
            </div>
            <span className="health-score">84 <small>/100</small></span>
          </div>

          <div className="health-ring">
            <div><strong>67%</strong><span>approval rate</span></div>
          </div>

          <div className="legend-list">
            <div><span className="legend-dot approved-dot" />Approved <strong>16</strong></div>
            <div><span className="legend-dot pending-dot" />Pending review <strong>5</strong></div>
            <div><span className="legend-dot rejected-dot" />Rejected <strong>3</strong></div>
          </div>
        </div>
      </div>

      <div className="recent-section review-queue">
        <div className="section-heading">
          <div>
            <p className="eyebrow">ACTION CENTER</p>
            <h3>Review queue</h3>
          </div>

          <button className="text-button" onClick={() => onNavigate("applications")}>
            View all <span>↗</span>
          </button>
        </div>

        <div className="queue-row">
          <div className="queue-person"><span className="queue-avatar avatar-orange">RS</span><div><strong>Ravi Sharma</strong><small>Submitted 18 min ago · Delivery partner</small></div></div>
          <span className="queue-risk medium-risk">Medium risk</span>
          <strong className="queue-amount">₹45,000</strong>
          <button className="queue-action" onClick={() => onNavigate("applications")}>Review <span>→</span></button>
        </div>
        <div className="queue-row">
          <div className="queue-person"><span className="queue-avatar avatar-blue">NM</span><div><strong>Neha Mehta</strong><small>Submitted 42 min ago · Freelance designer</small></div></div>
          <span className="queue-risk low-risk">Low risk</span>
          <strong className="queue-amount">₹30,000</strong>
          <button className="queue-action" onClick={() => onNavigate("applications")}>Review <span>→</span></button>
        </div>
      </div>
    </section>
  );
}

export default Dashboard;