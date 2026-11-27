# Ticket 44 — Prepare the consolidated single-L4 execution batch

## Objective

Prepare the workstation, infrastructure, compatibility checks, and GPU-dependent
work order so a future AWS-approved session can use one bounded instance window
efficiently. This is non-billable preparation and does not authorize an apply.

## Current state

The On-Demand G/VT applied quota still reads `0.0`; the owner reports submitting an
appeal through the existing Support Center case. Read-only instance and tagged
resource checks in `us-east-1` found no project resources. No L4 work has been run.
The shared Terraform state bucket, DynamoDB lock table, and budget were previously
confirmed absent, so they remain separate prerequisites.

## Research and decisions

The current official NVIDIA Ubuntu guide supports headless installations and directs
operators to install matching kernel headers, pin a driver package where needed, and
verify after reboot. NVIDIA's CUDA guide remains the source for the exact Ubuntu,
kernel, compiler, and Toolkit matrix. NVIDIA Container Toolkit documentation requires
a working host driver and configures Docker through `nvidia-ctk`. PyTorch's official
selector chooses a CUDA-matched package and its docs recommend a real availability
check. Current vLLM Docker documentation describes the official OpenAI-compatible
image and states that CUDA 13 images need an R580-or-newer driver for the ordinary
path. These findings and links are in `RESEARCH_NOTES.md`.

The recorded version set is provisional. Recheck the signed package repositories,
driver/runtime compatibility, image digest, model revision/license/hash, and price on
the run date. Keep the host CUDA Toolkit for compiler exercises, but do not install a
second CUDA or PyTorch stack inside the pinned vLLM image.

## Changes

- Added `GPU_BATCH_RUNBOOK.md` with quota, price, account, state, saved-plan, expiry,
  runtime, and explicit approval gates.
- Ordered manual host inventory, driver, CUDA, Docker/Container Toolkit, PyTorch,
  manual vLLM, gateway/tenant checks, observability, benchmark/evaluation, release and
  incident drills, evidence export, and teardown.
- Added a ten-hour planning ceiling totaling the work blocks. It is an estimate, not
  an AWS authorization or measured duration.
- Recorded current read-only account/quota/resource inventory without account IDs.

## Validation

- Official source links and their effect on install order and compatibility decisions
  are recorded in `RESEARCH_NOTES.md`.
- `make verify` passed on the parent PR #43 branch: Ruff, 72 tests, pip-audit, and
  Compose configuration. The runbook-only package receives the repository CI checks
  after PR publication.
- `git diff --check` is required before publication.
- AWS caller/quota/project resource calls were read-only; applied G/VT quota was
  `0.0`; no EC2 instance or exact-tag resource was found.

## Security and financial considerations

The $25 maximum total project budget remains a hard ceiling. No Terraform apply is
authorized by this ticket. The exact saved remote-state plan, full current cost,
runtime cap, expiry, instance limit, SSM access, and cleanup process require explicit
review before any billable operation. No credentials, model artifact, prompt data,
raw plan, or account identifier is added to the public repository.

## Outstanding work

- PR #44 was opened at `868e11d` against PR #43; CI is pending.
- Recheck service quota, regional capacity, prices, package pins, image digest, and
  model integrity immediately before any authorized GPU batch.
- Establish the reviewed shared backend and budget through their separate guarded
  bootstrap path.
- Keep all instance and model execution commands unclaimed until a real L4 run.
