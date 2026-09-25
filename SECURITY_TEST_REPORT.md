# CyberShield XDR Security Test Report

Generated: 2026-09-25

## Executed Tests

Command:

```bash
cd backend
python -m pytest tests/test_security_hardening.py -q
```

Result:

```text
..........  [100%]
```

## Test Results

| Area | Test | Result |
| --- | --- | --- |
| Authentication | Hard-coded `admin@cybershield.dev` / `CyberShield!2026` cannot authenticate | PASS |
| Bootstrap admin | Environment-provisioned admin can authenticate and receives Admin permissions | PASS |
| Registration | Public registration cannot self-assign Admin | PASS |
| Registration | Public registration receives safe default Viewer role | PASS |
| Login protection | Repeated failed login attempts lock the account | PASS |
| Refresh rotation | Rotated refresh token cannot be reused | PASS |
| Password reset | Reset token is generated, hashed at rest, accepted once | PASS |
| Password reset | Reused reset token is rejected | PASS |
| Email verification | Verification token is generated, hashed at rest, accepted once | PASS |
| Email verification | Reused verification token is rejected | PASS |
| MFA | Demo code `000000` is rejected | PASS |
| MFA | Real TOTP code enables MFA | PASS |
| MFA | Login without MFA is rejected after MFA enablement | PASS |
| MFA | Login with valid TOTP succeeds | PASS |
| Authorization | Viewer cannot update settings | PASS |
| API security | Security headers and request ID are present | PASS |

## Other Verification

| Check | Command | Result |
| --- | --- | --- |
| Python compile | `python -m compileall backend/app backend/tests` | PASS |
| Alembic fresh DB upgrade | `alembic upgrade head` with SQLite test DB | PASS |
| Frontend production build | `pnpm run build` | PASS |
| Hard-coded credential scan | `rg "admin@cybershield\|CyberShield!2026\|change-me-in-production"` | PASS, no matches |
| Docker Compose config | `docker compose config` with required env vars | PASS |

## Not Yet Fully Covered

The following need additional automated coverage before claiming full enterprise production readiness:

- Full object-level authorization / BOLA tests across incidents, reports, malware reports, vulnerability reports, and sessions.
- Multi-tenant resource isolation across all tenant-owned models.
- WebSocket rate limits and connection limits.
- Full malware sandbox execution isolation test.
- CI runtime results from GitHub Actions after pushing.
- Frontend component/unit tests for permission-aware navigation.
