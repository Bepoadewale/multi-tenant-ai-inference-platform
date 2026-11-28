# Ticket 50 — Prepare the single-L4 host installation manifest

## Objective

Record every required host and container component, the installation order, researched
version candidates, verification commands, and failure stop conditions before any
GPU instance is launched. This is static preparation; it does not install software or
claim L4 compatibility.

## Current state

- The repository already has a detailed batch runbook and dated vendor research.
- The workstation is macOS arm64 and is not the target Ubuntu host. No Ansible package
  has been installed on the workstation and no host was configured.
- The latest read-only check on 2026-11-28 confirms 4.0 applied On-Demand G/VT vCPUs
  and `CASE_CLOSED`, enough by quota for one `g6.xlarge`. Remote state, Budget,
  exact-plan/cost, expiry, live capacity, and separate apply authorization still gate
  infrastructure. No AWS resource has been created by this ticket.
- This work is [PR #50](https://github.com/Bepoadewale/multi-tenant-ai-inference-platform/pull/50), stacked on open PR #49. A read-only GitHub CLI check on 2026-11-28 confirms the PR is open, non-draft, and all five required jobs passed in run `46016503614`. This records CI status only; it does not authorize an AWS call or spend.

## Research and decisions

- Use standard Ubuntu Server 24.04 amd64 from the Terraform-pinned Canonical AMI.
- Install a compute-only NVIDIA driver before the NVIDIA Container Toolkit.
- Use a toolkit-only CUDA package for `nvcc`; do not accidentally replace the driver
  through a broad CUDA meta-package.
- Keep standalone PyTorch isolated from vLLM's bundled Python and Torch libraries.
- Run model serving, Redis, gateway, and observability services from the dedicated
  Docker Compose profile.
- Keep SSM as the host access path; no public inbound ports are required.
- Candidate stack and freshness requirements are in `RESEARCH_NOTES.md`; the new
  `GPU_HOST_INSTALL_MANIFEST.md` gives the ordered installation checklist.

## Changes

- Added an ordered manifest for host packages, driver, CUDA Toolkit, Docker, NVIDIA
  Container Toolkit, isolated PyTorch, vLLM, the pinned Qwen model, gateway/Redis,
  and observability containers.
- Added a 29-package hash-locked PyTorch CUDA 13.0 environment for Linux x86_64 and
  CPython 3.12, plus installation instructions for the future EC2 execution.
- Explained why the order matters, what belongs in containers, how to verify each
  layer, and which mismatches require stopping rather than improvising.
- Linked the manifest from the documentation index and marked Phase 3 as static
  preparation only.

## Validation

- Reviewed the manifest against the existing runbook, Terraform host configuration,
  Compose profile, and official-source research notes.
- Local Markdown link checks and `git diff --check` passed before the initial PR push.
- `uv 0.9.15` resolved the 29-package CUDA environment from the official PyTorch
  index first and PyPI second; no package was installed. Refresh the lock before the
  live batch.
- No driver, CUDA Toolkit, Docker image, model, or Ansible package was downloaded or
  installed. No Terraform plan/apply, AWS API call, GPU operation, or spend occurred.
- The resolver fetched a 1.2-MiB setuptools distribution for metadata; a separate
  direct-wheel attempt began a 529-MiB Torch transfer and was interrupted before
  installation. Cache state was not inspected or cleaned.

## Security and cost

The host has no inbound rules and uses Systems Manager. Container services are private
or loopback-bound. Versions are candidates and must be rechecked before installation.
All future billable work remains subject to the $25 ceiling, quota approval, exact-plan
approval, runtime cap, expiry, and teardown gates.

## Outstanding work

- Refresh package metadata signatures and exact package names on the reviewed AMI.
- Refresh Docker package signatures and versions; pin the Ansible controller and
  project-scoped automation when the roles are ready.
- Perform the manual installation on one authorized L4, record actual outputs, then
  write Ansible roles from verified steps and run them twice.
- Confirm host memory/CPU fit for the full Compose stack before starting monitoring
  services.
- Decide and implement how GPU evaluation/release records reach MLflow, because the
  current single-GPU Compose profile does not include or connect to the existing local
  MLflow service.

## Acceptance status

**Static preparation only. The GPU software is not installed and no runtime has been
verified.**
