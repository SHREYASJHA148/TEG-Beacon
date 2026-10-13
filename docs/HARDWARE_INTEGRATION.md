# Future hardware integration

Proposal architecture: skin/ambient TEG, candidate TEC1-12706, LTC3108 with matched transformer, 0.22–1 F capacitor, ESP32-C3, short BLE advertisement and shutdown. No prototype, firmware or serial/BLE path was available for validation.

## Version-1 normalized telemetry
Create a measured experiment in the UI/API first. It returns an experiment UUID. Use exactly that experiment ID, device ID and source on all samples/events.

```json
{
  "protocol_version": 1,
  "sample_id": "ESP32-C3-01:boot7:seq1",
  "device_id": "ESP32-C3-01",
  "experiment_id": "REPLACE_WITH_CREATED_EXPERIMENT_ID",
  "source": "measured",
  "timestamp": "2026-10-13T16:00:00Z",
  "units": "SI",
  "voltage_v": 0.03,
  "current_a": null,
  "capacitor_v": 3.1,
  "hot_c": null,
  "cold_c": null,
  "measurement_point": "teg_loaded",
  "quality": "valid"
}
```

The sample values above demonstrate the protocol only; not project measurements. Use an actual current UTC timestamp. Missing sensor fields stay null. Measure both current and voltage at the same electrical point; open_circuit/converter_output are valid labels but do not yield source power. Quality is valid/invalid/disconnected. The API accepts only SI units. Retain IDs across retries, include boot sequence to avoid collisions. Do not resend altered data under an existing ID.

## Adapters
1. Simulation: server-owned synthetic source; never automatically activated on disconnect.
2. JSON/CSV replay: Settings validates up to 1,000 samples, exact normalized JSON or this app's exported simple CSV. Experiment must already exist. Generic quoted CSV is outside this import contract.
3. Local REST: POST /api/v1/telemetry or /telemetry/batch. Hardware gateway must normalize timestamps and units.
4. Optional serial: firmware/gateway must output newline-delimited normalized JSON. From root: `.\.venv\Scripts\python.exe backend/serial_gateway.py --port COM3 --baud 115200`. This script has not been tested with a device.
5. BLE: a platform-compatible scanner/receiver can forward observations to REST. No browser scanner is implemented. Advertisement reception is not connection state. Confirmed measured success must include receiver_id; device transmit attempt alone should use unknown outcome.

## Validation before claims
Measure loaded source output vs ΔT, sensor placement and instrument noise; verify LTC3108 transformer/startup/source impedance; measure capacitor tolerance/leakage/ESR and losses; validate brownout and power-gating path; instrument boot+radio+support circuit current; log packet reception and range. Set safe voltage settings only after checking actual components. Event-energy integration is not implemented because event-window instrumentation is absent. Threshold-only readiness cannot guarantee a burst. The application neither commands the ESP32 nor proves energy-neutral operation.
