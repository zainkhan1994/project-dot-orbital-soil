import { describe, expect, it } from "vitest";
import { calibrate, createBiome, DEFAULT_PARAMS, dnDt, equilibriumInjection, healthScore, rk4 } from "./sim.js";

describe("nutrient model", () => {
  it("implements dN/dt = alpha*I - beta*N - gamma*U", () => {
    expect(dnDt(10, 2, 1, { alpha: 1, beta: 0.1, gamma: 0.5 })).toBeCloseTo(1 * 2 - 0.1 * 10 - 0.5 * 1);
  });
  it("RK4 matches the closed form for constant inputs", () => {
    const p = { alpha: 0.8, beta: 0.2, gamma: 0.5 };
    let n = 10;
    for (let k = 0; k < 100; k++) n = rk4(n, 3, 1, p, 0.05);
    const inf = (p.alpha * 3 - p.gamma * 1) / p.beta;
    expect(n).toBeCloseTo(inf + (10 - inf) * Math.exp(-p.beta * 5), 5);
  });
  it("equilibrium injection holds the target", () => {
    expect(Math.abs(dnDt(100, equilibriumInjection(100, 0.4, DEFAULT_PARAMS), 0.4, DEFAULT_PARAMS))).toBeLessThan(1e-9);
  });
});

describe("biome", () => {
  it("controller drives N to the target within tolerance", () => {
    const b = createBiome(1);
    b.state.n = 20;
    for (let k = 0; k < 400; k++) b.tick();
    expect(Math.abs(b.state.n - 100)).toBeLessThan(6);
  });
  it("calibration recovers the coefficients", () => {
    const b = createBiome(7);
    const rows = Array.from({ length: 600 }, () => b.tick());
    const fit = calibrate(rows);
    expect(Math.abs(fit.alpha - 0.8) / 0.8).toBeLessThan(0.2);
    expect(Math.abs(fit.beta - 0.02) / 0.02).toBeLessThan(0.3);
    expect(Math.abs(fit.gamma - 0.5) / 0.5).toBeLessThan(0.4);
  });
  it("health score is 100 inside every window", () => {
    expect(healthScore({ nitrogen: 100, moisture: 62, ph: 6.5, temperature: 23, humidity: 60, radiation: 0.7 })).toBe(100);
  });
});
