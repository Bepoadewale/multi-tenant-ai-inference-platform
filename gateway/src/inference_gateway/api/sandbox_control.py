"""A narrow local control API for disposable, hardened agent execution."""

from __future__ import annotations

import os
import re
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from fastapi import Depends, FastAPI, Header, HTTPException, Response
from inference_gateway.auth.sandbox import SandboxAgentIdentity, sandbox_agent
from inference_gateway.observability.tracing import configure_tracing
from inference_gateway.sandbox.executor import HardenedSandboxExecutor
from inference_gateway.sandbox.store import SandboxTaskStore
from prometheus_client import CONTENT_TYPE_LATEST, Counter, generate_latest
from pydantic import BaseModel, ConfigDict, Field

TASKS = Counter(
    "inference_gateway_sandbox_tasks_total",
    "Bounded sandbox task outcomes",
    ["tenant", "task_kind", "outcome"],
)


class SandboxTaskRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    task_kind: str = Field(pattern=r"^(fixture_patch|containment_probe)$")


app = FastAPI(title="Flagship Sandboxed Agent Control", version="0.1.0")
configure_tracing(app, "sandbox-control")
store = SandboxTaskStore(os.getenv("SANDBOX_DB_PATH", ".local/sandbox/tasks.db"))


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok", "store": Path(store.path).name, "scope": "bounded-sandbox-control"}


@app.get("/metrics")
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/sandbox/v1/tasks", status_code=201)
def run_task(
    request: SandboxTaskRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    identity: SandboxAgentIdentity = Depends(sandbox_agent),
) -> dict[str, object]:
    if not idempotency_key or not re.fullmatch(r"[A-Za-z0-9._-]{8,128}", idempotency_key):
        raise HTTPException(422, "an Idempotency-Key of 8-128 safe characters is required")
    existing = store.by_idempotency_key(identity.tenant, idempotency_key)
    if existing:
        if existing["task_kind"] != request.task_kind:
            raise HTTPException(409, "idempotency key was already used for a different sandbox task")
        return {"task": existing, "idempotent_replay": True}

    result = HardenedSandboxExecutor().execute(request.task_kind)
    if result.exit_code != 0:
        TASKS.labels(tenant=identity.tenant, task_kind=request.task_kind, outcome="FAILED").inc()
        raise HTTPException(502, "bounded sandbox task failed")
    task = {
        "id": str(uuid4()),
        "tenant": identity.tenant,
        "agent": identity.subject,
        "delegated_by": identity.delegated_by,
        "task_kind": request.task_kind,
        "state": "DESTROYED",
        "exit_code": result.exit_code,
        "patch_sha256": result.patch_sha256,
        "hardening": result.hardening,
        "created_at": datetime.now(UTC).isoformat(),
    }
    store.save(task, idempotency_key=idempotency_key)
    TASKS.labels(tenant=identity.tenant, task_kind=request.task_kind, outcome="DESTROYED").inc()
    return {"task": task, "idempotent_replay": False}


@app.get("/sandbox/v1/tasks")
def list_tasks(identity: SandboxAgentIdentity = Depends(sandbox_agent)) -> dict[str, object]:
    return {"tasks": store.list_for_tenant(identity.tenant)}
