"""Load only the fictional Jenovate LMS dataset into the CyberShield demo org."""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.core.config import settings
from app.core.security import hash_password, validate_password_strength
from app.db.models import Alert, Incident, NetworkEvent, Notification, Organization, Role, SecurityLog, User, VulnerabilityReport, MalwareReport, ThreatIntelIndicator
from app.db.session import SessionLocal
from app.seed import seed_database
from app.services.jenovate_lms import ingest_events

DATASET = Path(__file__).resolve().parents[2] / "datasets" / "jenovate_lms" / "security_events.jsonl"
ORG_NAME = "Jenovate LMS"
ORG_SLUG = "jenovate-lms"
USERS = [
    ("Admin", "Jenovate SOC Administrator", "test.admin@cybershield.local", "TEST_ADMIN_PASSWORD"),
    ("SOC Analyst", "Jenovate SOC Analyst", "test.soc@cybershield.local", "TEST_SOC_PASSWORD"),
    ("Malware Analyst", "Jenovate Malware Analyst", "test.malware@cybershield.local", "TEST_MALWARE_PASSWORD"),
    ("Vulnerability Analyst", "Jenovate Vulnerability Analyst", "test.vuln@cybershield.local", "TEST_VULN_PASSWORD"),
    ("Viewer", "Jenovate Security Viewer", "test.viewer@cybershield.local", "TEST_VIEWER_PASSWORD"),
]


def _password(name: str) -> str:
    value = os.getenv(name, "")
    if not value:
        raise RuntimeError(f"Missing {name}")
    validate_password_strength(value)
    return value


def _remove_generic_demo(db) -> None:
    """Remove only the known old generated demo rows, never user-created records."""
    for source in ("waf-east", "identity", "edr", "dns"):
        db.query(SecurityLog).filter(SecurityLog.organization_id.is_(None), SecurityLog.source == source).delete()
    for title in ("SQL Injection Attempt", "Credential Stuffing Burst", "DNS Beaconing"):
        db.query(Alert).filter(Alert.organization_id.is_(None), Alert.title == title).delete()
    for title in ("Potential web application compromise", "Privileged account attack"):
        db.query(Incident).filter(Incident.organization_id.is_(None), Incident.title == title).delete()
    db.query(NetworkEvent).filter(NetworkEvent.organization_id.is_(None), NetworkEvent.src_ip.in_(["203.0.113.13", "198.51.100.44", "192.0.2.77"])).delete()
    db.query(Notification).filter(Notification.organization_id.is_(None), Notification.title == "Critical alert opened").delete()


def seed_jenovate_data() -> dict:
    if settings.is_production:
        raise RuntimeError("Refusing to load fictional LMS data in production")
    if not DATASET.exists():
        raise RuntimeError(f"Dataset missing: {DATASET}")
    seed_database()
    db = SessionLocal()
    try:
        _remove_generic_demo(db)
        org = db.query(Organization).filter(Organization.slug == ORG_SLUG).first()
        if not org:
            org = db.query(Organization).filter(Organization.slug == "cybershield-test").first()
        if not org:
            org = Organization(name=ORG_NAME, slug=ORG_SLUG)
            db.add(org); db.flush()
        else:
            # This is the development-only organization created by the former
            # test seed. Reusing it preserves local analyst accounts while
            # removing its unrelated generated records.
            org.name, org.slug = ORG_NAME, ORG_SLUG
            db.query(Notification).filter(Notification.organization_id == org.id).delete()
            db.query(Incident).filter(Incident.organization_id == org.id).delete()
            db.query(Alert).filter(Alert.organization_id == org.id).delete()
            db.query(SecurityLog).filter(SecurityLog.organization_id == org.id).delete()
            db.query(NetworkEvent).filter(NetworkEvent.organization_id == org.id).delete()
            db.query(MalwareReport).filter(MalwareReport.organization_id == org.id).delete()
            db.query(VulnerabilityReport).filter(VulnerabilityReport.organization_id == org.id).delete()
            db.query(ThreatIntelIndicator).filter(ThreatIntelIndicator.organization_id == org.id).delete()
        accounts = {}
        for role_name, full_name, email, password_var in USERS:
            role = db.query(Role).filter(Role.name == role_name).one()
            user = db.query(User).filter(User.email == email).first()
            if not user:
                user = User(email=email, full_name=full_name, password_hash=hash_password(_password(password_var)), role_id=role.id)
                db.add(user)
            user.full_name, user.role_id, user.organization_id = full_name, role.id, org.id
            user.is_active, user.is_verified = True, True
            accounts[email] = user
        db.flush()
        events = [json.loads(line) for line in DATASET.read_text(encoding="utf-8").splitlines() if line]
        # Keep the recorded order, but place the LMS activity in a recent window
        # so operators can read the dashboard as a live investigation timeline.
        now = datetime.now(timezone.utc)
        for index, event in enumerate(events):
            event["timestamp"] = (now - timedelta(minutes=len(events) - index - 1)).isoformat()
        imported = ingest_events(db, events, org.id)
        db.query(Notification).filter(Notification.organization_id == org.id).delete()
        db.query(Incident).filter(Incident.organization_id == org.id).delete()
        db.query(Alert).filter(Alert.organization_id == org.id).delete()
        suspicious = [event for event in events if event.get("ground_truth") == "suspicious"]
        for index, event in enumerate(suspicious, 1):
            title = f"Jenovate LMS: {event['event_type'].replace('_', ' ').title()}"
            created_at = datetime.fromisoformat(event["timestamp"])
            alert = Alert(title=title, severity=event["severity"], status="open", source="jenovate_lms", tactic="LMS Authorization", technique=event["event_type"], confidence=0.82, description=event["action"], organization_id=org.id, user_email=event["actor_id"], created_at=created_at)
            db.add(alert); db.flush()
            if index <= 8:
                db.add(Incident(title=f"Investigate {event['event_type'].replace('_', ' ')}", severity=event["severity"], status="triage", assignee="test.soc@cybershield.local", evidence={"event_id": event["event_id"], "target": event["target_id"], "outcome": event["outcome"]}, timeline=[{"event": "Detection created from LMS telemetry", "actor": "jenovate_lms", "time": event["timestamp"]}], organization_id=org.id, created_at=created_at))
            network = event.get("metadata", {}).get("network")
            if network:
                db.add(NetworkEvent(src_ip=network["src_ip"], dst_ip=network["dst_ip"], protocol=network["protocol"], port=network["port"], event_type=event["event_type"], severity=event["severity"], status="detected", bytes_in=network["bytes_in"], bytes_out=network["bytes_out"], geo={}, organization_id=org.id, created_at=created_at))
            if event["event_type"] == "assignment_upload_quarantined":
                db.add(MalwareReport(file_name=f"assignment-upload-{event['event_id']}.bin", md5="", sha1="", sha256="", entropy=0.0, verdict="quarantined", yara_matches=["LMS_Assignment_Malware_Indicator"], details={"event_id": event["event_id"], "status": "quarantined"}, organization_id=org.id, submitted_by=event["actor_id"], created_at=created_at))
        db.add(Notification(channel="browser", title="Jenovate LMS telemetry loaded", message=f"Imported {imported['created']} fictional LMS events.", delivered=True, recipient_user_id=accounts["test.admin@cybershield.local"].id, organization_id=org.id, severity="info", priority="normal", required_permission="dashboard:read", metadata_json={"dataset":"jenovate_lms"}))
        db.commit()
        return {"organization": ORG_SLUG, **imported, "events": len(events), "alerts": len(suspicious)}
    finally:
        db.close()


if __name__ == "__main__":
    print(seed_jenovate_data())
