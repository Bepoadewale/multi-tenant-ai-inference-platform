from __future__ import annotations

from dataclasses import replace

import pytest
from fastapi import HTTPException
from inference_gateway.release.store import ReleasePlan
from inference_gateway.remediation.executor import CanaryRollbackExecutor
from inference_gateway.remediation.models import RemediationIncident, RemediationPlan, TimelineEvent
from inference_gateway.remediation.policy import evaluate
from inference_gateway.remediation.store import RemediationStore


def _incident() -> RemediationIncident:
    return RemediationIncident(
        source_request_id="request-1",
        tenant="team-search",
        model="chat-default",
        backend="onnx-candidate-v2",
        deployment_version="v2",
        release_plan_id="release-1",
        release_phase="CANARY",
        outcome="backend_error",
        slo_status="VIOLATED",
    )


def _plan(incident: RemediationIncident, weights: dict[str, int]) -> RemediationPlan:
    return RemediationPlan(
        incident_id=incident.id,
        requester="platform-admin",
        model=incident.model,
        release_plan_id=incident.release_plan_id,
        expected_weights=weights,
        plan_hash="bound-plan-hash",
    )


def test_store_is_durable_and_enforces_a_bounded_action_budget(tmp_path):
    path = tmp_path / "remediation.db"
    incident = _incident()
    store = RemediationStore(path)
    store.save_incident(incident)
    event = TimelineEvent(event="INCIDENT_DETECTED", actor="admin")
    store.append(incident.id, event)

    recovered = RemediationStore(path)
    assert recovered.get_incident(incident.id).source_request_id == "request-1"
    assert recovered.timeline(incident.id) == [event]

    assert recovered.reserve_action("chat-default", cooldown_seconds=0, max_actions=2) == (True, "RESERVED")
    assert recovered.reserve_action("chat-default", cooldown_seconds=0, max_actions=2) == (True, "RESERVED")
    assert recovered.reserve_action("chat-default", cooldown_seconds=0, max_actions=2) == (
        False,
        "REMEDIATION_ACTION_BUDGET_EXHAUSTED",
    )


def test_policy_requires_independent_approval_and_a_canary_plan():
    incident = _incident()
    plan = _plan(incident, {"onnx-stable-v1": 1, "onnx-candidate-v2": 99})
    assert evaluate(plan, approved=False).decision == "APPROVAL_REQUIRED"
    assert evaluate(plan, approved=True).decision == "ALLOW"
    assert evaluate(plan.model_copy(update={"expected_release_phase": "PROMOTED"}), approved=True).decision == "DENY"


class _Rollouts:
    def __init__(self):
        self.context = {
            "weights": {"onnx-stable-v1": 1, "onnx-candidate-v2": 99},
            "release_plan_id": "release-1",
            "release_phase": "CANARY",
        }

    def get_context(self, alias):
        return self.context

    def put(self, alias, weights, *, release_plan_id, release_phase):
        self.context = {
            "weights": weights,
            "release_plan_id": release_plan_id,
            "release_phase": release_phase,
        }


class _Releases:
    def __init__(self):
        self.plan = ReleasePlan(
            id="release-1",
            alias="chat-default",
            requester="platform-admin",
            champion_version="1",
            candidate_version="2",
            candidate_digest="digest",
            canary_weight=99,
            plan_hash="release-hash",
            status="CANARY",
            approved_by="release-approver",
            created_at="2026-01-01T00:00:00Z",
        )

    def get(self, plan_id):
        assert plan_id == self.plan.id
        return self.plan

    def transition(self, plan_id, expected, target):
        if self.plan.status != expected:
            raise HTTPException(409, "STALE_PLAN")
        self.plan = replace(self.plan, status=target)
        return self.plan


def test_executor_rechecks_rollout_and_release_preconditions_before_a_bounded_rollback():
    incident = _incident()
    rollouts, releases = _Rollouts(), _Releases()
    executor = CanaryRollbackExecutor(rollouts, releases)
    plan = _plan(incident, rollouts.context["weights"])

    assert executor.precondition(plan)
    assert executor.execute(plan) == {"onnx-stable-v1": 100, "onnx-candidate-v2": 0}
    assert executor.verify(plan)

    stale = _plan(incident, {"onnx-stable-v1": 10, "onnx-candidate-v2": 90})
    with pytest.raises(HTTPException, match="STALE_REMEDIATION_PLAN"):
        executor.execute(stale)
