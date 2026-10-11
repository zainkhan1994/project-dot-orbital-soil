import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "bridge"))
from serial_bridge import parse_line  # noqa: E402


def test_parse_line_fills_radiation_and_skips_noise():
    r = parse_line('{"nitrogen":98,"moisture":61.0,"ph":6.5,"temperature":22.5,"humidity":58}', 0.7)
    assert r["radiation"] == 0.7 and r["nitrogen"] == 98
    assert parse_line("", 0.7) is None
    assert parse_line("garbage", 0.7) is None
    assert parse_line('{"error":"sensor read failed"}', 0.7) is None
    assert parse_line('{"radiation":1.1,"nitrogen":1}', 0.7)["radiation"] == 1.1
