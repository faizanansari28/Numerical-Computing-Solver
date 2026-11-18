import { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import { CheckCircle2, AlertTriangle } from "lucide-react";
import { fmtNum, describeValue, isNum } from "../lib/format";
import Katex from "./Katex";

export const ease = [0.22, 1, 0.36, 1];

/* scroll-triggered fade up */
export function Reveal({ children, delay = 0, y = 26, className = "", style }) {
  return (
    <motion.div className={className} style={style} initial={{ opacity: 0, y }} whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-60px" }} transition={{ duration: 0.8, delay, ease }}>
      {children}
    </motion.div>
  );
}

/* number that counts up */
export function CountUp({ value, digits = 10, duration = 900 }) {
  const [shown, setShown] = useState(0);
  useEffect(() => {
    if (!isNum(value)) return;
    let raf, start;
    const tick = (t) => {
      start = start ?? t;
      const k = Math.min((t - start) / duration, 1);
      setShown(value * (1 - Math.pow(1 - k, 3)));
      if (k < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [value, duration]);
  if (!isNum(value)) return <>{fmtNum(value)}</>;
  const done = shown === value;
  return <>{fmtNum(done ? value : shown, done ? digits : 7)}</>;
}

export function Loader({ label = "Computing with Python…" }) {
  return (
    <div style={{ display: "grid", placeItems: "center", gap: 22, padding: "70px 0" }}>
      <div style={{ position: "relative", width: 86, height: 86 }}>
        {[0, 1, 2].map((i) => (
          <motion.span key={i} style={{ position: "absolute", inset: 0, borderRadius: "50%", border: "1px solid rgba(128,85,255,.7)" }}
            animate={{ scale: [0.3, 1.25], opacity: [0.9, 0] }} transition={{ duration: 1.8, repeat: Infinity, delay: i * 0.6, ease: "easeOut" }} />
        ))}
        <motion.span style={{ position: "absolute", inset: 30, borderRadius: "50%", background: "var(--grad)", boxShadow: "0 0 30px rgba(128,85,255,.9)" }}
          animate={{ scale: [1, 1.25, 1] }} transition={{ duration: 1.2, repeat: Infinity }} />
      </div>
      <span className="muted mono" style={{ fontSize: 12, letterSpacing: "0.12em" }}>{label}</span>
    </div>
  );
}

export function ErrorBox({ message }) {
  return (
    <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} style={{ border: "1px solid rgba(255,107,129,.4)", background: "rgba(255,107,129,.07)", borderRadius: 14, padding: "18px 20px", display: "flex", gap: 14 }}>
      <AlertTriangle size={20} color="var(--red)" style={{ flexShrink: 0, marginTop: 2 }} />
      <div><div style={{ fontWeight: 600, marginBottom: 4 }}>This input can't be computed</div><div className="muted" style={{ fontSize: 14 }}>{message}</div></div>
    </motion.div>
  );
}

export function StatusBar({ status, time, iterations }) {
  const warn = status.state === "warning";
  return (
    <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: 14, padding: "12px 16px", border: "1px solid var(--line)", borderRadius: 12, background: "var(--panel)" }}>
      <span className={`dot ${warn ? "warn" : ""}`} />
      <span style={{ fontSize: 13.5, flex: 1, minWidth: 200 }}>{status.message}</span>
      {iterations != null && <span className="mono muted" style={{ fontSize: 12 }}>{iterations} iterations</span>}
      <span className="mono muted" style={{ fontSize: 12 }}>{time} ms</span>
      {warn ? <AlertTriangle size={16} color="var(--gold)" /> : <CheckCircle2 size={16} color="var(--green)" />}
    </div>
  );
}

/* big answer cards */
export function AnswerCards({ answers }) {
  return (
    <div style={{ display: "grid", gap: 12 }}>
      {answers.map((a, i) => {
        const scalar = isNum(a.value);
        return (
          <motion.div key={a.label} initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.08, duration: 0.6, ease }}
            style={{ border: "1px solid var(--line-2)", borderRadius: 16, padding: "20px 22px", background: i === 0 ? "linear-gradient(135deg, rgba(128,85,255,.16), rgba(98,123,255,.05))" : "var(--panel)", position: "relative", overflow: "hidden" }}>
            <div className="eyebrow" style={{ color: i === 0 ? "#b9a3ff" : "var(--dim)", marginBottom: 10 }}>{a.label}</div>
            {scalar ? (
              <div className="mono" style={{ fontSize: "clamp(26px, 4vw, 40px)", fontWeight: 500, letterSpacing: "-0.03em", wordBreak: "break-all" }}><CountUp value={a.value} /></div>
            ) : (
              <pre className="mono" style={{ margin: 0, fontSize: 13.5, whiteSpace: "pre-wrap", wordBreak: "break-word", lineHeight: 1.7 }}>{describeValue(a.value)}</pre>
            )}
          </motion.div>
        );
      })}
    </div>
  );
}

