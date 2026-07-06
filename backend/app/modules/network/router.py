from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.models import NetworkEvent
from app.db.session import get_db

router = APIRouter()


@router.get("")
def network_events(db: Session = Depends(get_db)) -> dict:
    rows = db.query(NetworkEvent).order_by(NetworkEvent.created_at.desc()).limit(100).all()
    return {"success": True, "data": [{"id": row.id, "src_ip": row.src_ip, "dst_ip": row.dst_ip, "protocol": row.protocol, "port": row.port, "bytes_in": row.bytes_in, "bytes_out": row.bytes_out, "geo": row.geo, "created_at": row.created_at} for row in rows]}


@router.get("/stats")
def stats() -> dict:
    return {"success": True, "data": {"bandwidth": 824, "connections": 1288, "protocols": [{"name": "HTTPS", "value": 62}, {"name": "DNS", "value": 18}, {"name": "SSH", "value": 9}, {"name": "Other", "value": 11}], "ports": [443, 53, 22, 3389, 8080]}}

