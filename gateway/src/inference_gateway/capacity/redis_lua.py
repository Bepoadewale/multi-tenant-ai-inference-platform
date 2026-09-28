"""Atomic allocation scripts for one explicitly simulated accelerator pool."""

ADMIT_LUA = """
-- KEYS: pool allocated, tenant allocated, queued requests
-- ARGV: pool capacity, tenant capacity, requested slots, allow CPU fallback,
--       queue capacity, has queue slot
local pool_capacity = tonumber(ARGV[1])
local tenant_capacity = tonumber(ARGV[2])
local requested = tonumber(ARGV[3])
local fallback = ARGV[4] == '1'
local queue_capacity = tonumber(ARGV[5])
local has_queue_slot = ARGV[6] == '1'
local pool_allocated = tonumber(redis.call('GET', KEYS[1]) or '0')
local tenant_allocated = tonumber(redis.call('GET', KEYS[2]) or '0')

if tenant_allocated + requested > tenant_capacity then
  return {0, 'tenant_quota'}
end
if pool_allocated + requested > pool_capacity then
  if fallback then return {1, 'cpu_fallback'} end
  if has_queue_slot then return {0, 'waiting_for_capacity'} end
  if tonumber(redis.call('GET', KEYS[3]) or '0') >= queue_capacity then return {0, 'queue_full'} end
  redis.call('INCR', KEYS[3])
  redis.call('PEXPIRE', KEYS[3], 60000)
  return {0, 'queued'}
end
if has_queue_slot then redis.call('DECR', KEYS[3]) end
redis.call('INCRBY', KEYS[1], requested)
redis.call('INCRBY', KEYS[2], requested)
return {1, 'admitted'}
""".strip()

RELEASE_LUA = """
local requested = tonumber(ARGV[1])
for _, key in ipairs(KEYS) do
  local current = tonumber(redis.call('GET', key) or '0')
  redis.call('SET', key, math.max(0, current - requested))
end
return 1
""".strip()

RELEASE_QUEUE_LUA = """
if tonumber(redis.call('GET', KEYS[1]) or '0') > 0 then redis.call('DECR', KEYS[1]) end
return 1
""".strip()