export function StepsList({ steps }) {
  return (
    <ol style={{ listStyle: "none", margin: 0, padding: 0, display: "grid", gap: 10 }}>
      {steps.map((s, i) => (
        <motion.li key={i} initial={{ opacity: 0, x: -14 }} whileInView={{ opacity: 1, x: 0 }} viewport={{ once: true, margin: "-30px" }} transition={{ duration: 0.5, delay: Math.min(i, 6) * 0.04, ease }}
          style={{ display: "grid", gridTemplateColumns: "34px 1fr", gap: 12, alignItems: "start" }}>
          <span className="mono" style={{ width: 28, height: 28, borderRadius: 8, border: "1px solid var(--line-2)", display: "grid", placeItems: "center", fontSize: 11, color: "var(--purple)" }}>{i + 1}</span>
          <span style={{ fontSize: 14.5, color: "#dcdce6", paddingTop: 3, overflowWrap: "anywhere" }}>{s}</span>
        </motion.li>
      ))}
    </ol>
  );
}

export function DataTable({ table }) {
  const { columns, rows, title, total_rows, truncated_at } = table;
  if (!columns.length) return null;
  return (
    <div>
      {title && <div style={{ fontSize: 13, color: "var(--muted)", marginBottom: 10, fontWeight: 500 }}>{title}</div>}
      <div className="table-wrap">
        <table className="data">
          <thead><tr>{columns.map((c) => <th key={c}>{c}</th>)}</tr></thead>
          <tbody>
            {rows.map((r, i) => (
              <motion.tr key={i} initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }} transition={{ delay: Math.min(i, 14) * 0.035, duration: 0.4 }}>
                {r.map((c, j) => <td key={j} className={typeof c === "string" && j > 0 ? "txt" : ""}>{fmtNum(c, 9)}</td>)}
              </motion.tr>
            ))}
          </tbody>
        </table>
      </div>
      {total_rows && <div className="help" style={{ marginTop: 8 }}>Showing the first {truncated_at} and last {truncated_at} of {total_rows} rows.</div>}
    </div>
  );
}

/* graph that is revealed with a smooth wipe */
export function PlotImage({ b64, alt = "Graph" }) {
  if (!b64) return null;
  return (
    <motion.div initial={{ clipPath: "inset(0 100% 0 0)", opacity: 0.2 }} whileInView={{ clipPath: "inset(0 0% 0 0)", opacity: 1 }} viewport={{ once: true }} transition={{ duration: 1.3, ease }}
      style={{ border: "1px solid var(--line)", borderRadius: 16, overflow: "hidden", background: "#0c0c14" }}>
      <img src={`data:image/png;base64,${b64}`} alt={alt} style={{ width: "100%", display: "block" }} />
    </motion.div>
  );
}

