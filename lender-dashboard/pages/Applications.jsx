import { applications } from "../src/data/mockdata";

function Applications({ onReview })  {
  return (
    <section className="applications-page">
      <div className="page-heading">
        <div>
          <p className="eyebrow">LOAN APPLICATIONS</p>
          <h2>Applications</h2>
          <p>
            Review worker profiles, alternative credit data, and
            model recommendations.
          </p>
        </div>

        <div className="application-count">
          {applications.length} Applications
        </div>
      </div>

      <div className="filter-bar">
        <input
          type="text"
          placeholder="Search worker name or application ID..."
          className="search-input"
        />

        <select className="filter-select" defaultValue="All">
          <option>All</option>
          <option>Pending Review</option>
          <option>Approved</option>
          <option>Rejected</option>
        </select>
      </div>

      <div className="applications-list">
        {applications.map((application) => (
          <div className="application-card" key={application.id}>
            <div className="application-main">
              <div className="worker-avatar">
                {application.workerName.charAt(0)}
              </div>

              <div className="worker-info">
                <h3>{application.workerName}</h3>

                <p>{application.occupation}</p>

                <span className="application-id">
                  {application.id}
                </span>
              </div>
            </div>

            <div className="application-income">
              <span>Monthly Income</span>
              <strong>
                ₹{application.monthlyIncome.toLocaleString("en-IN")}
              </strong>
            </div>

            <div className="application-score">
              <span>Credit Score</span>
              <strong>{application.creditScore}</strong>
              <small>/{application.scoreMax}</small>
            </div>

            <div className="application-risk">
              <span>Risk Level</span>
              <strong
                className={
                  application.riskLevel === "LOW RISK"
                    ? "risk-low"
                    : "risk-medium"
                }
              >
                {application.riskLevel}
              </strong>
            </div>

            <div className="application-loan">
              <span>Requested</span>
              <strong>
                ₹{application.requestedAmount.toLocaleString("en-IN")}
              </strong>
              <small>{application.tenure}</small>
            </div>

            <button
  className="review-button"
  onClick={() => onReview(application)}
>
  Review
</button>
          </div>
        ))}
      </div>
    </section>
  );
}

export default Applications;