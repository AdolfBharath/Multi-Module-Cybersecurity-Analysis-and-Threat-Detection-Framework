# Runtime Status

Date: 2026-10-23

## Executed Validation

- `docker compose --env-file .local-run/docker.env up -d`
- `Invoke-WebRequest http://127.0.0.1:5173`
- `Invoke-WebRequest http://127.0.0.1:8000/api/v1/health`
- Live role login and authorization checks for Admin, SOC Analyst, Malware Analyst, Vulnerability Analyst, and Viewer.

## Observed Results

Frontend `http://localhost:5173` returned 200. API `http://localhost:8000/api/v1/health` returned 200. Backend, PostgreSQL, Redis, and the Celery worker reported healthy after the Docker fixes.

Initial `--build` was blocked by a transient Docker Hub token connection failure. Existing local images started successfully without rebuilding. No data volumes were removed or reset.

## Developer Commands

```powershell
docker compose --env-file .local-run/docker.env up -d
docker compose --env-file .local-run/docker.env ps
docker compose --env-file .local-run/docker.env down
```

For a fresh machine, copy `.env.example` to a private `.env`, replace every placeholder, then run `docker compose up --build -d`.
