"""Autonomous replenishment controller: feed-forward from the model plus a PI correction,
plus an optional small pseudo-random probing signal (persistent excitation) so the
coefficients stay identifiable while the loop is closed."""
from __future__ import annotations

import random
from dataclasses import dataclass, field

from .model import Params, equilibrium_injection


@dataclass
class NutrientController:
    params: Params
    n_target: float = 100.0      # mg/kg target nitrogen
    kp: float = 0.04
    ki: float = 0.002
    i_max: float = 12.0          # actuator limit (injection rate units)
    probe: float = 0.0           # amplitude of the +/- probing signal added to I(t)
    probe_hold: int = 4          # steps each probe level is held
    _integral: float = 0.0
    _rng: random.Random = field(default_factory=lambda: random.Random(0))
    _level: float = 1.0
    _count: int = 0

    def injection(self, n: float, u_estimate: float, dt: float) -> float:
        """Return the injection rate I(t) to command for the next step."""
        error = self.n_target - n
        ff = equilibrium_injection(self.n_target, u_estimate, self.params)
        raw = ff + self.kp * error + self.ki * self._integral
        if self.probe:
            if self._count % self.probe_hold == 0:
                self._level = self._rng.choice((-1.0, 1.0))
            self._count += 1
        out = min(self.i_max, max(0.0, raw + self.probe * self._level))
        # anti-windup: integrate only while the actuator is unsaturated AND N is near the
        # target, so the large error during the initial ramp-up cannot wind the integrator up
        if 0.0 < raw < self.i_max and abs(error) < 0.15 * self.n_target:
            self._integral += error * dt
        return out

    def reset(self) -> None:
        self._integral = 0.0
