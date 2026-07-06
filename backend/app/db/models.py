from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Severity(str, Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"
    info = "info"


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    description: Mapped[str] = mapped_column(String(255), default="")
    permissions: Mapped[list["Permission"]] = relationship(back_populates="role", cascade="all, delete-orphan")


class Permission(Base):
    __tablename__ = "permissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"))
    action: Mapped[str] = mapped_column(String(120), index=True)
    role: Mapped[Role] = relationship(back_populates="permissions")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(160))
    password_hash: Mapped[str] = mapped_column(String(255))
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=True)
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    role: Mapped[Role] = relationship()


class SessionToken(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    refresh_token: Mapped[str] = mapped_column(Text)
    user_agent: Mapped[str] = mapped_column(String(255), default="")
    ip_address: Mapped[str] = mapped_column(String(64), default="")
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SecurityLog(Base):
    __tablename__ = "logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(120), index=True)
    log_type: Mapped[str] = mapped_column(String(80), index=True)
    message: Mapped[str] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(20), default=Severity.info.value, index=True)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    raw: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(180))
    severity: Mapped[str] = mapped_column(String(20), index=True)
    status: Mapped[str] = mapped_column(String(40), default="open", index=True)
    source: Mapped[str] = mapped_column(String(120), index=True)
    tactic: Mapped[str] = mapped_column(String(120), default="")
    technique: Mapped[str] = mapped_column(String(120), default="")
    confidence: Mapped[float] = mapped_column(Float, default=0.7)
    description: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class Detection(Base):
    __tablename__ = "detections"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160), index=True)
    category: Mapped[str] = mapped_column(String(100), index=True)
    severity: Mapped[str] = mapped_column(String(20))
    pattern: Mapped[str] = mapped_column(Text)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(180), index=True)
    severity: Mapped[str] = mapped_column(String(20), index=True)
    status: Mapped[str] = mapped_column(String(40), default="triage", index=True)
    assignee: Mapped[str] = mapped_column(String(160), default="Unassigned")
    evidence: Mapped[dict] = mapped_column(JSON, default=dict)
    timeline: Mapped[list[dict]] = mapped_column(JSON, default=list)
    resolution_notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class NetworkEvent(Base):
    __tablename__ = "network_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    src_ip: Mapped[str] = mapped_column(String(64), index=True)
    dst_ip: Mapped[str] = mapped_column(String(64), index=True)
    protocol: Mapped[str] = mapped_column(String(24), index=True)
    port: Mapped[int] = mapped_column(Integer, index=True)
    bytes_in: Mapped[int] = mapped_column(Integer, default=0)
    bytes_out: Mapped[int] = mapped_column(Integer, default=0)
    geo: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class MalwareReport(Base):
    __tablename__ = "malware_reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    file_name: Mapped[str] = mapped_column(String(255))
    md5: Mapped[str] = mapped_column(String(64), index=True)
    sha1: Mapped[str] = mapped_column(String(64), index=True)
    sha256: Mapped[str] = mapped_column(String(128), index=True)
    entropy: Mapped[float] = mapped_column(Float)
    verdict: Mapped[str] = mapped_column(String(80), index=True)
    yara_matches: Mapped[list[str]] = mapped_column(JSON, default=list)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class VulnerabilityReport(Base):
    __tablename__ = "vulnerability_reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    target: Mapped[str] = mapped_column(String(255), index=True)
    open_ports: Mapped[list[dict]] = mapped_column(JSON, default=list)
    cves: Mapped[list[dict]] = mapped_column(JSON, default=list)
    os_detection: Mapped[str] = mapped_column(String(120), default="Unknown")
    recommendations: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(180))
    report_type: Mapped[str] = mapped_column(String(80), index=True)
    format: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(40), default="ready")
    path: Mapped[str] = mapped_column(String(255), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    channel: Mapped[str] = mapped_column(String(60), index=True)
    title: Mapped[str] = mapped_column(String(180))
    message: Mapped[str] = mapped_column(Text)
    delivered: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    actor: Mapped[str] = mapped_column(String(160), index=True)
    action: Mapped[str] = mapped_column(String(120), index=True)
    entity: Mapped[str] = mapped_column(String(120), index=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    ip_address: Mapped[str] = mapped_column(String(64), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ApiKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[int] = mapped_column(primary_key=True)
    provider: Mapped[str] = mapped_column(String(80), index=True)
    key_hint: Mapped[str] = mapped_column(String(40))
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)


class SystemSetting(Base):
    __tablename__ = "system_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    value: Mapped[dict] = mapped_column(JSON, default=dict)

