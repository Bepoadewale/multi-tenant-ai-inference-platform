"""Shared rollout intent for local gateway replicas.

Redis is already a required local platform dependency. Keeping the current rollout
intent there makes a release action visible to every gateway without turning routing
into a second control plane.
"""

from __future__ import annotations

import json

import redis


class RolloutStore:
    def __init__(self, redis_url: str | None) -> None:
        self.client = redis.Redis.from_url(redis_url, decode_responses=True) if redis_url else None

    @staticmethod
    def _key(alias: str) -> str:
        return f"inference:rollout:{alias}"

    def get(self, alias: str) -> dict[str, int] | None:
        context = self.get_context(alias)
        return None if context is None else context["weights"]

    def get_context(self, alias: str) -> dict[str, object] | None:
        if not self.client:
            return None
        value = self.client.get(self._key(alias))
        if value is None:
            return None
        decoded = json.loads(value)
        # Accept the original map to avoid breaking an in-flight local rollout.
        if "weights" not in decoded:
            return {"weights": {str(name): int(weight) for name, weight in decoded.items()}}
        return {
            "weights": {str(name): int(weight) for name, weight in decoded["weights"].items()},
            "release_plan_id": decoded.get("release_plan_id"),
            "release_phase": decoded.get("release_phase"),
        }

    def put(
        self,
        alias: str,
        weights: dict[str, int],
        *,
        release_plan_id: str | None = None,
        release_phase: str | None = None,
    ) -> None:
        if self.client:
            payload = {
                "weights": weights,
                "release_plan_id": release_plan_id,
                "release_phase": release_phase,
            }
            self.client.set(self._key(alias), json.dumps(payload, sort_keys=True))
