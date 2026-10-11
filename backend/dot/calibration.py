"""Calibrate (alpha, beta, gamma) from telemetry by linear system identification.

Discretizing the balance equation gives, for consecutive samples k and k+1:

    (N[k+1] - N[k]) / dt  =  alpha * I[k]  -  beta * N[k]  -  gamma * U[k]

which is linear in the three unknowns, so ordinary least squares recovers them.
Ridge regularization keeps the fit stable when the signals are nearly collinear.

N is a noisy measurement, so plain least squares is biased (errors-in-variables: the noise in
N[k] appears both in the regressor and in the target). By default the fit therefore uses
instrumental variables: the previous sample N[k-1] stands in for N[k] as the instrument, since
its noise is independent of the noise that enters the target. The injection signal must also be
persistently exciting, which is why the controller adds a small probing signal.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .model import Params


@dataclass(frozen=True)
class Fit:
    params: Params
    rmse: float      # root-mean-square error of dN/dt (concentration / time)
    samples: int


def fit(n, i, u, dt: float, ridge: float = 1e-6, clip: bool = True, iv: bool = True) -> Fit:
    n, i, u = (np.asarray(x, dtype=float) for x in (n, i, u))
    if not (len(n) == len(i) == len(u)):
        raise ValueError("n, i and u must have the same length")
    if len(n) < 10:
        raise ValueError("need at least 10 samples to calibrate")
    if iv:
        # rows k = 1..len-2: target uses N[k+1]-N[k]; instrument for N[k] is N[k-1]
        dn = (n[2:] - n[1:-1]) / dt
        x = np.column_stack([i[1:-1], -n[1:-1], -u[1:-1]])
        z = np.column_stack([i[1:-1], -n[:-2], -u[1:-1]])
        coef = np.linalg.solve(z.T @ x + ridge * np.eye(3), z.T @ dn)
    else:
        dn = (n[1:] - n[:-1]) / dt
        x = np.column_stack([i[:-1], -n[:-1], -u[:-1]])
        coef = np.linalg.solve(x.T @ x + ridge * np.eye(3), x.T @ dn)
    if clip:
        coef = np.clip(coef, 1e-6, None)   # coefficients are physically non-negative
    resid = dn - x @ coef
    return Fit(Params(float(coef[0]), float(coef[1]), float(coef[2])), float(np.sqrt(np.mean(resid ** 2))), len(dn))
