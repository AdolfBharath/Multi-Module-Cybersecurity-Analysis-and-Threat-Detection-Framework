from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.deps import require_permissions
from app.db.models import AuditLog, Notification, Permission, User
from app.db.session import get_db

router = APIRouter()


def _permission_set(db: Session, user: User) -> set[str]:
    if user.role.name == "Admin":
        return {"*"}
    return {row.action for row in db.query(Permission).filter(Permission.role_id == user.role_id).all()}


def _can_view(notification: Notification, user: User, permissions: set[str]) -> bool:
    if notification.organization_id and user.organization_id and notification.organization_id != user.organization_id:
        return False
    if notification.recipient_user_id and notification.recipient_user_id != user.id:
        return False
    return "*" in permissions or notification.required_permission in permissions


def _serialize(row: Notification) -> dict:
    return {
        "id": row.id,
        "channel": row.channel,
        "title": row.title,
        "message": row.message,
        "delivered": row.delivered,
        "severity": row.severity,
        "priority": row.priority,
        "status": row.status,
        "read_at": row.read_at,
        "archived_at": row.archived_at,
        "related_entity": row.related_entity,
        "related_id": row.related_id,
        "required_permission": row.required_permission,
        "metadata": row.metadata_json,
        "created_at": row.created_at,
    }


def _visible_query(db: Session, user: User):
    query = db.query(Notification)
    if user.organization_id:
        query = query.filter(or_(Notification.organization_id == user.organization_id, Notification.organization_id.is_(None)))
    else:
        query = query.filter(Notification.organization_id.is_(None))
    return query.filter(or_(Notification.recipient_user_id == user.id, Notification.recipient_user_id.is_(None)))


@router.get("")
def notifications(user: User = Depends(require_permissions("dashboard:read")), db: Session = Depends(get_db)) -> dict:
    permissions = _permission_set(db, user)
    rows = _visible_query(db, user).order_by(Notification.created_at.desc()).limit(100).all()
    data = [_serialize(row) for row in rows if _can_view(row, user, permissions)]
    return {"success": True, "data": data, "meta": {"count": len(data), "unread_count": sum(1 for item in data if item["status"] == "unread")}}


@router.get("/unread-count")
def unread_count(user: User = Depends(require_permissions("dashboard:read")), db: Session = Depends(get_db)) -> dict:
    permissions = _permission_set(db, user)
    rows = _visible_query(db, user).filter(Notification.status == "unread").all()
    count = sum(1 for row in rows if _can_view(row, user, permissions))
    return {"success": True, "data": {"unread_count": count}}


@router.put("/{notification_id}/read")
def mark_read(notification_id: int, request: Request, user: User = Depends(require_permissions("dashboard:read")), db: Session = Depends(get_db)) -> dict:
    row = db.get(Notification, notification_id)
    if not row or not _can_view(row, user, _permission_set(db, user)):
        raise HTTPException(status_code=404, detail="Notification not found")
    row.status = "read"
    row.read_at = datetime.now(timezone.utc)
    db.add(AuditLog(actor=user.email, action="notifications:read", entity="notifications", metadata_json={"notification_id": row.id}, ip_address=request.client.host if request.client else ""))
    db.commit()
    return {"success": True, "data": _serialize(row)}


@router.put("/{notification_id}/archive")
def archive(notification_id: int, request: Request, user: User = Depends(require_permissions("dashboard:read")), db: Session = Depends(get_db)) -> dict:
    row = db.get(Notification, notification_id)
    if not row or not _can_view(row, user, _permission_set(db, user)):
        raise HTTPException(status_code=404, detail="Notification not found")
    row.status = "archived"
    row.archived_at = datetime.now(timezone.utc)
    db.add(AuditLog(actor=user.email, action="notifications:archive", entity="notifications", metadata_json={"notification_id": row.id}, ip_address=request.client.host if request.client else ""))
    db.commit()
    return {"success": True, "data": _serialize(row)}


@router.post("/test")
def test_notification(payload: dict, user: User = Depends(require_permissions("dashboard:read"))) -> dict:
    return {"success": True, "data": {"channel": payload.get("channel", "browser"), "status": "queued", "recipient": user.email}}
