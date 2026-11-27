#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
profile="${repo_root}/deployments/single-gpu"
[[ "${GPU_EC2_INCIDENT_CONFIRM:-}" == "redis-outage" ]] || {
  echo "refusing incident drill: set GPU_EC2_INCIDENT_CONFIRM=redis-outage after reviewing the procedure" >&2
  exit 1
}
[[ "${EUID}" -eq 0 ]] || { echo "run the Compose incident drill from a root shell" >&2; exit 1; }
python3 "${repo_root}/scripts/gpu_ec2_host_guard.py" --require-l4
compose=(docker compose --env-file "${profile}/.env" -f "${profile}/compose.yaml")
redis_stopped=0
restore() {
  if [[ "$redis_stopped" == 1 ]]; then
    "${compose[@]}" start redis >/dev/null
  fi
}
trap restore EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

python3 "${repo_root}/scripts/gpu_ec2_smoke.py" --readiness-only --wait-seconds 120
redis_stopped=1
"${compose[@]}" stop redis >/dev/null
python3 - <<'PY'
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, new_url):
        return None

opener = build_opener(NoRedirect())
for port in (8081, 8082):
    request = Request(f"http://127.0.0.1:{port}/healthz", method="GET")
    try:
        with opener.open(request, timeout=5) as response:
            status = response.status
    except HTTPError as error:
        status = error.code
    except URLError as error:
        raise SystemExit(f"gateway {port} unavailable during Redis outage: {type(error).__name__}")
    if status != 503:
        raise SystemExit(f"gateway {port} returned unexpected status {status} during Redis outage")
    print(f"gateway {port}: HTTP 503 while Redis is stopped")
PY

"${compose[@]}" start redis >/dev/null
deadline=$((SECONDS + 60))
until "${compose[@]}" exec -T redis redis-cli ping 2>/dev/null | grep -q '^PONG$'; do
  if (( SECONDS >= deadline )); then
    echo "Redis did not recover within 60 seconds" >&2
    exit 1
  fi
  sleep 2
done
redis_stopped=0
python3 "${repo_root}/scripts/gpu_ec2_smoke.py" --readiness-only --wait-seconds 120
echo "Redis recovered and both gateway replicas passed readiness. No prompts or tokens were collected."
