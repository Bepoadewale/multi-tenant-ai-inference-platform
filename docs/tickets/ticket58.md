# Ticket 58 — prepare GPU reproduction and tenant identity flows

## Objective

Create a command-by-command guide for a technically experienced operator to
reproduce the single-L4 project without hidden agent work. Prepare authenticated
support, engineering, and research tenants with different permissions and limits so
the guide can exercise the real gateway path after quota approval. Explain where each
command runs, why it is needed, what success looks like, and how to stop safely.

## Current state

- Work is on `codex/gpu-manual-reproduction-guide`, PR #58, stacked on ready-for-review
  PR #57 head `4795f12`.
- PR #57 passed all six CI jobs, including one clean-runner local end-to-end cycle,
  in run `46045068200`. It is open and unmerged.
- The manual guide is static preparation; AWS/GPU commands shown there have not run on
  an EC2 host. The live applied G/VT quota remains zero and the $25 ceiling applies.
- The GPU catalog initially had only generic team identities. Three GPU-lab tenant
  profiles and corresponding signed-token entries are now added without removing
  existing tenants. Local token generation now makes the private key and token file
  mode `0600`, while the mounted public key is readable by the gateway container.
- PR #58 run `46049398387` failed before Trivy scanning while resolving the action's
  default `v0.70.0`. Follow-up run `46050614853` confirmed that `v0.76.2` is
  published, but the action's release resolver still could not find that tag on the
  runner. The workflow now downloads the official Linux AMD64 archive directly and
  verifies its SHA-256 before running the scan.
- Both fresh local end-to-end jobs failed at `make smoke`. The latest run's service
  inventory showed containers running and healthy, and logs showed successful
  gateway/model and edge-device HTTP requests. It did not show which silent JSON
  assertion failed, so the cause remains unconfirmed. The smoke script now names each
  JSON assertion on failure without printing response bodies or identity tokens.
- Run `46052092657` passed the Trivy scan and every other job except local E2E. The
  named assertion identified the failing check: the simulated edge-device registry
  did not contain both devices. The containers ran as image UID `65532`, while
  `tokens.json` is intentionally owner-only (`0600`); source inspection shows edge
  agents retry registration after token-read errors, then still return a healthy
  `/healthz`. The Compose services now run as the host UID/GID supplied by
  `bootstrap-local`, preserving the owner-only token permissions. The smoke script
  also waits for both registrations before asserting the inventory.
- PR review on head `d759b8e` found three operator-guide gaps: required Terraform
  wrapper variables were not exported, the foreground manual vLLM container kept
  port 8000/GPU allocated before Compose, and teardown commands were shown from the
  EC2 shell instead of the authorized workstation. The guide now names plan/apply/
  destroy inputs, documents the separately approved state bootstrap, stops and removes
  the manual container while retaining its model-cache volume, and splits host
  shutdown from workstation Terraform destruction.
- A final cross-check found the batch runbook manual-serving example diverged from the hands-on guide: it used a separate host bind mount, removed the container automatically, and omitted the served alias. The batch runbook now reuses the Compose named cache volume, preserves container logs, sets `gpu-default`, and explicitly stops/removes the manual container after checking that GPU and port 8000 are released. Placeholder arguments are quoted so Bash parses them safely. Added a direct non-streaming adapter contract test for the served alias, OpenAI chat-completion path, response content, and backend-reported usage. A security review also found Python’s default urllib redirect handler copies authorization headers to the redirect URL; the evaluator now refuses redirects, with a local two-server test proving the bearer token is not forwarded. An API-level tenant-spoof regression test proves a signed support tenant stays restricted when a request supplies `X-Tenant: research`, and an invalid bearer token is still rejected.
- The three findings were answered and resolved after commit `a1616ec`. Final-head
  CI run `46055428111` passed all six jobs, including the workflow E2E job. The batch
  runbook correction in `8ca57ed` also passed all six jobs in `46058891531`. No
  separate local clean-room run was launched.

## Research and design

- Follow the actual Terraform, Ansible, Compose, PyTorch, inference benchmark,
  evaluation, quota, and cleanup interfaces already committed in the repository.
- Use dated image/package digests only as candidates and label the mandatory
  pre-launch refresh checks.
- Separate local workstation, EC2/Session Manager, container, gateway, and GitHub
  Actions command locations.
- Seed three named tenants with different allowed model sets, request/token limits,
  concurrency limits, and signed identities. The profiles are logical controls over
  a shared L4, not hardware isolation.
- State security, financial, execution, and evidence boundaries at each phase.
- Do not claim a command has run unless a recorded execution artifact proves it.

## Acceptance criteria

