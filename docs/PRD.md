# ThermoTrack product requirements

## Problem and objective
Body-heat electrical harvesting is tiny and variable. The proposal must validate source power, LTC3108 startup, reservoir losses, and repeatable BLE bursts. ThermoTrack makes the software data pipeline and intended experiment workflow demonstrable without implying feasibility.

## Users and journeys
Students/presenters select a labelled synthetic scenario; researchers create instrumented experiments and submit samples; gym users self-report workouts; supervisors inspect plots, missing intervals, exports and reward explanations. One local project workspace is supported, without accounts or unnecessary personal data.

## Functional scope
- FR-01: independent activity kcal, electrical output, capacitor estimates, beacon and points metrics.
- FR-02/03: persistent start/pause/resume/finish workflows, explicit mass, MET assumptions and elapsed-time estimate.
- FR-04/05/06: loaded V×I, interval integration and ideal capacitor energy in backend calculations.
- FR-07/08: success/failure/unknown events, transactional idempotent rewards with caps and explanations.
- FR-09/10/11: eight deterministic software scenarios; validated REST/replay; nullable fields, quality and freshness.
- FR-12/13: SQLite experiments and histories; unit/provenance CSV exports and printable reports.
- FR-14/15: API errors, empty states, responsive semantic UI and reduced-motion handling.
- FR-16/17/18: tests of scientific and persistence boundaries; immutable source labels; reset synthetic records only.

Pages: Overview, Workout, Energy Lab, Beacon, Rewards, Experiments, Settings. Controls act on the local API. No fake connection appears without data.

## Quality and exclusions
No medical measurement, no calories-to-electricity conversion, no claimed energy neutrality, no direct browser BLE scanning, no payments, no cloud or account infrastructure. Leaderboard is optional fictional demonstration data. Points are software incentives with no environmental or monetary significance.

## Acceptance criteria
The complete demo must run without hardware, save a workout across refresh, keep simulated points separate, show sensor/stale/failure scenarios, and export a traceable run. Unit/integration tests verify formulas, validation, provenance, idempotency, atomic batch rollback, safe thresholds and reset preservation. Build and live frontend/backend checks must be reported accurately.

## Assumptions and risks
MET values are illustrative generic activities. Manual activity is self-reported. Instrument-submitted telemetry is not independently authenticated scientific evidence. Hardware specifications, low-leakage control, transformer, module suitability, thresholds, losses, sensor placement and radio budget require future physical tests. No existing firmware protocol is assumed.
