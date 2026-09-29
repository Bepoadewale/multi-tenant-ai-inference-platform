#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"
./scripts/smoke.sh

sandbox_token=$(jq -r '.sandbox_agent' .local/identity/tokens.json)
headers=(-H "Authorization: Bearer ${sandbox_token}" -H 'Content-Type: application/json')

patch=$(curl -fsS http://localhost:8090/sandbox/v1/tasks "${headers[@]}" \
  -H 'Idempotency-Key: sandbox-patch-001' -d '{"task_kind":"fixture_patch"}')
echo "$patch" | jq -e '
  .idempotent_replay == false and
  .task.state == "DESTROYED" and
  .task.exit_code == 0 and
  (.task.patch_sha256 | length == 64) and
  .task.hardening.user == "65532:65532" and
  .task.hardening.read_only_rootfs and
  .task.hardening.cap_drop == ["ALL"] and
  .task.hardening.no_new_privileges and
  .task.hardening.network_mode == "none" and
  (.task.hardening.docker_socket_mounted | not) and
  (.task.hardening.host_bind_mounted | not)
' >/dev/null

replay=$(curl -fsS http://localhost:8090/sandbox/v1/tasks "${headers[@]}" \
  -H 'Idempotency-Key: sandbox-patch-001' -d '{"task_kind":"fixture_patch"}')
echo "$replay" | jq -e '.idempotent_replay and .task.state == "DESTROYED"' >/dev/null

probe=$(curl -fsS http://localhost:8090/sandbox/v1/tasks "${headers[@]}" \
  -H 'Idempotency-Key: sandbox-probe-001' -d '{"task_kind":"containment_probe"}')
echo "$probe" | jq -e '.task.state == "DESTROYED" and .task.exit_code == 0' >/dev/null

status=$(curl -sS -o /tmp/sandbox-invalid-task.json -w '%{http_code}' http://localhost:8090/sandbox/v1/tasks \
  "${headers[@]}" -H 'Idempotency-Key: sandbox-invalid-001' \
  -d '{"task_kind":"exfiltrate","command":["sh","-c","id"]}')
test "$status" = 422
rm -f /tmp/sandbox-invalid-task.json

curl -fsS http://localhost:8090/metrics | awk '
  /inference_gateway_sandbox_tasks_total\{outcome="DESTROYED",task_kind="fixture_patch",tenant="team-search"\}/ { patch=1 }
  /inference_gateway_sandbox_tasks_total\{outcome="DESTROYED",task_kind="containment_probe",tenant="team-search"\}/ { probe=1 }
  END { exit(patch && probe ? 0 : 1) }
'

tasks=$(curl -fsS http://localhost:8090/sandbox/v1/tasks "${headers[@]}")
echo "$tasks" | jq -e '.tasks | length == 2 and all(.[]; .state == "DESTROYED")' >/dev/null

docker compose restart sandbox-control >/dev/null
for _ in $(seq 1 30); do
  if curl -fsS http://localhost:8090/healthz >/dev/null 2>&1; then break; fi
  sleep 1
done
curl -fsS http://localhost:8090/sandbox/v1/tasks "${headers[@]}" | jq -e '.tasks | length == 2' >/dev/null

if docker ps -aq --filter 'label=inference.platform.resource=sandbox' | grep -q .; then
  echo 'A sandbox child was left behind.' >&2
  exit 1
fi
if docker volume ls -q --filter 'label=inference.platform.resource=sandbox' | grep -q .; then
  echo 'A sandbox workspace volume was left behind.' >&2
  exit 1
fi

echo 'Sandboxed-agent demo passed: a short-lived signed delegated agent ran only named fixture tasks; a hardened non-root child tested and patched a disposable repository; arbitrary command input was rejected; an outbound network probe was blocked; child containers and workspaces were destroyed; metadata-only task audit survived controller restart.'
