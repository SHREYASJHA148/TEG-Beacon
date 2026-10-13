# Validation record — 13 October 2026

## Executed checks
- Backend: 23 pytest cases passed. One upstream Starlette/AnyIO deprecation warning; no test failures.
- Frontend: final TypeScript/Vite production build passed; five Vitest cases passed, including readable structured validation errors and non-JSON backend failures. No final build chunk warning (largest chart chunk approximately 404 kB).
- Dependency audit after upgrades: zero npm-reported vulnerabilities. Exact versions in package.json and transitive package-lock.json. Versions were updated to Vite 6.4.4, Vitest 4.1.11 and React Router 7.18.4; source-map-js transitive update applied.
- Live backend/database health responded 200, frontend HTML responded 200.
- Browser: simulation run generated 120 samples and three success events; failed scenario generated failure outcomes. Workout start/pause/resume/finish succeeded and completed history survived browser reload and server restart. Energy Lab, Beacon, Rewards, Experiments and Settings rendered through navigation.
- Download control produced a 120-row sample CSV; file contents inspected, with source, timestamp, units, quality and nullable-field headers.
- Hardware selection displayed disconnected with empty electrical readings and zero instrumented events; no simulation fallback started.
- Desktop 1366×900 and mobile 390×844 inspected visually; mobile navigation exercised, document width did not exceed viewport. Tablet/default ~700px layout also inspected.
- Invalid voltage-window submission produced a visible validation error; valid values restored. Mutation errors are independent of polling errors so successful reads cannot dismiss rejected writes.
- Windows start script refused already occupied ports. Start/stop/restart lifecycle tested; fix handles the Windows virtual-environment child interpreter and parsed timestamp comparison. Saved records survived restart.

## Test coverage
SI conversion, missing current/open-circuit exclusion, trapezoidal integration, invalid endpoints, gaps/duplicates, ideal capacitor limits, MET estimates, atomic batch rollback, source/device mismatch, future/naive timestamps, immutable IDs, event confirmation and unique awards, workout transitions and repeat completion, database reinitialization persistence, all eight scenarios, fixed scenario timestamps, speed-invariant energy, freshness/disconnection, CSV output, local origin/token access, measured-data preservation on reset, energy caps, self-report reward labels, per-experiment statistics and unsafe-voltage readiness.

## Remaining limitations and incomplete requirements
- No physical hardware test, firmware, controller commands, serial/BLE transport verification, event-current-window energy, energy-budget readiness or energy-neutrality validation.
- Optional serial companion is supplied but requires future firmware emitting the documented protocol. Direct browser BLE scanning is unavailable.
- A local single-user workspace replaces multiuser accounts and historical achievement-award tables. Achievements/streaks/challenges derive from saved records. No redemption system.
- SI display units fixed; configurable alternative display units are not implemented. Generic fully quoted CSV import is not supported; exported simple CSV and normalized JSON are supported.
- Print stylesheet and report UI implemented; physical print/PDF output was not visually verified in a printer dialog. Do not treat the report as experimental evidence.
- No public deployment hardening or measurement attestation. Device-submitted source and receiver IDs are trusted local instrument declarations.
- MET constants are generic illustrative approximations, not device activity measurements.
- No hardware feasibility, loaded module suitability, transformer startup, practical usable reservoir energy, BLE range or sustainability claims were validated.

No user presentation was edited; no commits, pushes or deployment performed.

## Subsequent one-port hosting verification
The unified release was committed/pushed after the original validation. FastAPI now serves the built frontend, SPA routes and API on one port. All 33 backend tests passed (23 existing + 10 hosting/security cases). Production frontend build passed. Live browser at port 8000 loaded the dashboard, started the simulation successfully, opened /experiments directly and refreshed it; no browser console errors were observed. Windows unified launcher successfully started the one-port process. The live homepage and JSON health endpoint responded 200 from the same port, and generated telemetry appeared in dashboard responses.

Docker executable is installed, but its daemon was unavailable (Docker Desktop Linux engine pipe absent). Therefore the actual Docker image build/run was not executed locally. The Dockerfile and Render Docker Blueprint are prepared, but cloud deployment is not verified; a hosting-account deployment remains required. Persistent hosted storage remains a separate requirement for research data.
