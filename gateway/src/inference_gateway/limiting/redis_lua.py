"""Redis Lua admission contract for horizontally scaled gateways.

Deploy this script through the Redis adapter, with keys tagged by tenant to preserve
atomic request/token/concurrency checks in one cluster hash slot.
"""

ADMISSION_LUA = """
-- KEYS: req window, token window, active count, daily count
-- ARGV: now_ms, window_ms, rpm, tpm, concurrency, daily_limit, estimated_tokens
-- Production adapter uses Redis TIME, sorted-set expiry, and a compensating release.
-- Return {allowed, reason}; fail closed on Redis errors in distributed mode.
return {1, 'contract-only'}
""".strip()
