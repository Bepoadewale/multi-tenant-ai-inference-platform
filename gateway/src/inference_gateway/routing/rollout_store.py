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
        if not self.client:
            return None
        value = self.client.get(self._key(alias))
        if value is None:
            return None
        decoded = json.loads(value)
        return {str(name): int(weight) for name, weight in decoded.items()}

    def put(self, alias: str, weights: dict[str, int]) -> None:
        if self.client:
            self.client.set(self._key(alias), json.dumps(weights, sort_keys=True))
