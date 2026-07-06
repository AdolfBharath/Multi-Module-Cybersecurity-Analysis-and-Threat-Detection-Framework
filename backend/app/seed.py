from app.core.security import hash_password
from app.db.models import Alert, Incident, NetworkEvent, Notification, Permission, Role, SecurityLog, SystemSetting, User
from app.db.session import SessionLocal


def seed_database() -> None:
    db = SessionLocal()
    try:
        role_names = {
            "Admin": "Full platform administration",
            "Security Analyst": "Investigate alerts and incidents",
            "SOC Manager": "Manage SOC operations and reporting",
            "Viewer": "Read-only access",
        }
        for name, description in role_names.items():
            if not db.query(Role).filter(Role.name == name).first():
                db.add(Role(name=name, description=description))
        db.flush()

        for role in db.query(Role).all():
            existing_permissions = {permission.action for permission in role.permissions}
            for action in ["dashboard:read", "logs:read", "alerts:read", "incidents:read"]:
                if action not in existing_permissions:
                    db.add(Permission(role_id=role.id, action=action))

        admin_role = db.query(Role).filter(Role.name == "Admin").first()
        admin_user = db.query(User).filter(User.email == "admin@cybershield.dev").first()
        legacy_admin = db.query(User).filter(User.email == "admin@cybershield.local").first()
        if legacy_admin and not admin_user:
            legacy_admin.email = "admin@cybershield.dev"
            legacy_admin.password_hash = hash_password("CyberShield!2026")
            legacy_admin.role_id = admin_role.id
            admin_user = legacy_admin
        elif legacy_admin and admin_user and legacy_admin.id != admin_user.id:
            legacy_admin.email = f"legacy-admin-{legacy_admin.id}@cybershield.dev"

        if not admin_user:
            db.add(User(email="admin@cybershield.dev", full_name="CyberShield Administrator", password_hash=hash_password("CyberShield!2026"), role_id=admin_role.id))
        else:
            admin_user.password_hash = hash_password("CyberShield!2026")
            admin_user.role_id = admin_role.id

        if db.query(SecurityLog).count() == 0:
            db.add_all(
                [
                    SecurityLog(source="waf-east", log_type="nginx", message="GET /search?q=' UNION SELECT password FROM users --", severity="critical", tags=["sql-injection", "waf"]),
                    SecurityLog(source="identity", log_type="windows", message="4625 failed login burst for admin from 203.0.113.13", severity="high", tags=["brute-force"]),
                    SecurityLog(source="edr", log_type="process", message="powershell.exe -enc SQBFAFgA suspicious encoded command", severity="high", tags=["powershell"]),
                    SecurityLog(source="dns", log_type="resolver", message="Long base64-like subdomain observed from FIN-22", severity="medium", tags=["dns-tunneling"]),
                ]
            )

        if db.query(Alert).count() == 0:
            db.add_all(
                [
                    Alert(title="SQL Injection Attempt", severity="critical", status="open", source="waf-east", tactic="Initial Access", technique="T1190", confidence=0.96, description="Public-facing app exploit pattern blocked."),
                    Alert(title="Credential Stuffing Burst", severity="high", status="investigating", source="identity", tactic="Credential Access", technique="T1110", confidence=0.88, description="Repeated failed authentication against privileged user."),
                    Alert(title="DNS Beaconing", severity="medium", status="open", source="dns", tactic="Command and Control", technique="T1071", confidence=0.74, description="Periodic DNS callbacks with suspicious entropy."),
                ]
            )

        if db.query(Incident).count() == 0:
            db.add_all(
                [
                    Incident(title="Potential web application compromise", severity="critical", status="triage", assignee="Asha Rao", evidence={"alert_ids": [1]}, timeline=[{"event": "Alert correlated", "actor": "engine"}]),
                    Incident(title="Privileged account attack", severity="high", status="contained", assignee="Marcus Lee", evidence={"source_ip": "203.0.113.13"}, timeline=[{"event": "Account locked", "actor": "identity"}]),
                ]
            )

        if db.query(NetworkEvent).count() == 0:
            db.add_all(
                [
                    NetworkEvent(src_ip="203.0.113.13", dst_ip="10.0.4.12", protocol="TCP", port=443, bytes_in=18292, bytes_out=921, geo={"country": "US"}),
                    NetworkEvent(src_ip="198.51.100.44", dst_ip="10.0.8.21", protocol="UDP", port=53, bytes_in=4521, bytes_out=7710, geo={"country": "DE"}),
                    NetworkEvent(src_ip="192.0.2.77", dst_ip="10.0.1.6", protocol="TCP", port=22, bytes_in=918, bytes_out=319, geo={"country": "SG"}),
                ]
            )

        if db.query(Notification).count() == 0:
            db.add(Notification(channel="browser", title="Critical alert opened", message="SQL Injection Attempt requires triage", delivered=True))

        if db.query(SystemSetting).count() == 0:
            db.add_all(
                [
                    SystemSetting(key="company", value={"name": "CyberShield Labs"}),
                    SystemSetting(key="retention", value={"logs_days": 180, "audit_days": 365}),
                    SystemSetting(key="soc", value={"timezone": "UTC", "severity_sla_hours": {"critical": 4, "high": 12, "medium": 48}}),
                ]
            )

        db.commit()
    finally:
        db.close()