export function ErrorPanel({ analysis, exact }) {
  const rows = [];
  if (exact) {
    rows.push(["Exact answer", <span className="mono" key="e">{describeValue(exact.value)}</span>, exact.label]);
    rows.push(["Absolute error (vs exact)", fmtNum(exact.absolute_error), "|numerical − exact|"]);
    if (exact.relative_error != null) rows.push(["Relative error (vs exact)", fmtNum(exact.relative_error), "|numerical − exact| / |exact|"]);
  }
  if (analysis.reference_label) {
    const v = analysis.reference_value;
    rows.push([`Reference: ${analysis.reference_label}`, <span className="mono" key="r" style={{ whiteSpace: "pre-wrap" }}>{describeValue(v)}</span>, "independent check with a library routine"]);
    rows.push([exact ? "Absolute difference (vs reference)" : "Absolute error", fmtNum(analysis.absolute_error), "|NUMERIQ − reference|"]);
    if (analysis.relative_error != null) rows.push([exact ? "Relative difference (vs reference)" : "Relative error", fmtNum(analysis.relative_error), ""]);
  }
  if (analysis.iterations != null) rows.push(["Iterations / steps", analysis.iterations, ""]);
  if (analysis.converged != null) rows.push(["Converged", analysis.converged ? "Yes" : "No", ""]);
  analysis.metrics.forEach((m) => rows.push([m.label, fmtNum(m.value), ""]));
  return (
    <div>
      <div style={{ border: "1px solid var(--line)", borderRadius: 14, overflow: "hidden" }}>
        {rows.map(([k, v, hint], i) => (
          <div key={i} style={{ display: "grid", gridTemplateColumns: "minmax(140px, 1.1fr) 1.2fr", gap: 14, padding: "12px 16px", borderBottom: i < rows.length - 1 ? "1px solid var(--line)" : "none", alignItems: "baseline" }}>
            <div><div style={{ fontSize: 13.5 }}>{k}</div>{hint && <div className="help">{hint}</div>}</div>
            <div className="mono" style={{ fontSize: 13.5, overflowWrap: "anywhere" }}>{v}</div>
          </div>
        ))}
      </div>
      {analysis.notes.filter(Boolean).map((n, i) => (<p key={i} className="muted" style={{ fontSize: 13, marginTop: 10, display: "flex", gap: 8 }}><span style={{ color: "var(--purple)" }}>›</span>{n}</p>))}
    </div>
  );
}

export function FormulaBlock({ tex }) {
  return (
    <div style={{ border: "1px solid var(--line)", borderRadius: 14, padding: "10px 18px", background: "var(--panel)", textAlign: "center", overflowX: "auto" }}>
      <Katex tex={tex} display />
    </div>
  );
}

/* Python code with the explanation of every line on the right */
const KW = /\b(def|return|for|in|if|else|elif|while|break|import|from|print|range|len|abs|max|min|sum|True|False|None|and|or|not)\b/g;
function highlight(src) {
  const parts = [];
  const re = /("[^"]*"|'[^']*')|(\b\d+\.?\d*(?:e[-+]?\d+)?\b)|\b(def|return|for|in|if|else|elif|while|break|import|from|and|or|not|True|False|None)\b|\b(print|range|len|abs|max|min|sum)\b/g;
  let last = 0, m, k = 0;
  while ((m = re.exec(src))) {
    if (m.index > last) parts.push(src.slice(last, m.index));
    const cls = m[1] ? "tk-str" : m[2] ? "tk-num" : m[3] ? "tk-kw" : "tk-fn";
    parts.push(<span key={k++} className={cls}>{m[0]}</span>);
    last = m.index + m[0].length;
  }
  parts.push(src.slice(last));
  return parts;
}

export function CodeBlock({ code }) {
  const lines = code.split("\n");
  return (
    <div className="code">
      <div style={{ padding: "10px 0" }}>
        {lines.map((raw, i) => {
          const hash = raw.indexOf("#");
          const inString = hash >= 0 && (raw.slice(0, hash).match(/["']/g) || []).length % 2 === 1;
          const hasNote = hash >= 0 && !inString;
          const src = hasNote ? raw.slice(0, hash).replace(/\s+$/, "") : raw;
          const note = hasNote ? raw.slice(hash + 1).trim() : "";
          const fullComment = hasNote && src.trim() === "";
          return (
            <div className="code-line" key={i}>
              <span className="code-no">{i + 1}</span>
              {fullComment ? <span className="tk-cm" style={{ gridColumn: "2 / span 2", whiteSpace: "pre-wrap" }}># {note}</span> : (<><span className="code-src">{highlight(src) || " "}</span><span className="code-note" style={{ visibility: note ? "visible" : "hidden" }}>{note || "."}</span></>)}
            </div>
          );
        })}
      </div>
    </div>
  );
}
