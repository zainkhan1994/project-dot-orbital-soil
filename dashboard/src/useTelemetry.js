import { useCallback, useEffect, useRef, useState } from "react";
import { alertsFor, calibrate, createBiome, DEFAULT_PARAMS, healthScore } from "./sim.js";

const MAX_ROWS = 300;
const apiBase = () => {
  const q = new URLSearchParams(window.location.search).get("api");
  return (q || import.meta.env.VITE_API_URL || "").replace(/\/$/, "");
};

/** Telemetry source: the Flask API when ?api=<url> (or VITE_API_URL) is set, else an in-browser simulation. */
export function useTelemetry() {
  const api = apiBase();
  const mode = api ? "live" : "demo";
  const [rows, setRows] = useState([]);
  const [params, setParams] = useState(DEFAULT_PARAMS);
  const [fit, setFit] = useState(null);
  const [nTarget, setNTarget] = useState(100);
  const [error, setError] = useState(null);
  const biome = useRef(null);

  useEffect(() => {
    if (mode === "demo") {
      const b = createBiome(42);
      biome.current = b;
      const seed = Array.from({ length: 120 }, () => b.tick());
      setRows(seed);
      const id = setInterval(() => {
        setRows((prev) => [...prev, b.tick()].slice(-MAX_ROWS));
      }, 500);
      return () => clearInterval(id);
    }
    let alive = true;
    const poll = async () => {
      try {
        const [h, s] = await Promise.all([
          fetch(`${api}/api/history?limit=${MAX_ROWS}`).then((r) => r.json()),
          fetch(`${api}/api/state`).then((r) => r.json()),
        ]);
        if (!alive) return;
        setRows(h);
        setParams(s.params);
        setNTarget(s.n_target);
        setError(null);
      } catch (e) {
        if (alive) setError(`Cannot reach ${api}: ${e.message}`);
      }
    };
    poll();
    const id = setInterval(poll, 1000);
    return () => { alive = false; clearInterval(id); };
  }, [api, mode]);

  const post = useCallback((path, body) =>
    fetch(`${api}${path}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body || {}) }).then((r) => r.json()), [api]);

  const actions = {
    storm: () => (mode === "demo" ? biome.current.solarStorm(6) : post("/api/storm")),
    setTarget: (v) => { setNTarget(v); return mode === "demo" ? biome.current.setTarget(v) : post("/api/setpoint", { nitrogen: v }); },
    calibrate: async () => {
      try {
        if (mode === "demo") {
          const f = calibrate(rows);
          setParams(f); setFit(f);
        } else {
          const r = await post("/api/calibrate");
          if (r.params) { setParams(r.params); setFit(r.params); } else setError(r.error || "calibration failed");
        }
      } catch (e) { setError(e.message); }
    },
  };

  const latest = rows[rows.length - 1] || null;
  return { mode, api, rows, latest, params, fit, nTarget, error,
    health: latest ? healthScore(latest) : null, alerts: latest ? alertsFor(latest) : [], actions };
}
