import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import { ChevronLeft, ChevronRight, ArrowUpRight } from "lucide-react";
import MethodArt from "../components/MethodArt";
import { CATEGORIES, METHODS, catById } from "../data/methods";

export default function Learn() {
  const nav = useNavigate();
  const [cat, setCat] = useState("all");
  const [active, setActive] = useState(0);
  const [hover, setHover] = useState(null);
  const [leaving, setLeaving] = useState(null);
  const list = useMemo(() => (cat === "all" ? METHODS : METHODS.filter((m) => m.cat === cat)), [cat]);
  const stage = useRef(null);
  const wheelLock = useRef(0);
  const drag = useRef(null);
  const n = list.length;
  const go = useCallback((d) => setActive((a) => Math.min(Math.max(a + d, 0), n - 1)), [n]);
  useEffect(() => setActive(0), [cat]);

  const open = (m) => { setLeaving(m.id); setTimeout(() => nav(`/methods/${m.id}`), 420); };

  useEffect(() => {
    const key = (e) => {
      if (e.key === "ArrowRight") go(1);
      else if (e.key === "ArrowLeft") go(-1);
      else if (e.key === "Enter" && list[active]) open(list[active]);
    };
    window.addEventListener("keydown", key);
    return () => window.removeEventListener("keydown", key);
  });
  useEffect(() => {
    const el = stage.current;
    const wheel = (e) => {
      const d = Math.abs(e.deltaX) > Math.abs(e.deltaY) ? e.deltaX : e.deltaY;
      if (Math.abs(d) < 12) return;
      e.preventDefault();
      const now = Date.now();
      if (now - wheelLock.current < 260) return;
      wheelLock.current = now;
      go(d > 0 ? 1 : -1);
    };
    el.addEventListener("wheel", wheel, { passive: false });
    return () => el.removeEventListener("wheel", wheel);
  }, [go]);

  const onDown = (e) => { drag.current = { x: e.clientX, moved: false }; };
  const onMove = (e) => {
    const d = drag.current; if (!d) return;
    const dx = e.clientX - d.x;
    if (Math.abs(dx) > 70) { go(dx < 0 ? 1 : -1); d.x = e.clientX; d.moved = true; }
  };
  const onUp = () => setTimeout(() => (drag.current = null), 0);

  const focus = list[hover ?? active] || list[0];
  const c = focus && catById[focus.cat];

  return (
    <div className="page">
      <div className="container">
        <div className="page-head">
          <div className="eyebrow">Method archive</div>
          <h1>Forty methods.<br /><span className="grad-text">One way to understand each.</span></h1>
        </div>
        <div className="chip-row">
          <button className={`chip ${cat === "all" ? "on" : ""}`} onClick={() => setCat("all")}>All · {METHODS.length}</button>
          {CATEGORIES.map((k) => (
            <button key={k.id} className={`chip ${cat === k.id ? "on" : ""}`} onClick={() => setCat(k.id)}>{k.short}</button>
          ))}
        </div>
      </div>

      <div className="carousel" ref={stage} onPointerDown={onDown} onPointerMove={onMove} onPointerUp={onUp} onPointerLeave={onUp}>
        <button className="car-arrow left" onClick={() => go(-1)} disabled={active === 0} aria-label="Previous"><ChevronLeft /></button>
        <button className="car-arrow right" onClick={() => go(1)} disabled={active === n - 1} aria-label="Next"><ChevronRight /></button>
        <div className="car-track">
          {list.map((m, i) => {
            const d = i - active;
            if (Math.abs(d) > 3) return null;
            const ad = Math.abs(d), sgn = Math.sign(d);
            const hoveredSide = hover !== null && hover !== active && Math.abs(hover - i) === 1 ? 1 : 0;
            const tx = d === 0 ? 0 : sgn * (270 + (ad - 1) * 150 + hoveredSide * 0);
            const style = {
              transform: `translate(-50%, -50%) translateX(${tx}px) translateZ(${-ad * 120}px) rotateY(${-sgn * Math.min(ad, 1.4) * 38}deg) scale(${d === 0 ? 1 : 0.84 - ad * 0.04})`,
              opacity: leaving ? (leaving === m.id ? 1 : 0) : 1 - ad * 0.22,
              zIndex: 10 - ad, filter: d === 0 ? "none" : `brightness(${0.78 - ad * 0.1})`,
            };
            return (
              <div key={m.id} className={`car-card ${d === 0 ? "center" : ""} ${leaving === m.id ? "leaving" : ""}`} style={style}
                onMouseEnter={() => setHover(i)} onMouseLeave={() => setHover(null)}
                onClick={() => { if (drag.current?.moved) return; d === 0 ? open(m) : setActive(i); }}>
                <div className="car-art"><MethodArt cat={m.cat} seed={i} /></div>
                <div className="car-meta"><span className="mono">{String(METHODS.indexOf(m) + 1).padStart(2, "0")}</span><span>{catById[m.cat].short}</span></div>
                <div className="car-name">{m.name}</div>
                <div className="car-view"><span>VIEW</span><ArrowUpRight size={14} /></div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="container">
        <AnimatePresence mode="wait">
          {focus && (
            <motion.div key={focus.id} className="car-caption" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} transition={{ duration: 0.28 }}>
              <div className="eyebrow">{c.name}</div>
              <h2>{focus.name}</h2>
              <p>{focus.blurb}</p>
            </motion.div>
          )}
        </AnimatePresence>
        <div className="car-dots">
          {list.map((m, i) => <button key={m.id} aria-label={m.name} className={i === active ? "on" : ""} onClick={() => setActive(i)} />)}
        </div>
        <p className="help" style={{ textAlign: "center", marginTop: 14 }}>← → arrow keys, mouse wheel or drag to browse · Enter or click the centre card to open</p>
      </div>
    </div>
  );
}
