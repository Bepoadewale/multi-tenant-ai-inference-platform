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
- The first PR #58 CI run `46049398387` failed in supply-chain setup because the
  Trivy action defaulted to unpublished release `v0.70.0`. Its fresh local end-to-end
  job also failed at `make smoke` without identifying the failed assertion. The
  follow-up pins a current verified Trivy release and adds project-container
  diagnostics after a smoke failure; the smoke root cause is still unconfirmed.

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
- [ ] The follow-up CI run passes all required checks, including the fresh local
  end-to-end cycle. The first run failed as described above.
- [ ] Human review; do not merge without owner authorization.
- [ ] After GPU approval, revise any command or package candidate that live evidence
  disproves and rerun the relevant reproduction stage.

## Validation

`make verify` passed Ruff, 146 tests (2 skipped), dependency audit, Compose and
monitoring validation, and benchmark/evaluation/CUDA dry-run plans. The new token test
ran the generator in an isolated temporary directory and checked permissions and
Ed25519 claims. AWS/GPU commands in the guide remain unexecuted. Initial CI run
`46049398387` had Python, manifests, GPU observability, and Ansible pass;
supply-chain failed while locating Trivy `v0.70.0`; local E2E failed at `make smoke`
without diagnostics to identify which readiness/assertion failed. The follow-up adds
an explicit published Trivy version and failure-only project container logs. No cause
is claimed for smoke until those logs or a successful rerun establishes it. Final CI
and relative Markdown-link validation remain pending.

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
