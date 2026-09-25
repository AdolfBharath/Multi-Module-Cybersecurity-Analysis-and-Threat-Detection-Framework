import asyncio
import random
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from jose import JWTError

from app.core.security import decode_token
from app.db.models import Permission, RevokedToken, User
from app.db.session import SessionLocal

router = APIRouter()


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
        permissions = {row.action for row in db.query(Permission).filter(Permission.role_id == user.role_id).all()}
        if user.role.name != "Admin" and "alerts:read" not in permissions:
            await websocket.close(code=1008)
            return
    finally:
        db.close()
    await websocket.accept()
    try:
        while True:
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
