"""A deliberately narrow delegated-agent tool facade.

This is an HTTP integration slice, not a replacement for the separately validated MCP
gateway project. It proves the same essential control: tool discovery and authority
are filtered before an agent can reach a privileged platform action.
"""

from __future__ import annotations

import os
from pathlib import Path

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException, Response
from inference_gateway.agent_tools.store import AgentToolAuditStore
from inference_gateway.auth.agent import AgentIdentity, delegated_agent, require_agent_scope
from inference_gateway.metering.redis_service import RedisMeter
from inference_gateway.observability.tracing import configure_tracing
from inference_gateway.operations.service import analyse
from prometheus_client import CONTENT_TYPE_LATEST, Counter, generate_latest
from pydantic import BaseModel

TOOLS_DISCOVERED = Counter(
    "inference_gateway_agent_tools_discovered_total",
    "Delegated-agent tools returned by filtered discovery",
    ["tenant"],
)
TOOLS_CALLED = Counter(
    "inference_gateway_agent_tool_calls_total",
    "Delegated-agent tool call outcomes",
    ["tool", "outcome"],
)


class ToolCall(BaseModel):
    arguments: dict[str, str]


TOOLS = {
    "get_request_evidence": {
        "scope": "inference.read",
        "description": "Read metadata-only evidence for a request belonging to the delegated tenant.",
    },
    "plan_canary_rollback": {
        "scope": "remediation.plan",
        "description": "Prepare a canary rollback plan from a failed request; approval and execution stay human-gated.",
    },
}

app = FastAPI(title="Flagship Delegated Agent Tools", version="0.1.0")
configure_tracing(app, "delegated-agent-tools")
store = AgentToolAuditStore(os.getenv("AGENT_TOOLS_DB_PATH", ".local/agent-tools/audit.db"))
meter = RedisMeter(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
remediation_url = os.getenv("REMEDIATION_CONTROL_URL", "http://localhost:8084")


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok", "store": Path(store.path).name, "scope": "delegated-agent-tools"}


@app.get("/metrics")
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/agent/v1/tools")
def list_tools(agent: AgentIdentity = Depends(delegated_agent)) -> dict[str, object]:
    allowed = [
        {"name": name, "description": definition["description"]}
        for name, definition in TOOLS.items()
        if definition["scope"] in agent.scopes
    ]
    store.append(event="TOOLS_DISCOVERED", actor=agent.subject, tenant=agent.tenant, tool="catalog", arguments={})
    TOOLS_DISCOVERED.labels(tenant=agent.tenant).inc(len(allowed))
    return {"delegated_by": agent.delegated_by, "tools": allowed}


@app.get("/agent/v1/audit")
def audit(agent: AgentIdentity = Depends(delegated_agent)) -> dict[str, object]:
    return {"events": [event for event in store.list() if event["tenant"] == agent.tenant]}


@app.post("/agent/v1/tools/{tool_name}")
async def call_tool(
    tool_name: str,
    request: ToolCall,
    authorization: str | None = Header(default=None),
    agent: AgentIdentity = Depends(delegated_agent),
) -> dict[str, object]:
    definition = TOOLS.get(tool_name)
    if definition is None or definition["scope"] not in agent.scopes:
        store.append(
            event="TOOL_DENIED",
            actor=agent.subject,
            tenant=agent.tenant,
            tool=tool_name,
            arguments=request.arguments,
        )
        TOOLS_CALLED.labels(tool=tool_name, outcome="DENIED").inc()
        raise HTTPException(404, "tool is not available to this delegated agent")
    require_agent_scope(agent, str(definition["scope"]))
    request_id = request.arguments.get("request_id")
    if not request_id or set(request.arguments) != {"request_id"}:
        raise HTTPException(422, "tool requires exactly request_id")

    if tool_name == "get_request_evidence":
        record = await meter.get_request(request_id)
        if record is None:
            raise HTTPException(404, "request operational evidence not found")
        if record.tenant_id != agent.tenant:
            store.append(
                event="CROSS_TENANT_READ_DENIED",
                actor=agent.subject,
                tenant=agent.tenant,
                tool=tool_name,
                arguments=request.arguments,
            )
            TOOLS_CALLED.labels(tool=tool_name, outcome="DENIED").inc()
            raise HTTPException(403, "cross-tenant request evidence denied")
        result: dict[str, object] = analyse(record)
    else:
        if not authorization:
            raise HTTPException(401, "delegated agent identity required")
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                f"{remediation_url}/remediation/v1/agent/incidents/{request_id}/plans",
                headers={"Authorization": authorization},
            )
        if response.status_code >= 400:
            TOOLS_CALLED.labels(tool=tool_name, outcome="UPSTREAM_DENIED").inc()
            raise HTTPException(response.status_code, response.text)
        result = response.json()

    store.append(
        event="TOOL_CALLED",
        actor=agent.subject,
        tenant=agent.tenant,
        tool=tool_name,
        arguments=request.arguments,
    )
    TOOLS_CALLED.labels(tool=tool_name, outcome="ALLOWED").inc()
    return {"tool": tool_name, "delegated_by": agent.delegated_by, "result": result}
