from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.models import AuditLog, Incident
from app.db.session import get_db
from app.schemas.modules import IncidentCreate, IncidentRead

router = APIRouter()


@router.get("", response_model=list[IncidentRead])
def list_incidents(db: Session = Depends(get_db)) -> list[Incident]:
    return db.query(Incident).order_by(Incident.created_at.desc()).all()


@router.post("", response_model=IncidentRead)
def create_incident(payload: IncidentCreate, db: Session = Depends(get_db)) -> Incident:
    incident = Incident(**payload.model_dump(), timeline=[{"event": "Incident created", "actor": "api"}])
    db.add(incident)
    db.add(AuditLog(actor="api", action="create", entity="incidents", metadata_json={"title": payload.title}))
    db.commit()
    db.refresh(incident)
    return incident

