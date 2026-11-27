import time
from collections import deque
from datetime import UTC, datetime, timedelta

from inference_gateway.catalog.store import Catalog
from inference_gateway.limiting.service import TenantLimiter


def test_release_reconciles_usage_once_and_frees_concurrency():
    tenant = Catalog().tenant("team-search")
    limiter = TenantLimiter()
    reservation = limiter.admit(tenant, estimated_tokens=20, request_id="request-1")

    assert len(limiter.active[tenant.id]) == 1
    assert limiter.release(tenant, reservation, actual_tokens=7) is True
    assert limiter.release(tenant, reservation, actual_tokens=7) is False
    assert not limiter.active[tenant.id]
    assert sum(value for _, _, value in limiter.tokens[tenant.id]) == 7
    assert sum(value for _, _, value in limiter.daily[tenant.id]) == 7


def test_unknown_usage_keeps_the_full_reservation_until_quota_window_expires():
    tenant = Catalog().tenant("team-search")
    limiter = TenantLimiter()
    reservation = limiter.admit(tenant, estimated_tokens=20, request_id="request-2")

    assert limiter.release(tenant, reservation, actual_tokens=None) is True
    assert not limiter.active[tenant.id]
    assert sum(value for _, _, value in limiter.tokens[tenant.id]) == 20
    assert sum(value for _, _, value in limiter.daily[tenant.id]) == 20


def test_reconciliation_preserves_time_order_and_negative_usage_keeps_estimate():
    tenant = Catalog().tenant("team-search")
    limiter = TenantLimiter()
    old = datetime.now(UTC) - timedelta(seconds=50)
    recent = datetime.now(UTC) - timedelta(seconds=10)
    limiter.tokens[tenant.id] = deque([(old, "old", 20), (recent, "recent", 5)])
    limiter.daily[tenant.id] = deque([(old, "old", 20), (recent, "recent", 5)])
    reservation = limiter.admit(tenant, estimated_tokens=12, request_id="negative-usage")

    TenantLimiter._reconcile(limiter.tokens[tenant.id], "old", 3)
    limiter.release(tenant, reservation, actual_tokens=-1)

    assert [entry[1] for entry in limiter.tokens[tenant.id]] == [
        "old",
        "recent",
        "negative-usage",
    ]
    assert limiter.tokens[tenant.id][0] == (old, "old", 3)
    assert sum(value for _, _, value in limiter.tokens[tenant.id]) == 20


def test_expired_lease_is_removed_before_the_next_concurrency_check():
    tenant = Catalog().tenant("team-search")
    limiter = TenantLimiter(lease_seconds=0.01)
    limiter.admit(tenant, estimated_tokens=1, request_id="stale-request")
    time.sleep(0.02)

    replacement = limiter.admit(tenant, estimated_tokens=1, request_id="new-request")

    assert replacement.request_id == "new-request"
    assert limiter.active[tenant.id] == {"new-request"}
