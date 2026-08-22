import { useEffect, useState } from "react";

import { fallbackAnalytics, getAnalytics } from "../src/data/api";

function Analytics() {
  const [analytics, setAnalytics] = useState(fallbackAnalytics);
  const [source, setSource] = useState("demo");

  useEffect(() => {
    getAnalytics()
      .then((data) => {
        setAnalytics(data);
        setSource("live");
      })
      .catch(() => setSource("demo"));
  }, []);

  const maxApplications = Math.max(...analytics.monthly.map((month) => month.applications), 1);
  const { summary } = analytics;

  return (
    <section className="management-page">
      <div className="page-intro">
        <div>
          <p className="eyebrow">PORTFOLIO INTELLIGENCE</p>
          <h2>Analytics</h2>
          <p>Track application volume and lending decisions in one view.</p>
        </div>
        <span className={`data-status ${source}`}>{source === "live" ? "Live data" : "Demo data"}</span>
      </div>

      <div className="dashboard-grid management-stats">
        <div className="dashboard-card"><p>Total applications</p><h3>{summary.total}</h3><span className="card-change">Across all statuses</span></div>
        <div className="dashboard-card"><p>Approval rate</p><h3>{summary.approval_rate}%</h3><span className="card-change">Of reviewed applications</span></div>
        <div className="dashboard-card"><p>Pending review</p><h3>{summary.pending}</h3><span className="card-change">Needs attention</span></div>
        <div className="dashboard-card"><p>Rejected</p><h3>{summary.rejected}</h3><span className="card-change">Decision outcome</span></div>
      </div>

      <div className="management-panel">
        <div className="section-heading"><div><p className="eyebrow">VOLUME</p><h3>Applications by month</h3></div><span className="period-pill">Last 6 months</span></div>
        <div className="analytics-bars">
          {analytics.monthly.map((month) => (
            <div className="analytics-bar-column" key={month.label}>
              <strong>{month.applications}</strong>
              <div className="analytics-bar-track"><i style={{ height: `${(month.applications / maxApplications) * 100}%` }} /></div>
              <span>{month.label}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

export default Analytics;
