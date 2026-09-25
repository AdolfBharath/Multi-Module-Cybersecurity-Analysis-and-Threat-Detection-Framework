from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

from app.core.config import settings
from app.core.security import hash_password, validate_password_strength
from app.db.models import (
    Alert,
    AuditLog,
    Incident,
    MalwareReport,
    NetworkEvent,
    Notification,
    Organization,
    Role,
    SecurityLog,
    ThreatIntelIndicator,
    User,
    VulnerabilityReport,
)
from app.db.session import SessionLocal
from app.seed import seed_database

TEST_ORG_NAME = "CyberShield Test Organization"
TEST_ORG_SLUG = "cybershield-test"

TEST_USERS = [
    ("Admin", "Test Administrator", "test.admin@cybershield.local", "TEST_ADMIN_PASSWORD"),
    ("SOC Analyst", "Test SOC Analyst", "test.soc@cybershield.local", "TEST_SOC_PASSWORD"),
    ("Malware Analyst", "Test Malware Analyst", "test.malware@cybershield.local", "TEST_MALWARE_PASSWORD"),
    ("Vulnerability Analyst", "Test Vulnerability Analyst", "test.vuln@cybershield.local", "TEST_VULN_PASSWORD"),
    ("Viewer", "Test Security Viewer", "test.viewer@cybershield.local", "TEST_VIEWER_PASSWORD"),
]


def _require_enabled() -> None:
    if settings.is_production:
        raise RuntimeError("Refusing to load test data in production")
    if os.getenv("LOAD_TEST_DATA", "false").lower() not in {"1", "true", "yes"}:
        raise RuntimeError("Set LOAD_TEST_DATA=true to load development/staging test data")


def _password(env_name: str) -> str:
    value = os.getenv(env_name, "")
    if not value:
        raise RuntimeError(f"Missing {env_name}; test passwords must come from environment variables")
    validate_password_strength(value)
    return value


def _get_or_create_org(db) -> Organization:
    org = db.query(Organization).filter(Organization.slug == TEST_ORG_SLUG).first()
    if not org:
        org = Organization(name=TEST_ORG_NAME, slug=TEST_ORG_SLUG)
        db.add(org)
        db.flush()
    return org


def _get_or_create_user(db, org: Organization, role_name: str, full_name: str, email: str, password_env: str) -> User:
    role = db.query(Role).filter(Role.name == role_name).first()
    if not role:
        raise RuntimeError(f"Role does not exist: {role_name}")
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            email=email,
            full_name=full_name,
            password_hash=hash_password(_password(password_env)),
            role_id=role.id,
            is_active=True,
            is_verified=True,
            organization_id=org.id,
        )
        db.add(user)
    else:
        user.full_name = full_name
        user.password_hash = hash_password(_password(password_env))
        user.role_id = role.id
        user.is_active = True
        user.is_verified = True
        user.organization_id = org.id
    db.flush()
    return user


def _upsert_by_title(db, model, title: str, values: dict):
    row = db.query(model).filter(model.title == title).first()
    if not row:
        row = model(title=title, **values)
        db.add(row)
    else:
        for key, value in values.items():
            setattr(row, key, value)
    db.flush()
    return row


