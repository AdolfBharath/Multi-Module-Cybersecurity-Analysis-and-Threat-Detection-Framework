import asyncio
import random
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


@router.websocket("/live")
async def live(websocket: WebSocket) -> None:
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

