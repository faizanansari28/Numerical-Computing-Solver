import { Link } from "react-router-dom";
import { PROJECT, TEAM } from "../data/team";

export default function Footer() {
  return (
    <footer className="footer">
      <div className="container">
        <div className="footer-grid">
          <div>
            <div className="brand" style={{ marginBottom: 14 }}>{PROJECT.name}</div>
            <p className="muted" style={{ fontSize: 14, maxWidth: 360 }}>{PROJECT.full}. Understand the mathematics, experience the computation.</p>
            <p className="muted" style={{ fontSize: 13, marginTop: 18 }}>{PROJECT.course}<br />{PROJECT.university}</p>
          </div>
          <div>
            <h4>Navigate</h4>
            <Link to="/">Home</Link><Link to="/methods">Explore methods</Link><Link to="/calculator">Calculator</Link><Link to="/challenge">Challenge arena</Link>
          </div>
          <div>
            <h4>Built by</h4>
            {TEAM.map((t) => (<span key={t.roll} style={{ display: "block", color: "var(--muted)", fontSize: 14, padding: "4px 0" }}>{t.name} <span className="mono" style={{ color: "var(--dim)", fontSize: 12 }}>· {t.roll}</span></span>))}
            <span style={{ display: "block", color: "var(--dim)", fontSize: 13, paddingTop: 8 }}>{PROJECT.dept}</span>
          </div>
        </div>
        <div className="footer-bottom"><span>© 2026 {PROJECT.name} · {PROJECT.short}</span><span>Every result is computed by real Python algorithms.</span></div>
      </div>
    </footer>
  );
}
