/* Small abstract SVG illustration per category, used on carousel cards. */
const P = "#8055FF", B = "#627BFF", W = "#e8e8f2", G = "#F5B85C";
const curve = (f, x0, x1, n = 60, sx = 1, sy = 1, ox = 0, oy = 0) =>
  Array.from({ length: n + 1 }, (_, i) => { const x = x0 + ((x1 - x0) * i) / n; return `${i ? "L" : "M"}${(ox + x * sx).toFixed(1)},${(oy - f(x) * sy).toFixed(1)}`; }).join(" ");

export default function MethodArt({ cat, seed = 0 }) {
  const s = (seed % 5) + 1;
  const art = {
    root: (<>
      <path d={curve((x) => Math.sin(x * 0.9 + s * 0.3) * 0.8 + 0.1 * x - 0.2, 0, 7, 80, 28, 30, 10, 100)} stroke={P} strokeWidth="2.5" fill="none" />
      <line x1="10" x2="210" y1="100" y2="100" stroke="#555" /><circle cx={60 + s * 14} cy="100" r="5" fill={G} />
      {[0, 1, 2].map((i) => <line key={i} x1={60 + s * 14 + i * 9} x2={60 + s * 14 + i * 9} y1="60" y2="140" stroke={B} strokeDasharray="3 4" opacity={0.8 - i * 0.25} />)}
    </>),
    interp: (<>
      <path d={curve((x) => Math.sin(x) * 0.9 + 0.2 * x, 0, 6.5, 80, 30, 28, 14, 105)} stroke={P} strokeWidth="2.5" fill="none" />
      {[0.5, 1.8, 3, 4.3, 5.7].map((x, i) => <circle key={i} cx={14 + x * 30} cy={105 - (Math.sin(x) * 0.9 + 0.2 * x) * 28} r="4.5" fill={G} />)}
    </>),
    integration: (<>
      <path d={`${curve((x) => 0.8 + Math.sin(x * 0.8 + s) * 0.6, 0, 6, 60, 32, 36, 14, 130)} L206,130 L14,130 Z`} fill={P} opacity="0.35" />
      <path d={curve((x) => 0.8 + Math.sin(x * 0.8 + s) * 0.6, 0, 6, 60, 32, 36, 14, 130)} stroke={W} strokeWidth="2" fill="none" />
      {Array.from({ length: 7 }, (_, i) => <line key={i} x1={14 + i * 32} x2={14 + i * 32} y1="130" y2={130 - (0.8 + Math.sin(i * 0.8 + s) * 0.6) * 36} stroke={B} />)}
    </>),
    diffode: (<>
      {Array.from({ length: 28 }, (_, i) => { const x = 22 + (i % 7) * 28, y = 30 + Math.floor(i / 7) * 32, a = Math.atan(Math.sin((i % 7) * 0.7) * 0.8 - Math.floor(i / 7) * 0.2); return <line key={i} x1={x - 8 * Math.cos(a)} y1={y + 8 * Math.sin(a)} x2={x + 8 * Math.cos(a)} y2={y - 8 * Math.sin(a)} stroke={B} strokeWidth="2" strokeLinecap="round" opacity="0.6" />; })}
      <path d={curve((x) => 0.4 + 0.5 * x - 0.06 * x * x, 0, 6, 40, 30, 14, 16, 120)} stroke={P} strokeWidth="2.5" fill="none" />
    </>),
    linalg: (<>
      {Array.from({ length: 16 }, (_, i) => { const r = Math.floor(i / 4), c = i % 4, v = (r === c ? 1 : 0.2 + ((i * s) % 5) / 8); return <rect key={i} x={40 + c * 32} y={32 + r * 26} width="26" height="20" rx="4" fill={r === c ? P : B} opacity={0.25 + v * 0.65} />; })}
    </>),
    approx: (<>
      <line x1="20" y1="130" x2="200" y2="40" stroke={P} strokeWidth="2.5" />
      {[[40, 100], [70, 108], [100, 70], [130, 94], [160, 55], [185, 62]].map(([x, y], i) => <g key={i}><line x1={x} x2={x} y1={y} y2={130 - ((x - 20) / 180) * 90} stroke={B} strokeDasharray="2 3" /><circle cx={x} cy={y} r="4.5" fill={G} /></g>)}
    </>),
    optim: (<>
      {[18, 36, 56, 78].map((r, i) => <ellipse key={i} cx="110" cy="80" rx={r * 1.5} ry={r * 0.8} fill="none" stroke={i % 2 ? B : P} opacity={0.35 + i * 0.1} transform={`rotate(-20 110 80)`} />)}
      <path d="M30,130 L60,104 L82,96 L98,86 L106,82" stroke={W} strokeWidth="2" fill="none" /><circle cx="108" cy="80" r="5" fill={G} />
    </>),
    arith: (<>
      {"0100000000111001".split("").map((b, i) => <rect key={i} x={14 + i * 12.2} y="64" width="10" height="26" rx="2" fill={i === 0 ? P : i < 6 ? B : "#555"} opacity={b === "1" ? 0.95 : 0.3} />)}
      <text x="110" y="124" textAnchor="middle" fill="#a1a1aa" fontFamily="monospace" fontSize="13">0.1 + 0.2 ≠ 0.3</text>
    </>),
  }[cat];
  return <svg viewBox="0 0 220 160" width="100%" height="100%" aria-hidden>{art}</svg>;
}
