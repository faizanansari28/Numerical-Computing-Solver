import { useEffect, useRef } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowRight, BookOpen, Eye, Calculator, Trophy, ChevronDown } from "lucide-react";
import Brain from "../components/Brain";
import { Reveal } from "../components/Results";
import { PROJECT, TEAM } from "../data/team";

const clamp = (x, a = 0, b = 1) => Math.min(Math.max(x, a), b);
const smooth = (x) => x * x * (3 - 2 * x);
const tri = (p, c, w) => smooth(clamp(1 - Math.abs(p - c) / w));

const HIGHLIGHTS = [
  { icon: BookOpen, title: "EXPLORE", text: "Understand numerical methods.", to: "/methods" },
  { icon: Eye, title: "VISUALIZE", text: "See mathematical concepts.", to: "/methods" },
  { icon: Calculator, title: "CALCULATE", text: "Solve your own problems.", to: "/calculator" },
  { icon: Trophy, title: "PRACTICE", text: "Test your understanding.", to: "/challenge" },
];

export default function Home() {
  const story = useRef(null);
  const progress = useRef(0);
  const layers = { hero: useRef(null), s2: useRef(null), s3: useRef(null), s4: useRef(null) };

  useEffect(() => {
    let raf;
    const update = () => {
      const el = story.current;
      if (el) {
        const vh = window.innerHeight;
        const top = el.getBoundingClientRect().top;
        const p = clamp(-top / vh, 0, 3);
        progress.current = p;
        const set = (ref, o, y = 0) => {
          if (!ref.current) return;
          ref.current.style.opacity = o;
          ref.current.style.transform = `translateY(${y}px)`;
          ref.current.style.visibility = o < 0.02 ? "hidden" : "visible";
          ref.current.style.pointerEvents = o > 0.5 ? "auto" : "none";
        };
        set(layers.hero, 1 - smooth(clamp(p / 0.55)), -p * 60);
        set(layers.s2, tri(p, 1, 0.5), (1 - p) * 40);
        set(layers.s3, tri(p, 2, 0.5), (2 - p) * 40);
        set(layers.s4, smooth(clamp((p - 2.5) / 0.5)), (1 - clamp((p - 2.5) / 0.5)) * 30);
      }
      raf = requestAnimationFrame(update);
    };
    raf = requestAnimationFrame(update);
    return () => cancelAnimationFrame(raf);
  }, []);

  return (
    <>
      <div className="story" ref={story}>
        <div className="stage">
          <div className="stage-canvas"><Brain progress={progress} /></div>
          <div className="stage-vignette" />

          <div className="layer layer-hero" ref={layers.hero}>
            <div className="container hero-inner">
              <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 1, delay: 0.2, ease: [0.22, 1, 0.36, 1] }} className="hero-copy">
                <div className="eyebrow">The future of numerical computing</div>
                <h1 className="hero-title">Understand the Mathematics.<br /><span className="grad-text">Experience the Computation.</span></h1>
                <p className="hero-sub">Explore numerical methods, understand the mathematics behind them, and solve real computational problems through interactive visualizations.</p>
                <div className="hero-actions">
                  <Link to="/methods" className="btn btn-primary">Explore methods <ArrowRight size={15} /></Link>
                  <Link to="/calculator" className="btn">Start calculating</Link>
                </div>
              </motion.div>
            </div>
            <div className="scroll-hint"><span>SCROLL</span><motion.i animate={{ y: [0, 7, 0] }} transition={{ duration: 1.6, repeat: Infinity }}><ChevronDown size={16} /></motion.i></div>
          </div>

          <div className="layer layer-center" ref={layers.s2} style={{ opacity: 0, visibility: "hidden" }}>
            <div className="center-copy">
              <div className="eyebrow">01 — Method</div>
              <h2>Mathematics meets computation.</h2>
              <p>Numerical methods transform complex mathematical problems into computational solutions. Discover how different algorithms approximate, calculate and solve problems.</p>
            </div>
          </div>

          <div className="layer layer-center" ref={layers.s3} style={{ opacity: 0, visibility: "hidden" }}>
            <div className="center-copy">
              <div className="eyebrow">02 — Process</div>
              <h2>From equations to solutions.</h2>
              <p>Every calculation has a method. Every method has a story. Understand the process, explore the mathematics and see the results.</p>
            </div>
          </div>

          <div className="layer layer-highlights" ref={layers.s4} style={{ opacity: 0, visibility: "hidden" }}>
            <div className="container">
              <div className="highlight-grid">
                {HIGHLIGHTS.map((h, i) => (
                  <Link key={h.title} to={h.to} className="highlight">
                    <span className="hl-no mono">0{i + 1}</span>
                    <h.icon size={20} strokeWidth={1.6} />
                    <h3>{h.title}</h3>
                    <p>{h.text}</p>
                    <ArrowRight size={16} className="hl-arrow" />
                  </Link>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      <section id="about" className="team">
        <div className="container">
          <Reveal><div className="eyebrow">The developers</div></Reveal>
          <Reveal delay={0.08}><h2 className="team-title">Built by two engineers<br /><span className="muted">who wanted to see the mathematics move.</span></h2></Reveal>
          <div className="team-grid">
            {TEAM.map((t, i) => (
              <Reveal key={t.roll} delay={0.1 + i * 0.12}>
                <div className="person hot">
                  <div className="person-mono mono">{t.name.split(" ").map((w) => w[0]).slice(-2).join("")}</div>
                  <div className="person-name">{t.name}</div>
                  <div className="person-roll mono">Roll Number: {t.roll}</div>
                  <div className="person-meta">{PROJECT.short}<br />{PROJECT.dept}</div>
                  <span className="person-line" />
                </div>
              </Reveal>
            ))}
          </div>
          <Reveal delay={0.1}>
            <div className="course-strip">
              <div><div className="eyebrow" style={{ color: "var(--dim)" }}>Course</div><div>{PROJECT.course}</div></div>
              <div><div className="eyebrow" style={{ color: "var(--dim)" }}>University</div><div>{PROJECT.university}</div></div>
              <Link to="/methods" className="btn btn-primary">Enter the archive <ArrowRight size={15} /></Link>
            </div>
          </Reveal>
        </div>
      </section>
    </>
  );
}
