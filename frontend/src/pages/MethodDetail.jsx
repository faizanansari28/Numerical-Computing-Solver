import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, ArrowRight, Calculator } from "lucide-react";
import Katex from "../components/Katex";
import { Reveal, Loader, ErrorBox, StepsList, DataTable, PlotImage, ErrorPanel, FormulaBlock, CodeBlock, AnswerCards, StatusBar } from "../components/Results";
import { api } from "../api";
import { METHODS, byId, catById, indexOfMethod } from "../data/methods";

const SECTIONS = [
  ["A", "Introduction"], ["B", "Mathematical foundation"], ["C", "Worked example"], ["D", "Iteration table"],
  ["E", "Graph"], ["F", "Final result"], ["G", "Advantages & limitations"], ["H", "Related methods"],
];

function Section({ id, letter, title, children }) {
  return (
    <section id={`sec-${id}`} className="md-sec" data-sec={id}>
      <Reveal><h2><span className="mono">{letter}</span>{title}</h2></Reveal>
      {children}
    </section>
  );
}

export default function MethodDetail() {
  const { id } = useParams();
  const [data, setData] = useState(null);
  const [err, setErr] = useState("");
  const [on, setOn] = useState("A");
  const meta = byId[id];

  useEffect(() => {
    setData(null); setErr(""); window.scrollTo(0, 0);
    api.learn(id).then(setData).catch((e) => setErr(e.message));
  }, [id]);

  useEffect(() => {
    if (!data) return;
    const secs = [...document.querySelectorAll("[data-sec]")];
    const io = new IntersectionObserver((es) => es.forEach((e) => e.isIntersecting && setOn(e.target.dataset.sec)), { rootMargin: "-30% 0px -60% 0px" });
    secs.forEach((s) => io.observe(s));
    return () => io.disconnect();
  }, [data]);

  if (!meta) return <div className="page container"><ErrorBox message="Unknown method." /></div>;
  const idx = indexOfMethod(id), prev = METHODS[idx - 1], next = METHODS[idx + 1];
  const c = data?.content, r = data?.result;

  return (
    <div className="page">
      <div className="container">
        <Link to="/methods" className="btn btn-ghost btn-sm" style={{ paddingLeft: 0 }}><ArrowLeft size={14} /> All methods</Link>
        <div className="page-head" style={{ paddingTop: 14 }}>
          <div className="eyebrow">{catById[meta.cat].name}</div>
          <h1>{meta.name}</h1>
          <p>{meta.blurb}</p>
          <div style={{ marginTop: 22 }}><Link to={`/calculator?method=${id}`} className="btn btn-primary btn-sm"><Calculator size={14} /> Try it in the solver</Link></div>
        </div>
        {err && <ErrorBox message={err} />}
        {!data && !err && <Loader label="Loading lesson and running the worked example…" />}
        {data && (
          <div className="md-layout">
            <nav className="md-side">
              {SECTIONS.map(([l, t]) => <a key={l} href={`#sec-${l}`} className={on === l ? "on" : ""} onClick={(e) => { e.preventDefault(); document.getElementById(`sec-${l}`)?.scrollIntoView({ behavior: "smooth" }); }}><b>{l}</b>{t}</a>)}
            </nav>
            <div>
              <Section id="A" letter="A" title="Introduction">
                <div className="qa">
                  <div><h4>What is it?</h4><p>{c.intro.what}</p></div>
                  <div><h4>Why do we use it?</h4><p>{c.intro.why}</p></div>
                  <div><h4>What does it solve?</h4><p>{c.intro.solves}</p></div>
                  <div><h4>Where is it used?</h4><p>{c.intro.uses}</p></div>
                </div>
              </Section>

              <Section id="B" letter="B" title="Mathematical foundation">
                <p>{c.foundation.explain}</p>
                <FormulaBlock tex={c.foundation.formula} />
                <div className="vars">
                  {c.foundation.variables.map(([v, d], i) => <div key={i}><span><Katex tex={v} /></span><span>{d}</span></div>)}
                </div>
                <p style={{ marginTop: 18 }}><b style={{ color: "#fff" }}>Why it works. </b>{c.foundation.why}</p>
              </Section>

              <Section id="C" letter="C" title="Worked example in Python">
                <p>{c.example_intro}</p>
                <div className="params-line">
                  {data.inputs.filter((f) => data.example_params[f.name] !== undefined).map((f) => <span key={f.name}>{f.name} = <b>{String(data.example_params[f.name])}</b></span>)}
                </div>
                <p>Every line of the program below is written in plain beginner Python, and the note on the right explains what it does. Running exactly this program gives the answer shown in section F.</p>
                <CodeBlock code={c.code} />
                <h3 style={{ margin: "30px 0 14px", fontSize: 17 }}>The computation, step by step</h3>
                <StepsList steps={r.steps} />
              </Section>

              <Section id="D" letter="D" title="Iteration table">
                {r.tables.filter((t) => t.columns.length).map((t, i) => <div key={i} style={{ marginBottom: 22 }}><DataTable table={t} /></div>)}
                {!r.tables.some((t) => t.columns.length) && <p className="muted">This method has no iterations to tabulate.</p>}
              </Section>

              <Section id="E" letter="E" title="Graph (Matplotlib)">
                {r.plot ? <PlotImage b64={r.plot} alt={`${meta.name} graph`} /> : <p className="muted">No graph for this method.</p>}
              </Section>

              <Section id="F" letter="F" title="Final result and error">
                <StatusBar status={r.status} time={r.time_ms} iterations={r.error_analysis.iterations} />
                <div style={{ margin: "16px 0 22px" }}><AnswerCards answers={r.answers} /></div>
                <ErrorPanel analysis={r.error_analysis} exact={r.exact_answer} />
              </Section>

              <Section id="G" letter="G" title="Advantages & limitations">
                <div className="two">
                  <div className="pro"><h4 style={{ color: "#5eead4" }}>Advantages</h4><ul>{c.advantages.map((a, i) => <li key={i}>{a}</li>)}</ul></div>
                  <div className="con"><h4 style={{ color: "#f87171" }}>Limitations</h4><ul>{c.limitations.map((a, i) => <li key={i}>{a}</li>)}</ul></div>
                </div>
              </Section>

              <Section id="H" letter="H" title="Related methods">
                <div className="rel-grid">
                  {c.related.filter((x) => byId[x]).map((x) => <Link key={x} to={`/methods/${x}`} className="rel"><div>{byId[x].name}<small>{catById[byId[x].cat].short}</small></div><ArrowRight size={16} /></Link>)}
                </div>
              </Section>

              <div className="pager">
                {prev ? <Link to={`/methods/${prev.id}`} className="btn"><ArrowLeft size={14} /> {prev.name}</Link> : <span />}
                {next ? <Link to={`/methods/${next.id}`} className="btn">{next.name} <ArrowRight size={14} /></Link> : <span />}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
