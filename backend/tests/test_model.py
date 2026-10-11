import math

from dot.calibration import fit
from dot.controller import NutrientController
from dot.model import Params, dn_dt, equilibrium_injection, step
from dot.simulator import Biome, alerts, health_score


def test_balance_equation_signs():
    p = Params(alpha=1.0, beta=0.1, gamma=0.5)
    assert dn_dt(10, 2, 1, p) == 1.0 * 2 - 0.1 * 10 - 0.5 * 1


def test_rk4_matches_closed_form_for_constant_inputs():
    p = Params(alpha=0.8, beta=0.2, gamma=0.5)
    i, u, n0, dt = 3.0, 1.0, 10.0, 0.05
    n = n0
    for _ in range(int(5 / dt)):
        n = step(n, i, u, p, dt)
    n_inf = (p.alpha * i - p.gamma * u) / p.beta
    exact = n_inf + (n0 - n_inf) * math.exp(-p.beta * 5)
    assert abs(n - exact) < 1e-6


def test_equilibrium_injection_holds_target():
    p = Params()
    i = equilibrium_injection(100.0, 0.4, p)
    assert abs(dn_dt(100.0, i, 0.4, p)) < 1e-9


def test_concentration_never_negative():
    assert step(0.1, 0.0, 5.0, Params(), 1.0) == 0.0


def test_controller_converges_and_respects_limit():
    b = Biome(seed=1, n=20.0)
    for _ in range(400):
        r = b.tick(0.25)
        assert 0.0 <= r["injection"] <= b.controller.i_max
    assert abs(b.n - b.controller.n_target) < 5.0


def test_calibration_recovers_coefficients_from_noisy_data():
    truth = Params(alpha=0.9, beta=0.03, gamma=0.4)
    b = Biome(seed=7, truth=truth, n=40.0)
    b.controller = NutrientController(truth, n_target=100.0, probe=1.5)
    rows = [b.tick(0.25) for _ in range(600)]
    result = fit([r["nitrogen"] for r in rows], [r["injection"] for r in rows], [r["uptake"] for r in rows], 0.25)
    assert abs(result.params.alpha - truth.alpha) / truth.alpha < 0.15
    assert abs(result.params.beta - truth.beta) / truth.beta < 0.25
    assert abs(result.params.gamma - truth.gamma) / truth.gamma < 0.35


def test_health_and_alerts():
    good = {"nitrogen": 100, "moisture": 62, "ph": 6.5, "temperature": 23, "humidity": 60, "radiation": 0.7}
    assert health_score(good) == 100 and alerts(good) == []
    bad = dict(good, radiation=3.2, moisture=40)
    assert health_score(bad) < 100
    levels = {a["parameter"]: a["level"] for a in alerts(bad)}
    assert levels == {"moisture": "low", "radiation": "critical"}
