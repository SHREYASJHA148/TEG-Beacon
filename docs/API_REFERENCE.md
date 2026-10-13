# API v1

Base http://127.0.0.1:8000/api/v1. Complete request/response contracts are generated at `/docs` and `/openapi.json`. Application data include SI units, timezone-aware UTC timestamps, source provenance, IDs and nullable measurements.

| Endpoint | Method | Contract |
|---|---|---|
| /health | GET | Database health and unvalidated hardware status |
| /dashboard/summary | GET | source=simulated/measured; optional experiment_id; combined metrics/histories |
| /settings | GET / PUT | Complete validated Settings object |
| /workouts | GET / POST | activity, mass_kg (20–300), planned_minutes (1–360), source=user_entered/simulated |
| /workouts/{id} | GET / PATCH | action=pause/resume/finish; completed finish is idempotent |
| /experiments | GET / POST | name, description, conditions, source, device_id, module |
| /experiments/{id} | GET | Metadata, energy summary, events |
| /experiments/{id}/export | GET | CSV samples with units in headers, provenance, timestamp and quality |
| /telemetry | POST | Version-1 Telemetry object; see HARDWARE_INTEGRATION.md |
| /telemetry/batch | POST | 1–1,000 normalized samples, all-or-nothing transaction |
| /telemetry/latest, /telemetry/history | GET | experiment_id required; latest may be null |
| /energy/summary, /energy/history | GET | experiment_id required |
| /beacon/events | POST / GET | Event object / experiment_id query |
| /beacon/status | GET | source query; status is telemetry freshness, not a connection |
| /rewards/balance, /rewards/history, /rewards/achievements | GET | source query, hardware workspace includes labelled user_entered activity awards |
| /simulation/scenarios | GET | Eight supported scenario keys and descriptions |
| /simulation/start | POST | scenario key, speed 1–10; resumes same scenario, otherwise creates a run |
| /simulation/pause | POST | Pause at current position |
| /simulation/reset | POST | Remove only synthetic records, reset playback |

Example session body: `{"activity":"Walking","mass_kg":70,"planned_minutes":20,"source":"simulated"}`.
Example scenario body: `{"scenario":"normal","speed":10}`.
Example event: `{"event_id":"boot7:ad1","device_id":"ESP32-C3-01","experiment_id":"YOUR_UUID","timestamp":"CURRENT_UTC_TIME","source":"measured","event_type":"advertisement","outcome":"success","receiver_id":"scanner-1","capacitor_v":3.25}`. Permitted types advertisement/brownout/restart; outcomes success/failure/unknown. Measurement/event payloads reject unknown keys.

## Errors and authentication
201 created for ingestion; duplicate identical records return duplicate=true without changing data/rewards. 409 changed payload under reused ID, duplicate timestamp, invalid workflow or simulation in hardware mode. 422 field validation/provenance mismatch; 404 absent experiment/session; 401 missing bearer token; 403 untrusted origin/nonlocal mutation; 413 oversized Content-Length; 503 SQLite operation error. Error detail is either a readable string or structured Pydantic validation list.

Default loopback-only mutation access. If THERMOTRACK_ADMIN_TOKEN is set, all mutation requests require Authorization: Bearer TOKEN. No endpoint accepts arbitrary points. Read endpoints remain public on the configured bind address; do not deploy publicly without full authentication and TLS. The environment example is not automatically loaded.
