"""Atomic Redis admission and release scripts for horizontally scaled gateways."""

ADMISSION_LUA = """
-- KEYS: requests, tokens, active_leases, daily_tokens, queued, reservations
-- ARGV: now_ms, window_ms, rpm, tpm, concurrency, daily_limit, estimated_tokens,
--       request_id, queue_capacity, has_queue_slot, lease_ms
local now = tonumber(ARGV[1])
local cutoff = now - tonumber(ARGV[2])
local daily_cutoff = now - 86400000
local rpm = tonumber(ARGV[3])
local tpm = tonumber(ARGV[4])
local concurrency = tonumber(ARGV[5])
local daily_limit = tonumber(ARGV[6])
local estimated = tonumber(ARGV[7])
local request_id = ARGV[8]
local queue_capacity = tonumber(ARGV[9])
local has_queue_slot = ARGV[10] == '1'

redis.call('ZREMRANGEBYSCORE', KEYS[1], '-inf', cutoff)
redis.call('ZREMRANGEBYSCORE', KEYS[2], '-inf', cutoff)
redis.call('ZREMRANGEBYSCORE', KEYS[3], '-inf', now)
redis.call('ZREMRANGEBYSCORE', KEYS[4], '-inf', daily_cutoff)
if redis.call('ZCARD', KEYS[1]) >= rpm then return {0, 'requests_per_minute'} end

local token_total = 0
for _, member in ipairs(redis.call('ZRANGE', KEYS[2], 0, -1)) do
  token_total = token_total + tonumber(string.match(member, ':(%d+)$'))
end
if token_total + estimated > tpm then return {0, 'tokens_per_minute'} end
local daily_total = 0
for _, member in ipairs(redis.call('ZRANGE', KEYS[4], 0, -1)) do
  daily_total = daily_total + tonumber(string.match(member, ':(%d+)$'))
end
if daily_total + estimated > daily_limit then
  return {0, 'daily_token_quota'}
end

if redis.call('ZCARD', KEYS[3]) >= concurrency then
  if has_queue_slot then return {0, 'waiting_for_capacity'} end
  if tonumber(redis.call('GET', KEYS[5]) or '0') >= queue_capacity then return {0, 'queue_full'} end
  redis.call('INCR', KEYS[5])
  redis.call('PEXPIRE', KEYS[5], 60000)
  return {0, 'queued'}
end

if has_queue_slot then redis.call('DECR', KEYS[5]) end
redis.call('ZADD', KEYS[1], now, request_id)
redis.call('PEXPIRE', KEYS[1], ARGV[2])
redis.call('ZADD', KEYS[2], now, request_id .. ':' .. estimated)
redis.call('PEXPIRE', KEYS[2], ARGV[2])
redis.call('ZADD', KEYS[3], now + tonumber(ARGV[11]), request_id)
redis.call('ZADD', KEYS[4], now, request_id .. ':' .. estimated)
redis.call('PEXPIRE', KEYS[4], 86400000)
redis.call('HSET', KEYS[6], request_id, estimated)
redis.call('PEXPIRE', KEYS[6], 86400000)
return {1, 'allowed'}
""".strip()

RELEASE_LUA = """
-- KEYS: minute_tokens, active_leases, daily_tokens, reservations
-- ARGV: request_id, actual_tokens (-1 means unknown), now_ms
local request_id = ARGV[1]
local estimate = redis.call('HGET', KEYS[4], request_id)
if not estimate then return 0 end
redis.call('HDEL', KEYS[4], request_id)
redis.call('ZREM', KEYS[2], request_id)
local actual = tonumber(ARGV[2])
if actual >= 0 then
  local reserved_member = request_id .. ':' .. estimate
  local minute_score = redis.call('ZSCORE', KEYS[1], reserved_member)
  if minute_score then
    redis.call('ZREM', KEYS[1], reserved_member)
    if actual > 0 then redis.call('ZADD', KEYS[1], minute_score, request_id .. ':' .. actual) end
  end
  local daily_score = redis.call('ZSCORE', KEYS[3], reserved_member)
  if daily_score then
    redis.call('ZREM', KEYS[3], reserved_member)
    if actual > 0 then redis.call('ZADD', KEYS[3], daily_score, request_id .. ':' .. actual) end
  end
end
if redis.call('ZCARD', KEYS[2]) == 0 then redis.call('DEL', KEYS[2]) end
return 1
""".strip()

RENEW_LUA = """
-- KEYS: active_leases, reservations
-- ARGV: request_id, now_ms, lease_ms
if not redis.call('HEXISTS', KEYS[2], ARGV[1]) then return 0 end
if not redis.call('ZSCORE', KEYS[1], ARGV[1]) then return 0 end
redis.call('ZADD', KEYS[1], tonumber(ARGV[2]) + tonumber(ARGV[3]), ARGV[1])
redis.call('PEXPIRE', KEYS[2], 86400000)
return 1
""".strip()

RELEASE_QUEUE_LUA = """
if tonumber(redis.call('GET', KEYS[1]) or '0') > 0 then redis.call('DECR', KEYS[1]) end
return 1
""".strip()
