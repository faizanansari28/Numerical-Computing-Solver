import { useEffect, useState } from "react";
import { Link, NavLink, useLocation } from "react-router-dom";
import { Menu, X } from "lucide-react";
import { PROJECT } from "../data/team";

function Logo() {
  return (
    <svg width="18" height="18" viewBox="0 0 32 32" aria-hidden>
      <defs><linearGradient id="lg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stopColor="#8055FF" /><stop offset="1" stopColor="#627BFF" /></linearGradient></defs>
      <path d="M6 23 L12 9 L19 23 L26 9" fill="none" stroke="url(#lg)" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

const HOME_LINKS = [["HOME", "/"], ["EXPLORE METHODS", "/methods"], ["CALCULATOR", "/calculator"], ["ABOUT", "/#about"]];
const APP_LINKS = [["HOME", "/"], ["METHODS", "/methods"], ["CALCULATOR", "/calculator"], ["CHALLENGE", "/challenge"]];

export default function Navbar() {
  const { pathname } = useLocation();
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);
  const home = pathname === "/";
  const links = home ? HOME_LINKS : APP_LINKS;
  const sub = pathname.startsWith("/methods") ? "METHOD ARCHIVE" : pathname.startsWith("/calculator") ? "SOLVER" : pathname.startsWith("/challenge") ? "ARENA" : null;

  useEffect(() => {
    const on = () => setScrolled(window.scrollY > 20);
    on();
    window.addEventListener("scroll", on, { passive: true });
    return () => window.removeEventListener("scroll", on);
  }, []);
  useEffect(() => setOpen(false), [pathname]);

  const isActive = (to) => (to === "/" ? pathname === "/" : to.startsWith("/#") ? false : pathname.startsWith(to));

  return (
    <>
      <header className={`nav ${scrolled ? "scrolled" : ""}`}>
        <div className="container nav-inner">
          <Link to="/" className="brand" aria-label="NUMERIQ home">
            <span className="brand-mark"><Logo /></span>
            <span>{PROJECT.name}</span>
            {sub && <span className="brand-sub">/ {sub}</span>}
          </Link>
          <nav className="nav-links">
            {links.map(([label, to]) => (
              <NavLink key={label} to={to} className={`nav-link ${isActive(to) ? "active" : ""}`}>{label}</NavLink>
            ))}
            {home && <Link to="/calculator" className="btn btn-primary btn-sm nav-cta">Get started</Link>}
          </nav>
          <button className="nav-burger" onClick={() => setOpen(!open)} aria-label="Menu">{open ? <X size={18} /> : <Menu size={18} />}</button>
        </div>
      </header>
      {open && (
        <div className="mobile-menu">
          {[["Home", "/"], ["Explore methods", "/methods"], ["Calculator", "/calculator"], ["Challenge", "/challenge"], ["About", "/#about"]].map(([l, to]) => (
            <Link key={l} to={to} className={isActive(to) ? "active" : ""}>{l}</Link>
          ))}
        </div>
      )}
    </>
  );
}
