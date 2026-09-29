"""A narrow, policy-gated rollback controller for an unhealthy local canary.

This service deliberately accepts no arbitrary command, Kubernetes credential, or
generic infrastructure action. It can only restore the stable ONNX target for the
current ``chat-default`` canary after independent approval and exact precondition
checks against Redis routing state and the durable release plan.
"""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Response
from inference_gateway.auth.admin import platform_admin, remediation_approver
from inference_gateway.auth.agent import AgentIdentity, delegated_agent, require_agent_scope
from inference_gateway.metering.redis_service import RedisMeter
from inference_gateway.observability.metrics import (
    REMEDIATION_ACTIONS,
    REMEDIATION_INCIDENTS,
    REMEDIATION_PLANS,
    REMEDIATION_VERIFICATIONS,
)
from inference_gateway.observability.tracing import configure_tracing
from inference_gateway.release.store import ReleaseStore
from inference_gateway.remediation.executor import CanaryRollbackExecutor
from inference_gateway.remediation.models import (
    IncidentRequest,
    IncidentState,
    RemediationIncident,
    RemediationPlan,
    TimelineEvent,
)
from inference_gateway.remediation.policy import evaluate
from inference_gateway.remediation.store import RemediationStore
from inference_gateway.routing.rollout_store import RolloutStore
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

MODEL = "chat-default"

