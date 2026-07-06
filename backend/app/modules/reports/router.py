from fastapi import APIRouter

router = APIRouter()


@router.get("")
def reports() -> dict:
    return {"success": True, "data": [{"id": 1, "name": "Executive SOC Summary", "report_type": "executive", "format": "pdf", "status": "ready"}, {"id": 2, "name": "Technical Detection Export", "report_type": "technical", "format": "xlsx", "status": "ready"}]}


@router.post("/generate")
def generate(payload: dict) -> dict:
    return {"success": True, "data": {"name": payload.get("name", "SOC Report"), "format": payload.get("format", "pdf"), "status": "queued"}}

