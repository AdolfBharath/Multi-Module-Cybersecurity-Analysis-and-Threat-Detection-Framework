from fastapi import APIRouter

router = APIRouter()


@router.get("/lookup")
def lookup(indicator: str, indicator_type: str = "ip") -> dict:
    reputation = "malicious" if indicator.endswith(".13") or "evil" in indicator else "unknown"
    return {
        "success": True,
        "data": {
            "indicator": indicator,
            "type": indicator_type,
            "reputation": reputation,
            "sources": ["VirusTotal-ready", "AbuseIPDB-ready", "AlienVault OTX-ready"],
            "mitre": [{"tactic": "Command and Control", "technique": "T1071 Application Layer Protocol"}],
            "confidence": 84 if reputation == "malicious" else 41,
        },
    }

