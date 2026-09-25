import asyncio
import random
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from jose import JWTError
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.models import Notification, Permission, RevokedToken, User
from app.db.session import SessionLocal

router = APIRouter()


def _permission_set(db: Session, user: User) -> set[str]:
    if user.role.name == "Admin":
        return {"*"}
    return {row.action for row in db.query(Permission).filter(Permission.role_id == user.role_id).all()}


def _can_view_notification(notification: Notification, user: User, permissions: set[str]) -> bool:
    if notification.organization_id and user.organization_id and notification.organization_id != user.organization_id:
        return False
    if notification.recipient_user_id and notification.recipient_user_id != user.id:
        return False
    return "*" in permissions or notification.required_permission in permissions


def _notification_snapshot(db: Session, user: User, permissions: set[str]) -> dict:
    query = db.query(Notification)
    if user.organization_id:
        query = query.filter(or_(Notification.organization_id == user.organization_id, Notification.organization_id.is_(None)))
    else:
        query = query.filter(Notification.organization_id.is_(None))
    query = query.filter(or_(Notification.recipient_user_id == user.id, Notification.recipient_user_id.is_(None)))
    rows = [row for row in query.order_by(Notification.created_at.desc()).limit(25).all() if _can_view_notification(row, user, permissions)]
    return {
        "type": "notification_snapshot",
        "unread_count": sum(1 for row in rows if row.status == "unread"),
        "notifications": [
            {
                "id": row.id,
                "title": row.title,
                "severity": row.severity,
                "priority": row.priority,
                "status": row.status,
                "related_entity": row.related_entity,
                "related_id": row.related_id,
                "timestamp": row.created_at.isoformat() if row.created_at else None,
            }
            for row in rows[:5]
        ],
    }


@router.websocket("/live")
async def live(websocket: WebSocket) -> None:
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008)
        return
    db = SessionLocal()
    try:
        try:
            payload = decode_token(token)
        except (ValueError, JWTError):
            await websocket.close(code=1008)
            return
        if payload.get("type") != "access" or db.query(RevokedToken).filter(RevokedToken.jti == payload.get("jti")).first():
            await websocket.close(code=1008)
            return
        user = db.get(User, int(payload["sub"]))
        if not user or not user.is_active:
            await websocket.close(code=1008)
            return
        permissions = _permission_set(db, user)
        if "*" not in permissions and "dashboard:read" not in permissions:
            await websocket.close(code=1008)
            return
        user_id = user.id
        can_read_alerts = "*" in permissions or "alerts:read" in permissions
    finally:
        db.close()
    await websocket.accept()
    try:
        while True:
            db = SessionLocal()
            try:
                current_user = db.get(User, user_id)
                if not current_user or not current_user.is_active:
                    await websocket.close(code=1008)
                    return
                current_permissions = _permission_set(db, current_user)
                await websocket.send_json(_notification_snapshot(db, current_user, current_permissions))
            finally:
                db.close()
            if can_read_alerts:
                await websocket.send_json(
                    {
                        "type": "alert",
                        "title": random.choice(["Brute force burst", "Suspicious DNS beacon", "PowerShell encoded command", "New critical incident"]),
                        "severity": random.choice(["critical", "high", "medium", "low"]),
                        "source": random.choice(["firewall", "edr", "waf", "identity"]),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                )
            await asyncio.sleep(4)
    except WebSocketDisconnect:
        return
