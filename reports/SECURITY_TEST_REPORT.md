# Security and Functional Test Report

Date: 2026-10-23

## Executed Results

- Backend automated suite in the Linux backend image: **18 passed** in 33.53 seconds.
- Jenovate adapter focused tests: **2 passed** in 2.79 seconds.
- Frontend lint: passed.
- Frontend production build: passed.
- Live API: health and readiness endpoints returned 200.
- Live roles: five role accounts authenticated successfully.
- Live modules returning 200: dashboard, logs, incidents, detection, malware, vulnerabilities, network, threat intelligence, reports, notifications, audit, settings.
- Authorization checks: Viewer settings update and audit access returned 403.

The Playwright test browser started only through the installed system Chrome in this environment; browser navigation to loopback was denied by the execution sandbox. This is an environment limitation, not reported as a passing UI test.

Docker Desktop stopped after the earlier successful stack validation, so a new full container-suite run after adding the two adapter tests was not available. This is recorded as a runtime-environment blocker rather than a test pass.
