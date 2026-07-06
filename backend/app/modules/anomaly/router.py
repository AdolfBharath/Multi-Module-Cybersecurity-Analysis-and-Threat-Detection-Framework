from fastapi import APIRouter

router = APIRouter()


@router.get("")
def anomalies() -> dict:
    data = [
        {"id": 1, "title": "Unusual outbound data volume", "severity": "high", "status": "investigate", "description": "Isolation Forest score 0.94 for workstation FIN-22", "metadata": {"risk_score": 94, "model": "IsolationForest"}},
        {"id": 2, "title": "Rare admin login hour", "severity": "medium", "status": "watch", "description": "Behavior baseline deviation for privileged account", "metadata": {"risk_score": 71, "model": "LOF"}},
    ]
    return {"success": True, "data": data}


@router.post("/predict")
def predict(payload: dict) -> dict:
    events = payload.get("events", [])
    score = min(100, 45 + len(events) * 8)
    return {"success": True, "data": {"risk_score": score, "is_anomaly": score > 70, "model": "IsolationForest"}}

