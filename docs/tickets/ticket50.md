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
- The owner reports manually sending an appeal in the existing AWS support case. The
  last documented applied G/VT quota is zero, so infrastructure remains blocked.
- This work is [PR #50](https://github.com/Bepoadewale/multi-tenant-ai-inference-platform/pull/50), stacked on open PR #49; required checks are pending. It does not authorize an AWS call or spend.

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
- Explained why the order matters, what belongs in containers, how to verify each
  layer, and which mismatches require stopping rather than improvising.
- Linked the manifest from the documentation index and marked Phase 3 as static
  preparation only.

## Validation

- Reviewed the manifest against the existing runbook, Terraform host configuration,
  Compose profile, and official-source research notes.
- `git diff --check` and documentation link checks are required before publication.
- No driver, CUDA Toolkit, Docker image, model, or Ansible package was downloaded or
  installed. No Terraform plan/apply, AWS API call, GPU operation, or spend occurred.

## Security and cost

The host has no inbound rules and uses Systems Manager. Container services are private
or loopback-bound. Versions are candidates and must be rechecked before installation.
All future billable work remains subject to the $25 ceiling, quota approval, exact-plan
approval, runtime cap, expiry, and teardown gates.

## Outstanding work

- Refresh package metadata signatures and exact package names on the reviewed AMI.
- Confirm Docker and Ansible controller versions and pin project-scoped automation.
- Perform the manual installation on one authorized L4, record actual outputs, then
  write Ansible roles from verified steps and run them twice.
- Confirm host memory/CPU fit for the full Compose stack before starting monitoring
  services.

## Acceptance status

**Static preparation only. The GPU software is not installed and no runtime has been
verified.**
