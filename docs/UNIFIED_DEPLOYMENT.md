# One-service deployment (recommended)

FastAPI serves both the built React application and `/api/v1` on the same host and port. API calls use relative URLs. One Docker image builds the frontend and includes it beside the Python backend. No VITE_API_URL or CORS setup is needed when opening the app at the unified service URL.

## Local one-port run
From the project root:
```powershell
npm --prefix frontend ci
npm --prefix frontend run build
.\stop.ps1
.\start-unified.ps1
```
Open http://127.0.0.1:8000. API docs: http://127.0.0.1:8000/docs. Stop with `./stop.ps1`. To use a visible terminal instead: `.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000`.

For editing with Vite hot reload, the original `start.ps1` remains available as a two-port development launcher. Rebuild frontend after changes before starting the unified production server.

## Deploy frontend and backend together
Open https://dashboard.render.com/select-repo?type=blueprint and select SHREYASJHA148/TEG-Beacon (or New → Blueprint). The committed `render.yaml` defines **one Docker web service**. Render builds frontend and backend using the Dockerfile and starts the whole app on its assigned PORT. Use the actual Render HTTPS service URL as the website URL. No separate frontend deploy is required.

The service generates THERMOTRACK_ADMIN_TOKEN. Copy it from Render's Environment settings and enter it in ThermoTrack → Settings → Optional administrator token → Save token for this tab. Public mutation requests remain protected, so simulation/workout writes require that token. Never embed the secret in frontend build variables. Reads and initial UI are available without it.

A static Netlify deployment does not run this Python backend. Netlify can still host a separate frontend using `netlify.toml` and VITE_API_URL, but the recommended whole-project deployment uses the single Docker service URL.

## Docker locally
```powershell
docker build -t thermotrack .
docker run --rm -p 8000:8000 -e THERMOTRACK_ADMIN_TOKEN=YOUR_SECRET -v thermotrack-data:/data thermotrack
```
Open http://localhost:8000 and enter your chosen token in Settings. Container runs as a non-root user. Database defaults to /data; the named volume retains local records. Container honours the hosting provider's PORT variable.

## Hosted persistence
The free Render Blueprint overrides database location to /tmp for disposable demonstration. Free service filesystem changes disappear on restart, redeploy or spin-down; use persistent hosting for actual experimental records. Mount a disk at /data and set THERMOTRACK_DB=/data/thermotrack.sqlite3 on a suitable plan. No paid resource is created by the free Blueprint.

## Verification
Homepage, six SPA pages and direct refresh, assets, JSON API responses, unknown API 404s, path traversal rejection, same-origin mutations and token protection have automated checks. Docker build requires a running Docker daemon. See VALIDATION.md for executed checks.
