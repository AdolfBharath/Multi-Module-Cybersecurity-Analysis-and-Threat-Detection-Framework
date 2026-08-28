import psutil
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import require_permissions
from app.db.models import NetworkEvent
from app.db.session import get_db

router = APIRouter(dependencies=[Depends(require_permissions("dashboard:read"))])


@router.get("")
def network_events(db: Session = Depends(get_db)) -> dict:
    rows = db.query(NetworkEvent).order_by(NetworkEvent.created_at.desc()).limit(100).all()
    return {"success": True, "data": [{"id": row.id, "src_ip": row.src_ip, "dst_ip": row.dst_ip, "protocol": row.protocol, "port": row.port, "bytes_in": row.bytes_in, "bytes_out": row.bytes_out, "geo": row.geo, "created_at": row.created_at} for row in rows]}


@router.get("/stats")
def stats() -> dict:
    counters = psutil.net_io_counters()
    connections = psutil.net_connections(kind="inet")
    ports = sorted({conn.laddr.port for conn in connections if conn.laddr})[:10]
    return {"success": True, "data": {"bandwidth": counters.bytes_sent + counters.bytes_recv, "connections": len(connections), "protocols": [{"name": "TCP/UDP", "value": len(connections)}], "ports": ports}}


@router.get("/connections")
def connections() -> dict:
    rows = []
    for conn in psutil.net_connections(kind="inet")[:100]:
        rows.append(
            {
                "fd": conn.fd,
                "family": str(conn.family),
                "type": str(conn.type),
                "local": f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "",
                "remote": f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "",
                "status": conn.status,
                "pid": conn.pid,
            }
        )
    return {"success": True, "data": rows}
