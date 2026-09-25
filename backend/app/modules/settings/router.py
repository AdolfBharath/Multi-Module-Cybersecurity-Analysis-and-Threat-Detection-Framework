from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.deps import require_permissions
from app.db.models import AuditLog, SystemSetting, User
from app.db.session import get_db

router = APIRouter()


@router.get("")
def get_settings(_: User = Depends(require_permissions("settings:read")), db: Session = Depends(get_db)) -> dict:
    rows = db.query(SystemSetting).all()
    return {"success": True, "data": {row.key: row.value for row in rows}}


@router.put("/{key}")
def update_setting(key: str, payload: dict, request: Request, user: User = Depends(require_permissions("settings:update")), db: Session = Depends(get_db)) -> dict:
    row = db.query(SystemSetting).filter(SystemSetting.key == key).first()
    if row:
        row.value = payload
    else:
        row = SystemSetting(key=key, value=payload)
        db.add(row)
    db.add(AuditLog(actor=user.email, action="settings:update", entity="system_settings", metadata_json={"key": key}, ip_address=request.client.host if request.client else ""))
    db.commit()
    return {"success": True, "data": {key: payload}}
