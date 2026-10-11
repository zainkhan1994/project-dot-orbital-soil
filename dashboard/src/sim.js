// In-browser port of backend/dot (model, controller, simulator, calibration).
// Keep the equations identical to the Python so demo mode behaves like the real backend.

export const RANGES = {
  nitrogen: [80, 120], moisture: [55, 70], ph: [6.0, 7.0],
  temperature: [20, 26], humidity: [50, 70], radiation: [0, 1.5],
};

export const DEFAULT_PARAMS = { alpha: 0.8, beta: 0.02, gamma: 0.5 };

// dN/dt = alpha*I - beta*N - gamma*U
export const dnDt = (n, i, u, p) => p.alpha * i - p.beta * n - p.gamma * u;

export function rk4(n, i, u, p, dt) {
  const k1 = dnDt(n, i, u, p);
  const k2 = dnDt(n + 0.5 * dt * k1, i, u, p);
  const k3 = dnDt(n + 0.5 * dt * k2, i, u, p);
  const k4 = dnDt(n + dt * k3, i, u, p);
  return Math.max(0, n + (dt * (k1 + 2 * k2 + 2 * k3 + k4)) / 6);
}

export const equilibriumInjection = (nTarget, u, p) => Math.max(0, (p.beta * nTarget + p.gamma * u) / p.alpha);

// small seeded RNG (mulberry32) + Box-Muller
function rng(seed) {
  let a = seed >>> 0;
  const next = () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
  const gauss = (s) => s * Math.sqrt(-2 * Math.log(next() || 1e-9)) * Math.cos(2 * Math.PI * next());
  return { next, gauss, uniform: (lo, hi) => lo + (hi - lo) * next() };
}

const band = (x, lo, hi, soft) => (x >= lo && x <= hi ? 1 : Math.max(0, 1 - (x < lo ? lo - x : x - hi) / soft));

export function createBiome(seed = 42) {
  const r = rng(seed);
  const s = { n: 60, moisture: 58, ph: 6.6, temperature: 23, humidity: 60, radiation: 0.7, biomass: 0.25, t: 0, storm: 0, integral: 0, nTarget: 100 };
  const truth = { ...DEFAULT_PARAMS };
  const kp = 0.04, ki = 0.002, iMax = 12, probe = 1.5, probeHold = 4;
  let level = 1, count = 0;

  const uptake = () => (1.2 * s.biomass * s.n) / (40 + s.n);
  const stress = () => band(s.n, 80, 120, 80) * band(s.moisture, 55, 70, 30) * band(s.ph, 6, 7, 1.5) * band(s.radiation, 0, 1.5, 3);

  return {
    state: s,
    solarStorm(hours = 6) { s.storm = hours; },
    setTarget(v) { s.nTarget = v; },
    tick(dt = 0.25) {
      const base = 0.7 + 0.15 * Math.sin(s.t / 9);
      if (s.storm > 0) { s.radiation = base + 2.6 + r.uniform(-0.2, 0.2); s.storm = Math.max(0, s.storm - dt); }
      else s.radiation += (base - s.radiation) * 0.3;

      const u = uptake();
      const nRead = s.n; // the sensor reads N[k]; the command I[k] then produces N[k+1]
      const err = s.nTarget - s.n;
      const raw = equilibriumInjection(s.nTarget, u, truth) + kp * err + ki * s.integral;
      if (count % probeHold === 0) level = r.next() < 0.5 ? -1 : 1;
      count += 1;
      const iCmd = Math.min(iMax, Math.max(0, raw + probe * level));
      if (raw > 0 && raw < iMax && Math.abs(err) < 0.15 * s.nTarget) s.integral += err * dt;
      s.n = rk4(s.n, iCmd, u, truth, dt);

      const drip = s.moisture < 60 ? 2.4 : 0;
      s.moisture = Math.min(100, Math.max(0, s.moisture + (drip - 0.9 - 0.8 * s.biomass) * dt));
      s.ph += (-0.006 * iCmd + 0.12 * (6.6 - s.ph)) * dt;
      s.temperature += (23 + 0.8 * Math.sin(s.t / 12) - s.temperature) * 0.2;
      s.humidity += (60 + 5 * Math.sin(s.t / 7) - s.humidity) * 0.2;
      s.biomass += 0.05 * s.biomass * (1 - s.biomass / 2) * stress() * dt;
      s.t += dt;

      const round = (x, d) => Number(x.toFixed(d));
      return {
        t: round(s.t, 3),
        nitrogen: round(nRead + r.gauss(0.6), 2), moisture: round(s.moisture + r.gauss(0.4), 2), ph: round(s.ph + r.gauss(0.02), 3),
        temperature: round(s.temperature + r.gauss(0.1), 2), humidity: round(s.humidity + r.gauss(0.3), 2),
        radiation: round(Math.max(0, s.radiation + r.gauss(0.03)), 3),
        injection: round(iCmd, 3), uptake: round(u, 4), biomass: round(s.biomass, 4),
      };
    },
  };
}

