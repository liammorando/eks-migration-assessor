from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class Severity(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class Category(StrEnum):
    STATE = "state"
    CONFIG = "config"
    NETWORKING = "networking"
    CONTAINER = "container"
    LOGGING = "logging"
    LIFECYCLE = "lifecycle"
    STORAGE = "storage"
    SECURITY = "security"


class Finding(BaseModel):
    id: str
    category: Category
    severity: Severity
    title: str
    description: str
    file: str | None = None
    line: int | None = None
    evidence: str | None = None
    remediation: str
    eks_hint: str | None = None


class PlanStep(BaseModel):
    phase: int
    title: str
    why: str
    actions: list[str]
    finding_ids: list[str]
    effort: str  # S, M, L


class AssessmentResult(BaseModel):
    repo_url: str
    scanned_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    files_scanned: int
    findings: list[Finding] = Field(default_factory=list)
    score: int = 0
    readiness: str = ""
    summary: str | None = None
    plan: list[PlanStep] = Field(default_factory=list)
    stored_at: list[str] = Field(default_factory=list)
