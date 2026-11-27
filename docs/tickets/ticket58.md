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
- [ ] Final review commands against actual scripts and files in the repository.
- [ ] The next CI run passes the scanner and fresh local end-to-end cycle. Runs
  `46049398387`, `46050614853`, and `46052092657` failed as described above; the
  third run passed the scanner and named the edge inventory failure.
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
bootstrap script and waits for two registrations before asserting. This fix has not
yet run in CI. Final CI and relative Markdown-link validation remain pending.

## Security and financial limits

- No credentials, account number, token, or host endpoint is embedded in the guide.
- No AWS resource, GPU instance, model weights, or inference image is provisioned or
  downloaded by this work.
- All eventual paid work remains subject to applied quota, exact cost estimate under
  $25, bounded run time, expiry, reviewed plan, cleanup method, and explicit approval.

## Remaining limitations

The guide cannot yet include actual command output or empirically confirmed expected
GPU metrics because no L4 instance is available. Those sections remain prospective
until evidence from a real approved GPU session is collected.