def _seed_logs(db, org: Organization) -> list[SecurityLog]:
    now = datetime.now(timezone.utc)
    scenarios = [
        ("identity", "auth", "Failed SSH login for root from 192.0.2.10", "high", ["ssh", "failed-login"]),
        ("identity", "auth", "Multiple failed authentication attempts for svc-backup from 203.0.113.25", "high", ["brute-force"]),
        ("identity", "auth", "Successful login after failed attempts for test.soc@cybershield.local", "medium", ["login"]),
        ("edr", "process", "Suspicious PowerShell execution with encoded command on test-win-01", "high", ["powershell"]),
        ("ids", "network", "TCP port scan detected from 198.51.100.42 to test-api-01", "medium", ["port-scan"]),
        ("api-gateway", "api", "Unauthorized API request against /api/v1/settings", "medium", ["unauthorized"]),
        ("edr", "privilege", "Privilege escalation attempt using local admin group modification", "critical", ["privilege-escalation"]),
        ("dns", "resolver", "Suspicious DNS request to test-indicator.example.test", "medium", ["dns"]),
        ("edr", "malware", "Synthetic malware signature TEST-EICAR-LIKE detected", "critical", ["malware"]),
        ("identity", "auth", "Impossible-travel login pattern for analyst account", "high", ["impossible-travel"]),
        ("identity", "auth", "Account lockout for test.viewer@cybershield.local after failed attempts", "low", ["lockout"]),
        ("firewall", "network", "Firewall deny event from 203.0.113.77 to 10.10.5.20:22", "medium", ["firewall"]),
        ("waf", "http", "SQL injection probe blocked on test-web-01", "critical", ["waf", "sql-injection"]),
        ("proxy", "http", "Possible data exfiltration via unusual upload volume", "high", ["exfiltration"]),
        ("ids", "network", "DNS tunneling indicator with long encoded labels", "high", ["dns-tunneling"]),
        ("linux", "syslog", "sudo command executed by test.soc@cybershield.local", "info", ["sudo"]),
        ("edr", "process", "Credential dumping tool name observed in command line", "critical", ["credential-access"]),
        ("cloud", "iam", "Denied attempt to attach administrator policy", "high", ["iam"]),
        ("db", "database", "Repeated failed database login for reporting_user", "medium", ["database"]),
        ("vpn", "auth", "VPN login from documentation IP 192.0.2.44", "low", ["vpn"]),
        ("mail", "email", "Suspicious attachment quarantined in test mailbox", "medium", ["email"]),
        ("edr", "file", "Sensitive file access anomaly on test-db-01", "high", ["data-access"]),
        ("ids", "network", "Multiple failed TCP connections to test-linux-01", "low", ["connection-failure"]),
        ("waf", "http", "Unauthorized admin panel access attempt", "medium", ["admin-panel"]),
        ("identity", "auth", "Password spray pattern across five test users", "high", ["password-spray"]),
    ]
    rows = []
    for index, (source, log_type, message, severity, tags) in enumerate(scenarios):
        row = db.query(SecurityLog).filter(SecurityLog.message == message, SecurityLog.organization_id == org.id).first()
        if not row:
            row = SecurityLog(source=source, log_type=log_type, message=message, severity=severity, tags=tags, raw={"synthetic": True, "test_id": f"TEST-LOG-{index+1:03d}"}, organization_id=org.id, created_at=now - timedelta(minutes=index * 9))
            db.add(row)
        rows.append(row)
    db.flush()
    return rows


def _seed_alerts(db, org: Organization) -> dict[str, Alert]:
    alerts = [
        ("Brute Force Authentication Attempt", "high", "identity", "Credential Access", "T1110", "A high-volume failed login pattern was detected.", "test.soc@cybershield.local"),
        ("Suspicious Port Scan", "medium", "ids", "Discovery", "T1046", "Sequential port access was observed against test-api-01.", ""),
        ("Malware Signature Detected", "critical", "edr", "Execution", "T1204", "Synthetic malware signature TEST-EICAR-LIKE was detected.", "test.malware@cybershield.local"),
        ("Privilege Escalation Attempt", "critical", "edr", "Privilege Escalation", "T1068", "Local administrator group modification was blocked.", "test.soc@cybershield.local"),
        ("Suspicious PowerShell Activity", "high", "edr", "Execution", "T1059.001", "Encoded PowerShell command observed on endpoint.", "test.soc@cybershield.local"),
        ("Possible Data Exfiltration", "high", "proxy", "Exfiltration", "T1041", "Unusual outbound upload volume detected.", ""),
        ("Unauthorized API Access", "medium", "api-gateway", "Initial Access", "T1190", "Unauthorized API request blocked.", ""),
        ("Suspicious DNS Activity", "medium", "dns", "Command and Control", "T1071.004", "Suspicious DNS tunneling indicator observed.", ""),
        ("Multiple Failed Logins", "low", "identity", "Credential Access", "T1110", "Multiple failed login attempts detected.", "test.viewer@cybershield.local"),
        ("Critical Vulnerability Detected", "critical", "scanner", "Initial Access", "T1190", "Critical synthetic vulnerability found on test-web-01.", "test.vuln@cybershield.local"),
    ]
    result = {}
    for title, severity, source, tactic, technique, description, email in alerts:
        result[title] = _upsert_by_title(
            db,
            Alert,
            title,
            {
                "severity": severity,
                "status": "open" if severity in {"critical", "high"} else "triage",
                "source": source,
                "tactic": tactic,
                "technique": technique,
                "confidence": 0.91 if severity == "critical" else 0.78,
                "description": description,
                "organization_id": org.id,
                "user_email": email,
            },
        )
    return result


