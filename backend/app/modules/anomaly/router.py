from fastapi import APIRouter, Depends

from app.core.deps import require_permissions
from app.schemas.modules import TrainingRequest
from app.services.anomaly import predict_anomaly, train_model

router = APIRouter(dependencies=[Depends(require_permissions("alerts:read"))])


@router.get("")
def anomalies() -> dict:
    data = [
        {"id": 1, "title": "Unusual outbound data volume", "severity": "high", "status": "investigate", "description": "Isolation Forest score 0.94 for workstation FIN-22", "metadata": {"risk_score": 94, "model": "IsolationForest"}},
        {"id": 2, "title": "Rare admin login hour", "severity": "medium", "status": "watch", "description": "Behavior baseline deviation for privileged account", "metadata": {"risk_score": 71, "model": "LOF"}},
    ]
    return {"success": True, "data": data}


@router.post("/predict")
def predict(payload: dict) -> dict:
    return {"success": True, "data": predict_anomaly(payload.get("events", []))}


@router.post("/train")
def train(payload: TrainingRequest) -> dict:
    return {"success": True, "data": train_model(payload.samples)}
