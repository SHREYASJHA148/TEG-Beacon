# Technical requirements and decisions

## Stack and structure
frontend/src contains the typed API client, application/pages, types and styles. backend/app separates schemas, transactional storage, calculations, services, deterministic simulator and API routing. backend/tests holds domain and integration tests. SQLite uses standard-library sqlite3 rather than an ORM to keep this single-workspace application lightweight. No frontend scientific totals compete with backend totals; instantaneous chart points plot same-point SI samples.

## Persistence
Schema version 1 initializes tables/indexes idempotently. Experiments, telemetry, events, workouts, rewards, settings and playback state persist. Foreign keys and WAL enabled. Samples have unique IDs and unique experiment/device/time tuples. Events and reward keys are unique. Duplicate exact payloads are accepted without processing twice, changed payloads conflict. Related ingestion/reward changes and complete replay batches are atomic. Hardware records cannot be relabelled. One local workspace replaces multiuser entities. Achievements and weekly challenges derive from persisted source records; they are not separate awarded transaction types.

## Calculations and units
SI at API: V, A, F, °C, s, J. Positive source current means delivery from the loaded TEG. P=V×I only for valid loaded measurements. Power in µW equals mV×mA. Missing current or open-circuit measurements produce null power. Energy uses trapezoidal adjacent valid endpoints, strictly positive dt ≤ configurable maximum gap. Integration is per experiment/device, sorted by time. Invalid endpoints, duplicates and long gaps are excluded. There is no extrapolation before/after samples. A singleton valid sample gives 0 integrated J, not proof of continuity.

E=½CV²; ideal usable E=½C max(0,V²−Vlow²), null above configured maximum. Capacitance must be 0.22–1 F; 0≤low<ready≤high≤5 V. Defaults 0.47 F, 3.0/3.25/3.3 V are illustrative. No budget-based radio guarantee. Delta T is hot TEG face minus cold TEG face. Energy-change rate is capacitor ΔE/dt, not assumed TEG input. MET calories=MET×3.5×mass/200×active minutes; version and chosen MET are recorded. 1 kcal=4184 J if comparing units; UI does not infer conversion efficiency.

## Simulator
Fixed fixture UTC clock starts 2026-01-01, one virtual second per sample. Readings, timestamps and outcomes reproducible across runs; unique experiment IDs differ. Playback 1–10 samples per wall-clock tick never changes the calculation timeline. Server received_at drives simulation freshness; stale scenario ages reception by five minutes. Measured freshness always uses the device sample timestamp. Restart pauses playback. Pause preserves position. Reset deletes only simulated records. Reservoir trajectory and TEG power are independently chosen software fixtures, explicitly not a physical energy-conservation model.

## Rewards
Completion + capped elapsed-minute points; confirmed unique BLE events; accumulated energy units capped per run. No negative/zero award transactions. Self-reported activity retains user_entered provenance, shown alongside instrumented rewards in hardware workspace with explicit labels. Simulated rewards remain separate. Energy awards account for previously awarded points, avoiding re-awards from replay or rule changes. Historical transaction explanations retain original configuration. No redemption; balance equals lifetime positive awards.

## Security and lifecycle
Pydantic rejects extras, non-finite values, negative/out-of-range readings, naive timestamps and >30s future timestamps. Measured success needs a receiver ID. Configured CORS plus mutation-origin validation. Loopback mutation restriction when no token configured; bearer token required when configured. Uploaded replay max 2 MB client-side, 1,000 samples server-side; API Content-Length capped. This is not a hardened public service: no accounts, rate limiting or full streaming-body size enforcement. Avoid public exposure. Backend polls simulation once/second; frontend reads once/second. SQLite writes are short synchronous transactions.

## Tests and limitations
Pytest via FastAPI TestClient, numeric fixtures and temporary disk databases. Vitest covers unavailable/zero display values. Live browser verification covers main workflows. Transport integration remains testable API contracts, without claims of physical execution. Scientific statistics and exports preserve source and nulls. Optional serial tool consumes already normalized NDJSON rather than inventing firmware capabilities.

Framework references: [FastAPI request bodies](https://fastapi.tiangolo.com/tutorial/body/) and [Vite guide](https://vite.dev/guide/).
