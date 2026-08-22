function Landing({ onNavigate }) {
  return (
    <main className="landing-page">
      <nav className="landing-nav">
        <div className="brand-lockup"><span className="brand-mark">G</span><strong>GigCredit</strong></div>
        <button className="landing-login" onClick={() => onNavigate("login")}>Sign in <span>↗</span></button>
      </nav>
      <section className="landing-hero">
        <div className="landing-copy">
          <p className="eyebrow">ALTERNATIVE CREDIT INTELLIGENCE</p>
          <h1>Lending decisions built around how people really work.</h1>
          <p className="landing-description">A clearer view of gig-worker income, consistency, and repayment capacity for lenders who want to move with confidence.</p>
          <div className="landing-actions"><button className="landing-primary" onClick={() => onNavigate("login")}>Open lender portal <span>→</span></button><span className="landing-note">Secure workspace for lending teams</span></div>
        </div>
        <div className="landing-visual" aria-label="GigCredit portfolio overview">
          <div className="visual-topline"><span>PORTFOLIO PULSE</span><b>● LIVE</b></div>
          <div className="visual-value">₹5.8L <small>total loan value</small></div>
          <div className="visual-chart"><i style={{ height: "36%" }} /><i style={{ height: "52%" }} /><i style={{ height: "43%" }} /><i style={{ height: "69%" }} /><i style={{ height: "61%" }} /><i style={{ height: "86%" }} /></div>
          <div className="visual-foot"><span>Application momentum</span><strong>+18.4%</strong></div>
          <div className="visual-badge"><span>84</span><div><strong>Portfolio health</strong><small>Strong decision signal</small></div></div>
        </div>
      </section>
      <section className="landing-proof"><div><strong>24</strong><span>applications reviewed</span></div><div><strong>67%</strong><span>approval clarity</span></div><div><strong>91%</strong><span>income stability signal</span></div></section>
    </main>
  );
}

export default Landing;
