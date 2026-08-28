from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import require_permissions
from app.db.session import get_db
from app.schemas.modules import DashboardMetrics
from app.services.dashboard import get_dashboard_metrics

router = APIRouter(dependencies=[Depends(require_permissions("dashboard:read"))])


@router.get("", response_model=DashboardMetrics)
def dashboard(db: Session = Depends(get_db)) -> DashboardMetrics:
    return DashboardMetrics(**get_dashboard_metrics(db))
