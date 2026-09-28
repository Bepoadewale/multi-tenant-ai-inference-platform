"""The local executor can only roll an active canary back to a verified stable target."""

from __future__ import annotations

from fastapi import HTTPException

from inference_gateway.release.store import ReleaseStore
from inference_gateway.remediation.models import RemediationPlan
from inference_gateway.routing.rollout_store import RolloutStore


class CanaryRollbackExecutor:
    def __init__(self, rollout_store: RolloutStore, release_store: ReleaseStore) -> None:
        self.rollouts = rollout_store
        self.releases = release_store

    def precondition(self, plan: RemediationPlan) -> bool:
        context = self.rollouts.get_context(plan.model)
        if not context:
            return False
        return (
            context.get("release_plan_id") == plan.release_plan_id
            and context.get("release_phase") == plan.expected_release_phase
            and context.get("weights") == plan.expected_weights
            and self.releases.get(plan.release_plan_id).status == "CANARY"
        )

    def execute(self, plan: RemediationPlan) -> dict[str, int]:
        if not self.precondition(plan):
            raise HTTPException(409, "STALE_REMEDIATION_PLAN")
        release = self.releases.get(plan.release_plan_id)
        weights = {"onnx-stable-v1": 100, "onnx-candidate-v2": 0}
        self.rollouts.put(
            plan.model,
            weights,
            release_plan_id=release.id,
            release_phase="ROLLED_BACK_BY_REMEDIATION",
        )
        self.releases.transition(release.id, "CANARY", "ROLLED_BACK")
        return weights

    def verify(self, plan: RemediationPlan) -> bool:
        context = self.rollouts.get_context(plan.model)
        if not context:
            return False
        release = self.releases.get(plan.release_plan_id)
        return (
            context.get("weights") == {"onnx-stable-v1": 100, "onnx-candidate-v2": 0}
            and context.get("release_phase") == "ROLLED_BACK_BY_REMEDIATION"
            and release.status == "ROLLED_BACK"
        )
