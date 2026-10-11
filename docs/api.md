# API

Base URL `http://localhost:5000`. All responses are JSON. CORS is open so the dashboard can be hosted elsewhere.

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/health` | `{status, mode}` where mode is `simulation`, `hardware` or `idle` |
| GET | `/api/state` | latest reading, health score (0–100), alerts, calibrated params, nitrogen target |
| GET | `/api/history?limit=200` | recent readings (max 5000) |
| POST | `/api/ingest` | hardware reading; requires numeric `nitrogen, moisture, ph, temperature, humidity, radiation`. 400 if invalid, 409 in simulation mode |
| POST | `/api/setpoint` | `{"nitrogen": 20–200}` nitrogen target (mg/kg) |
| POST | `/api/calibrate` | fit α, β, γ from history that includes `injection` and `uptake`; 422 if fewer than 30 samples |
| POST | `/api/storm` | simulation only: 6 h solar-storm radiation spike |

Example reading:

```json
{"nitrogen": 98.4, "moisture": 61.2, "ph": 6.5, "temperature": 22.8, "humidity": 58.0, "radiation": 0.7,
 "injection": 3.5, "uptake": 0.41}
```

`injection` and `uptake` are optional for ingest but required for calibration. Uptake is not directly measurable on real hardware; estimate it (for example from a biomass or water-use model) before calibrating.
