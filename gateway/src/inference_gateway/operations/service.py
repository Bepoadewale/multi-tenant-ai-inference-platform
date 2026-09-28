"""Release-aware, privacy-safe operational analysis for a completed request.

This is intentionally a small local control-plane read model.  It consumes only
metadata already captured by metering: never prompts, completions, credentials,
or physical-GPU billing data.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from inference_gateway.models import UsageRecord

MILLION = Decimal("1000000")
PRICING_VERSION = "local-fixture-2026-09-v1"
PROMPT_USD_PER_MILLION = Decimal("0.20")
COMPLETION_USD_PER_MILLION = Decimal("0.80")
LATENCY_SLO_MS = 750.0
TTFT_SLO_MS = 600.0


def _money(value: Decimal) -> str:
    return format(value.quantize(Decimal("0.00000001"), rounding=ROUND_HALF_UP), "f")


def estimate_cost(record: UsageRecord) -> dict[str, str]:
    """Use Decimal arithmetic for explicit local token-cost estimates."""
    prompt = Decimal(record.usage.prompt_tokens) / MILLION * PROMPT_USD_PER_MILLION
    completion = Decimal(record.usage.completion_tokens) / MILLION * COMPLETION_USD_PER_MILLION
    return {
        "currency": "USD",
        "pricing_version": PRICING_VERSION,
        "kind": "ESTIMATED_LOCAL_TOKEN_ALLOCATION",
        "prompt_cost_usd": _money(prompt),
        "completion_cost_usd": _money(completion),
        "total_cost_usd": _money(prompt + completion),
        "note": "Fixture token prices for local capacity analysis; not an invoice or cloud-provider bill.",
    }


def evaluate_slo(record: UsageRecord) -> dict[str, object]:
    """Evaluate a deliberately local, request-level latency/availability SLO."""
    reasons: list[str] = []
    if record.outcome != "success":
        reasons.append(f"outcome={record.outcome}")
    if record.latency_ms > LATENCY_SLO_MS:
        reasons.append("latency threshold exceeded")
    if record.ttft_ms is not None and record.ttft_ms > TTFT_SLO_MS:
        reasons.append("TTFT threshold exceeded")
    status = "SATISFIED" if not reasons else "VIOLATED"
    recommendation = (
        "No request-level action recommended. Continue observing the release."
        if status == "SATISFIED"
        else "Inspect the correlated trace and release state before changing routing or promoting a candidate."
    )
    return {
        "status": status,
        "availability_target": "successful request",
        "latency_threshold_ms": LATENCY_SLO_MS,
        "ttft_threshold_ms": TTFT_SLO_MS,
        "latency_ms": round(record.latency_ms, 3),
        "ttft_ms": round(record.ttft_ms, 3) if record.ttft_ms is not None else None,
        "error_budget_impact": "0" if status == "SATISFIED" else "1 failed local request",
        "reasons": reasons,
        "recommendation": recommendation,
        "scope": "Local fixture request SLO, not a production SLO commitment.",
    }


def analyse(record: UsageRecord) -> dict[str, object]:
    """Return one privacy-safe link between serving, release, SLO, trace and cost."""
    return {
        "request_id": str(record.request_id),
        "trace_id": record.trace_id,
        "tenant": record.tenant_id,
        "model": record.model,
        "deployment": {"backend": record.backend, "version": record.deployment_version},
        "release": {
            "plan_id": record.release_plan_id,
            "phase_at_request": record.release_phase,
        },
        "usage": record.usage.model_dump(),
        "streaming": record.streaming,
        "outcome": record.outcome,
        "cost": estimate_cost(record),
        "slo": evaluate_slo(record),
        "privacy": {
            "raw_prompt_stored": False,
            "raw_completion_stored": False,
            "record_type": "metadata-only",
        },
    }
