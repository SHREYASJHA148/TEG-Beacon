# ThermoTrack

Local research dashboard for the **Self-Powered Gym-Locker Beacon via Human Wearable Thermoelectric Harvesting**, MDP 2026, SENSE, VIT Chennai. The supplied Review-II presentation is preserved. Hardware and firmware are still proposal-stage.

## Install (Windows PowerShell)
Prerequisites: Node.js 22.12+ and Python 3.11+ (tested with Node 24 and Python 3.12).

```powershell
cd 'C:\MDP(The gymbeacon)'
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements-lock.txt
cd frontend
npm ci
```

This machine has no system Python. Its bundled runtime can create the environment:

```powershell
& 'C:\Users\SHREYAS JHA\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m venv .venv
```

## Run (two terminals)
From the project root:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

In another terminal:

```powershell
cd 'C:\MDP(The gymbeacon)\frontend'
npm run dev
```

Open http://127.0.0.1:5173. API docs: http://127.0.0.1:8000/docs.
You can also run `./start.ps1` from the root to start both hidden processes and open the browser. Use `./stop.ps1` to stop only those recorded processes.

## Verify
```powershell
cd 'C:\MDP(The gymbeacon)\backend'
..\.venv\Scripts\python.exe -m pytest -q
cd ..\frontend
npm test
npm run build
```

## Demo
Select Simulation workspace → choose Normal charging → Play. Speed 10× completes the 120-sample scenario in roughly 12 seconds. At sample 28 a synthetic reception event appears. Start and finish a workout with explicit body mass, review rewards, select a failure scenario, then export/print the experiment. Reset removes only synthetic records. See docs/DEMO_GUIDE.md.

## Architecture and configuration
React/TypeScript/Vite with custom semantic components, Tailwind, Recharts, Lucide, React Router. FastAPI/Pydantic validates inputs; SQLite via the standard library supplies transactional persistence and uniqueness constraints. Backend domain calculations supply scientific totals. The browser polls the API every second, while a server-owned simulation task advances independently of browser clients.

Copy `.env.example` values into your shell environment. The application does **not** automatically load `.env`. Default SQLite path is backend/thermotrack.sqlite3. `THERMOTRACK_DB` can override it. Origins and optional administrator token use the variables in `.env.example`. Set variables in PowerShell as `$env:THERMOTRACK_ADMIN_TOKEN='your-secret'`. Add the matching token in Settings for this browser tab. Default server binds only to loopback. Never expose it publicly without TLS and a proper authentication design.

## Integration status
Version-1 REST ingestion and CSV/JSON replay are implemented. Serial gateway is provided but untested on physical hardware. Direct browser BLE scanning, ESP32 firmware, actual thresholds and event energy remain unimplemented/unvalidated. Measured provenance means instrument-submitted data, not independent verification. User-entered activity rewards retain `user_entered` provenance.

## Troubleshooting
- Backend unavailable: verify port 8000 and health endpoint; UI keeps an explicit error visible.
- Port already occupied: check an existing server before starting another. Start script refuses duplicate listeners.
- No samples: explicitly play a simulation or create a measured experiment and ingest matching device records.
- Stale hardware: timestamps must be timezone-aware and current. No simulation fallback is automatic.
- Rejected payload: read `/docs`; units are SI, IDs unique, and experiment/device/source must match.
- Database error: check write permissions/disk space. Back up the database before changes; no migration beyond controlled version-1 initialization is supplied.
- Installation: use `npm ci` with the committed lockfile; dependencies are pinned. Backend lockfile pins transitive dependencies.

Details: docs/PRD.md, TRD.md, API_REFERENCE.md, HARDWARE_INTEGRATION.md, DEMO_GUIDE.md and VALIDATION.md.
