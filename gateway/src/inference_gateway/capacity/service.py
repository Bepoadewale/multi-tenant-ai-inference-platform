from __future__ import annotations

from collections import defaultdict

from fastapi import HTTPException

from inference_gateway.models import (
    CapacityAllocation,
    CapacityDecision,
    CapacityPolicy,
    ModelDefinition,
    Tenant,
)


class CapacityService:
    """Deterministic in-process fallback used by unit tests and non-Redis development."""

    def __init__(self, pool_slots: int = 2) -> None:
        self.pool_slots = pool_slots
        self.pool_allocated = 0
        self.tenant_allocated: dict[str, int] = defaultdict(int)

    async def admit(self, tenant: Tenant, model: ModelDefinition) -> CapacityAllocation:
        if model.capacity_policy == CapacityPolicy.CPU_ONLY or model.gpu_count == 0:
            return CapacityAllocation(decision=CapacityDecision.CPU_ONLY)
        if self.tenant_allocated[tenant.id] + model.gpu_count > tenant.quotas.simulated_gpu_slots:
            raise HTTPException(429, "simulated GPU tenant capacity quota exceeded")
        if self.pool_allocated + model.gpu_count > self.pool_slots:
            if model.capacity_policy == CapacityPolicy.ALLOW_CPU_FALLBACK:
                return CapacityAllocation(
                    decision=CapacityDecision.CPU_FALLBACK,
                    pool=model.gpu_type,
                    slots=model.gpu_count,
                    simulated_hardware=True,
                )
            raise HTTPException(429, "simulated GPU capacity exhausted", headers={"Retry-After": "1"})
        self.pool_allocated += model.gpu_count
        self.tenant_allocated[tenant.id] += model.gpu_count
        return CapacityAllocation(
            decision=CapacityDecision.SIMULATED_GPU_ADMITTED,
            pool=model.gpu_type,
            slots=model.gpu_count,
            simulated_hardware=True,
        )

    async def release(self, tenant: Tenant, allocation: CapacityAllocation) -> None:
        if allocation.decision != CapacityDecision.SIMULATED_GPU_ADMITTED:
            return
        self.pool_allocated = max(0, self.pool_allocated - allocation.slots)
        self.tenant_allocated[tenant.id] = max(
            0, self.tenant_allocated[tenant.id] - allocation.slots
        )

    async def snapshot(self) -> dict:
        return {
            "mode": "SIMULATED_HARDWARE_QUOTA_ACCOUNTING",
            "pools": [
                {
                    "name": "simulated-l40s",
                    "total_slots": self.pool_slots,
                    "allocated_slots": self.pool_allocated,
                    "available_slots": self.pool_slots - self.pool_allocated,
                }
            ],
            "tenant_allocations": dict(self.tenant_allocated),
        }
