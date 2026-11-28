# Local environment readiness

**Checked:** 2026-11-27. This records workstation tooling, not an AWS or GPU host.

## Workstation tools verified

| Tool | Observed version/state | Ready for |
| --- | --- | --- |
| Operating system | macOS 25.6.0, Apple Silicon (`arm64`) | Local code, Terraform static checks, Docker Compose configuration, and GitHub work |
| AWS CLI | 2.32.6 | AWS CLI operations after an explicit identity/quota/authorization preflight |
| Terraform | 1.14.0 | Repository static Terraform validation; cloud plan/apply still requires its state and cost gates |
| Docker Engine / Buildx / Compose | 29.0.1 / v0.29.1-desktop.1 / v2.40.3-desktop.1; daemon responds | Local image build, OCI manifest inspection, Compose rendering, and CPU validation |
| Python runtimes | `python3` resolves to 3.14.0; `python3.12` is available as 3.12.12, and `python3.13` as 3.13.9 | Use the explicit Python 3.12 executable for project locks and checks that target CPython 3.12. Do not assume the default `python3` selects the project runtime. |
| uv | 0.9.15 | Generate a target Linux/Python 3.12 hash lock; no CUDA packages were installed locally |
| GitHub CLI | Authenticated as `Bepoadewale` using the local keychain | PR and Actions operations |

The project `.venv` was absent at the start of the 2026-11-27 PR #53 follow-up.
Running `make install` created it with Python 3.12.12 and installed the repository's
development dependencies and generated local ONNX fixtures. The subsequent `make
verify` passed; details are in the execution journal. This is workstation readiness,
not GPU readiness.

## Not installed on this workstation

`ansible-playbook`, `nvcc`, `nvidia-smi`, and `nvidia-container-cli` are absent.
The workstation is Apple Silicon and is not the target NVIDIA L4 machine, so these
GPU host tools are not expected to work locally. The repository now includes a
hash-locked Ansible controller and a syntax-checked host role. It is designed to run
locally on the EC2 host through Session Manager after the manual installation lesson;
do not run the local-connection playbook on this Mac.

The GPU host must be prepared separately after the Budget, remote-state, exact-plan,
cost, and apply-authorization gates pass. The
current runbook covers the standard Ubuntu image, headless NVIDIA driver, CUDA
toolkit/compiler, Docker Engine, NVIDIA Container Toolkit, PyTorch GPU validation,
manual vLLM start, and only then the automation. Do not install a CUDA stack on the
workstation as a substitute for L4 validation.

## AWS and spending state

The local command-line tools were rechecked on 2026-11-27 at 19:20 UTC: Python
3.12.12, AWS CLI 2.32.6, Terraform 1.14.0, Docker client/server 29.0.1, and Compose
2.40.3 are available. `ansible-playbook`, `nvcc`, `nvidia-smi`, and
`nvidia-container-cli` remain absent on this Apple Silicon workstation, as expected;
the hash-locked Ansible controller runs on the future EC2 host, and NVIDIA tools are
installed there only after an authorized GPU launch.

- No AWS mutation was performed during this readiness check.
- The 2026-11-27 workstation inventory below is historical. A fresh read-only AWS CLI
  check on 2026-11-28 confirmed the expected account and `4.0` applied On-Demand G/VT
  vCPUs; the owner reports AWS approved the request. The request-history API still
  says `CASE_OPENED`. The numeric quota is sufficient on paper for one `g6.xlarge`,
  but does not reserve capacity. No L4 launch has occurred; the Budget recipient,
  remote-state, exact-plan/cost, expiry, and apply-authorization gates remain.
- The project ceiling remains USD $25. Quota approval alone does not authorize an
  apply; the exact plan, current complete cost estimate, runtime, expiry, and teardown
  gates remain required.
- Exact project/environment tag queries at 19:19 UTC found no active GPU instance and
  no project-tagged GPU resources in `us-east-1`. This does not rule out unrelated,
  untagged, or differently tagged resources.
- Do not store credentials, local AWS configuration, signed tokens, or Terraform state
  in this document or public Git.

The read-only GPU-stack research pass at 19:23 UTC queried the official NVIDIA CUDA,
NVIDIA Container Toolkit, and Docker APT package indexes. Every candidate version
pinned in the Ansible defaults was present, and the CUDA keyring package plus Docker
and NVIDIA Container Toolkit signing-key bytes matched the SHA-256 values already
recorded in the repository. This checks availability and artifact identity only; the
future host must still validate signed APT metadata and current compatibility against
the launched Ubuntu AMI and kernel. No packages were installed.

## Next local setup steps

1. Continue code, docs, and static CI work without paid resources.
2. Before any AWS mutation, verify the expected account using the key-based profile as
   instructed by the project credential map, then recheck region, applied quota, G6
   availability, exact resources, current prices, and the reviewed saved plan. Do not
   print credentials. The 2026-11-28 check found applied quota `4.0` vCPUs, while the
   request record remains `CASE_OPENED`. G6 offerings exist in several us-east-1 AZs,
   but do not guarantee capacity. The project state bucket, lock table, and budget are
   absent.
3. The hash-locked Ansible requirements and host role are prepared for the future EC2
   host. Do not run its local-connection playbook on this workstation.
4. After authorized provisioning and the manual learning pass, run Ansible on the Ubuntu
   EC2 host through Systems Manager. This Apple Silicon workstation cannot prove host
   driver, CUDA, container, PyTorch, or L4 runtime compatibility.
