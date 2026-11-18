import { useEffect, useState } from "react";
import { Play, Trophy, Zap, Target, Clock } from "lucide-react";
import { motion } from "framer-motion";
import Katex from "../components/Katex";
import { Loader, ErrorBox, PlotImage, ease } from "../components/Results";
import { Field } from "./Solver";
import { api } from "../api";
import { fmtNum, describeValue } from "../lib/format";

export default function Challenge() {
  const [defs, setDefs] = useState(null);
  const [loadErr, setLoadErr] = useState("");
  const [cid, setCid] = useState("root");
  const [picked, setPicked] = useState({});
  const [knobs, setKnobs] = useState({});
  const [out, setOut] = useState(null);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => { api.challenges().then((d) => setDefs(d.challenges)).catch((e) => setLoadErr(e.message)); }, []);
  const ch = defs?.find((d) => d.id === cid);
  const sel = picked[cid] || ch?.methods.map((m) => m.id) || [];
  const toggle = (id) => setPicked((p) => ({ ...p, [cid]: sel.includes(id) ? sel.filter((x) => x !== id) : [...sel, id] }));
  const kv = (k) => ({ ...Object.fromEntries((ch?.knobs || []).map((f) => [f.name, f.default])), ...(knobs[cid] || {}) })[k];
  const change = (id) => { setCid(id); setOut(null); setErr(""); };

  const run = async () => {
    setBusy(true); setErr("");
    try {
      const k = {}; ch.knobs.forEach((f) => (k[f.name] = kv(f.name)));
      setOut(await api.runChallenge(cid, sel, k));
    } catch (e) { setOut(null); setErr(e.message); }
    setBusy(false);
  };
  const maxErr = out ? Math.max(...out.results.map((r) => r.abs_error ?? 0), 1e-300) : 1;
  const rank = (id) => out.ranking.indexOf(id);
  const byId = out ? Object.fromEntries(out.results.map((r) => [r.id, r])) : {};

  return (
    <div className="page">
      <div className="container">
        <div className="page-head">
          <div className="eyebrow">Arena</div>
          <h1>One Problem.<br /><span className="grad-text">Multiple Perspectives.</span></h1>
          <p>Choose a problem, let several methods attack it, and compare accuracy, speed and effort side by side.</p>
        </div>
        {loadErr && <ErrorBox message={loadErr} />}
        {!defs && !loadErr && <Loader label="Connecting to the Python backend…" />}
        {ch && (
          <>
            <div className="chip-row" style={{ marginBottom: 26 }}>
              {defs.map((d) => <button key={d.id} className={`chip ${cid === d.id ? "on" : ""}`} onClick={() => change(d.id)}>{d.title.replace(" Challenge", "")}</button>)}
            </div>
            <div className="solver-grid">
              <aside className="panel solver-form">
                <div className="eyebrow">{ch.title}</div>
                <div className="formula-mini" style={{ fontSize: 15 }}><Katex tex={ch.statement} /></div>
                <p className="muted" style={{ fontSize: 13.5, margin: 0 }}>{ch.context}</p>
                <div className="field"><label>Methods to run</label>
                  <div className="chip-row">{ch.methods.map((m) => <button key={m.id} className={`chip ${sel.includes(m.id) ? "on" : ""}`} onClick={() => toggle(m.id)}>{m.name}</button>)}</div></div>
                <div className="form-fields">
                  {ch.knobs.map((f) => <Field key={cid + f.name} f={f} vals={{}} value={kv(f.name)} onChange={(v) => setKnobs((s) => ({ ...s, [cid]: { ...(s[cid] || {}), [f.name]: v } }))} />)}
                </div>
                <button className="btn btn-primary" onClick={run} disabled={busy || !sel.length}>{busy ? <span className="spinner" /> : <Play size={14} />} RUN ALL APPLICABLE METHODS</button>
              </aside>

              <section className="solver-out">
                {busy && <Loader label="Running every method…" />}
                {err && !busy && <ErrorBox message={err} />}
                {!out && !busy && !err && <div className="empty"><Trophy size={34} strokeWidth={1.3} /><h3>Pick your contenders</h3><p>Press the button and see who wins on accuracy and speed.</p></div>}
                {out && !busy && (
                  <div className="out-stack">
                    <div className="badges">
                      <span className="badge"><Target size={14} /> Most accurate: <b>{byId[out.ranking[0]]?.name}</b></span>
                      <span className="badge"><Clock size={14} /> Fastest: <b>{byId[out.fastest]?.name}</b></span>
                      {out.fewest_work && <span className="badge"><Zap size={14} /> Least work: <b>{byId[out.fewest_work]?.name}</b></span>}
                    </div>
                    <div className="board">
                      {out.ranking.map((id, i) => {
                        const r = byId[id];
                        const w = r.abs_error ? Math.max(4, 100 - (Math.log10(r.abs_error / maxErr) * -9)) : 100;
                        return (
                          <motion.div key={id} className="board-row" initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.08, ease }}>
                            <div className="board-rank mono">{i + 1}</div>
                            <div className="board-main">
                              <div className="board-name">{r.name}{!r.converged && <span className="tag warn">did not converge</span>}</div>
                              <div className="bar"><motion.i initial={{ width: 0 }} animate={{ width: `${Math.min(100, w)}%` }} transition={{ duration: 0.9, delay: 0.2 + i * 0.08, ease }} /></div>
                              <div className="board-note">{r.note}</div>
                            </div>
                            <div className="board-stats mono">
                              <span>err {fmtNum(r.abs_error, 4)}</span>
                              <span>{r.iterations != null ? `${r.iterations} it` : ""}{r.evaluations != null ? ` · ${r.evaluations} f-evals` : ""}</span>
                              <span>{fmtNum(r.time_ms, 3)} ms</span>
                            </div>
                          </motion.div>
                        );
                      })}
                    </div>
                    <div className="table-wrap">
                      <table className="data">
                        <thead><tr><th>Method</th><th>Result</th><th>Abs. error</th><th>Iterations</th><th>Evaluations</th><th>Time (ms)</th></tr></thead>
                        <tbody>{out.results.map((r) => (
                          <tr key={r.id}><td className="txt">{r.name}</td><td style={{ whiteSpace: "pre-wrap" }}>{describeValue(r.value)}</td><td>{fmtNum(r.abs_error, 4)}</td><td>{fmtNum(r.iterations)}</td><td>{fmtNum(r.evaluations)}</td><td>{fmtNum(r.time_ms, 3)}</td></tr>
                        ))}</tbody>
                      </table>
                    </div>
                    {out.plot && <PlotImage b64={out.plot} alt="Comparison graph" />}
                    <p className="help">Errors are measured against {out.reference?.label}: <span className="mono">{describeValue(out.reference?.value)}</span></p>
                  </div>
                )}
              </section>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
