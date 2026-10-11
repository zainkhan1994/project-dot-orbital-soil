import React from "react";

const path = (vals, w, h, lo, hi) => {
  if (!vals.length) return "";
  const span = hi - lo || 1;
  return vals.map((v, i) => `${i ? "L" : "M"}${((i / Math.max(vals.length - 1, 1)) * w).toFixed(1)} ${(h - ((v - lo) / span) * h).toFixed(1)}`).join("");
};

/** Small sparkline with the healthy range shaded. */
export function Spark({ values, range, color = "#45e0a1", w = 220, h = 54 }) {
  const lo = Math.min(...values, range ? range[0] : Infinity);
  const hi = Math.max(...values, range ? range[1] : -Infinity);
  const y = (v) => h - ((v - lo) / (hi - lo || 1)) * h;
  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="spark" preserveAspectRatio="none" role="img" aria-label="trend">
      {range && <rect x="0" y={y(range[1])} width={w} height={Math.max(2, y(range[0]) - y(range[1]))} fill="rgba(69,224,161,.10)" />}
      <path d={path(values, w, h, lo, hi)} fill="none" stroke={color} strokeWidth="2" vectorEffect="non-scaling-stroke" />
    </svg>
  );
}

/** Nitrogen chart with target line, healthy band, and injection / uptake traces. */
export function NutrientChart({ rows, target }) {
  const w = 720, h = 240;
  const n = rows.map((r) => r.nitrogen);
  const lo = Math.min(...n, target - 30, 60), hi = Math.max(...n, target + 30, 140);
  const y = (v) => h - ((v - lo) / (hi - lo)) * h;
  const inj = rows.map((r) => r.injection ?? 0), upt = rows.map((r) => (r.uptake ?? 0) * 10);
  const sMax = Math.max(...inj, ...upt, 1);
  const small = (vals, color) => (
    <path d={vals.map((v, i) => `${i ? "L" : "M"}${((i / Math.max(vals.length - 1, 1)) * w).toFixed(1)} ${(h - (v / sMax) * 60).toFixed(1)}`).join("")} fill="none" stroke={color} strokeWidth="1.5" opacity=".75" vectorEffect="non-scaling-stroke" />
  );
  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="nchart" preserveAspectRatio="none" role="img" aria-label="Nitrogen over time">
      <rect x="0" y={y(120)} width={w} height={y(80) - y(120)} fill="rgba(69,224,161,.09)" />
      <line x1="0" x2={w} y1={y(target)} y2={y(target)} stroke="#ffc857" strokeDasharray="6 6" strokeWidth="1.5" vectorEffect="non-scaling-stroke" />
      {small(inj, "#6ec1ff")}
      {small(upt, "#ff8a5b")}
      <path d={path(n, w, h, lo, hi)} fill="none" stroke="#45e0a1" strokeWidth="2.5" vectorEffect="non-scaling-stroke" />
    </svg>
  );
}

export function Ring({ value, label }) {
  const r = 52, c = 2 * Math.PI * r, off = c * (1 - (value ?? 0) / 100);
  const color = value >= 85 ? "#45e0a1" : value >= 60 ? "#ffc857" : "#ff6b6b";
  return (
    <svg viewBox="0 0 140 140" className="ring" role="img" aria-label={`${label} ${value}`}>
      <circle cx="70" cy="70" r={r} fill="none" stroke="rgba(255,255,255,.08)" strokeWidth="12" />
      <circle cx="70" cy="70" r={r} fill="none" stroke={color} strokeWidth="12" strokeLinecap="round" strokeDasharray={c} strokeDashoffset={off} transform="rotate(-90 70 70)" style={{ transition: "stroke-dashoffset .6s, stroke .6s" }} />
      <text x="70" y="74" textAnchor="middle" className="ring-v">{value ?? "–"}</text>
      <text x="70" y="98" textAnchor="middle" className="ring-l">{label}</text>
    </svg>
  );
}
