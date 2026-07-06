from datetime import datetime, timedelta, timezone

import psutil
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models import Alert, Incident, NetworkEvent, SecurityLog


def _series(days: int, label: str) -> list[dict]:
    today = datetime.now(timezone.utc).date()
    return [{"name": (today - timedelta(days=days - index - 1)).strftime("%b %d"), label: 18 + (index * 7) % 31} for index in range(days)]


def get_dashboard_metrics(db: Session) -> dict:
    severities = dict(db.query(Alert.severity, func.count(Alert.id)).group_by(Alert.severity).all())
    recent_logs = db.query(SecurityLog).order_by(SecurityLog.created_at.desc()).limit(8).all()
    recent_alerts = db.query(Alert).order_by(Alert.created_at.desc()).limit(8).all()
    sources = db.query(NetworkEvent.src_ip, func.count(NetworkEvent.id)).group_by(NetworkEvent.src_ip).limit(8).all()
    return {
        "total_logs": db.query(SecurityLog).count(),
        "critical_alerts": severities.get("critical", 0),
        "incidents": db.query(Incident).count(),
        "high_threats": severities.get("high", 0),
        "medium_threats": severities.get("medium", 0),
        "low_threats": severities.get("low", 0),
        "network_status": "Nominal",
        "cpu": psutil.cpu_percent(interval=0.1),
        "memory": psutil.virtual_memory().percent,
        "disk": psutil.disk_usage("/").percent,
        "todays_attacks": sum(severities.values()),
        "weekly_trend": _series(7, "attacks"),
        "monthly_trend": _series(12, "alerts"),
        "attack_timeline": [{"name": item.title, "severity": item.severity, "time": item.created_at.isoformat()} for item in recent_alerts],
        "alert_timeline": [{"name": item.title, "value": int(item.confidence * 100)} for item in recent_alerts],
        "recent_activity": [{"actor": "sensor", "action": item.message[:80], "time": item.created_at.isoformat()} for item in recent_logs],
        "live_feed": [{"title": item.title, "severity": item.severity, "source": item.source} for item in recent_alerts],
        "threat_map": [
            {"country": "US", "lat": 37.09, "lng": -95.71, "count": 24},
            {"country": "DE", "lat": 51.16, "lng": 10.45, "count": 17},
            {"country": "IN", "lat": 20.59, "lng": 78.96, "count": 21},
            {"country": "SG", "lat": 1.35, "lng": 103.82, "count": 11},
        ],
        "top_attack_sources": [{"ip": ip, "count": count} for ip, count in sources],
        "mitre_matrix": [
            {"tactic": "Initial Access", "technique": "T1190 Exploit Public-Facing App", "count": 14},
            {"tactic": "Execution", "technique": "T1059 Command and Scripting Interpreter", "count": 9},
            {"tactic": "Credential Access", "technique": "T1110 Brute Force", "count": 18},
            {"tactic": "Exfiltration", "technique": "T1041 Exfiltration Over C2", "count": 5},
        ],
    }

