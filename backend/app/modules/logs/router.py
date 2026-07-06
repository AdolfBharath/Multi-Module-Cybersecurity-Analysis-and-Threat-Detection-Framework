import csv
import io
import json

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.orm import Session

from app.db.models import AuditLog, SecurityLog
from app.db.session import get_db
from app.schemas.modules import LogCreate, LogRead
from app.services.security_detection import analyze_text

router = APIRouter()


@router.get("", response_model=list[LogRead])
def list_logs(
    search: str = "",
    severity: str = "",
    skip: int = 0,
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
) -> list[SecurityLog]:
    query = db.query(SecurityLog)
    if search:
        query = query.filter(SecurityLog.message.ilike(f"%{search}%"))
    if severity:
        query = query.filter(SecurityLog.severity == severity)
    return query.order_by(SecurityLog.created_at.desc()).offset(skip).limit(limit).all()


@router.post("", response_model=LogRead)
def create_log(payload: LogCreate, db: Session = Depends(get_db)) -> SecurityLog:
    log = SecurityLog(**payload.model_dump())
    db.add(log)
    db.add(AuditLog(actor="api", action="create", entity="logs", metadata_json={"source": payload.source}))
    for alert in analyze_text(payload.message, payload.source)["alerts"]:
        from app.db.models import Alert

        db.add(Alert(**alert, status="open", tactic="Detection", technique=alert["title"]))
    db.commit()
    db.refresh(log)
    return log


@router.post("/upload")
def upload_logs(file: UploadFile = File(...), db: Session = Depends(get_db)) -> dict:
    content = file.file.read().decode("utf-8", errors="ignore")
    created = 0
    if file.filename.endswith(".json"):
        payload = json.loads(content)
        rows = payload if isinstance(payload, list) else [payload]
        for row in rows:
            db.add(SecurityLog(source=row.get("source", file.filename), log_type=row.get("log_type", "json"), message=str(row.get("message", row)), severity=row.get("severity", "info"), raw=row))
            created += 1
    elif file.filename.endswith(".csv"):
        for row in csv.DictReader(io.StringIO(content)):
            db.add(SecurityLog(source=row.get("source", file.filename), log_type=row.get("log_type", "csv"), message=row.get("message", str(row)), severity=row.get("severity", "info"), raw=row))
            created += 1
    else:
        for line in content.splitlines():
            if line.strip():
                db.add(SecurityLog(source=file.filename, log_type="text", message=line[:4000], severity="info", raw={"line": line}))
                created += 1
    db.add(AuditLog(actor="api", action="upload", entity="logs", metadata_json={"file": file.filename, "count": created}))
    db.commit()
    return {"success": True, "data": {"created": created, "filename": file.filename}}

