import React from "react";
import { NutrientChart, Ring, Spark } from "./charts.jsx";
import { DEFAULT_PARAMS, RANGES } from "./sim.js";
import { useTelemetry } from "./useTelemetry.js";

const METRICS = [
  { key: "nitrogen", label: "Nitrogen (N)", unit: "mg/kg", digits: 1 },
  { key: "moisture", label: "Soil moisture", unit: "%", digits: 1 },
  { key: "ph", label: "Soil pH", unit: "", digits: 2 },
  { key: "temperature", label: "Temperature", unit: "°C", digits: 1 },
  { key: "humidity", label: "Humidity", unit: "%", digits: 1 },
  { key: "radiation", label: "Radiation", unit: "mSv/day", digits: 2 },
];

const inRange = (k, v) => v >= RANGES[k][0] && v <= RANGES[k][1];
const fmtHours = (t) => `${Math.floor(t / 24)}d ${String(Math.floor(t % 24)).padStart(2, "0")}h`;

export default function App() {
  const tel = useTelemetry();
  const { rows, latest, params, fit, alerts, health, mode, nTarget, actions, error } = tel;
  const last = (k) => rows.slice(-90).map((r) => r[k]);
  const f = (x, d = 3) => Number(x).toFixed(d);

  return (
    <div className="app">
      <header className="top">
        <div>
          <p className="eyebrow">Dynamic Orbital Terra-synthesis</p>
          <h1>Project D.O.T. <span>Mission Control</span></h1>
        </div>
        <div className="status">
          <span className={`badge ${mode}`}>{mode === "demo" ? "DEMO · in-browser simulation" : "LIVE · API"}</span>
          {latest && <span className="clock">Mission elapsed {fmtHours(latest.t)}</span>}
        </div>
      </header>

      {error && <p className="error" role="alert">{error}</p>}

      <section className="grid" aria-label="Sensor readings">
        {METRICS.map((m) => {
          const v = latest ? latest[m.key] : null;
          const ok = v != null && inRange(m.key, v);
          return (
            <article className={`card ${ok ? "ok" : "warn"}`} key={m.key}>
              <p className="label">{m.label}</p>
              <p className="value">{v == null ? "–" : v.toFixed(m.digits)}<small> {m.unit}</small></p>
              <Spark values={last(m.key)} range={RANGES[m.key]} color={ok ? "#45e0a1" : "#ff8a5b"} />
              <p className="range">healthy {RANGES[m.key][0]}–{RANGES[m.key][1]} {m.unit}</p>
            </article>
          );
        })}
      </section>

      <section className="split">
        <article className="panel wide">
          <div className="panel-head">
            <h2>Nutrient balance</h2>
            <p className="legend"><i className="l1" />N(t) <i className="l2" />injection I(t) <i className="l3" />uptake U(t) <i className="l4" />target</p>
          </div>
          <NutrientChart rows={rows.slice(-160)} target={nTarget} />
          <p className="eq" aria-label="dN/dt equals alpha times I of t minus beta times N of t minus gamma times U of t">
            dN/dt = <b>{f(params.alpha)}</b>·I(t) − <b>{f(params.beta, 4)}</b>·N(t) − <b>{f(params.gamma)}</b>·U(t)
          </p>
          <div className="controls">
            <label>Nitrogen target <b>{nTarget} mg/kg</b>
              <input type="range" min="60" max="140" step="1" value={nTarget} onChange={(e) => actions.setTarget(Number(e.target.value))} />
            </label>
            <button onClick={actions.storm}>☀ Solar storm (6 h)</button>
            <button onClick={actions.calibrate}>⚙ Calibrate α, β, γ</button>
          </div>
          {fit && (
            <p className="fit">
              Calibrated from telemetry: α {f(fit.alpha)}, β {f(fit.beta, 4)}, γ {f(fit.gamma)}
              {mode === "demo" && <> (pod truth: α {DEFAULT_PARAMS.alpha}, β {DEFAULT_PARAMS.beta}, γ {DEFAULT_PARAMS.gamma})</>}
            </p>
          )}
        </article>

        <article className="panel">
          <h2>Biome health</h2>
          <Ring value={health} label="health score" />
          {latest && <p className="biomass">Crop biomass index <b>{latest.biomass.toFixed(2)}</b> / 2.00</p>}
          <h3>Alerts</h3>
          {alerts.length === 0 ? <p className="none">All parameters within their healthy windows.</p> : (
            <ul className="alerts">
              {alerts.map((a) => (
                <li key={a.parameter} className={a.level}>
                  <b>{a.parameter}</b> {a.level}: {a.value} (healthy {a.range[0]}–{a.range[1]})
                </li>
              ))}
            </ul>
          )}
        </article>
      </section>

      <footer>
        <p>Demo mode runs the same nutrient model and controller as the Python backend in your browser. Point the dashboard at a running backend with <code>?api=http://localhost:5000</code>.</p>
        <p><a href="https://github.com/zainkhan1994/project-dot-orbital-soil">Source on GitHub</a></p>
      </footer>
    </div>
  );
}
