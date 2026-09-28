"""Deterministic policy is the authority for the one local remediation capability."""

from __future__ import annotations

from dataclasses import dataclass

from inference_gateway.remediation.models import RemediationPlan


@dataclass(frozen=True)
class PolicyDecision:
    decision: str
    reason: str


def evaluate(plan: RemediationPlan, *, approved: bool) -> PolicyDecision:
    if plan.action.value != "ROLLBACK_CANARY_TO_STABLE":
        return PolicyDecision("DENY", "UNSUPPORTED_REMEDIATION_ACTION")
    if plan.expected_release_phase != "CANARY":
        return PolicyDecision("DENY", "UNSAFE_RELEASE_PHASE")
    if not approved:
        return PolicyDecision("APPROVAL_REQUIRED", "INDEPENDENT_APPROVAL_REQUIRED")
    return PolicyDecision("ALLOW", "ALLOW")
