# Hardware notes

> **Scope.** This repository contains the firmware, the bridge and the software. CAD files, photos and the physical build are not included here. The list below follows the project write-up.

## Pod

- Modular acrylic pods
- Capillary-action drip system (3D printed) that delivers water to the root mesh without relying on gravity
- Arduino-class controller (a Raspberry Pi hosts the backend and bridge)

## Sensors (as described in the write-up)

| Quantity | How the firmware reads it | Calibration |
|---|---|---|
| NPK | RS485 Modbus RTU, request `01 03 00 1E 00 03 65 CD`, 3 registers (N, P, K, mg/kg) | check your probe's register map; verify against a reference mix. False positives from a synthetic fertilizer mix are a known issue: compare against lab values |
| Soil pH | analog pin A1, two-point calibration | measure raw ADC in pH 4.01 and 6.86 buffers, set `PH_RAW_A/B` |
| Soil moisture | capacitive sensor on A0 | measure raw ADC dry and submerged, set `MOISTURE_DRY/WET` |
| Temperature, humidity | DHT22 on D2 (Adafruit DHT library) | none |
| Radiation | **not read by the firmware** | the bridge uses a fixed `--radiation` value until a dosimeter is wired in |

## Wiring

DHT22 → D2 · moisture → A0 · pH → A1 · RS485 module RX → D10, TX → D11, DE/RE → D8.

## Running with hardware

```bash
cd backend && DOT_SIMULATE=0 python run.py          # backend in hardware mode
python bridge/serial_bridge.py --port /dev/ttyUSB0 --url http://localhost:5000
```

The sketch has not been compiled or flashed as part of this repository's CI; compile it in the Arduino IDE (install **DHT sensor library** and **Adafruit Unified Sensor**) and adjust pins and calibration constants to your build.
