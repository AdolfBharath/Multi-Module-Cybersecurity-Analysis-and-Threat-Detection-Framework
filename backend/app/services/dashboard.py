from datetime import datetime, timedelta, timezone

import psutil
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models import Alert, Incident, NetworkEvent, Permission, SecurityLog, User


def get_dashboard_metrics(db: Session, user: User | None = None) -> dict:
    permissions = {p.action for p in db.query(Permission).filter(Permission.role_id == user.role_id)} if user else set()

    def scoped(model, permission):
        query = db.query(model)
        if user:
            query = query.filter(model.organization_id == user.organization_id)
            if user.role.name != "Admin" and permission not in permissions:
                query = query.filter(False)
        return query

    alerts = scoped(Alert, "alerts:read")
    logs = scoped(SecurityLog, "logs:read")
    incidents = scoped(Incident, "incidents:read")
    network = scoped(NetworkEvent, "dashboard:read")
    severities = dict(alerts.with_entities(Alert.severity, func.count(Alert.id)).group_by(Alert.severity).all())
    recent_logs = logs.order_by(SecurityLog.created_at.desc()).limit(8).all()
    recent_alerts = alerts.order_by(Alert.created_at.desc()).limit(8).all()
    today = datetime.now(timezone.utc).date()
    daily = dict(alerts.filter(Alert.created_at >= today - timedelta(days=29)).with_entities(func.date(Alert.created_at), func.count(Alert.id)).group_by(func.date(Alert.created_at)).all())
    daily = {str(day): count for day, count in daily.items()}

    def series(days, key):
        dates = [today - timedelta(days=days - i - 1) for i in range(days)]
        return [{"name": day.strftime("%b %d"), key: daily.get(str(day), 0)} for day in dates]

    sources = network.with_entities(NetworkEvent.src_ip, func.count(NetworkEvent.id)).group_by(NetworkEvent.src_ip).limit(8).all()
    mitre = alerts.with_entities(Alert.tactic, Alert.technique, func.count(Alert.id)).group_by(Alert.tactic, Alert.technique).all()
    return {
        "total_logs": logs.count(),
        "critical_alerts": severities.get("critical", 0),
        "incidents": incidents.filter(Incident.status.notin_(["closed", "resolved"])).count(),
        "high_threats": severities.get("high", 0),
        "medium_threats": severities.get("medium", 0),
        "low_threats": severities.get("low", 0),
        "network_status": "Events recorded" if network.count() else "No network events",
        "cpu": psutil.cpu_percent(),
        "memory": psutil.virtual_memory().percent,
        "disk": psutil.disk_usage("/").percent,
        "todays_attacks": daily.get(str(today), 0),
        "weekly_trend": series(7, "attacks"),
        "monthly_trend": series(30, "alerts"),
        "attack_timeline": [{"name": a.title, "severity": a.severity, "time": a.created_at.isoformat()} for a in recent_alerts],
        "alert_timeline": [{"name": a.title, "value": int(a.confidence * 100)} for a in recent_alerts],
        "recent_activity": [{"actor": "sensor", "action": a.message[:80], "time": a.created_at.isoformat()} for a in recent_logs],
        "live_feed": [{"id": a.id, "title": a.title, "severity": a.severity, "source": a.source, "created_at": a.created_at.isoformat()} for a in recent_alerts],
        "threat_map": [],
        "top_attack_sources": [{"ip": ip, "count": count} for ip, count in sources],
        "mitre_matrix": [{"tactic": tactic, "technique": technique, "count": count} for tactic, technique, count in mitre if tactic or technique],
    }
