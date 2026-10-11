"""Nutrient model for the D.O.T. biodome.

The nitrogen balance in the synthesized soil follows

    dN/dt = alpha * I(t) - beta * N(t) - gamma * U(t)

N(t)  nutrient (nitrogen) concentration in the soil
I(t)  automated nutrient injection rate (the actuator)
U(t)  biomass uptake rate by the crops
alpha, beta, gamma  conversion, decay and absorption coefficients
                    (calibrated from telemetry, see calibration.py)
"""
from __future__ import annotations

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class Params:
    alpha: float = 0.80   # injected nutrient -> soil concentration
    beta: float = 0.02    # first-order decay (leaching, microbial immobilization)
    gamma: float = 0.50   # concentration lost per unit of crop uptake

    def with_(self, **kw) -> "Params":
        return replace(self, **kw)


def dn_dt(n: float, i: float, u: float, p: Params) -> float:
    """Right-hand side of the balance equation."""
    return p.alpha * i - p.beta * n - p.gamma * u


def step(n: float, i: float, u: float, p: Params, dt: float) -> float:
    """Advance N by dt with classical RK4 (I and U held constant over the step).

    Concentration cannot go negative.
    """
    k1 = dn_dt(n, i, u, p)
    k2 = dn_dt(n + 0.5 * dt * k1, i, u, p)
    k3 = dn_dt(n + 0.5 * dt * k2, i, u, p)
    k4 = dn_dt(n + dt * k3, i, u, p)
    return max(0.0, n + dt * (k1 + 2 * k2 + 2 * k3 + k4) / 6.0)


def equilibrium_injection(n_target: float, u: float, p: Params) -> float:
    """Injection rate that holds N at n_target when uptake is u (dN/dt = 0)."""
    return max(0.0, (p.beta * n_target + p.gamma * u) / p.alpha)
