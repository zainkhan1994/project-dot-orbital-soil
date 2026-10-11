"""Run the API. DOT_SIMULATE=0 disables the built-in simulator so hardware can post telemetry."""
import os

from dot.app import create_app

app = create_app(simulate=os.environ.get("DOT_SIMULATE", "1") != "0",
                 tick_seconds=float(os.environ.get("DOT_TICK_SECONDS", "1.0")))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))