- [x] Guide explains account/quota preflight, cost review, plan review, expiry,
  SSM access, Linux inventory, manual NVIDIA/CUDA/Docker/PyTorch setup, manual vLLM,
  Compose, Ansible, evidence, and teardown.
- [x] Includes success expectations, common failures, and safe stop/undo guidance.
- [x] Uses placeholders for private account-specific values.
- [x] Adds separate GPU-lab tenant identity fixtures, distinct limits/model sets, and
  file permissions suitable for the gateway's public-key mount.
- [x] Tests that new tenant tokens verify with the published Ed25519 public key and
  contain the intended tenant identity.
- [x] Links from the documentation index and clearly labels unexecuted GPU commands.
- [x] Final static guide cross-reference, Bash syntax, Make target, and command review,
  including the three automated review findings and matching manual/batch vLLM volume,
  alias, and stop/remove procedure.
- [x] Test the vLLM non-stream adapter against a representative OpenAI-compatible
  response, including the served model alias and backend-reported usage.
- [x] Prevent evaluation bearer-token forwarding across HTTP redirects and verify the
  redirect target receives no Authorization header.
- [x] Verify a caller-supplied tenant header cannot change the signed tenant identity
  or bypass invalid-token rejection at the gateway API.
- [x] Final-head CI run `46055428111` passed all six jobs, including the scanner and
  local E2E job. The successful fresh-runner E2E evidence first passed in
  `46054114999`; later PR workflows automatically repeated the job after guide and
  documentation updates, most recently in run `46056755505`.
- [ ] Human review; do not merge without owner authorization.
- [ ] After GPU approval, revise any command or package candidate that live evidence
  disproves and rerun the relevant reproduction stage.

## Validation

`make verify` passed Ruff, 146 tests (2 skipped), dependency audit, Compose and
monitoring validation, and benchmark/evaluation/CUDA dry-run plans. The new token test
ran the generator in an isolated temporary directory and checked permissions and
Ed25519 claims. AWS/GPU commands in the guide remain unexecuted. CI runs
`46049398387` and `46050614853` both passed Python, manifests, GPU observability, and
Ansible. The first scanner failed resolving `v0.70.0`; the second failed resolving
the API-confirmed published `v0.76.2` through the installer's release lookup. Run
`46052092657` passed Trivy using the versioned official release archive and checked
SHA-256; all jobs passed except local E2E. The named check showed an empty edge
inventory. Source inspection traced this to edge agents running as image UID `65532`
while the newly restricted token file is owned by the local user at mode `0600`;
agents silently retry registration but still report healthy. Compose now runs these
two local-only agents with the `LOCAL_UID`/`LOCAL_GID` already exported by the
bootstrap script and waits for two registrations before asserting. The manual guide
was also corrected for Terraform wrapper inputs, private bootstrap, stopping the
manual vLLM container before Compose, and workstation-only destroy commands. All 40
Bash blocks parsed, all eight Make targets exist, and the manual guide and ticket have
no broken relative links. The final guide commit `a1616ec` passed all six jobs in CI run
`46055428111`; docs follow-up commit `2d508a9` passed all six in `46056755505`;
runbook commit `8ca57ed` passed all six in `46058891531`. The targeted adapter test passed 23 tests in `gateway/tests/test_vllm_streaming.py`.
The evaluation suite passed 7 focused tests including the redirect-token test. The API
module passed 7 tests including the signed-tenant/header-spoof case. Ruff passed on all
changed Python files. Run `46059847575` for head `0239cbb` passed all
six CI jobs; the redirect mitigation and tenant-header API test are follow-ups and still need CI. Those workflows automatically repeated local E2E; no separate local
clean-room run was launched. The runbook follow-up has 50 Bash blocks parsed with
`bash -n`, zero broken relative links across changed Markdown, and `git diff --check`
passed.

## Security and financial limits

- No credentials, account number, token, or host endpoint is embedded in the guide.
- No AWS resource, GPU instance, model weights, or inference image is provisioned or
  downloaded by this work.
- All eventual paid work remains subject to applied quota, exact cost estimate under
  $25, bounded run time, expiry, reviewed plan, cleanup method, and explicit approval.

## API model authorization follow-up

- **Objective:** verify a caller cannot use `X-Tenant` to request a model assigned to
  another tenant.
- **Change:** the signed customer-support identity test now submits `embeddings`
  alongside `X-Tenant: internal-engineering`. The API returns HTTP 403 with the
  expected tenant authorization detail before backend execution.
- **Validation:** from the repository root,
  `uv run --project gateway pytest -q gateway/tests/test_api.py` passed 7 tests and
  `uv run --project gateway ruff check gateway/tests/test_api.py` passed. Running the
  same pytest file from `gateway/` failed during import because the existing ONNX
  model path is resolved relative to the repository root; no test assertion ran in
  that attempt. The correct working directory is now recorded here.
