from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ServingMode(StrEnum):
    SHARED = "shared"
    DEDICATED = "dedicated"


class TenantQuota(BaseModel):
    requests_per_minute: int = Field(gt=0)
    tokens_per_minute: int = Field(gt=0)
    concurrent_requests: int = Field(gt=0)
    daily_token_quota: int = Field(gt=0)


class Tenant(BaseModel):
    id: str
    allowed_models: set[str]
    quotas: TenantQuota
    priority: int = Field(default=50, ge=0, le=100)
    environment: str = "development"
    cost_center: str


class ModelTarget(BaseModel):
    name: str
    version: str
    weight: int = Field(ge=0, le=100)
    healthy: bool = True
    backend_url: str | None = None


class ModelDefinition(BaseModel):
    name: str
    provider: str = "local"
    runtime: Literal["mock", "vllm"] = "mock"
    model_id: str
    serving_mode: ServingMode = ServingMode.SHARED
    min_replicas: int = Field(default=1, ge=0)
    max_replicas: int = Field(default=4, ge=1)
    gpu_count: int = Field(default=0, ge=0)
    gpu_type: str | None = None
    tensor_parallel_size: int = Field(default=1, ge=1)
    max_model_len: int = Field(default=8192, ge=128)
    max_num_seqs: int = Field(default=32, ge=1)
    max_num_batched_tokens: int = Field(default=8192, ge=128)
    gpu_memory_utilization: float = Field(default=0.9, gt=0, le=1)
    dtype: str = "auto"
    quantization: str | None = None
    prefix_caching: bool = True
    targets: list[ModelTarget]


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class ChatCompletionRequest(BaseModel):
    model: str
    messages: list[ChatMessage] = Field(min_length=1)
    max_tokens: int = Field(default=64, ge=1, le=2048)
    stream: bool = False
    temperature: float = Field(default=0.7, ge=0, le=2)


class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class UsageRecord(BaseModel):
    request_id: UUID = Field(default_factory=uuid4)
    tenant_id: str
    model: str
    backend: str
    deployment_version: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    usage: Usage
    latency_ms: float
    ttft_ms: float | None
    streaming: bool
    outcome: str


class CapacityState(StrEnum):
    HEALTHY = "HEALTHY"
    BUSY = "BUSY"
    SATURATED = "SATURATED"
    DEGRADED = "DEGRADED"


class RolloutWeights(BaseModel):
    weights: dict[str, int]


class AdminAuditEvent(BaseModel):
    actor: str
    action: str
    model: str
    details: dict[str, str] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
