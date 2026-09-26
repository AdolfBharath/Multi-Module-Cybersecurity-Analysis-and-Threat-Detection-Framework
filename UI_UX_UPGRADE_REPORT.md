# CyberShield XDR Dashboard and Notification Upgrade

## Delivered

- Updated compact header, profile menu, module search, grouped permission-aware sidebar, desktop collapse, and mobile drawer.
- Dashboard uses recorded organization-scoped alerts/logs/incidents, with real 7-day and 30-day aggregation. Removed fixed readiness percentages, fabricated map points, generated chart values, and random WebSocket alerts.
- Security posture shows recorded severity distribution. No security score or percentage is claimed because the backend has no validated posture-scoring model.
- Added active incidents with assignee/status/time, recent security events, recent notifications, and retained host resource usage, recorded MITRE mappings, and recent log activity.
- Notification bell, dashboard panel, and notification center share one TanStack Query cache. Read, mark-all-read, and archive actions refresh that cache.
- Broadcast notifications now have independent per-user read/archive receipts; direct-recipient notifications retain their existing storage behavior.
- Existing WebSocket endpoint sends authorized database snapshots every 10 seconds. Frontend uses one connection, exponential reconnect, and a 60-second HTTP fallback while disconnected.
- Text detection creates persistent recipient notifications linked to the stored alert. Other integrations must explicitly create notification records to appear in the center.
- API failures produce safe, temporary toasts. Authentication refresh is single-flight, failed sessions clear their state, and logout clears only application session keys and cached queries.
- Added focus styles, accessible bell labels, keyboard dismissal, mobile navigation focus trapping, restrained transitions, and reduced-motion support.
- Preserved existing module routes and backend permission checks; dashboard/incident queries additionally enforce organization scope, and incident creation requires its create permission.

## Executed Verification

| Check | Result |
| --- | --- |
| Frontend production build | PASS; existing large-bundle warning remains |
| Notification/dashboard backend tests | 8 passed |
| Existing security hardening tests | 10 passed |
| Browser UI tests with deterministic API/WebSocket fixtures | 5 passed |
| Live browser login, dashboard, notification connection and bell | PASS for Admin, SOC Analyst, Malware Analyst, Vulnerability Analyst, Viewer |
| Responsive dashboard screenshots | PASS at 320, 375, 390, 768, 1024, 1440 pixels; no horizontal page overflow |
| Mobile notification panel and keyboard dismissal | PASS |
| SQLite migration fresh upgrade, receipt downgrade, receipt re-upgrade | PASS |
| Frontend lint | PASS; added ESLint 9 TypeScript and React Hooks configuration |

The backend tests previously forced the process to exit before normal pytest completion. Removed that hook. A filesystem permission issue blocks pytest's optional cache directory on this machine; tests were executed with `-p no:cacheprovider`, allowing full teardown and normal exit status.

The first browser run encountered a missing bundled Chromium executable; tests subsequently ran against installed Chrome. A drawer test initially checked geometry during its transition; it now waits for the drawer to settle. Final browser tests passed. Screenshot capture disables animations so images show settled states.

## Reproduce

Backend, using the repository virtual environment:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_notifications.py -q -p no:cacheprovider
.\.venv\Scripts\python.exe -m pytest tests/test_security_hardening.py -q -p no:cacheprovider
```

Frontend, with the application running:

```powershell
cd frontend
pnpm install --frozen-lockfile
pnpm exec playwright install chromium
$env:UI_BASE_URL='http://127.0.0.1:5174'
pnpm test
pnpm run build
```

Alternatively set `PLAYWRIGHT_CHANNEL=chrome` to test against installed Chrome. `tests/live-smoke.cjs` tests real sign-in for the five seeded accounts; it requires their five `TEST_*_PASSWORD` environment variables and never logs passwords.

## Database Upgrade

Apply `alembic upgrade head` before deploying the backend update. Revision `20260925_0002` adds only `notification_receipts`; existing notification records are preserved. Downgrading that revision removes per-user receipt history.

## Local Application

- Updated frontend: http://127.0.0.1:5174/
- Updated backend: http://127.0.0.1:8001/
- Existing development database and test accounts are preserved.
- Screenshots and server logs are local-only in `.local-run/` (Git ignored).

## Limits

- Module search searches authorized navigation destinations, not the contents of all security records.
- Notification center displays the newest 100 authorized records; the unread badge and mark-all-read include all authorized unread records.
- Delivery is periodic server-side snapshots, not an external event broker. New notifications normally arrive within 10 seconds.
- Posture scoring, geolocation, historical percentage comparisons, and fabricated telemetry are deliberately not presented as real measurements.
- Resource links open the existing module route with the resource ID; the existing application does not provide dedicated detail routes for every resource type.
- Production PostgreSQL, full Docker deployment, and the security of untouched modules were not certified by this UI upgrade. The existing production-readiness limitations still apply.
