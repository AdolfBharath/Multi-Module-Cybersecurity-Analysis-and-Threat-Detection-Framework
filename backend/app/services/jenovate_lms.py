"""Adapter for fictional Jenovate LMS security-event JSONL telemetry."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db.models import SecurityLog

REQUIRED_FIELDS = {"event_id", "timestamp", "source", "event_type", "actor_id", "actor_role", "target_type", "target_id", "action", "outcome", "severity", "metadata"}
ALLOWED_SEVERITIES = {"info", "low", "medium", "high", "critical"}


def normalize_event(event: dict) -> dict:
    missing = REQUIRED_FIELDS - set(event)
    if missing:
        raise ValueError(f"missing event fields: {', '.join(sorted(missing))}")
    if event["source"] != "jenovate_lms":
        raise ValueError("unexpected source")
    if event["severity"] not in ALLOWED_SEVERITIES:
        raise ValueError("invalid severity")
    timestamp = datetime.fromisoformat(str(event["timestamp"]).replace("Z", "+00:00"))
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    raw = {key: value for key, value in event.items() if key != "ground_truth"}
    return {
        "event_id": str(event["event_id"]),
        "timestamp": timestamp,
        "source": "jenovate_lms",
        "log_type": str(event["event_type"]),
        "message": f"{event['action']} ({event['outcome']}) for {event['target_type']}:{event['target_id']}",
        "severity": event["severity"],
        "tags": ["jenovate", str(event["actor_role"]), str(event["outcome"])],
        "raw": raw | {"normalized_timestamp": timestamp.isoformat()},
    }


def ingest_events(db: Session, events: list[dict], organization_id: int | None = None) -> dict:
    existing = {
        str(row.raw.get("event_id"))
        for row in db.query(SecurityLog).filter(SecurityLog.source == "jenovate_lms").all()
        if isinstance(row.raw, dict) and row.raw.get("event_id")
    }
    created = duplicates = 0
    for event in events:
        item = normalize_event(event)
        if item["event_id"] in existing:
            duplicates += 1
            continue
        db.add(SecurityLog(source=item["source"], log_type=item["log_type"], message=item["message"], severity=item["severity"], tags=item["tags"], raw=item["raw"], organization_id=organization_id, created_at=item["timestamp"]))
        existing.add(item["event_id"]); created += 1
    db.commit()
    return {"created": created, "duplicates": duplicates}
