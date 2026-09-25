# ruff: noqa: E402

import os
import re
from pathlib import Path

os.environ["ENVIRONMENT"] = "test"
os.environ["SECRET_KEY"] = "test-secret-key-that-is-long-enough-for-tests"
os.environ["FIELD_ENCRYPTION_KEY"] = "test-encryption-key-that-is-long-enough"
os.environ["DATABASE_URL"] = "sqlite:///../test_security.db"
os.environ["ADMIN_BOOTSTRAP_EMAIL"] = "owner@example.com"
os.environ["ADMIN_BOOTSTRAP_PASSWORD"] = "OwnerStrong!2026"
os.environ["DEFAULT_PUBLIC_ROLE"] = "Viewer"
os.environ["LOAD_DEMO_DATA"] = "false"
os.environ["AUTO_CREATE_TABLES"] = "true"

import pyotp
import pytest
from fastapi.testclient import TestClient

from app.core.security import decrypt_secret
from app.db.models import EmailVerificationToken, PasswordResetToken, User
from app.db.session import Base, SessionLocal, engine
from app.main import create_app
from app.seed import seed_database
from app.services.email import EMAIL_OUTBOX


def setup_module() -> None:
    Path("../test_security.db").unlink(missing_ok=True)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    seed_database()


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(create_app())


def _login(client: TestClient, email: str = "owner@example.com", password: str = "OwnerStrong!2026") -> dict:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return response.json()


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_hardcoded_admin_credentials_cannot_authenticate(client: TestClient) -> None:
    response = client.post("/api/v1/auth/login", json={"email": "admin@cybershield.dev", "password": "CyberShield!2026"})
    assert response.status_code == 401


def test_bootstrap_admin_authenticates_and_has_permissions(client: TestClient) -> None:
    payload = _login(client)
    assert payload["user"]["role"] == "Admin"
    assert "settings:update" in payload["user"]["permissions"]
    assert payload["user"]["force_password_change"] is True


def test_registration_cannot_escalate_role(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "new-user@example.com", "full_name": "New User", "password": "NewUserStrong!2026", "role": "Admin"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["role"] == "Viewer"


def test_login_lockout_after_repeated_failures(client: TestClient) -> None:
    for _ in range(5):
        client.post("/api/v1/auth/login", json={"email": "new-user@example.com", "password": "WrongPassword!2026"})
    response = client.post("/api/v1/auth/login", json={"email": "new-user@example.com", "password": "NewUserStrong!2026"})
    assert response.status_code == 401


def test_refresh_rotation_rejects_reuse(client: TestClient) -> None:
    payload = _login(client)
    refresh = payload["refresh_token"]
    first = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
    assert first.status_code == 200, first.text
    reused = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
    assert reused.status_code == 401


def test_password_reset_token_single_use(client: TestClient) -> None:
    EMAIL_OUTBOX.clear()
    request = client.post("/api/v1/auth/forgot-password", json={"email": "owner@example.com"})
    assert request.status_code == 200
    token_match = re.search(r"Password reset token: ([A-Za-z0-9_\-]+)", EMAIL_OUTBOX[-1]["body"])
    assert token_match
    token = token_match.group(1)
    reset = client.post("/api/v1/auth/reset-password", json={"token": token, "new_password": "OwnerNewStrong!2026"})
    assert reset.status_code == 200, reset.text
    reused = client.post("/api/v1/auth/reset-password", json={"token": token, "new_password": "OwnerNewStrong!2027"})
    assert reused.status_code == 400
    with SessionLocal() as db:
        assert db.query(PasswordResetToken).filter(PasswordResetToken.used_at.is_not(None)).count() >= 1


def test_email_verification_token_single_use(client: TestClient) -> None:
    EMAIL_OUTBOX.clear()
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "verify-me@example.com", "full_name": "Verify Me", "password": "VerifyStrong!2026"},
    )
    assert response.status_code == 200
    token_match = re.search(r"Verification token: ([A-Za-z0-9_\-]+)", EMAIL_OUTBOX[-1]["body"])
    assert token_match
    token = token_match.group(1)
    verify = client.post("/api/v1/auth/verify-email", json={"email": "verify-me@example.com", "token": token})
    assert verify.status_code == 200, verify.text
    reused = client.post("/api/v1/auth/verify-email", json={"email": "verify-me@example.com", "token": token})
    assert reused.status_code == 400
    with SessionLocal() as db:
        assert db.query(EmailVerificationToken).filter(EmailVerificationToken.used_at.is_not(None)).count() >= 1


def test_mfa_requires_real_totp(client: TestClient) -> None:
    payload = _login(client, password="OwnerNewStrong!2026")
    headers = _auth_headers(payload["access_token"])
    setup = client.post("/api/v1/auth/mfa/setup", headers=headers)
    assert setup.status_code == 200, setup.text
    invalid = client.post("/api/v1/auth/mfa/verify", json={"code": "000000"}, headers=headers)
    assert invalid.status_code == 400
    with SessionLocal() as db:
        user = db.query(User).filter(User.email == "owner@example.com").first()
        code = pyotp.TOTP(decrypt_secret(user.mfa_secret_encrypted)).now()
    valid = client.post("/api/v1/auth/mfa/verify", json={"code": code}, headers=headers)
    assert valid.status_code == 200, valid.text
    login_without_mfa = client.post("/api/v1/auth/login", json={"email": "owner@example.com", "password": "OwnerNewStrong!2026"})
    assert login_without_mfa.status_code == 401
    with SessionLocal() as db:
        user = db.query(User).filter(User.email == "owner@example.com").first()
        code = pyotp.TOTP(decrypt_secret(user.mfa_secret_encrypted)).now()
    login_with_mfa = client.post("/api/v1/auth/login", json={"email": "owner@example.com", "password": "OwnerNewStrong!2026", "mfa_code": code})
    assert login_with_mfa.status_code == 200, login_with_mfa.text


def test_viewer_cannot_update_settings(client: TestClient) -> None:
    login = client.post("/api/v1/auth/login", json={"email": "verify-me@example.com", "password": "VerifyStrong!2026"})
    assert login.status_code == 200
    response = client.put("/api/v1/settings/company", json={"name": "Evil"}, headers=_auth_headers(login.json()["access_token"]))
    assert response.status_code == 403


def test_security_headers_present(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert "x-request-id" in response.headers
