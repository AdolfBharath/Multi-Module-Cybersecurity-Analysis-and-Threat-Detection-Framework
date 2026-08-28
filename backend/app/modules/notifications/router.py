from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import require_permissions
from app.db.models import Notification
from app.db.session import get_db

router = APIRouter(dependencies=[Depends(require_permissions("dashboard:read"))])


@router.get("")
def notifications(db: Session = Depends(get_db)) -> dict:
    rows = db.query(Notification).order_by(Notification.created_at.desc()).limit(50).all()
    return {"success": True, "data": [{"id": row.id, "channel": row.channel, "title": row.title, "message": row.message, "delivered": row.delivered, "created_at": row.created_at} for row in rows]}


@router.post("/test")
def test_notification(payload: dict) -> dict:
    return {"success": True, "data": {"channel": payload.get("channel", "browser"), "status": "queued"}}
