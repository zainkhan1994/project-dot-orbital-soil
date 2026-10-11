# Project D.O.T.

An autonomous IoT biodome that synthesizes soil and keeps the biome healthy for crops in space.

## Commands

- `python -m pytest -q` — backend tests (from repo root, venv active)
- `cd backend && python run.py` — API on :5000 in simulation mode
- `DOT_SIMULATE=0 python backend/run.py` — API in hardware mode
- `cd dashboard && npm install && npm run dev` — dashboard dev server
- `cd dashboard && npm test` — dashboard unit tests
- `cd dashboard && npm run build` — production build

## Structure

- `backend/dot/` — model, controller, calibration, simulator, Flask app
- `backend/tests/` — pytest suite
- `dashboard/` — Vite + React mission control; src/sim.js mirrors the Python model
- `firmware/dot_pod/` — Arduino sketch (uncompiled in CI)
- `bridge/` — serial to HTTP forwarder
- `ml/` — optional TensorFlow forecaster (not run in CI)
- `docs/` — model, architecture, API, hardware
- `devpost/` — hackathon submission copy

## Conventions

- Keep `backend/dot/` (Python) and `dashboard/src/sim.js` (JavaScript) numerically in sync: same equations, ranges, probe signal and sample alignment (read N[k], command I[k]).
- Sensor sample order is read N[k] then command I[k]; log the pre-step N with that injection.
- Healthy windows live in RANGES in simulator.py and sim.js.
- Never claim hardware behavior that is not tested: mark unverified parts (firmware, TensorFlow) as such.
- Run `python -m pytest -q` and `cd dashboard && npm test` before committing.
- Secrets never go in the repo. Variables are named in `.env.example` (if present); real values live in untracked env files or the host's settings.
- Keep docs in `docs/`. Update `CHANGELOG.md` for user-visible changes.
- Judge every request against [`SCOPE.md`](SCOPE.md); use the terms in [`GLOSSARY.md`](GLOSSARY.md).

## Do not change without asking

- .github/workflows/pages.yml (deploys the demo)

## Agent skills

### Issue tracker

GitHub Issues are the tracker. See [`docs/agents/issue-tracker.md`](docs/agents/issue-tracker.md).

### Triage labels

See [`docs/agents/triage-labels.md`](docs/agents/triage-labels.md).

### Domain docs

Single-context repo: read [`GLOSSARY.md`](GLOSSARY.md) and [`SCOPE.md`](SCOPE.md) first. See [`docs/agents/domain.md`](docs/agents/domain.md).