export function healthScore(reading) {
  let total = 0;
  for (const [k, [lo, hi]] of Object.entries(RANGES)) {
    const x = reading[k];
    if (x >= lo && x <= hi) total += 1;
    else total += Math.max(0, 1 - (x < lo ? lo - x : x - hi) / Math.max(hi - lo, 1e-9));
  }
  const score = Math.round((100 * total) / Object.keys(RANGES).length);
  // never display a perfect score while any parameter is outside its window
  return total < Object.keys(RANGES).length ? Math.min(score, 99) : score;
}

export function alertsFor(reading) {
  const out = [];
  for (const [k, [lo, hi]] of Object.entries(RANGES)) {
    const x = reading[k];
    if (x < lo) out.push({ parameter: k, level: "low", value: x, range: [lo, hi] });
    else if (x > hi) out.push({ parameter: k, level: k === "radiation" && x > 2.5 ? "critical" : "high", value: x, range: [lo, hi] });
  }
  return out;
}

// Instrumental-variable fit of (alpha, beta, gamma) from rows with nitrogen, injection, uptake.
// Mirrors backend/dot/calibration.py: N[k-1] is the instrument for the noisy regressor N[k].
export function calibrate(rows, dt = 0.25, ridge = 1e-6) {
  if (rows.length < 30) throw new Error("need at least 30 samples");
  const A = [[ridge, 0, 0], [0, ridge, 0], [0, 0, ridge]];
  const b = [0, 0, 0];
  for (let k = 1; k < rows.length - 1; k++) {
    const x = [rows[k].injection, -rows[k].nitrogen, -rows[k].uptake];
    const z = [rows[k].injection, -rows[k - 1].nitrogen, -rows[k].uptake];
    const y = (rows[k + 1].nitrogen - rows[k].nitrogen) / dt;
    for (let a = 0; a < 3; a++) { b[a] += z[a] * y; for (let c = 0; c < 3; c++) A[a][c] += z[a] * x[c]; }
  }
  const M = A.map((row, i) => [...row, b[i]]);   // solve the 3x3 system by Gauss-Jordan
  for (let i = 0; i < 3; i++) {
    let p = i;
    for (let j = i + 1; j < 3; j++) if (Math.abs(M[j][i]) > Math.abs(M[p][i])) p = j;
    [M[i], M[p]] = [M[p], M[i]];
    for (let j = 0; j < 3; j++) if (j !== i) { const f = M[j][i] / M[i][i]; for (let c = i; c < 4; c++) M[j][c] -= f * M[i][c]; }
  }
  const [alpha, beta, gamma] = [0, 1, 2].map((i) => Math.max(1e-6, M[i][3] / M[i][i]));
  return { alpha, beta, gamma };
}
