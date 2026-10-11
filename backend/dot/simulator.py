"""Biome simulator: stands in for the hardware pod when no Arduino is attached.

Time is in hours. One call to ``tick`` advances the pod by ``dt`` hours and returns a
telemetry reading in the same schema the Arduino bridge posts to /api/ingest.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from .controller import NutrientController
from .model import Params, step

# Healthy operating windows, shared with the health score and alerts.
RANGES = {
    "nitrogen": (80.0, 120.0),      # mg/kg
    "moisture": (55.0, 70.0),       # % volumetric water content
    "ph": (6.0, 7.0),
    "temperature": (20.0, 26.0),    # deg C
    "humidity": (50.0, 70.0),       # % relative
    "radiation": (0.0, 1.5),        # mSv/day
}


@dataclass
class Biome:
    seed: int = 42
    truth: Params = Params()                       # the pod's real coefficients
    n: float = 60.0
    moisture: float = 58.0
    ph: float = 6.6
    temperature: float = 23.0
    humidity: float = 60.0
    radiation: float = 0.7
    biomass: float = 0.25
    t: float = 0.0
    storm_hours_left: float = 0.0
    controller: NutrientController = field(default=None)
    rng: random.Random = field(default=None)

    def __post_init__(self) -> None:
        self.rng = random.Random(self.seed)
        if self.controller is None:
            self.controller = NutrientController(self.truth, probe=1.5)

    # ---- external events -------------------------------------------------
    def solar_storm(self, hours: float = 6.0) -> None:
        self.storm_hours_left = hours

    # ---- internals ---------------------------------------------------------
    def _uptake(self) -> float:
        """U(t): crop uptake grows with biomass and saturates with available N."""
        return 1.2 * self.biomass * self.n / (40.0 + self.n)

    def _stress(self) -> float:
        """Multiplier in [0, 1] on growth from nutrient, water, pH and radiation."""
        def band(x, lo, hi, soft):
            if lo <= x <= hi:
                return 1.0
            d = (lo - x) if x < lo else (x - hi)
            return max(0.0, 1.0 - d / soft)
        return (band(self.n, 80, 120, 80) * band(self.moisture, 55, 70, 30)
                * band(self.ph, 6.0, 7.0, 1.5) * band(self.radiation, 0, 1.5, 3.0))

    def tick(self, dt: float = 0.25) -> dict:
        r = self.rng
        # radiation: baseline with slow variation, plus storms
        base = 0.7 + 0.15 * math.sin(self.t / 9.0)
        if self.storm_hours_left > 0:
            self.radiation = base + 2.6 + r.uniform(-0.2, 0.2)
            self.storm_hours_left = max(0.0, self.storm_hours_left - dt)
        else:
            self.radiation += (base - self.radiation) * 0.3

        # nutrient loop: controller picks I(t), the model integrates N
        u = self._uptake()
        n_read = self.n                                  # the sensor reads N[k] ...
        i_cmd = self.controller.injection(self.n, u, dt)  # ... the controller commands I[k] ...
        self.n = step(self.n, i_cmd, u, self.truth, dt)   # ... which produces N[k+1]

        # capillary drip keeps moisture inside the band (bang-bang), evaporation + uptake dry it
        drip = 2.4 if self.moisture < 60.0 else 0.0
        self.moisture = min(100.0, max(0.0, self.moisture + (drip - 0.9 - 0.8 * self.biomass) * dt))

        # injection acidifies slightly; buffering pulls back toward 6.6
        self.ph += (-0.01 * i_cmd + 0.05 * (6.6 - self.ph)) * dt
        self.temperature += (23.0 + 0.8 * math.sin(self.t / 12.0) - self.temperature) * 0.2
        self.humidity += (60.0 + 5.0 * math.sin(self.t / 7.0) - self.humidity) * 0.2

        # logistic growth throttled by stress
        self.biomass += 0.05 * self.biomass * (1 - self.biomass / 2.0) * self._stress() * dt
        self.t += dt

        noise = lambda s: r.gauss(0.0, s)  # noqa: E731
        return {
            "t": round(self.t, 3),
            "nitrogen": round(n_read + noise(0.6), 2),
            "moisture": round(self.moisture + noise(0.4), 2),
            "ph": round(self.ph + noise(0.02), 3),
            "temperature": round(self.temperature + noise(0.1), 2),
            "humidity": round(self.humidity + noise(0.3), 2),
            "radiation": round(max(0.0, self.radiation + noise(0.03)), 3),
            "injection": round(i_cmd, 3),
            "uptake": round(u, 4),
            "biomass": round(self.biomass, 4),
        }


def health_score(reading: dict) -> int:
    """0-100: how many parameters are inside their healthy window, weighted by distance."""
    total = 0.0
    for key, (lo, hi) in RANGES.items():
        x = reading[key]
        if lo <= x <= hi:
            total += 1.0
        else:
            span = max(hi - lo, 1e-9)
            d = (lo - x) if x < lo else (x - hi)
            total += max(0.0, 1.0 - d / span)
    return round(100.0 * total / len(RANGES))


def alerts(reading: dict) -> list[dict]:
    out = []
    for key, (lo, hi) in RANGES.items():
        x = reading[key]
        if x < lo:
            out.append({"parameter": key, "level": "low", "value": x, "range": [lo, hi]})
        elif x > hi:
            level = "critical" if key == "radiation" and x > 2.5 else "high"
            out.append({"parameter": key, "level": level, "value": x, "range": [lo, hi]})
    return out