def _seed_incidents(db, org: Organization, alerts: dict[str, Alert]) -> dict[str, Incident]:
    incidents = [
        ("Possible Brute Force Attack", "high", "open", "test.soc@cybershield.local", alerts["Brute Force Authentication Attempt"].id),
        ("Suspected Malware Infection", "critical", "investigating", "test.malware@cybershield.local", alerts["Malware Signature Detected"].id),
        ("Critical Web Server Vulnerability", "high", "open", "test.vuln@cybershield.local", alerts["Critical Vulnerability Detected"].id),
        ("Suspicious Network Scanning", "medium", "investigating", "test.soc@cybershield.local", alerts["Suspicious Port Scan"].id),
        ("Unauthorized Privileged Access", "critical", "open", "test.soc@cybershield.local", alerts["Privilege Escalation Attempt"].id),
    ]
    result = {}
    for title, severity, status, assignee, alert_id in incidents:
        result[title] = _upsert_by_title(
            db,
            Incident,
            title,
            {
                "severity": severity,
                "status": status,
                "assignee": assignee,
                "evidence": {"alert_id": alert_id, "synthetic": True},
                "timeline": [{"event": "Created from synthetic alert", "actor": "seed_test_data"}],
                "organization_id": org.id,
            },
        )
    return result


def _seed_network_events(db, org: Organization) -> None:
    events = [
        ("198.51.100.42", "10.10.10.5", 54122, 22, "TCP", "SSH brute force", "high"),
        ("203.0.113.77", "10.10.20.10", 40001, 443, "TCP", "HTTP suspicious request", "medium"),
        ("192.0.2.55", "10.10.30.8", 53000, 53, "UDP", "DNS tunneling indicator", "high"),
        ("10.10.40.12", "198.51.100.88", 51515, 443, "TCP", "Outbound suspicious destination", "medium"),
        ("203.0.113.90", "10.10.20.10", 41000, 1, "TCP", "TCP port scan", "medium"),
        ("192.0.2.60", "10.10.50.11", 30000, 3389, "TCP", "Multiple failed connections", "low"),
        ("10.10.20.10", "198.51.100.101", 443, 443, "TCP", "Unusual traffic spike", "high"),
    ]
    for src, dst, src_port, port, proto, event_type, severity in events:
        row = db.query(NetworkEvent).filter(NetworkEvent.src_ip == src, NetworkEvent.dst_ip == dst, NetworkEvent.event_type == event_type).first()
        if not row:
            db.add(NetworkEvent(src_ip=src, dst_ip=dst, src_port=src_port, port=port, protocol=proto, event_type=event_type, severity=severity, status="detected", bytes_in=12000, bytes_out=4200, geo={"test": True}, organization_id=org.id))


def _seed_vulnerabilities(db, org: Organization) -> dict[str, VulnerabilityReport]:
    findings = [
        ("test-web-01", "SQL Injection", "critical", 9.8, [{"id": "CVE-2026-TEST-0001", "name": "Synthetic SQL Injection"}], "Validate inputs and use parameterized queries."),
        ("test-api-01", "Outdated OpenSSL", "high", 8.1, [{"id": "CVE-2026-TEST-0002", "name": "Synthetic OpenSSL Finding"}], "Patch OpenSSL package."),
        ("test-linux-01", "Weak SSH Configuration", "high", 7.5, [], "Disable password authentication and weak ciphers."),
        ("test-web-01", "Missing Security Headers", "medium", 5.4, [], "Add CSP, HSTS, and no-sniff headers."),
        ("test-db-01", "Information Disclosure", "low", 3.2, [], "Restrict verbose error output."),
    ]
    result = {}
    for asset, title, severity, cvss, cves, remediation in findings:
        row = db.query(VulnerabilityReport).filter(VulnerabilityReport.target == asset, VulnerabilityReport.severity == severity, VulnerabilityReport.cvss_score == cvss).first()
        if not row:
            row = VulnerabilityReport(target=asset, open_ports=[{"port": 443, "service": "https", "risk": severity}], cves=cves, os_detection="Synthetic Linux", recommendations=[remediation], organization_id=org.id, severity=severity, status="open", cvss_score=cvss)
            db.add(row)
        result[title] = row
    db.flush()
    return result


