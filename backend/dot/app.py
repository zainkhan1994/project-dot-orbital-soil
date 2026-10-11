"""Flask API: telemetry ingest, state, history and model calibration."""
from __future__ import annotations

import threading
import time
from collections import deque

from flask import Flask, jsonify, request

from .calibration import fit
from .model import Params
from .simulator import Biome, alerts, health_score

REQUIRED = ("nitrogen", "moisture", "ph", "temperature", "humidity", "radiation")


class Store:
    def __init__(self, maxlen: int = 5000) -> None:
        self.lock = threading.Lock()
        self.history: deque[dict] = deque(maxlen=maxlen)
        self.params = Params()
        self.n_target = 100.0
        self.mode = "idle"


def create_app(simulate: bool = True, tick_seconds: float = 1.0, seed: int = 42) -> Flask:
    app = Flask(__name__)
    store = Store()
    app.config["STORE"] = store
    biome = Biome(seed=seed)
    app.config["BIOME"] = biome

    @app.after_request
    def cors(resp):  # the dashboard may be served from another origin (e.g. GitHub Pages)
        resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
        resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        return resp

    def record(reading: dict) -> None:
        with store.lock:
            store.history.append(reading)

    if simulate:
        store.mode = "simulation"

        def loop() -> None:
            while True:
                biome.controller.n_target = store.n_target
                record(biome.tick(0.25))
                time.sleep(tick_seconds)

        threading.Thread(target=loop, daemon=True).start()

    @app.get("/api/health")
    def health():
        return jsonify(status="ok", mode=store.mode)

    @app.get("/api/state")
    def state():
        with store.lock:
            latest = store.history[-1] if store.history else None
            count = len(store.history)
        body = {"mode": store.mode, "count": count, "n_target": store.n_target,
                "params": store.params.__dict__, "latest": latest}
        if latest:
            body["health"] = health_score(latest)
            body["alerts"] = alerts(latest)
        return jsonify(body)

    @app.get("/api/history")
    def history():
        limit = min(int(request.args.get("limit", 200)), 5000)
        with store.lock:
            rows = list(store.history)[-limit:]
        return jsonify(rows)

    @app.route("/api/ingest", methods=["POST", "OPTIONS"])
    def ingest():
        if request.method == "OPTIONS":
            return ("", 204)
        data = request.get_json(silent=True) or {}
        missing = [k for k in REQUIRED if not isinstance(data.get(k), (int, float))]
        if missing:
            return jsonify(error="missing or non-numeric fields", fields=missing), 400
        if store.mode == "simulation":
            return jsonify(error="server is in simulation mode; start with DOT_SIMULATE=0 to ingest hardware data"), 409
        store.mode = "hardware"
        reading = {k: data[k] for k in data if isinstance(data[k], (int, float))}
        reading.setdefault("t", round(time.time(), 3))
        record(reading)
        return jsonify(ok=True), 201

    @app.route("/api/setpoint", methods=["POST", "OPTIONS"])
    def setpoint():
        if request.method == "OPTIONS":
            return ("", 204)
        value = (request.get_json(silent=True) or {}).get("nitrogen")
        if not isinstance(value, (int, float)) or not 20 <= value <= 200:
            return jsonify(error="nitrogen must be a number between 20 and 200"), 400
        store.n_target = float(value)
        return jsonify(n_target=store.n_target)

    @app.route("/api/storm", methods=["POST", "OPTIONS"])
    def storm():
        if request.method == "OPTIONS":
            return ("", 204)
        if store.mode != "simulation":
            return jsonify(error="solar storms can only be injected in simulation mode"), 409
        biome.solar_storm(6.0)
        return jsonify(ok=True, hours=6.0)

    @app.route("/api/calibrate", methods=["POST", "OPTIONS"])
    def calibrate():
        if request.method == "OPTIONS":
            return ("", 204)
        with store.lock:
            rows = [r for r in store.history if "injection" in r and "uptake" in r]
        if len(rows) < 30:
            return jsonify(error="need at least 30 samples with injection and uptake"), 422
        dt = 0.25 if store.mode == "simulation" else float(request.args.get("dt", 0.25))
        result = fit([r["nitrogen"] for r in rows], [r["injection"] for r in rows], [r["uptake"] for r in rows], dt)
        store.params = result.params
        return jsonify(params=result.params.__dict__, rmse=result.rmse, samples=result.samples)

    return app
