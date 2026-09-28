import pytest
from fastapi import HTTPException
from inference_gateway.release.store import ReleaseStore


def _create(store: ReleaseStore):
    return store.create(
        alias="chat-default",
        requester="release-requester",
        champion_version="1",
        candidate_version="2",
        candidate_digest="candidate-sha",
        canary_weight=10,
    )


def test_release_plan_is_durable_and_requires_independent_approval(tmp_path):
    path = tmp_path / "release.db"
    plan = _create(ReleaseStore(path))
    restored = ReleaseStore(path).get(plan.id)
    assert restored.plan_hash == plan.plan_hash
    with pytest.raises(HTTPException, match="cannot approve"):
        ReleaseStore(path).approve(plan.id, "release-requester")
    assert ReleaseStore(path).approve(plan.id, "independent-approver").status == "APPROVED"


def test_release_transition_rejects_stale_state(tmp_path):
    store = ReleaseStore(tmp_path / "release.db")
    plan = _create(store)
    with pytest.raises(HTTPException, match="STALE_PLAN"):
        store.transition(plan.id, "APPROVED", "CANARY")
