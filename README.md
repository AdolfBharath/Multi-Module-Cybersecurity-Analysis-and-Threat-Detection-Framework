# CyberShield XDR

Multi-Module Cybersecurity Analysis and Threat Detection Framework.

CyberShield XDR is a Dockerized enterprise SOC platform prototype with a FastAPI backend, PostgreSQL/Redis services, WebSocket live feeds, and a premium React/Vite dark UI.

## Quick Start

```bash
cp .env.example .env
docker compose up --build
```

Services:

- Frontend: 
- Backend API:
- OpenAPI: 

Demo credentials:

- Email: `admin@cybershield.dev`
- Password: `CyberShield!2026`

## Stack

- Backend: Python 3.12, FastAPI, SQLAlchemy, Pydantic v2, JWT-ready auth, WebSockets
- Frontend: React 19, TypeScript, Vite, TailwindCSS, React Router, TanStack Query, Recharts, Framer Motion, Lucide
- Data: PostgreSQL, Redis
- Deployment: Docker Compose, Nginx, GitHub Actions

## Modules

Authentication, Dashboard, Log Management, Threat Detection, Anomaly Detection, Network Monitoring, Malware Analysis, Vulnerability Scanner, Threat Intelligence, Incident Management, Reports, Notifications, Audit Logs, and System Settings are implemented as independent backend routers/services with matching frontend routes.
