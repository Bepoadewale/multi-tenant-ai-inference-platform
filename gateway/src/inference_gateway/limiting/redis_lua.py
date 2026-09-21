"""Atomic Redis admission and release scripts for horizontally scaled gateways."""

ADMISSION_LUA = """
-- KEYS: requests, tokens, active, daily, queued
-- ARGV: now_ms, window_ms, rpm, tpm, concurrency, daily_limit, estimated_tokens,
--       request_id, queue_capacity, has_queue_slot
local now = tonumber(ARGV[1])
local cutoff = now - tonumber(ARGV[2])
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
if redis.call('ZCARD', KEYS[1]) >= rpm then return {0, 'requests_per_minute'} end

local token_total = 0
for _, member in ipairs(redis.call('ZRANGE', KEYS[2], 0, -1)) do
  token_total = token_total + tonumber(string.match(member, ':(%d+)$'))
end
if token_total + estimated > tpm then return {0, 'tokens_per_minute'} end
if tonumber(redis.call('GET', KEYS[4]) or '0') + estimated > daily_limit then
  return {0, 'daily_token_quota'}
end

if tonumber(redis.call('GET', KEYS[3]) or '0') >= concurrency then
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
redis.call('INCR', KEYS[3])
redis.call('INCRBY', KEYS[4], estimated)
redis.call('PEXPIRE', KEYS[4], 86400000)
return {1, 'allowed'}
""".strip()

RELEASE_LUA = """
if tonumber(redis.call('GET', KEYS[1]) or '0') > 0 then redis.call('DECR', KEYS[1]) end
return 1
""".strip()

RELEASE_QUEUE_LUA = """
if tonumber(redis.call('GET', KEYS[1]) or '0') > 0 then redis.call('DECR', KEYS[1]) end
return 1
""".strip()
