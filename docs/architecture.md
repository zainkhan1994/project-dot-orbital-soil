# Architecture

```
 ┌────────────────────────── pod (hardware) ──────────────────────────┐
 │ NPK probe (RS485) · pH · soil moisture · DHT22 temp/humidity        │
 │             Arduino  ── JSON line per 2 s over USB serial ──┐       │
 └─────────────────────────────────────────────────────────────┼───────┘
                                                               ▼
                                     bridge/serial_bridge.py (pyserial)
                                                               │ POST /api/ingest
                                                               ▼
   dashboard (React, polls every 1 s)  ◄──────  Flask API (backend/dot/app.py)
   or in-browser demo simulation               · history ring buffer (5000)
                                               · health score + alerts
                                               · /api/calibrate (IV fit)
                                               · controller set-point
                                               · built-in simulator (no hardware)
```

| Part | Path | Notes |
|---|---|---|
| Model, controller, calibration, simulator | `backend/dot/` | pure Python + numpy, 12 tests |
| API | `backend/dot/app.py`, `backend/run.py` | Flask; `DOT_SIMULATE=0` for hardware mode |
| Firmware | `firmware/dot_pod/dot_pod.ino` | not compiled in CI |
| Bridge | `bridge/serial_bridge.py` | line parser is unit-tested |
| Dashboard | `dashboard/` | Vite + React; a JS port of the model runs when no API is set |
| ML extension | `ml/forecast_tf.py` | optional, not run in CI |

## Modes

- **Simulation** (default): the backend ticks a `Biome` every second (each tick = 0.25 h). `POST /api/ingest` is refused so simulated and real data never mix.
- **Hardware** (`DOT_SIMULATE=0`): the bridge posts readings; the backend stores them and computes health and alerts.
- **Demo** (dashboard only): no backend; the dashboard runs the same equations in the browser. This is what GitHub Pages serves.

## Healthy windows

Nitrogen 80–120 mg/kg, moisture 55–70 %, pH 6.0–7.0, temperature 20–26 °C, humidity 50–70 %, radiation ≤ 1.5 mSv/day. They live in `RANGES` in both `simulator.py` and `sim.js`; keep them in sync.
