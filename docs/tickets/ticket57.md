# Ticket 57 — prepare repeatable L4 host configuration with Ansible

## Objective

Prepare a pinned Ansible playbook for the approved Ubuntu 24.04 single-L4 EC2 host
before GPU quota is granted. The operator must first complete the manual driver,
CUDA, Docker, and PyTorch learning pass. Then Ansible must reproduce the host package
and runtime configuration on the same host.

## Current state

- Work is on `codex/gpu-ansible-host-configuration`, stacked on PR #56 and therefore
  on PR #55. No change is made to `main`.
- AWS G/VT quota remains zero. No AWS resource, GPU instance, model, container image,
  or OS package was provisioned or installed on an EC2 host by this ticket. The small
  Ansible Python environment and wheels were kept under `/tmp` for local validation.
- No GPU result or package compatibility claim is made.

## Research and design

- Pin `ansible-core==2.21.6`, whose PyPI metadata requires Python 3.12 or newer.
  Universal SHA-256 dependency hashes are in `infrastructure/ansible/requirements.lock`.
- Pin date-reviewed NVIDIA driver, CUDA Toolkit, NVIDIA Container Toolkit, and Docker
  package versions in Ansible defaults. Source signing keys are pinned by SHA-256.
- Copy the existing 29-package, hash-locked PyTorch CUDA requirements into a separate
  host virtual environment, keeping its libraries out of vLLM's container.
- Run Ansible locally on the EC2 host through a Systems Manager Session Manager root
  shell. This avoids public SSH ingress and avoids giving Ansible AWS credentials.
- Refuse to configure any machine except Ubuntu 24.04 amd64 exposing exactly one L4;
  install `pciutils` only if the base image lacks the required read-only inventory
  command.
- Do not reboot automatically. A driver change is a manual reboot checkpoint, followed
  by a second Ansible run and independent GPU validation.

## Acceptance criteria

- [x] Pinned Ansible controller and universal hash lock.
- [x] Host playbook and role use exact reviewed version candidates and repository key
  checksums.
- [x] Role checks Ubuntu and the exposed L4 before changing the GPU stack, installing
  only `pciutils` first if the AMI has no `lspci` command.
- [x] Runtime configuration changes restart Docker only when needed.
- [x] PyTorch uses the existing Linux x86_64 hash lock in a separate Python 3.12
  environment and runs a synchronized one-GPU matrix check after reboot.
- [x] The role skips runtime verification while a reboot is pending and reports the
  operator checkpoint.
- [x] CI installs dependencies by hash and syntax-checks the playbook.
- [ ] CI checks pass for the latest PR head. The initial head passed Ansible,
  observability, manifests, Python, and supply-chain checks; its local end-to-end job
  was still pending when the safety follow-up was prepared.
- [ ] Human review; no merge without the owner's authorization.
- [ ] After manual installation on the approved host, run in check mode, review,
  configure, reboot through SSM if needed, rerun, and record second-run idempotency.
- [ ] Independently verify `nvidia-smi`, CUDA computation, Docker GPU access, and
  PyTorch computation on the L4.

## Commands and validation

Executed locally without AWS access:

```bash
uv pip compile infrastructure/ansible/requirements.in \
  --python-version 3.12 --universal --generate-hashes \
  --output-file infrastructure/ansible/requirements.lock
uv venv /tmp/gpu-ansible-venv --python python3.12
uv pip install --python /tmp/gpu-ansible-venv/bin/python \
  --require-hashes -r infrastructure/ansible/requirements.lock
PATH=/tmp/gpu-ansible-venv/bin:$PATH make gpu-ansible-validate
(cd infrastructure/ansible && ANSIBLE_CONFIG=ansible.cfg \
  ansible-playbook playbooks/configure-gpu-host.yml --list-tasks)
make verify
PATH=/tmp/gpu-ansible-venv/bin:$PATH make gpu-ansible-validate
git diff --check
```

`make verify` passed Ruff, 144 tests (2 skipped), the dependency audit, base and GPU
Compose checks, monitoring validation, and benchmark/evaluation/CUDA dry-run plans.
The Ansible syntax check and task-list command also passed. No task was run against a
host.

Final review added a conditional `pciutils` install for a stock AMI that lacks
`lspci`, and set read-only hardware/runtime inspection commands to run during Ansible
check mode. The playbook syntax check passed again; the updated source needs its own
CI run because these are execution-safety changes.

Syntax validation and `--list-tasks` parse the playbook; neither executes a task or
proves package/driver/GPU compatibility. One initial validation shell command ran
from the wrong working directory and could not resolve the Ansible binary. Rerunning
from the repository root with the temporary environment on `PATH` passed. An initial
system-wide `pip --dry-run` was refused by macOS's externally-managed-environment
protection; the hash-locked install succeeded inside the isolated `/tmp` virtual
environment. `make verify` first reported that this new worktree had no project
`.venv`; `make install` is now creating that project-scoped environment before the
full verification is rerun.

## Security, finance, and limitations

- No secrets, credentials, model content, or Terraform state are added.
- No SSH listener or public service port is configured.
- The $25 project cap and one-GPU constraint are unchanged; this work cost no AWS
  spend. A future GPU apply still requires quota approval, exact current cost, reviewed
  plan, runtime ceiling, expiry, teardown approval, and explicit authorization.
- Package versions and key fingerprints/checksums are dated candidates. Refresh them
  and verify signed APT metadata, target kernel headers, package dependencies, driver
  compatibility, and vLLM image requirements before launch.
- The role has not executed on an EC2 machine. CI syntax checks cannot prove runtime
  behavior or idempotency.

## Evidence and next step

Research details are in `docs/gpu-lab/RESEARCH_NOTES.md`; manual order and runtime
verification are in `docs/gpu-lab/GPU_BATCH_RUNBOOK.md`; role behavior is in
`infrastructure/ansible/README.md`. The next step is to complete static CI and human
review while continuing non-billable GPU preparation.
