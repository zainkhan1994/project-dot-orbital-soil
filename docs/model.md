# The nutrient model

## Balance equation

$$\frac{dN}{dt} = \alpha\,I(t) - \beta\,N(t) - \gamma\,U(t)$$

| Symbol | Meaning |
|---|---|
| `N(t)` | nitrogen concentration in the synthesized soil (mg/kg) |
| `I(t)` | automated nutrient injection rate, the actuator (limit: 12 units/h in the simulator) |
| `U(t)` | biomass uptake rate by the crops; in the simulator `U = 1.2 · B · N / (40 + N)` for biomass index `B` |
| `α` | how effectively injected nutrient becomes soil concentration |
| `β` | first-order decay (leaching, microbial immobilization) |
| `γ` | concentration lost per unit of uptake |

Code: [`backend/dot/model.py`](../backend/dot/model.py) integrates the equation with classical RK4, clamps `N ≥ 0`, and exposes `equilibrium_injection`, the injection that holds a target when uptake is known: `I* = (β·N_target + γ·U) / α`.

## Controller

[`controller.py`](../backend/dot/controller.py) commands `I(t)` as the equilibrium injection (feed-forward) plus a PI correction on the error to the target, clamped to the actuator limit. The integrator only accumulates while the actuator is unsaturated **and** `N` is within 15 % of the target, so the large error during start-up cannot wind it up. An optional ± probing signal (`probe`) keeps the loop persistently exciting for calibration.

## Calibration (the "ML" part that runs live)

The discretized equation is linear in `(α, β, γ)`:

$$\frac{N_{k+1}-N_k}{\Delta t} = \alpha I_k - \beta N_k - \gamma U_k$$

[`calibration.py`](../backend/dot/calibration.py) fits the coefficients from telemetry. Two practical problems showed up and are handled:

1. **Noise in `N`** appears in both the regressor and the target, which biases ordinary least squares (errors-in-variables). The fit uses **instrumental variables**, with `N[k-1]` as the instrument for `N[k]`.
2. **Closed-loop data is collinear**: the feed-forward makes `I` a function of `N` and `U`. The controller therefore adds a small pseudo-random probing signal (persistent excitation).

Measured on the simulator (5 seeds, 600 samples of 0.25 h, true values `α=0.8, β=0.02, γ=0.5`, 0.6 mg/kg sensor noise):

| Method | α | β | γ |
|---|---|---|---|
| Instrumental variables | 0.78–0.84 | 0.019–0.022 | 0.43–0.51 |
| Ordinary least squares | 0.81–0.88 | 0.022–0.025 | 0.31–0.39 |

The unit tests assert recovery within 15 % (α), 25 % (β) and 35 % (γ).

## Optional TensorFlow forecaster

[`ml/forecast_tf.py`](../ml/forecast_tf.py) trains a small dense network to forecast `N(t + horizon)` from the sensor and actuator state, using simulator data. It needs `pip install tensorflow`, is not part of the CI, and **has not been run in this repository**. The calibrated physics model is what the backend uses.

## Sample alignment

On the pod the order is *read `N[k]` → command `I[k]` → `N[k+1]` results*. The simulator logs the pre-step `N` next to the injection it triggered, matching that order, which is what the regression above assumes.
