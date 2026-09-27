"""HTTP boundary for the local governed model-release vertical slice."""

from __future__ import annotations

import json
import os
from pathlib import Path

import mlflow
import redis
from fastapi import Depends, FastAPI, HTTPException
from inference_gateway.auth.admin import platform_admin, release_approver
from inference_gateway.release.store import ReleasePlan, ReleaseStore

MODEL_NAME = "local-tiny-intent-classifier"
ALIAS = "chat-default"
TARGETS = {"stable": "onnx-stable-v1", "candidate": "onnx-candidate-v2"}

app = FastAPI(title="Flagship Model Release Control", version="0.1.0")
store = ReleaseStore(os.getenv("RELEASE_DB_PATH", ".local/release/release.db"))


def _client() -> mlflow.MlflowClient:
    mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://localhost:15010"))
    return mlflow.MlflowClient()


def _versions() -> tuple[str, str, str]:
    client = _client()
    champion = client.get_model_version_by_alias(MODEL_NAME, "champion")
    candidate = client.get_model_version_by_alias(MODEL_NAME, "candidate")
    digest = client.get_model_version(MODEL_NAME, candidate.version).tags.get("artifact.sha256")
    if not digest:
        raise HTTPException(409, "candidate artifact digest is missing")
    return champion.version, candidate.version, digest


def _weights(plan: ReleasePlan, candidate_weight: int) -> dict[str, int]:
    return {TARGETS["stable"]: 100 - candidate_weight, TARGETS["candidate"]: candidate_weight}


def _write_weights(weights: dict[str, int]) -> None:
    try:
        redis.Redis.from_url(os.environ["REDIS_URL"], decode_responses=True).set(
            f"inference:rollout:{ALIAS}", json.dumps(weights, sort_keys=True)
        )
    except (KeyError, redis.RedisError) as error:
        raise HTTPException(503, "release rollout store unavailable") from error


def _assert_current(plan: ReleasePlan) -> None:
    champion, candidate, digest = _versions()
    if (champion, candidate, digest) != (
        plan.champion_version,
        plan.candidate_version,
        plan.candidate_digest,
    ):
        raise HTTPException(409, "STALE_PLAN")


@app.get("/healthz")
def healthz():
    return {"status": "ok", "store": Path(store.path).name}


@app.post("/release/v1/plans", response_model=None)
def create_plan(requester: str = Depends(platform_admin)):
    champion, candidate, digest = _versions()
    return store.create(
        alias=ALIAS,
        requester=requester,
        champion_version=champion,
        candidate_version=candidate,
        candidate_digest=digest,
        canary_weight=10,
    )


@app.get("/release/v1/plans/{plan_id}")
def get_plan(plan_id: str, requester: str = Depends(platform_admin)):
    return store.get(plan_id)


@app.post("/release/v1/plans/{plan_id}/approve")
def approve_plan(plan_id: str, approver: str = Depends(release_approver)):
    return store.approve(plan_id, approver)


@app.post("/release/v1/plans/{plan_id}/canary")
def start_canary(plan_id: str, requester: str = Depends(platform_admin)):
    plan = store.get(plan_id)
    _assert_current(plan)
    if plan.status != "APPROVED":
        raise HTTPException(409, "release plan requires independent approval")
    _write_weights(_weights(plan, plan.canary_weight))
    return store.transition(plan_id, "APPROVED", "CANARY")


@app.post("/release/v1/plans/{plan_id}/promote")
def promote(plan_id: str, requester: str = Depends(platform_admin)):
    plan = store.get(plan_id)
    _assert_current(plan)
    if plan.status != "CANARY":
        raise HTTPException(409, "release plan is not in canary")
    _write_weights(_weights(plan, 100))
    _client().set_registered_model_alias(MODEL_NAME, "champion", plan.candidate_version)
    return store.transition(plan_id, "CANARY", "PROMOTED")


@app.post("/release/v1/plans/{plan_id}/rollback")
def rollback(plan_id: str, requester: str = Depends(platform_admin)):
    plan = store.get(plan_id)
    if plan.status not in {"CANARY", "PROMOTED"}:
        raise HTTPException(409, "release plan has no active rollout")
    _write_weights(_weights(plan, 0))
    _client().set_registered_model_alias(MODEL_NAME, "champion", plan.champion_version)
    with Path(store.path).parent.joinpath("rollback-audit.txt").open("a") as audit:
        audit.write(f"{plan.id} rollback to model version {plan.champion_version}\n")
    return store.transition(plan_id, plan.status, "ROLLED_BACK")
