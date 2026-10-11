import pytest

from dot.app import create_app


@pytest.fixture()
def hw():
    app = create_app(simulate=False)
    return app.test_client()


GOOD = {"nitrogen": 98, "moisture": 61, "ph": 6.5, "temperature": 22.5, "humidity": 58, "radiation": 0.8}


def test_ingest_validates_and_updates_state(hw):
    assert hw.post("/api/ingest", json={"nitrogen": 1}).status_code == 400
    assert hw.post("/api/ingest", json=GOOD).status_code == 201
    s = hw.get("/api/state").get_json()
    assert s["mode"] == "hardware" and s["latest"]["nitrogen"] == 98 and s["health"] == 100


def test_setpoint_bounds(hw):
    assert hw.post("/api/setpoint", json={"nitrogen": 5}).status_code == 400
    assert hw.post("/api/setpoint", json={"nitrogen": 110}).get_json()["n_target"] == 110


def test_calibrate_needs_data(hw):
    assert hw.post("/api/calibrate").status_code == 422


def test_simulation_mode_blocks_ingest_and_allows_storm():
    app = create_app(simulate=True, tick_seconds=0.01)
    c = app.test_client()
    assert c.post("/api/ingest", json=GOOD).status_code == 409
    assert c.post("/api/storm").status_code == 200
    assert c.get("/api/health").get_json()["mode"] == "simulation"
