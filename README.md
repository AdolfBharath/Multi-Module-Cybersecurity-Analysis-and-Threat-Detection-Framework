# CyberShield XDR

Multi-Module Cybersecurity Analysis and Threat Detection Framework.

CyberShield XDR is a Dockerized enterprise SOC platform prototype with a FastAPI backend, PostgreSQL/Redis services, WebSocket live feeds, and a premium React/Vite dark UI.

## Quick Start

```bash
cp .env.example .env
# Replace every placeholder in .env with private development values.
docker compose up --build -d
```

Services:

- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000/api/v1`
- OpenAPI: `http://localhost:8000/api/v1/docs`

No credentials are embedded in the repository. Configure `ADMIN_BOOTSTRAP_EMAIL`
and `ADMIN_BOOTSTRAP_PASSWORD` only in a private environment file for first-run
provisioning. Development-only role accounts can be loaded through
`backend/app/seed_test_data.py` with environment-provided passwords.

## Stack

- Backend: Python 3.12, FastAPI, SQLAlchemy, Pydantic v2, JWT-ready auth, WebSockets
- Frontend: React 19, TypeScript, Vite, TailwindCSS, React Router, TanStack Query, Recharts, Framer Motion, Lucide
- Data: PostgreSQL, Redis
- Deployment: Docker Compose, Nginx, GitHub Actions

## Modules

Authentication, Dashboard, Log Management, Threat Detection, Anomaly Detection, Network Monitoring, Malware Analysis, Vulnerability Scanner, Threat Intelligence, Incident Management, Reports, Notifications, Audit Logs, and System Settings are implemented as independent backend routers/services with matching frontend routes.
