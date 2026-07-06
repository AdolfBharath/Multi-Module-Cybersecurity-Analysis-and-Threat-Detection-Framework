from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.models import Alert
from app.db.session import get_db
from app.schemas.modules import DetectionRequest, DetectionResult
from app.services.security_detection import SIGNATURES, analyze_text

router = APIRouter()


@router.get("/rules")
def rules() -> dict:
    return {"success": True, "data": SIGNATURES}


@router.post("/analyze", response_model=DetectionResult)
def analyze(payload: DetectionRequest, db: Session = Depends(get_db)) -> DetectionResult:
    result = analyze_text(payload.text, payload.source)
    for alert in result["alerts"]:
        db.add(Alert(**alert, status="open", tactic="Detection", technique=alert["title"]))
    db.commit()
    return DetectionResult(**result)