app = FastAPI(title="Flagship Governed Remediation Control", version="0.1.0")
configure_tracing(app, "governed-remediation-control")
store = RemediationStore(os.getenv("REMEDIATION_DB_PATH", ".local/remediation/remediation.db"))
meter = RedisMeter(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
rollouts = RolloutStore(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
executor = CanaryRollbackExecutor(
    rollout_store=rollouts,
    release_store=ReleaseStore(os.getenv("RELEASE_DB_PATH", ".local/release/release.db")),
)


def _event(event: str, actor: str, **details: str) -> TimelineEvent:
    return TimelineEvent(event=event, actor=actor, details=details)


def _incident_response(incident: RemediationIncident) -> dict[str, object]:
    return {"incident": incident, "timeline": store.timeline(incident.id)}


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok", "store": Path(store.path).name, "scope": "canary-rollback-only"}


@app.get("/metrics")
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/remediation/v1/incidents")
async def create_incident(
    request: IncidentRequest, actor: str = Depends(platform_admin)
) -> dict[str, object]:
    existing = store.by_source_request(request.request_id)
    if existing:
        return _incident_response(existing)

    record = await meter.get_request(request.request_id)
    if (
        record is None
        or record.outcome == "success"
        or record.model != MODEL
        or not record.release_plan_id
        or record.release_phase != "CANARY"
    ):
        raise HTTPException(422, "request is not eligible for canary remediation")

    incident = RemediationIncident(
        source_request_id=request.request_id,
        tenant=record.tenant_id,
        model=record.model,
        backend=record.backend,
        deployment_version=record.deployment_version,
        release_plan_id=record.release_plan_id,
        release_phase=record.release_phase,
        outcome=record.outcome,
        slo_status="VIOLATED",
    )
    store.save_incident(incident)
    store.append(
        incident.id,
        _event(
            "INCIDENT_DETECTED",
            actor,
            request_id=request.request_id,
            outcome=record.outcome,
            release_plan_id=record.release_plan_id,
        ),
    )
    REMEDIATION_INCIDENTS.labels(model=incident.model, outcome=incident.outcome).inc()
    return _incident_response(incident)


@app.get("/remediation/v1/incidents")
def list_incidents(actor: str = Depends(platform_admin)) -> dict[str, object]:
    return {"incidents": store.list_incidents()}


@app.post("/remediation/v1/agent/incidents/{request_id}/plans")
async def agent_create_plan(
    request_id: str, agent: AgentIdentity = Depends(delegated_agent)
) -> RemediationPlan:
    """Allow a delegated agent to prepare—but never approve or execute—a rollback plan."""
    require_agent_scope(agent, "remediation.plan")
    incident = store.by_source_request(request_id)
    if incident is None:
        record = await meter.get_request(request_id)
        if (
            record is None
            or record.tenant_id != agent.tenant
            or record.outcome == "success"
            or record.model != MODEL
            or not record.release_plan_id
            or record.release_phase != "CANARY"
        ):
            raise HTTPException(422, "request is not eligible for delegated canary planning")
        incident = RemediationIncident(
            source_request_id=request_id,
            tenant=record.tenant_id,
            model=record.model,
            backend=record.backend,
            deployment_version=record.deployment_version,
            release_plan_id=record.release_plan_id,
            release_phase=record.release_phase,
            outcome=record.outcome,
            slo_status="VIOLATED",
        )
        store.save_incident(incident)
        store.append(
            incident.id,
            _event("AGENT_INCIDENT_DETECTED", agent.subject, request_id=request_id, delegator=agent.delegated_by),
        )
        REMEDIATION_INCIDENTS.labels(model=incident.model, outcome=incident.outcome).inc()
    if incident.tenant != agent.tenant:
        raise HTTPException(403, "cross-tenant remediation planning denied")
    if incident.state != IncidentState.DETECTED:
        raise HTTPException(409, "incident is not awaiting remediation planning")
    context = rollouts.get_context(incident.model)
    if (
        not context
        or context.get("release_plan_id") != incident.release_plan_id
        or context.get("release_phase") != "CANARY"
    ):
        raise HTTPException(409, "CANARY_CONTEXT_CHANGED")
    weights = context.get("weights")
    if not isinstance(weights, dict):
        raise HTTPException(409, "CANARY_CONTEXT_CHANGED")
    plan = RemediationPlan(
        incident_id=incident.id,
        requester=agent.subject,
        model=incident.model,
        release_plan_id=incident.release_plan_id,
        expected_weights=weights,
        plan_hash=store.plan_hash(incident=incident, weights=weights),
    )
    store.save_plan(plan)
    store.transition_incident(incident.id, IncidentState.PLAN_PENDING_APPROVAL)
    store.append(
        incident.id,
        _event("AGENT_PLAN_CREATED", agent.subject, plan_id=plan.id, delegator=agent.delegated_by),
    )
    REMEDIATION_PLANS.labels(action=plan.action, status=plan.status).inc()
    return plan


@app.get("/remediation/v1/incidents/{incident_id}")
def get_incident(incident_id: str, actor: str = Depends(platform_admin)) -> dict[str, object]:
    return _incident_response(store.get_incident(incident_id))


@app.post("/remediation/v1/incidents/{incident_id}/plans")
def create_plan(incident_id: str, actor: str = Depends(platform_admin)) -> RemediationPlan:
    incident = store.get_incident(incident_id)
    if incident.state != IncidentState.DETECTED:
        raise HTTPException(409, "incident is not awaiting remediation planning")
    context = rollouts.get_context(incident.model)
    if (
        not context
        or context.get("release_plan_id") != incident.release_plan_id
        or context.get("release_phase") != "CANARY"
    ):
        raise HTTPException(409, "CANARY_CONTEXT_CHANGED")
    weights = context.get("weights")
    if not isinstance(weights, dict):
        raise HTTPException(409, "CANARY_CONTEXT_CHANGED")
    plan = RemediationPlan(
        incident_id=incident.id,
        requester=actor,
        model=incident.model,
        release_plan_id=incident.release_plan_id,
        expected_weights=weights,
        plan_hash=store.plan_hash(incident=incident, weights=weights),
    )
    decision = evaluate(plan, approved=False)
    if decision.decision != "APPROVAL_REQUIRED":
        raise HTTPException(403, decision.reason)
    store.save_plan(plan)
    store.transition_incident(incident.id, IncidentState.PLAN_PENDING_APPROVAL)
    store.append(
        incident.id,
        _event("PLAN_CREATED", actor, plan_id=plan.id, plan_hash=plan.plan_hash, action=plan.action),
    )
    REMEDIATION_PLANS.labels(action=plan.action, status=plan.status).inc()
    return plan


@app.get("/remediation/v1/plans/{plan_id}")
def get_plan(plan_id: str, actor: str = Depends(platform_admin)) -> RemediationPlan:
    return store.get_plan(plan_id)


@app.post("/remediation/v1/plans/{plan_id}/approve")
def approve_plan(plan_id: str, approver: str = Depends(remediation_approver)) -> RemediationPlan:
    plan = store.get_plan(plan_id)
    if plan.status != "PENDING_APPROVAL":
        raise HTTPException(409, "remediation plan is not pending approval")
    if plan.requester == approver:
        raise HTTPException(403, "requester cannot approve its own remediation plan")
    plan.approved_by = approver
    plan.status = "APPROVED"
    store.save_plan(plan)
    store.transition_incident(plan.incident_id, IncidentState.APPROVED)
    store.append(plan.incident_id, _event("PLAN_APPROVED", approver, plan_id=plan.id))
    REMEDIATION_PLANS.labels(action=plan.action, status=plan.status).inc()
    return plan


@app.post("/remediation/v1/plans/{plan_id}/execute")
def execute_plan(plan_id: str, actor: str = Depends(platform_admin)) -> dict[str, object]:
    plan = store.get_plan(plan_id)
    decision = evaluate(plan, approved=plan.status == "APPROVED")
    if decision.decision != "ALLOW":
        raise HTTPException(403, decision.reason)
    if not executor.precondition(plan):
        REMEDIATION_ACTIONS.labels(model=plan.model, result="STALE_PLAN").inc()
        raise HTTPException(409, "STALE_REMEDIATION_PLAN")
    reserved, reason = store.reserve_action(
        plan.model,
        cooldown_seconds=int(os.getenv("REMEDIATION_COOLDOWN_SECONDS", "30")),
    )
    if not reserved:
        REMEDIATION_ACTIONS.labels(model=plan.model, result=reason).inc()
        raise HTTPException(429, reason)

    store.transition_incident(plan.incident_id, IncidentState.REMEDIATING)
    store.append(plan.incident_id, _event("REMEDIATION_STARTED", actor, plan_id=plan.id))
    executor.execute(plan)
    store.transition_incident(plan.incident_id, IncidentState.VERIFYING)
    verified = executor.verify(plan)
    if not verified:
        store.transition_incident(plan.incident_id, IncidentState.FAILED)
        store.append(plan.incident_id, _event("REMEDIATION_FAILED", actor, plan_id=plan.id))
        REMEDIATION_ACTIONS.labels(model=plan.model, result="VERIFICATION_FAILED").inc()
        REMEDIATION_VERIFICATIONS.labels(model=plan.model, status="FAILED").inc()
        raise HTTPException(502, "remediation verification failed")

    plan.status = "EXECUTED"
    store.save_plan(plan)
    incident = store.transition_incident(plan.incident_id, IncidentState.RESOLVED)
    store.append(plan.incident_id, _event("REMEDIATION_VERIFIED", actor, plan_id=plan.id))
    REMEDIATION_ACTIONS.labels(model=plan.model, result="ROLLED_BACK").inc()
    REMEDIATION_VERIFICATIONS.labels(model=plan.model, status="VERIFIED").inc()
    return {"incident": incident, "plan": plan, "verified": True}


@app.get("/remediation/v1/incidents/{incident_id}/timeline")
def timeline(incident_id: str, actor: str = Depends(platform_admin)) -> list[TimelineEvent]:
    store.get_incident(incident_id)
    return store.timeline(incident_id)
