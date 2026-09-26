import asyncio
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.models import RevokedToken, User
from app.db.session import SessionLocal
from app.modules.notifications.router import _permission_set, _unread_query, notifications

router = APIRouter()


def _notification_snapshot(db: Session, user: User, permissions: set[str]) -> dict:
    items = notifications(user=user, db=db)["data"]
    for row in items:
        for key, value in row.items():
            if isinstance(value, datetime):
                row[key] = value.isoformat()
    return {"type": "notification_snapshot", "unread_count": _unread_query(db, user).count(), "notifications": items}


@router.websocket("/live")
async def live(websocket: WebSocket) -> None:
    token = websocket.query_params.get("token")
    accepted = False
    try:
        while True:
            try:
                payload = decode_token(token or "")
                with SessionLocal() as db:
                    user = db.get(User, int(payload["sub"]))
                    if payload.get("type") != "access" or not user or not user.is_active or db.query(RevokedToken).filter(RevokedToken.jti == payload.get("jti")).first():
                        await websocket.close(code=1008)
                        return
                    permissions = _permission_set(db, user)
                    if "*" not in permissions and "dashboard:read" not in permissions:
                        await websocket.close(code=1008)
                        return
                    snapshot = _notification_snapshot(db, user, permissions)
            except (ValueError, KeyError, JWTError):
                await websocket.close(code=1008)
                return
            if not accepted:
                await websocket.accept()
                accepted = True
            await websocket.send_json(snapshot)
            try:
                message = await asyncio.wait_for(websocket.receive(), timeout=10)
                if message["type"] == "websocket.disconnect":
                    return
                # This is a server-push channel; client payloads are not accepted.
                await websocket.close(code=1008)
                return
            except asyncio.TimeoutError:
                pass
    except (WebSocketDisconnect, RuntimeError):
        return
