FROM node:22-bookworm-slim AS frontend-build
WORKDIR /build/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
# Relative /api calls use the same origin as the Python server.
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
COPY backend/requirements-lock.txt /app/backend/requirements-lock.txt
RUN pip install --no-cache-dir -r backend/requirements-lock.txt
COPY backend/ /app/backend/
COPY --from=frontend-build /build/frontend/dist /app/frontend/dist
ENV THERMOTRACK_DB=/data/thermotrack.sqlite3
RUN mkdir -p /data && useradd --uid 10001 --create-home thermotrack && chown -R thermotrack:thermotrack /app /data
USER thermotrack
EXPOSE 8000
CMD ["sh", "-c", "exec python -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port ${PORT:-8000}"]
