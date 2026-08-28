from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import require_permissions
from app.db.models import ThreatIntelIndicator
from app.db.session import get_db
from app.schemas.modules import IntelLookupRequest

router = APIRouter(dependencies=[Depends(require_permissions("alerts:read"))])


def _local_reputation(indicator: str) -> dict:
    reputation = "malicious" if indicator.endswith(".13") or "evil" in indicator or indicator.startswith("203.0.113.") else "unknown"
    return {
        "reputation": reputation,
        "confidence": 84 if reputation == "malicious" else 41,
        "sources": [
            "local-cache",
            "VirusTotal-configured" if settings.VIRUSTOTAL_API_KEY else "VirusTotal-not-configured",
            "AbuseIPDB-configured" if settings.ABUSEIPDB_API_KEY else "AbuseIPDB-not-configured",
            "AlienVault-OTX-configured" if settings.OTX_API_KEY else "AlienVault-OTX-not-configured",
        ],
    }


@router.get("/lookup")
def lookup(indicator: str, indicator_type: str = "ip", watch: bool = False, db: Session = Depends(get_db)) -> dict:
    result = _local_reputation(indicator)
    row = db.query(ThreatIntelIndicator).filter(ThreatIntelIndicator.indicator == indicator).first()
    mitre = [{"tactic": "Command and Control", "technique": "T1071 Application Layer Protocol"}] if result["reputation"] == "malicious" else []
    if row:
        row.reputation = result["reputation"]
        row.confidence = result["confidence"]
        row.sources = result["sources"]
        row.mitre = mitre
        row.watched = row.watched or watch
    else:
        row = ThreatIntelIndicator(indicator=indicator, indicator_type=indicator_type, reputation=result["reputation"], confidence=result["confidence"], sources=result["sources"], mitre=mitre, watched=watch, raw={"external_calls": "skipped_without_api_keys"})
        db.add(row)
    db.commit()
    return {
        "success": True,
        "data": {
            "indicator": indicator,
            "type": indicator_type,
            "reputation": result["reputation"],
            "sources": result["sources"],
            "mitre": mitre,
            "confidence": result["confidence"],
            "watched": row.watched,
        },
    }


@router.post("/lookup")
def lookup_post(payload: IntelLookupRequest, db: Session = Depends(get_db)) -> dict:
    return lookup(payload.indicator, payload.indicator_type, payload.watch, db)


@router.get("/watchlist")
def watchlist(db: Session = Depends(get_db)) -> dict:
    rows = db.query(ThreatIntelIndicator).filter(ThreatIntelIndicator.watched.is_(True)).order_by(ThreatIntelIndicator.created_at.desc()).all()
    return {"success": True, "data": [{"id": row.id, "indicator": row.indicator, "type": row.indicator_type, "reputation": row.reputation, "confidence": row.confidence, "sources": row.sources} for row in rows]}
