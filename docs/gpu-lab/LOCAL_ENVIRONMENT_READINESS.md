# Local environment readiness

**Checked:** 2026-11-27. This records workstation tooling, not an AWS or GPU host.

## Workstation tools verified

| Tool | Observed version/state | Ready for |
| --- | --- | --- |
| Operating system | macOS 25.6.0, Apple Silicon (`arm64`) | Local code, Terraform static checks, Docker Compose configuration, and GitHub work |
| AWS CLI | 2.32.6 | AWS CLI operations after an explicit identity/quota/authorization preflight |
| Terraform | 1.14.0 | Repository static Terraform validation; cloud plan/apply still requires its state and cost gates |
| Docker Compose | v2.40.3-desktop.1 | Local Compose rendering and CPU validation |
| Python | 3.12.12 | Project scripts and tests |
| GitHub CLI | Authenticated as `Bepoadewale` using the local keychain | PR and Actions operations |

## Not installed on this workstation

`ansible-playbook`, `nvcc`, `nvidia-smi`, and `nvidia-container-cli` are absent.
The workstation is Apple Silicon and is not the target NVIDIA L4 machine, so these
GPU host tools are not expected to work locally. Ansible is not yet part of this
repository's GPU configuration because the goal requires manual host installation
and learning first, then an Ansible implementation and repeatability check.

The GPU host must be prepared separately after quota and spending gates pass. The
current runbook covers the standard Ubuntu image, headless NVIDIA driver, CUDA
toolkit/compiler, Docker Engine, NVIDIA Container Toolkit, PyTorch GPU validation,
manual vLLM start, and only then the automation. Do not install a CUDA stack on the
workstation as a substitute for L4 validation.

## AWS and spending state

- No AWS mutation was performed during this readiness check.
- The owner reports sending an appeal through the existing AWS support case; no
  approval is confirmed in this record. The last documented applied G/VT quota is
  zero, so an L4 launch remains blocked.
- The project ceiling remains USD $25. Quota approval alone does not authorize an
  apply; the exact plan, current complete cost estimate, runtime, expiry, and teardown
  gates remain required.
- Do not store credentials, local AWS configuration, signed tokens, or Terraform state
  in this document or public Git.

## Next local setup steps

1. Continue code, docs, and static CI work without paid resources.
2. Before any AWS mutation, verify the expected account using the key-based profile as
   instructed by the project credential map, then recheck region, applied quota, G6
   availability, exact resources, current prices, and the reviewed saved plan. Do not
   print credentials.
3. Install Ansible only when its pinned project requirements and role are ready; use a
   project-scoped or isolated environment rather than changing unrelated tools.
4. After authorized provisioning, install and validate the GPU stack on the Ubuntu
   EC2 host through Systems Manager. This Apple Silicon workstation cannot prove host
   driver, CUDA, container, PyTorch, or L4 runtime compatibility.
