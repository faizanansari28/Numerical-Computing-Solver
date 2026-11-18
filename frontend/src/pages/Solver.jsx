import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Download, RotateCcw, Play, Sigma } from "lucide-react";
import Katex from "../components/Katex";
import { Reveal, Loader, ErrorBox, StatusBar, AnswerCards, StepsList, DataTable, PlotImage, ErrorPanel, FormulaBlock } from "../components/Results";
import { api } from "../api";
import { CATEGORIES } from "../data/methods";
import { download, downloadBase64Png, resultToText, tablesToCsv } from "../lib/format";

export function Field({ f, value, onChange, vals }) {
  if (f.showIf && !Object.entries(f.showIf).every(([k, v]) => vals[k] === v)) return null;
  const common = { id: `f-${f.name}`, value: value ?? "", onChange: (e) => onChange(e.target.value), spellCheck: false, autoComplete: "off" };
  return (
    <div className="field">
      <label htmlFor={common.id}>{f.label}{f.optional ? " (optional)" : ""}</label>
      {f.type === "select" ? (
        <select className="select" {...common}>{f.options.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}</select>
      ) : f.type === "matrix" ? (
        <textarea className="textarea" rows={Math.min(6, Math.max(3, String(value || "").split("\n").length))} {...common} />
      ) : (
        <input className={`input ${f.type === "expr" || f.type === "list" ? "mono" : ""}`} {...common} />
      )}
      {f.help && <div className="help">{f.help}</div>}
    </div>
  );
}

export default function Solver() {
  const [sp, setSp] = useSearchParams();
  const [catalog, setCatalog] = useState(null);
  const [loadErr, setLoadErr] = useState("");
  const [methodId, setMethodId] = useState(sp.get("method") || "");
  const [store, setStore] = useState({});
  const [res, setRes] = useState(null);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => { api.catalog().then(setCatalog).catch((e) => setLoadErr(e.message)); }, []);
  const methods = catalog?.methods || [];
  const method = methods.find((m) => m.id === methodId);
  const catId = method?.category || sp.get("cat") || CATEGORIES[0].id;
  const inCat = methods.filter((m) => m.category === catId);

  useEffect(() => {
    if (catalog && !method) setMethodId((methods.find((m) => m.category === catId) || methods[0]).id);
  }, [catalog]); // eslint-disable-line

  const defaults = useMemo(() => Object.fromEntries((method?.inputs || []).map((f) => [f.name, f.default])), [method]);
  const vals = { ...defaults, ...(store[methodId] || {}) };
  const setVal = (k, v) => setStore((s) => ({ ...s, [methodId]: { ...(s[methodId] || {}), [k]: v } }));
  const pick = (id) => { setMethodId(id); setRes(null); setErr(""); setSp({ method: id }, { replace: true }); };
  const pickCat = (c) => { const m = methods.find((x) => x.category === c); if (m) pick(m.id); };

  const run = async () => {
    setBusy(true); setErr("");
    try {
      const params = {};
      method.inputs.forEach((f) => { if (!f.showIf || Object.entries(f.showIf).every(([k, v]) => vals[k] === v)) params[f.name] = vals[f.name]; });
      const out = await api.solve(methodId, params);
      setRes({ ...out, _params: params });
    } catch (e) { setRes(null); setErr(e.message); }
    setBusy(false);
  };
  const reset = () => { setStore((s) => ({ ...s, [methodId]: {} })); setRes(null); setErr(""); };

  const slug = methodId;
  return (
    <div className="page">
      <div className="container">
        <div className="page-head">
          <div className="eyebrow">Solver</div>
          <h1>Your Problem.<br /><span className="grad-text">Our Computation.</span></h1>
          <p>Pick a method, enter your own values, and get the answer, every step, the iteration table, a graph and an honest error analysis, all computed by Python.</p>
        </div>
        {loadErr && <ErrorBox message={loadErr} />}
        {!catalog && !loadErr && <Loader label="Connecting to the Python backend…" />}
        {catalog && method && (
          <div className="solver-grid">
            <aside className="panel solver-form">
              <div className="field"><label>Category</label>
                <select className="select" value={catId} onChange={(e) => pickCat(e.target.value)}>{CATEGORIES.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}</select></div>
              <div className="field"><label>Method</label>
                <select className="select" value={methodId} onChange={(e) => pick(e.target.value)}>{inCat.map((m) => <option key={m.id} value={m.id}>{m.name}</option>)}</select></div>
              <div className="formula-mini"><Katex tex={method.formula} /></div>
              <div className="form-fields">
                {method.inputs.map((f) => <Field key={methodId + f.name} f={f} value={vals[f.name]} vals={vals} onChange={(v) => setVal(f.name, v)} />)}
              </div>
              <div className="form-actions">
                <button className="btn btn-primary" onClick={run} disabled={busy}>{busy ? <span className="spinner" /> : <Play size={14} />} Calculate</button>
                <button className="btn" onClick={reset} disabled={busy}><RotateCcw size={14} /> Reset</button>
              </div>
            </aside>

            <section className="solver-out">
              {busy && <Loader />}
              {err && !busy && <ErrorBox message={err} />}
              {!res && !busy && !err && (
                <div className="empty"><Sigma size={34} strokeWidth={1.3} /><h3>Ready when you are</h3><p>Fill in the form (the defaults already work) and press <b>Calculate</b>.</p></div>
              )}
              {res && !busy && (
                <div className="out-stack">
                  <div className="out-head">
                    <div><div className="eyebrow">Result</div><h2>{res.title}</h2></div>
                    <div className="dl">
                      <button className="btn btn-sm" onClick={() => download(`numeriq_${slug}.txt`, resultToText(res.title, res._params, res))}><Download size={13} /> TXT</button>
                      <button className="btn btn-sm" onClick={() => download(`numeriq_${slug}.csv`, tablesToCsv(res.tables), "text/csv")}><Download size={13} /> CSV</button>
                      {res.plot && <button className="btn btn-sm" onClick={() => downloadBase64Png(`numeriq_${slug}.png`, res.plot)}><Download size={13} /> PNG</button>}
                    </div>
                  </div>
                  <StatusBar status={res.status} time={res.time_ms} iterations={res.error_analysis.iterations} />
                  <AnswerCards answers={res.answers} />
                  <div><h3 className="blk">Formula used</h3><FormulaBlock tex={res.formula} /></div>
                  <div><h3 className="blk">Step-by-step solution</h3><StepsList steps={res.steps} /></div>
                  {res.tables.filter((t) => t.columns.length).map((t, i) => <DataTable key={i} table={t} />)}
                  {res.plot && <div><h3 className="blk">Graph</h3><PlotImage b64={res.plot} /></div>}
                  <div><h3 className="blk">Error analysis</h3><ErrorPanel analysis={res.error_analysis} /></div>
                </div>
              )}
            </section>
          </div>
        )}
      </div>
    </div>
  );
}
