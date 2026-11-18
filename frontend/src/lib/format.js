// Number formatting used everywhere in the interface.
export function fmtNum(x, digits = 10) {
  if (x === null || x === undefined) return "-";
  if (typeof x === "string") return x;
  if (typeof x === "boolean") return x ? "true" : "false";
  if (!Number.isFinite(x)) return String(x);
  if (x === 0) return "0";
  if (Number.isInteger(x) && Math.abs(x) < 1e15) return String(x);
  const a = Math.abs(x);
  if (a >= 1e9 || a < 1e-4) {
    const [m, e] = x.toExponential(Math.min(digits - 1, 7)).split("e");
    return `${m.replace(/\.?0+$/, "")}e${e.replace("+", "")}`;
  }
  return String(parseFloat(x.toPrecision(digits)));
}

export function fmtShort(x) {
  return fmtNum(x, 6);
}

export const isNum = (v) => typeof v === "number" && Number.isFinite(v);

// A value from the backend can be a number, a vector or a matrix.
export function describeValue(v) {
  if (Array.isArray(v) && Array.isArray(v[0])) return v.map((r) => "[" + r.map((n) => fmtNum(n, 8)).join(", ") + "]").join("\n");
  if (Array.isArray(v)) return "[" + v.map((n) => fmtNum(n, 10)).join(", ") + "]";
  return fmtNum(v, 12);
}

export function download(filename, text, mime = "text/plain") {
  const url = URL.createObjectURL(new Blob([text], { type: mime }));
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 500);
}

export function downloadBase64Png(filename, b64) {
  const a = document.createElement("a");
  a.href = "data:image/png;base64," + b64;
  a.download = filename;
  a.click();
}

export function resultToText(title, params, res) {
  const L = [];
  L.push(`NUMERIQ - ${title}`, "=".repeat(48), "");
  L.push("INPUTS");
  Object.entries(params).forEach(([k, v]) => L.push(`  ${k} = ${String(v).replace(/\n/g, " ; ")}`));
  L.push("", "RESULT");
  res.answers.forEach((a) => L.push(`  ${a.label}: ${describeValue(a.value).replace(/\n/g, "\n    ")}`));
  L.push("", "STEPS");
  res.steps.forEach((s, i) => L.push(`  ${i + 1}. ${s}`));
  res.tables.forEach((t) => {
    L.push("", t.title.toUpperCase(), "  " + t.columns.join(" | "));
    t.rows.forEach((r) => L.push("  " + r.map((c) => fmtNum(c, 8)).join(" | ")));
  });
  const e = res.error_analysis;
  L.push("", "ERROR ANALYSIS");
  if (e.reference_label) {
    L.push(`  Reference (${e.reference_label}): ${describeValue(e.reference_value)}`);
    L.push(`  Absolute error: ${fmtNum(e.absolute_error)}`, `  Relative error: ${fmtNum(e.relative_error)}`);
  }
  if (e.iterations != null) L.push(`  Iterations: ${e.iterations}`);
  e.metrics.forEach((m) => L.push(`  ${m.label}: ${fmtNum(m.value)}`));
  e.notes.forEach((n) => L.push(`  Note: ${n}`));
  L.push("", `Status: ${res.status.message}`, `Computed in ${res.time_ms} ms by the Python backend.`);
  return L.join("\n");
}

export function tablesToCsv(tables) {
  const esc = (c) => `"${String(c ?? "").replace(/"/g, '""')}"`;
  return tables
    .map((t) => [esc(t.title), t.columns.map(esc).join(","), ...t.rows.map((r) => r.map((c) => esc(typeof c === "number" ? c : c)).join(","))].join("\n"))
    .join("\n\n");
}
