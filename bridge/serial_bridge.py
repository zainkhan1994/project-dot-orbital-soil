"""Forward JSON lines from the pod's serial port to the backend.

    python bridge/serial_bridge.py --port /dev/ttyUSB0 --url http://localhost:5000

The pod has no radiation sensor by default, so the bridge fills ``radiation`` from
--radiation (a fixed value) unless the firmware reports one. Wire in a dosimeter and have
the firmware print "radiation" to replace the assumed value.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request


def parse_line(line: str, radiation_default: float) -> dict | None:
    """Return a reading dict ready for /api/ingest, or None for blank/invalid/error lines."""
    line = line.strip()
    if not line.startswith("{"):
        return None
    try:
        data = json.loads(line)
    except json.JSONDecodeError:
        return None
    if "error" in data:
        return None
    data.setdefault("radiation", radiation_default)
    return data


def post(url: str, reading: dict) -> int:
    req = urllib.request.Request(url.rstrip("/") + "/api/ingest", data=json.dumps(reading).encode(),
                                 headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=5) as resp:
        return resp.status


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--port", required=True)
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--url", default="http://localhost:5000")
    ap.add_argument("--radiation", type=float, default=0.7, help="assumed radiation (mSv/day) when the pod does not report it")
    args = ap.parse_args()
    import serial  # pyserial
    with serial.Serial(args.port, args.baud, timeout=3) as ser:
        print(f"reading {args.port} @ {args.baud}, posting to {args.url}", file=sys.stderr)
        while True:
            reading = parse_line(ser.readline().decode(errors="ignore"), args.radiation)
            if reading:
                try:
                    post(args.url, reading)
                except OSError as exc:
                    print(f"post failed: {exc}", file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
