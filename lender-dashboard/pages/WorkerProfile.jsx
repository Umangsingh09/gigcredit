import { useState } from "react";

function WorkerProfile({ application, onBack }) {
  const [decision, setDecision] = useState(null);
  const [showConfirmation, setShowConfirmation] = useState(false);

  const handleDecision = (type) => {
    setDecision(type);
    setShowConfirmation(true);
  };

  const closeConfirmation = () => {
    setShowConfirmation(false);
  };

  return (
    <section className="worker-profile-page">
      <button className="back-button" onClick={onBack}>
        ← Back to Applications
      </button>

      <div className="profile-heading">
        <div>
          <p className="eyebrow">WORKER PROFILE</p>

          <h2>{application.workerName}</h2>

          <p>
            {application.occupation} · Application {application.id}
          </p>
        </div>

        <span
          className={
            decision === "approved"
              ? "status-approved"
              : decision === "rejected"
              ? "status-rejected"
              : application.status === "Approved"
              ? "status-approved"
              : "status-pending"
          }
        >
          {decision === "approved"
            ? "Approved"
            : decision === "rejected"
            ? "Rejected"
            : application.status}
        </span>
      </div>

      <div className="credit-profile-card">
        <div className="score-section">
          <p className="card-label">CREDIT SCORE</p>

          <div className="score-value">
            {application.creditScore}
            <span>/{application.scoreMax}</span>
          </div>

          <span
            className={
              application.riskLevel === "LOW RISK"
                ? "risk-badge-low"
                : "risk-badge-medium"
            }
          >
            {application.riskLevel}
          </span>
        </div>

        <div className="score-description">
          <p className="card-label">MODEL SUMMARY</p>

          <h3>
            Alternative credit profile indicates{" "}
            {application.riskLevel.toLowerCase()}.
          </h3>

          <p>
            The score is based on earnings stability, work
            consistency, repayment behaviour, platform signals,
            and debt obligations.
          </p>
        </div>
      </div>

      <div className="profile-section">
        <div className="section-heading">
          <div>
            <p className="eyebrow">RISK BREAKDOWN</p>
            <h3>Credit Profile Factors</h3>
          </div>
        </div>

        <div className="risk-grid">
          <RiskFactor
            label="Income Stability"
            value={application.incomeStability}
          />

          <RiskFactor
            label="Work Consistency"
            value={application.workConsistency}
          />

          <RiskFactor
            label="Repayment History"
            value={application.repaymentHistory}
          />

          <RiskFactor
            label="Platform Rating"
            value={application.platformRating}
          />

          <RiskFactor
            label="Debt Burden"
            value={application.debtBurden}
            inverse
          />
        </div>
      </div>

      <div className="profile-section">
        <div className="section-heading">
          <div>
            <p className="eyebrow">ALTERNATIVE CREDIT DATA</p>
            <h3>Worker Financial Signals</h3>
          </div>
        </div>

        <div className="data-grid">
          <DataItem
            label="Monthly Earnings"
            value={`₹${application.monthlyIncome.toLocaleString(
              "en-IN"
            )}`}
          />

          <DataItem
            label="Requested Loan"
            value={`₹${application.requestedAmount.toLocaleString(
              "en-IN"
            )}`}
          />

          <DataItem
            label="Loan Tenure"
            value={application.tenure}
          />

          <DataItem
            label="Platform Rating"
            value={`${(
              application.platformRating / 20
            ).toFixed(1)} / 5`}
          />
        </div>
      </div>

      <div className="recommendation-card">
        <div>
          <p className="eyebrow">LOAN RECOMMENDATION</p>

          <h3>Recommended Loan</h3>

          <div className="recommendation-amount">
            ₹
            {application.requestedAmount.toLocaleString("en-IN")}
          </div>

          <p className="recommendation-tenure">
            Recommended tenure: {application.tenure}
          </p>
        </div>

        <div className="recommendation-reason">
          <span>MODEL REASON</span>

          <p>
            Stable earnings + consistent work history + low
            obligations
          </p>
        </div>

        <div className="decision-actions">
          <button
            className="approve-button"
            onClick={() => handleDecision("approved")}
            disabled={decision !== null}
          >
            ✓ Approve
          </button>

          <button
            className="reject-button"
            onClick={() => handleDecision("rejected")}
            disabled={decision !== null}
          >
            Reject
          </button>
        </div>
      </div>

      {decision && (
        <div
          className={
            decision === "approved"
              ? "decision-banner approved-banner"
              : "decision-banner rejected-banner"
          }
        >
          <div>
            <strong>
              {decision === "approved"
                ? "Application approved"
                : "Application rejected"}
            </strong>

            <p>
              This decision is currently stored in the frontend
              session only.
            </p>
          </div>

          <button
            className="back-to-applications"
            onClick={onBack}
          >
            Back to Applications
          </button>
        </div>
      )}

      {showConfirmation && (
        <div className="confirmation-overlay">
          <div className="confirmation-modal">
            <div className="confirmation-icon">
              {decision === "approved" ? "✓" : "!"}
            </div>

            <h3>
              {decision === "approved"
                ? "Approve this application?"
                : "Reject this application?"}
            </h3>

            <p>
              You selected{" "}
              <strong>
                {decision === "approved"
                  ? "Approve"
                  : "Reject"}
              </strong>{" "}
              for {application.workerName}.
            </p>

            <div className="confirmation-actions">
              <button
                className="cancel-button"
                onClick={closeConfirmation}
              >
                Cancel
              </button>

              <button
                className={
                  decision === "approved"
                    ? "confirm-approve-button"
                    : "confirm-reject-button"
                }
                onClick={closeConfirmation}
              >
                Confirm
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}

function RiskFactor({ label, value, inverse = false }) {
  return (
    <div className="risk-factor">
      <div className="risk-factor-header">
        <span>{label}</span>
        <strong>{value}%</strong>
      </div>

      <div className="progress-track">
        <div
          className={`progress-fill ${
            inverse ? "progress-inverse" : ""
          }`}
          style={{ width: `${value}%` }}
        />
      </div>
    </div>
  );
}

function DataItem({ label, value }) {
  return (
    <div className="data-item">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

export default WorkerProfile;