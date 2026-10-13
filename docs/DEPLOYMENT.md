# Netlify frontend deployment

**For frontend and backend deployed together, use [UNIFIED_DEPLOYMENT.md](UNIFIED_DEPLOYMENT.md).** The Render Blueprint now defines a single Docker service. The following Netlify instructions remain an alternative for separately hosting the frontend.

The repository root `netlify.toml` sets base directory `frontend`, build command `npm run build`, and publish directory `dist` (relative to base). Deploy the Git-connected `main` branch. Netlify installs dependencies using the frontend lockfile. The public `_redirects` file supplies rewrites for the six supported React routes and is copied into the build output by Vite. Root `/` serves `dist/index.html`. Missing API paths remain errors, not app HTML.

If Netlify's existing site settings override or do not discover the configuration, set:
- Base directory: `frontend`
- Build command: `npm run build`
- Publish directory: `frontend/dist` relative to repository root, or `dist` if the UI shows it relative to base.
- Production branch: `main`
Trigger a fresh production deployment. For drag-and-drop deployments, upload the built `frontend/dist` folder, not the source repository.

## Backend is a separate service
Netlify's static frontend deployment does not run the Python/FastAPI backend or SQLite database. The local Vite development proxy is not available in a published build. Deploy the backend on a Python-capable service with persistent storage, then set Netlify build variable `VITE_API_URL` to its HTTPS origin (without `/api/v1` or trailing slash). Redeploy after changing it. Never use localhost/127.0.0.1 as a public backend URL.

Backend variables:
- `THERMOTRACK_ORIGINS=https://teg-beacon.netlify.app` (include additional exact trusted frontend origins if needed).
- `THERMOTRACK_ADMIN_TOKEN`: strong secret, kept on the backend. Enter its matching value in the app's Settings for an administrator session. Never place this token in a VITE variable.
- `THERMOTRACK_DB`: absolute persistent SQLite path supplied by the hosting provider.
Backend launch command: `python -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port PORT` with the provider's actual assigned port. TLS should be handled by the provider. This is still a single trusted-admin demonstration, not a multiuser production system.

The routing/build fix resolves frontend hosting configuration. API-dependent features still require a reachable configured backend. No backend was deployed by this fix.

## Quick Render setup
Open https://dashboard.render.com/select-repo?type=blueprint and select SHREYASJHA148/TEG-Beacon (or use New → Blueprint in Render). The repository's `render.yaml` supplies the Python service, health check, allowed Netlify origin and a generated administrator secret. Deploy it, then copy the actual HTTPS service URL Render assigns. Do not guess the hostname.

In Netlify → Project configuration → Environment variables, add `VITE_API_URL` equal to the Render service origin, without `/api/v1` or a trailing slash. Trigger a new production deploy. Check BACKEND_ORIGIN/api/v1/health responds with status=ok. In ThermoTrack → Settings, enter the Render `THERMOTRACK_ADMIN_TOKEN` value and save it for this tab to enable workouts/simulation/settings writes. Do not put that secret into the Netlify frontend build environment.

The supplied free service is for disposable demonstrations: Render free services sleep and their filesystem is ephemeral, so SQLite records are lost when the service restarts, redeploys or spins down. Use persistent storage before collecting real research data. This configuration does not create a paid service or guarantee persistent hosted data.
