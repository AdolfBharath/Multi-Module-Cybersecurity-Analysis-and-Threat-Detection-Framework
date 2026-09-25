# ruff: noqa: E402

import os
from pathlib import Path

import pytest
from starlette.websockets import WebSocketDisconnect

os.environ["ENVIRONMENT"] = "test"
os.environ["SECRET_KEY"] = "test-secret-key-that-is-long-enough-for-tests"
os.environ["FIELD_ENCRYPTION_KEY"] = "test-encryption-key-that-is-long-enough"
os.environ["DATABASE_URL"] = "sqlite:///../test_notifications.db"
os.environ["ADMIN_BOOTSTRAP_EMAIL"] = "owner.notifications@example.com"
os.environ["ADMIN_BOOTSTRAP_PASSWORD"] = "OwnerNotifyStrong!2026"
os.environ["DEFAULT_PUBLIC_ROLE"] = "Viewer"
os.environ["LOAD_DEMO_DATA"] = "false"
os.environ["LOAD_TEST_DATA"] = "true"
os.environ["AUTO_CREATE_TABLES"] = "true"
os.environ["TEST_ADMIN_PASSWORD"] = "TestAdmin@2026!Secure"
os.environ["TEST_SOC_PASSWORD"] = "TestSOC@2026!Secure"
os.environ["TEST_MALWARE_PASSWORD"] = "TestMalware@2026!Secure"
os.environ["TEST_VULN_PASSWORD"] = "TestVuln@2026!Secure"
os.environ["TEST_VIEWER_PASSWORD"] = "TestViewer@2026!Secure"

from fastapi.testclient import TestClient

from app.db.models import Notification, Organization, Role, User
from app.db.session import Base, SessionLocal, engine
from app.main import create_app
from app.seed_test_data import seed_test_data


def setup_module() -> None:
    Path("../test_notifications.db").unlink(missing_ok=True)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    seed_test_data()


client = TestClient(create_app())


def _login(email: str, password: str) -> str:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_notifications_require_authentication() -> None:
    assert client.get("/api/v1/notifications").status_code == 401
    assert client.get("/api/v1/notifications", headers={"Authorization": "Bearer invalid"}).status_code == 401


def test_role_specific_notifications_visible() -> None:
    admin = _login("test.admin@cybershield.local", "TestAdmin@2026!Secure")
    soc = _login("test.soc@cybershield.local", "TestSOC@2026!Secure")
    malware = _login("test.malware@cybershield.local", "TestMalware@2026!Secure")
    vuln = _login("test.vuln@cybershield.local", "TestVuln@2026!Secure")
    viewer = _login("test.viewer@cybershield.local", "TestViewer@2026!Secure")

    assert "Critical security event detected" in {item["title"] for item in client.get("/api/v1/notifications", headers=_headers(admin)).json()["data"]}
    assert "New high-severity alert" in {item["title"] for item in client.get("/api/v1/notifications", headers=_headers(soc)).json()["data"]}
    assert "Malware analysis required" in {item["title"] for item in client.get("/api/v1/notifications", headers=_headers(malware)).json()["data"]}
    assert "Critical vulnerability discovered" in {item["title"] for item in client.get("/api/v1/notifications", headers=_headers(vuln)).json()["data"]}
    viewer_titles = {item["title"] for item in client.get("/api/v1/notifications", headers=_headers(viewer)).json()["data"]}
    assert "Security posture summary available" in viewer_titles
    assert "Malware analysis required" not in viewer_titles
    assert "Critical vulnerability discovered" not in viewer_titles


def test_notification_object_level_access_and_read_state() -> None:
    soc = _login("test.soc@cybershield.local", "TestSOC@2026!Secure")
    viewer = _login("test.viewer@cybershield.local", "TestViewer@2026!Secure")
    soc_rows = client.get("/api/v1/notifications", headers=_headers(soc)).json()["data"]
    target = next(item for item in soc_rows if item["title"] == "New high-severity alert")

    denied = client.put(f"/api/v1/notifications/{target['id']}/read", headers=_headers(viewer))
    assert denied.status_code == 404

    before = client.get("/api/v1/notifications/unread-count", headers=_headers(soc)).json()["data"]["unread_count"]
    marked = client.put(f"/api/v1/notifications/{target['id']}/read", headers=_headers(soc))
    assert marked.status_code == 200, marked.text
    after = client.get("/api/v1/notifications/unread-count", headers=_headers(soc)).json()["data"]["unread_count"]
    assert after == before - 1


def test_cross_organization_notification_hidden() -> None:
    with SessionLocal() as db:
        other_org = Organization(name="Other Test Organization", slug="other-test-org")
        db.add(other_org)
        db.flush()
        viewer_role = db.query(Role).filter(Role.name == "Viewer").first()
        other_user = User(email="other.viewer@cybershield.local", full_name="Other Viewer", password_hash="unused", role_id=viewer_role.id, organization_id=other_org.id)
        db.add(other_user)
        db.flush()
        db.add(Notification(channel="browser", title="Other tenant message", message="Hidden", recipient_user_id=other_user.id, organization_id=other_org.id, required_permission="dashboard:read"))
        db.commit()

    viewer = _login("test.viewer@cybershield.local", "TestViewer@2026!Secure")
    titles = {item["title"] for item in client.get("/api/v1/notifications", headers=_headers(viewer)).json()["data"]}
    assert "Other tenant message" not in titles


def test_websocket_notification_snapshot_is_authorized() -> None:
    viewer = _login("test.viewer@cybershield.local", "TestViewer@2026!Secure")
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/api/v1/ws/live?token=invalid"):
            pass

    with client.websocket_connect(f"/api/v1/ws/live?token={viewer}") as websocket:
        snapshot = websocket.receive_json()
        assert snapshot["type"] == "notification_snapshot"
        assert snapshot["unread_count"] == 0
        titles = {item["title"] for item in snapshot["notifications"]}
        assert "Security posture summary available" in titles
        assert "Malware analysis required" not in titles
