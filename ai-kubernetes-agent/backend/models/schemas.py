"""Pydantic models for the AI Kubernetes Agent."""

from datetime import datetime

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    service: str


class PodInfo(BaseModel):
    name: str
    namespace: str
    status: str
    ready: str
    restarts: int
    age: str


class NodeInfo(BaseModel):
    name: str
    status: str
    roles: str
    age: str
    version: str


class EventInfo(BaseModel):
    name: str
    namespace: str
    type: str
    reason: str
    message: str
    age: str


class InvestigationRequest(BaseModel):
    namespace: str | None = None
    context: str | None = None


class Issue(BaseModel):
    severity: str
    component: str
    description: str
    suggestion: str


class DiagnosisResponse(BaseModel):
    issues: list[Issue]
    root_cause: str
    suggested_fixes: list[str]
    timestamp: datetime = datetime.utcnow()


class AIDiagnosis(BaseModel):
    root_cause: str
    explanation: str
    fix: str
    kubectl_commands: list[str]
    prevention: str
    confidence: int


class InvestigationResponse(BaseModel):
    status: str
    investigation: dict
    diagnosis: AIDiagnosis | None = None
