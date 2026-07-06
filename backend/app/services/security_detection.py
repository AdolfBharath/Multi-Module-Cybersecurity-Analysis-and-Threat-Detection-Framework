import re


SIGNATURES: list[dict[str, str]] = [
    {"name": "SQL Injection", "severity": "critical", "pattern": r"(?i)(union\s+select|or\s+1=1|sleep\(|drop\s+table)"},
    {"name": "Cross-Site Scripting", "severity": "high", "pattern": r"(?i)(<script|javascript:|onerror=)"},
    {"name": "Directory Traversal", "severity": "high", "pattern": r"(\.\./|\.\.\\|/etc/passwd|boot\.ini)"},
    {"name": "PowerShell Abuse", "severity": "high", "pattern": r"(?i)(powershell.+-enc|invoke-expression|downloadstring)"},
    {"name": "Reverse Shell", "severity": "critical", "pattern": r"(?i)(/bin/sh|nc\s+-e|bash\s+-i|socket\.connect)"},
    {"name": "Port Scan", "severity": "medium", "pattern": r"(?i)(nmap|masscan|syn scan|port scan)"},
    {"name": "Ransomware Indicator", "severity": "critical", "pattern": r"(?i)(vssadmin delete shadows|bcdedit /set|\.locked|ransom)"},
    {"name": "DNS Tunneling", "severity": "medium", "pattern": r"(?i)(base64|long-subdomain|dnscat|iodine)"},
]


def analyze_text(text: str, source: str = "manual") -> dict:
    alerts: list[dict] = []
    for signature in SIGNATURES:
        if re.search(signature["pattern"], text):
            alerts.append(
                {
                    "title": signature["name"],
                    "severity": signature["severity"],
                    "source": source,
                    "confidence": 0.92 if signature["severity"] == "critical" else 0.78,
                    "description": f"Detected {signature['name']} indicators in submitted telemetry.",
                }
            )
    severity_weight = {"critical": 1.0, "high": 0.78, "medium": 0.52, "low": 0.25}
    risk_score = min(100.0, sum(severity_weight.get(item["severity"], 0.2) * 35 for item in alerts))
    return {
        "matched": bool(alerts),
        "alerts": alerts,
        "risk_score": round(risk_score, 2),
        "recommendations": [
            "Isolate affected host when critical indicators are present.",
            "Preserve logs and memory artifacts for incident response.",
            "Correlate source IP, user identity, and process lineage.",
        ],
    }

