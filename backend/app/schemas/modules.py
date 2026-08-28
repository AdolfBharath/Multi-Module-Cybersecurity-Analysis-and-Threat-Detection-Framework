from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DashboardMetrics(BaseModel):
    total_logs: int
    critical_alerts: int
    incidents: int
    high_threats: int
    medium_threats: int
    low_threats: int
    network_status: str
    cpu: float
    memory: float
    disk: float
    todays_attacks: int
    weekly_trend: list[dict]
    monthly_trend: list[dict]
    attack_timeline: list[dict]
    alert_timeline: list[dict]
    recent_activity: list[dict]
    live_feed: list[dict]
    threat_map: list[dict]
    top_attack_sources: list[dict]
    mitre_matrix: list[dict]


class LogCreate(BaseModel):
    source: str
    log_type: str
    message: str
    severity: str = "info"
    tags: list[str] = Field(default_factory=list)
    raw: dict = Field(default_factory=dict)


class LogRead(LogCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class AlertRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    severity: str
    status: str
    source: str
    tactic: str
    technique: str
    confidence: float
    description: str
    created_at: datetime


class IncidentCreate(BaseModel):
    title: str
    severity: str
    status: str = "triage"
    assignee: str = "Unassigned"
    evidence: dict = Field(default_factory=dict)


class IncidentRead(IncidentCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    timeline: list[dict]
    resolution_notes: str
    created_at: datetime


class ModuleRecord(BaseModel):
    id: int
    title: str
    severity: str = "medium"
    status: str = "active"
    description: str
    metadata: dict = Field(default_factory=dict)
    created_at: datetime

class DetectionRequest(BaseModel):
    text: str
    source: str = "manual"


class DetectionResult(BaseModel):
    matched: bool
    alerts: list[dict]
    risk_score: float
    recommendations: list[str]


class RuleCreate(BaseModel):
    name: str
    category: str
    severity: str
    pattern: str
    enabled: bool = True


class SuppressionCreate(BaseModel):
    signature_name: str
    source: str
    reason: str = ""


class ReportGenerateRequest(BaseModel):
    name: str = "SOC Report"
    report_type: str = "executive"
    format: str = "pdf"


class ScanRequest(BaseModel):
    target: str = "127.0.0.1"
    scan_type: str = "nmap"
    execute: bool = False


class ScheduleRequest(BaseModel):
    target: str
    cadence: str = "weekly"
    scan_type: str = "nmap"


class IntelLookupRequest(BaseModel):
    indicator: str
    indicator_type: str = "ip"
    watch: bool = False


class TrainingRequest(BaseModel):
    samples: list[dict] = Field(default_factory=list)