- **Scope:** this is a local TestClient/API check. It does not demonstrate a live
  vLLM request, Redis sharing between deployed replicas, or hardware isolation.
- **CI / review:** local change only at this point; existing PR run `46064223245`
  targets the earlier `ea86dcb` head. A new PR workflow must include the test before
  it can be called CI-verified. PR #58 remains open and unmerged.
- **AWS / cost:** quota preflight returned `0.0` G/VT vCPUs and no running project-
  tagged EC2 instance. No AWS mutation, GPU use, or spend occurred.

## Current AWS launch-preflight result

The repository's actual `make gpu-ec2-preflight` target was run read-only with the
expected AWS profile/account, the pinned Canonical Ubuntu 24.04 AMI, an offered
`us-east-1` zone, and a future expiry within the 12-hour limit. It verified the
account and AMI, then stopped at the intended fail-closed gate:
`On-Demand G/VT quota is 0.0 vCPUs; 4 are required`. It did not reach Terraform,
backend, budget, or resource-creation steps. The existing case remains
`CASE_OPENED`; no AWS mutation occurred. No GPU hours or spend were used.

The API test is now published as commit `56a0493`; all six PR jobs passed in run
`46065078837`, including the automatic local E2E job. This workflow ran before the
new Redis outage and cross-gateway cancellation drills were added, so those changes
still require their own PR workflow. No separate local clean-room run was launched.

## Local, no-GPU admission fault drills

- **Objective:** close the static/local integration gap for cross-process cancellation,
  Redis fail-closed behavior, and Redis recovery before the L4 becomes available.
- **Change:** `make demo-gateway-cancellation` issues ten streamed requests through
  both independent local gateways, closes each response after its first data chunk,
  and verifies both the process-local active-request metric and shared Redis active
  lease hash return to zero. `make demo-redis-outage` stops only the project Redis
  container, requires both gateways to return the documented 503, starts Redis in an
  exit trap, and verifies both readiness checks recover. Both are wired into the
  flagship local E2E flow. The manual reproduction guide explains the commands and
  recovery.
- **Static validation:** Bash syntax, Ruff, bytecode compilation, Make target
  resolution, and `git diff --check` passed. A first Ruff run found an import-order
  issue; it was fixed. The new scripts have not yet been run against containers.
- **Pending:** validate actual cancellation/disconnect semantics and Redis restart in
  the single GitHub local E2E run on the new PR head; update this record with the
  result. No second manual clean-room run is planned.
- **AWS / GPU:** none. The existing AWS preflight stopped at quota `0.0`; no cloud
  mutation or spend occurred.

## Fault-drill result and rollout-store fix

- **CI evidence:** run `46066808334` executed the new local drills. The cancellation
  drill passed ten cancelled SSE requests across both gateways and verified the
  process-local active gauges and shared Redis leases returned to zero. The Redis
  outage drill then observed HTTP 500 from gateway 8081 instead of the expected 503.
  The exit trap restarted Redis and its ping recovery guard completed; the failed
  assertion meant the test did not reach gateway 8082 or post-recovery readiness.
- **Root cause:** `GatewayService.chat` reads shared rollout state synchronously
  before admission; `RolloutStore.get_context` did not translate the Redis connection
  error, so it escaped as HTTP 500 before the admission layer's existing 503 mapping.
  Rollout writes also changed local weights before persisting shared state.
- **Fix:** map Redis rollout reads and writes to HTTP 503; persist a rollout before
  changing local target weights. Added regressions prove unavailable reads fail
  closed and failed writes leave local weights and the audit unchanged.
- **Drill expectation:** because shared rollout lookup runs before admission, the
  outage test now expects `503 shared rollout state unavailable` from both replicas.
- **Local validation:** repository-root API and rollout test modules passed **10
  tests**; Ruff passed. Bash syntax and documentation whitespace checks pass. The
  fixed cross-process outage plus recovery drill has not run yet.
- **Incident report:** `docs/gpu-lab/incidents/INCIDENT-LOCAL-REDIS-001.md` preserves
  the actual failure, detection, limits, root cause, and fix without calling it a
  production or GPU incident.
- **Next gate:** publish the fix and run one CI workflow. Require both gateways to
  return HTTP 503 while Redis is stopped, Redis `PING` to recover, and both gateway
  readiness checks to pass. Keep PR #58 open; no merge is authorized.

## Remaining limitations

The guide cannot yet include actual command output or empirically confirmed expected
GPU metrics because no L4 instance is available. Those sections remain prospective
until evidence from a real approved GPU session is collected.
