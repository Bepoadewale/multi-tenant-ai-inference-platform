from __future__ import annotations

import json

import pytest
from fastapi import HTTPException
from inference_gateway.agent_tools.store import AgentToolAuditStore
from inference_gateway.auth.agent import AgentIdentity, require_agent_scope


def test_delegated_agent_audit_is_durable_and_hashes_arguments(tmp_path):
    path = tmp_path / "agent-tools.db"
    store = AgentToolAuditStore(path)
    store.append(
        event="TOOL_CALLED",
        actor="release-observer-agent",
        tenant="team-search",
        tool="get_request_evidence",
        arguments={"request_id": "request-123"},
    )

    recovered = AgentToolAuditStore(path)
    events = recovered.list()
    assert len(events) == 1
    assert events[0]["event"] == "TOOL_CALLED"
    assert events[0]["tenant"] == "team-search"
    assert events[0]["arguments_sha256"]
    assert "request-123" not in json.dumps(events[0])


def test_delegated_agent_scope_is_required_before_a_tool_action():
    agent = AgentIdentity(
        subject="release-observer-agent",
        tenant="team-search",
        delegated_by="developer-search",
        scopes=frozenset({"inference.read"}),
    )
    assert require_agent_scope(agent, "inference.read") is agent
    with pytest.raises(HTTPException, match="remediation.plan"):
        require_agent_scope(agent, "remediation.plan")
