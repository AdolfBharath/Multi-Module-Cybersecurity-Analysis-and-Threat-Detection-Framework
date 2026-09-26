from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import or_, and_, func
from sqlalchemy.orm import Session

from app.core.deps import require_permissions
from app.db.models import AuditLog, Notification, NotificationReceipt, Permission, User
from app.db.session import get_db

router = APIRouter()


def _permission_set(db: Session, user: User) -> set[str]:
    if user.role.name == "Admin":
        return {"*"}
    return {row.action for row in db.query(Permission).filter(Permission.role_id == user.role_id).all()}


def _can_view(notification: Notification, user: User, permissions: set[str]) -> bool:
    if notification.organization_id is not None and notification.organization_id != user.organization_id:
        return False
    if notification.recipient_user_id and notification.recipient_user_id != user.id:
        return False
    return "*" in permissions or notification.required_permission in permissions


def _serialize(row: Notification, receipt: NotificationReceipt | None = None) -> dict:
    state = receipt or row
    return {
        "id": row.id,
        "channel": row.channel,
        "title": row.title,
        "message": row.message,
        "delivered": row.delivered,
        "severity": row.severity,
        "priority": row.priority,
        "status": state.status,
        "read_at": state.read_at,
        "archived_at": state.archived_at,
        "related_entity": row.related_entity,
        "related_id": row.related_id,
        "required_permission": row.required_permission,
        "metadata": row.metadata_json,
        "created_at": row.created_at,
    }


def _visible_query(db: Session, user: User):
    query = db.query(Notification)
    permissions = _permission_set(db, user)
    if "*" not in permissions:
        query = query.filter(Notification.required_permission.in_(permissions))
    if user.organization_id:
        query = query.filter(or_(Notification.organization_id == user.organization_id, Notification.organization_id.is_(None)))
    else:
        query = query.filter(Notification.organization_id.is_(None))
    return query.filter(or_(Notification.recipient_user_id == user.id, Notification.recipient_user_id.is_(None)))


def _unread_query(db: Session, user: User):
    return _visible_query(db, user).outerjoin(NotificationReceipt, and_(NotificationReceipt.notification_id == Notification.id, NotificationReceipt.user_id == user.id)).filter(func.coalesce(NotificationReceipt.status, Notification.status) == "unread")


def _set_status(db: Session, row: Notification, user: User, status: str):
    state = row
    if row.recipient_user_id is None:
        state = db.get(NotificationReceipt, (row.id, user.id))
        if state is None:
            state = NotificationReceipt(notification_id=row.id, user_id=user.id)
            db.add(state)
    state.status = status
    if status == "read":
        state.read_at = datetime.now(timezone.utc)
    else:
        state.archived_at = datetime.now(timezone.utc)
    return state


@router.put("/read-all")
def mark_all_read(user: User = Depends(require_permissions("dashboard:read")), db: Session = Depends(get_db)) -> dict:
    rows = _unread_query(db, user).all()
    for row in rows:
        _set_status(db, row, user, "read")
    db.add(AuditLog(actor=user.email, action="notifications:read-all", entity="notifications", metadata_json={"count": len(rows)}))
    db.commit()
    return {"success": True, "data": {"updated": len(rows)}}


@router.get("")
def notifications(user: User = Depends(require_permissions("dashboard:read")), db: Session = Depends(get_db)) -> dict:
    permissions = _permission_set(db, user)
    rows = _visible_query(db, user).order_by(Notification.created_at.desc()).limit(100).all()
    receipts = {r.notification_id: r for r in db.query(NotificationReceipt).filter(NotificationReceipt.user_id == user.id, NotificationReceipt.notification_id.in_([row.id for row in rows]))}
    data = [_serialize(row, receipts.get(row.id)) for row in rows if _can_view(row, user, permissions)]
    return {"success": True, "data": data, "meta": {"count": len(data), "unread_count": sum(1 for item in data if item["status"] == "unread")}}


@router.get("/unread-count")
def unread_count(user: User = Depends(require_permissions("dashboard:read")), db: Session = Depends(get_db)) -> dict:
    permissions = _permission_set(db, user)
    rows = _unread_query(db, user).all()
    count = sum(1 for row in rows if _can_view(row, user, permissions))
    return {"success": True, "data": {"unread_count": count}}


@router.put("/{notification_id}/read")
def mark_read(notification_id: int, request: Request, user: User = Depends(require_permissions("dashboard:read")), db: Session = Depends(get_db)) -> dict:
    row = db.get(Notification, notification_id)
    if not row or not _can_view(row, user, _permission_set(db, user)):
        raise HTTPException(status_code=404, detail="Notification not found")
    state = _set_status(db, row, user, "read")
    db.add(AuditLog(actor=user.email, action="notifications:read", entity="notifications", metadata_json={"notification_id": row.id}, ip_address=request.client.host if request.client else ""))
    db.commit()
    return {"success": True, "data": _serialize(row, state)}


@router.put("/{notification_id}/archive")
def archive(notification_id: int, request: Request, user: User = Depends(require_permissions("dashboard:read")), db: Session = Depends(get_db)) -> dict:
    row = db.get(Notification, notification_id)
    if not row or not _can_view(row, user, _permission_set(db, user)):
        raise HTTPException(status_code=404, detail="Notification not found")
    state = _set_status(db, row, user, "archived")
    db.add(AuditLog(actor=user.email, action="notifications:archive", entity="notifications", metadata_json={"notification_id": row.id}, ip_address=request.client.host if request.client else ""))
    db.commit()
    return {"success": True, "data": _serialize(row, state)}


@router.post("/test")
def test_notification(payload: dict, user: User = Depends(require_permissions("dashboard:read"))) -> dict:
    return {"success": True, "data": {"channel": payload.get("channel", "browser"), "status": "queued", "recipient": user.email}}