def _seed_malware(db, org: Organization) -> MalwareReport:
    row = db.query(MalwareReport).filter(MalwareReport.file_name == "Suspicious_Test_Sample_001").first()
    if not row:
        row = MalwareReport(
            file_name="Suspicious_Test_Sample_001",
            md5="0" * 32,
            sha1="1" * 40,
            sha256="a" * 64,
            entropy=7.81,
            verdict="suspicious",
            yara_matches=["TEST_Suspicious_Static_Sample"],
            details={"risk": "high", "file_type": "PE", "detection_count": 7, "analysis_status": "completed", "synthetic": True},
            organization_id=org.id,
            submitted_by="test.malware@cybershield.local",
        )
        db.add(row)
    db.flush()
    return row


def _seed_threat_intel(db, org: Organization) -> None:
    indicators = [
        ("198.51.100.42", "ip"),
        ("test-indicator.example.test", "domain"),
        ("https://example.test/synthetic-c2", "url"),
        ("b" * 64, "sha256"),
        ("phish@example.test", "email"),
    ]
    for indicator, indicator_type in indicators:
        row = db.query(ThreatIntelIndicator).filter(ThreatIntelIndicator.indicator == indicator).first()
        if not row:
            db.add(ThreatIntelIndicator(indicator=indicator, indicator_type=indicator_type, reputation="TEST_INDICATOR", confidence=50, sources=["synthetic-test-feed"], mitre=[{"tactic": "Test", "technique": "TEST_INDICATOR"}], raw={"synthetic": True}, watched=True, organization_id=org.id))


def _notification(db, org, recipient: User, title: str, message: str, severity: str, priority: str, related_entity: str, related_id: int, permission: str, status: str = "unread") -> None:
    row = db.query(Notification).filter(Notification.title == title, Notification.recipient_user_id == recipient.id, Notification.organization_id == org.id).first()
    values = {
        "channel": "browser",
        "message": message,
        "delivered": True,
        "severity": severity,
        "priority": priority,
        "status": status,
        "related_entity": related_entity,
        "related_id": related_id,
        "required_permission": permission,
        "metadata_json": {"flow": "event->detection->alert->incident->notification", "synthetic": True},
    }
    if not row:
        db.add(Notification(title=title, recipient_user_id=recipient.id, organization_id=org.id, **values))
    else:
        for key, value in values.items():
            setattr(row, key, value)


def seed_test_data() -> None:
    _require_enabled()
    seed_database()
    db = SessionLocal()
    try:
        org = _get_or_create_org(db)
        users = {email: _get_or_create_user(db, org, role, name, email, env) for role, name, email, env in TEST_USERS}
        _seed_logs(db, org)
        alerts = _seed_alerts(db, org)
        incidents = _seed_incidents(db, org, alerts)
        _seed_network_events(db, org)
        vulns = _seed_vulnerabilities(db, org)
        malware = _seed_malware(db, org)
        _seed_threat_intel(db, org)

        _notification(db, org, users["test.admin@cybershield.local"], "Critical security event detected", "A critical security event was detected in the CyberShield Test Organization.", "critical", "critical", "alert", alerts["Privilege Escalation Attempt"].id, "alerts:read")
        _notification(db, org, users["test.soc@cybershield.local"], "New high-severity alert", "A high-severity brute-force authentication alert requires investigation.", "high", "high", "incident", incidents["Possible Brute Force Attack"].id, "incidents:read")
        _notification(db, org, users["test.malware@cybershield.local"], "Malware analysis required", "A suspicious sample has been submitted for malware analysis.", "high", "high", "malware_report", malware.id, "malware:analyze")
        _notification(db, org, users["test.vuln@cybershield.local"], "Critical vulnerability discovered", "A critical vulnerability finding requires remediation.", "critical", "critical", "vulnerability_report", vulns["SQL Injection"].id, "vulnerability:scan")
        _notification(db, org, users["test.viewer@cybershield.local"], "Security posture summary available", "A read-only security posture summary is available for review.", "info", "normal", "report", 0, "reports:read", status="read")

        db.add(AuditLog(actor="seed_test_data", action="test_data:seed", entity="development_dataset", metadata_json={"organization": org.slug, "users": len(users)}))
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed_test_data()
