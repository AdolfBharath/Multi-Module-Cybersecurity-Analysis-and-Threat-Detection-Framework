from app.services.jenovate_lms import normalize_event


def test_jenovate_event_normalization_removes_evaluation_label() -> None:
    event = {"event_id":"EVT-1","timestamp":"2026-10-01T09:00:00+00:00","source":"jenovate_lms","event_type":"failed_login","actor_id":"USR-1","actor_role":"student","target_type":"course","target_id":"CRS-001","action":"failed login attempt","outcome":"denied","severity":"medium","metadata":{"dataset":"jenovate_lms"},"ground_truth":"suspicious"}
    item = normalize_event(event)
    assert item["log_type"] == "failed_login"
    assert item["raw"]["event_id"] == "EVT-1"
    assert "ground_truth" not in item["raw"]


def test_jenovate_event_rejects_missing_fields() -> None:
    try:
        normalize_event({"event_id":"EVT-1"})
    except ValueError as exc:
        assert "missing event fields" in str(exc)
    else:
        raise AssertionError("invalid event was accepted")
