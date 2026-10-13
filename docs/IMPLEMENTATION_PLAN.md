# Implementation checklist and audit

Initial workspace: one Review-II PPTX, no source, Git repository, firmware, or configuration. All 15 slide XML bodies inspected in their entirety. Hardware is proposal-stage. Architecture: candidate TEC1-12706, LTC3108 with matched transformer, 0.22–1 F reservoir, ESP32-C3, intermittent BLE burst. The original presentation is preserved.

## Gaps and risks
- No validated telemetry protocol or measured power, charging, radio energy or thresholds.
- No prototype or firmware. Software must not assert energy neutrality or direct browser scanning.
- System Python is unavailable; a bundled Python 3.12 runtime is available.
- Source voltage does not establish LTC3108 startup or usable power.

## Ordered checklist
- [x] Foundation: React/TypeScript/Vite and FastAPI/SQLite; health and API connectivity.
- [x] Domain: nullable measurements, trapezoidal integration, capacitor and MET calculations; unit tests.
- [x] Pipeline: deterministic scenarios, idempotent ingestion, replay, freshness and provenance.
- [x] Interface: seven pages, responsive navigation, charts, workouts and error states.
- [x] Rewards: transactional, capped awards, separate provenance, history and derived achievements.
- [x] Experiments: metadata, comparison, CSV export and printable report.
- [x] Integration readiness: versioned API adapter and optional serial gateway; documented limitations.
- [x] Review: automated backend/frontend tests, build, live API and browser verification.

First acceptance flow: health → explicitly start normal simulation → consume samples → inspect energy and events → complete workout → refresh → verify saved workout/reward → export experiment. Failure flow: hardware selected with no samples remains disconnected, never starts simulation automatically.

Each phase depends on the preceding domain/persistence foundations. Use focused repairs and record actual validation results in VALIDATION.md. No commits, deployment, or deletion of user data.

## Final phase record
Phases 0–6 implemented and tested. Phase 7 provides the REST/replay contract and optional serial gateway; physical integration remains pending. Phase 8 completed software review, tests, build, audit and browser workflows. Hardware, event-energy instrumentation, alternative units, public authentication and physical print output are unresolved limitations, recorded in VALIDATION.md. No experiment evidence was fabricated.
