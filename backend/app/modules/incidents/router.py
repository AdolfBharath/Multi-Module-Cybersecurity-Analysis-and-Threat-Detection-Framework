from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import require_permissions
from app.db.models import AuditLog, Incident, User
from app.db.session import get_db
from app.schemas.modules import IncidentCreate, IncidentRead

router = APIRouter(dependencies=[Depends(require_permissions("incidents:read"))])


@router.get("", response_model=list[IncidentRead])
def list_incidents(db: Session = Depends(get_db), user: User = Depends(require_permissions("incidents:read"))) -> list[Incident]:
    return db.query(Incident).filter(Incident.organization_id == user.organization_id).order_by(Incident.created_at.desc()).all()


@router.post("", response_model=IncidentRead)
def create_incident(payload: IncidentCreate, db: Session = Depends(get_db), user: User = Depends(require_permissions("incidents:create"))) -> Incident:
    incident = Incident(**payload.model_dump(), organization_id=user.organization_id, timeline=[{"event": "Incident created", "actor": user.email}])
    db.add(incident)
    db.add(AuditLog(actor="api", action="create", entity="incidents", metadata_json={"title": payload.title}))
    db.commit()
    db.refresh(incident)
    return incident
