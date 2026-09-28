from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, Field


class IncidentState(StrEnum):
    DETECTED = "DETECTED"
    PLAN_PENDING_APPROVAL = "PLAN_PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REMEDIATING = "REMEDIATING"
    VERIFYING = "VERIFYING"
    RESOLVED = "RESOLVED"
    FAILED = "FAILED"


class RemediationAction(StrEnum):
    ROLLBACK_CANARY_TO_STABLE = "ROLLBACK_CANARY_TO_STABLE"


class RemediationIncident(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    source_request_id: str
    tenant: str
    model: str
    backend: str
    deployment_version: str
    release_plan_id: str
    release_phase: str
    outcome: str
    slo_status: str
    state: IncidentState = IncidentState.DETECTED
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class RemediationPlan(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    incident_id: str
    requester: str
    action: RemediationAction = RemediationAction.ROLLBACK_CANARY_TO_STABLE
    model: str
    release_plan_id: str
    expected_release_phase: str = "CANARY"
    expected_weights: dict[str, int]
    plan_hash: str
    status: str = "PENDING_APPROVAL"
    approved_by: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class IncidentRequest(BaseModel):
    request_id: str


class TimelineEvent(BaseModel):
    event: str
    actor: str
    details: dict[str, str] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
