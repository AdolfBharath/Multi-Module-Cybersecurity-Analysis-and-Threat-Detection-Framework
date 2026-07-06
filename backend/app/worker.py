from celery import Celery

from app.core.config import settings

celery_app = Celery("cybershield", broker=settings.REDIS_URL, backend=settings.REDIS_URL)


@celery_app.task(name="cybershield.generate_report")
def generate_report(report_id: int) -> dict:
    return {"report_id": report_id, "status": "ready"}


@celery_app.task(name="cybershield.enrich_indicator")
def enrich_indicator(indicator: str) -> dict:
    return {"indicator": indicator, "status": "enriched"}

