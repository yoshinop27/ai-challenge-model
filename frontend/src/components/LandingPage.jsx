export default function LandingPage({ onEnter }) {
  return (
    <div className="landing">
      {/* ── Hero ── */}
      <div className="landing-hero">
        <div className="landing-hero-inner">
          <span className="landing-badge">Pi515 AI Challenge 2026 &nbsp;·&nbsp; Grinnell AI</span>
          <h1 className="landing-title">SoilSense</h1>
          <div className="landing-divider" />
          <p className="landing-tagline">AI-Powered Soil Quality Mapping for Iowa Farmers</p>
          <p className="landing-sub">Addressing Iowa's Farm Debt Crisis Through Precision Agriculture</p>
          <div className="landing-btn-grid" style={{ marginTop: '2.5rem' }}>
            <a href="#demo" className="landing-btn landing-btn-outline">Watch a Demo</a>
            <a href="#ethics" className="landing-btn landing-btn-outline">Ethical &amp; Inclusive Design</a>
            <a href="#impact" className="landing-btn landing-btn-outline">Impact Analysis</a>
            <button className="landing-btn landing-btn-primary" onClick={onEnter}>
              Try It Out →
            </button>
          </div>
        </div>
        <div className="landing-orb landing-orb-1" />
        <div className="landing-orb landing-orb-2" />
      </div>

      {/* ── Description ── */}
      <div className="landing-section">
        <h2 className="landing-section-title">Point. Scan. Know.</h2>
        <p className="landing-body">
          Iowa's 86,000+ farms are under mounting financial pressure — large farms carry over $1.8M in
          debt on average and bankruptcies are rising. Most farmers still make planting decisions with
          incomplete soil data, leaving profitability on the table.
        </p>
        <p className="landing-body">
          SoilSense turns a smartphone camera into an instant soil quality lab. Our on-device AI
          classifies soil type and moisture condition, then maps your entire farm — giving you
          actionable insights at zero lab cost, right where you stand.
        </p>
      </div>

      {/* ── Stats ── */}
      <div className="landing-stats">
        <div className="landing-stat">
          <span className="landing-stat-value">$1.8M+</span>
          <span className="landing-stat-label">Average debt for large Iowa farms</span>
        </div>
        <div className="landing-stat">
          <span className="landing-stat-value">86,911</span>
          <span className="landing-stat-label">Farms across Iowa</span>
        </div>
        <div className="landing-stat">
          <span className="landing-stat-value">92.6%</span>
          <span className="landing-stat-label">Model accuracy on held-out test set</span>
        </div>
      </div>

      {/* ── How it works ── */}
      <div className="landing-section">
        <p className="landing-eyebrow">Our Solution</p>
        <h2 className="landing-section-title">How SoilSense Works</h2>
        <div className="landing-steps">
          <div className="landing-step">
            <div className="landing-step-num">1</div>
            <h3 className="landing-step-head">Capture</h3>
            <p className="landing-step-body">Point your phone camera at the soil. The app accepts any ground-level photo.</p>
          </div>
          <div className="landing-step-arrow">→</div>
          <div className="landing-step">
            <div className="landing-step-num">2</div>
            <h3 className="landing-step-head">Classify</h3>
            <p className="landing-step-body">AI identifies soil type and moisture level in under 2 seconds, fully on-device.</p>
          </div>
          <div className="landing-step-arrow">→</div>
          <div className="landing-step">
            <div className="landing-step-num">3</div>
            <h3 className="landing-step-head">Map &amp; Act</h3>
            <p className="landing-step-body">Results overlay a field map showing good, moderate, and poor zones across your farm.</p>
          </div>
        </div>
      </div>

      {/* ── Ethical & Inclusive Design ── */}
      <div id="ethics" className="landing-wide-section">
        <div className="landing-wide-inner">
          <p className="landing-eyebrow">Design Principles</p>
          <h2 className="landing-section-title">Ethical &amp; Inclusive Design</h2>
          <div className="landing-wide-divider" />
          <div className="landing-ethics-grid">
            <div className="landing-ethics-card">
              <h3 className="landing-ethics-head">Fairness</h3>
              <ul className="landing-ethics-list">
                <li>Free access — no costly soil testing or equipment required</li>
                <li>Allows farmers to have soil analyzed for free without specialized equipment</li>
                <li>Provides equal-quality insights for small and large farms (not cost dependent)</li>
              </ul>
            </div>
            <div className="landing-ethics-card">
              <h3 className="landing-ethics-head">Privacy</h3>
              <ul className="landing-ethics-list">
                <li>No personal farmer data collected or transmitted</li>
                <li>All inference runs on-device by default</li>
                <li>No farm location, yield, or financial data stored</li>
              </ul>
            </div>
            <div className="landing-ethics-card">
              <h3 className="landing-ethics-head">Inclusivity &amp; Access</h3>
              <ul className="landing-ethics-list">
                <li>Built around consumer smartphones — no specialized hardware</li>
                <li>Equal accessibility for small, mid-size, and large farms</li>
                <li>Results in plain language — no data science background needed</li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      {/* ── Impact & Feasibility ── */}
      <div id="impact" className="landing-wide-section landing-wide-section--alt">
        <div className="landing-wide-inner">
          <p className="landing-eyebrow">Why It Matters</p>
          <h2 className="landing-section-title">Impact &amp; Feasibility</h2>
          <div className="landing-wide-divider" />
          <div className="landing-impact-grid">
            {/* Panel 1 — Per-Farm Economic */}
            <div className="landing-impact-panel">
              <h3 className="landing-impact-head">Per-Farm Economic Impact <span className="landing-impact-sub">(359-acre corn operation)</span></h3>
              <table className="landing-impact-table">
                <thead>
                  <tr>
                    <th>Savings Source</th>
                    <th>Est. Savings</th>
                  </tr>
                </thead>
                <tbody>
                  <tr><td>Fertilizer reduction (12%)<sup>1,2</sup></td><td>~$8,600/season</td></tr>
                  <tr><td>Soil testing cost avoided<sup>3</sup></td><td>~$2,900/season</td></tr>
                  <tr className="landing-impact-total"><td>Total per farm</td><td>~$11,500/season</td></tr>
                </tbody>
              </table>
            </div>

            {/* Panel 2 — Environmental */}
            <div className="landing-impact-panel">
              <h3 className="landing-impact-head">Environmental Impact</h3>
              <ul className="landing-ethics-list">
                <li>Iowa applies ~3.7B lbs of N+P fertilizer annually<sup>4</sup></li>
                <li>12% reduction = ~444M lbs less per year</li>
                <li>Iowa agriculture contributes ~29% of nitrogen load to Gulf of Mexico hypoxic zone<sup>5</sup></li>
                <li>On-device inference eliminates cloud energy cost</li>
              </ul>
            </div>

            {/* Panel 3 — State-Level */}
            <div className="landing-impact-panel">
              <h3 className="landing-impact-head">State-Level Projection <span className="landing-impact-sub">(Iowa — 86,911 farms)</span></h3>
              <table className="landing-impact-table">
                <thead>
                  <tr>
                    <th>Adoption</th>
                    <th>Farms Reached</th>
                    <th>Annual Savings</th>
                  </tr>
                </thead>
                <tbody>
                  <tr><td>10%</td><td>~8,700 farms</td><td>~$100M</td></tr>
                  <tr><td>25%</td><td>~21,700 farms</td><td>~$250M</td></tr>
                </tbody>
              </table>
            </div>

            {/* Panel 4 — Scalability */}
            <div className="landing-impact-panel">
              <h3 className="landing-impact-head">Scalability</h3>
              <ul className="landing-ethics-list">
                <li>Works on any smartphone — 85%+ of US farmers already own one<sup>6</sup></li>
                <li>16 MB on-device model — no internet required in rural fields</li>
                <li>Open-source stack — minimal ongoing infrastructure cost</li>
              </ul>
            </div>
          </div>

          <p className="landing-footnotes">
            <sup>1</sup> Schimmelpfennig &amp; Ebel, USDA ERS (2016) &nbsp;
            <sup>2</sup> 359 acres × $200/acre × 12% &nbsp;
            <sup>3</sup> ISU Extension: 144 samples × $20 &nbsp;
            <sup>4</sup> Iowa Nutrient Reduction Strategy (2022) &nbsp;
            <sup>5</sup> EPA/USGS Gulf Hypoxia &nbsp;
            <sup>6</sup> USDA ERS (2023)
          </p>
        </div>
      </div>

      {/* ── Footer ── */}
      <footer className="landing-footer">
        SoilSense · Grinnell AI · Pi515 AI Challenge 2026 · Phase 3 Final Presentation · April 2026
      </footer>
    </div>
  )
}
