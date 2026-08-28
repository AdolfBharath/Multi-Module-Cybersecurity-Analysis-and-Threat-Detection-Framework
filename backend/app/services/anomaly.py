from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import IsolationForest

MODEL_DIR = Path("models")
MODEL_PATH = MODEL_DIR / "isolation_forest.joblib"
FEATURES = ["failed_logins", "data_volume_mb", "distinct_ips", "off_hours_events", "privileged_actions"]


def _vectorize(rows: list[dict]) -> np.ndarray:
    if not rows:
        rows = [
            {"failed_logins": 1, "data_volume_mb": 40, "distinct_ips": 1, "off_hours_events": 0, "privileged_actions": 1},
            {"failed_logins": 2, "data_volume_mb": 55, "distinct_ips": 1, "off_hours_events": 1, "privileged_actions": 1},
            {"failed_logins": 12, "data_volume_mb": 900, "distinct_ips": 5, "off_hours_events": 8, "privileged_actions": 6},
        ]
    return np.array([[float(row.get(feature, 0)) for feature in FEATURES] for row in rows], dtype=float)


def train_model(samples: list[dict]) -> dict:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    matrix = _vectorize(samples)
    contamination = 0.15 if len(matrix) > 8 else 0.25
    model = IsolationForest(n_estimators=100, contamination=contamination, random_state=42)
    model.fit(matrix)
    joblib.dump(model, MODEL_PATH)
    return {"model": "IsolationForest", "samples": int(len(matrix)), "features": FEATURES, "path": str(MODEL_PATH)}


def predict_anomaly(events: list[dict]) -> dict:
    if not MODEL_PATH.exists():
        train_model([])
    model = joblib.load(MODEL_PATH)
    matrix = _vectorize(events)
    decisions = model.decision_function(matrix)
    predictions = model.predict(matrix)
    results = []
    for index, decision in enumerate(decisions):
        risk_score = round(float(max(0, min(100, (0.5 - decision) * 140))), 2)
        results.append({"index": index, "is_anomaly": bool(predictions[index] == -1), "risk_score": risk_score, "decision_score": round(float(decision), 4)})
    return {"model": "IsolationForest", "features": FEATURES, "results": results, "max_risk": max((item["risk_score"] for item in results), default=0)}
