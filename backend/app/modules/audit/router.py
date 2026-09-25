from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import require_permissions
from app.db.models import AuditLog
from app.db.session import get_db

router = APIRouter(dependencies=[Depends(require_permissions("audit:read"))])


@router.get("")
def audit_logs(db: Session = Depends(get_db)) -> dict:
    rows = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(100).all()
    return {"success": True, "data": [{"id": row.id, "actor": row.actor, "action": row.action, "entity": row.entity, "metadata": row.metadata_json, "ip_address": row.ip_address, "created_at": row.created_at} for row in rows]}
