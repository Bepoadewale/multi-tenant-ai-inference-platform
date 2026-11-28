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
- [ ] CI checks pass for the latest rebased PR head. The earlier head passed Ansible,
  observability, manifests, Python, and supply-chain checks; the safety follow-up
  requires a fresh complete workflow.
- [ ] Human review; no merge without the owner's authorization.
- [ ] After manual installation on the approved host, run in check mode, review,
  configure, reboot through SSM if needed, rerun, and record second-run idempotency.
- [ ] Independently verify `nvidia-smi`, CUDA computation, Docker GPU access, and
  PyTorch computation on the L4.

## Rebase and validation follow-up — 2026-11-28

PR #57 was rebased from PR #56 head `3292af9` onto updated PR #56 head `b9d41f6`.
The shared execution journal conflicted; its current PR #56 state and the PR #57
Ansible preparation and review-fix history were retained. The original Ansible
validation command first failed because the isolated Ansible environment was not on
`PATH`. Rerunning with `PATH=/tmp/gpu-ansible-venv/bin:$PATH` passed the playbook
syntax check. Ruff and `git diff --check` also passed. No EC2 or GPU configuration ran.
The rebased head needs a new required CI run.

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
check mode. The updated playbook syntax check passed. The final PR head `4795f12`
passed all six required CI jobs, including one fresh-runner local end-to-end cycle,
in run `46045068200`.

## Review follow-up — defer unavailable hardware checks safely

Review found that forcing `lspci` to run during check mode still failed on a stock AMI:
Ansible previews installing `pciutils` but does not install it. The inventory command
and its L4 assertion now defer when check mode sees no existing `lspci`; a message says
the check will run during normal configuration after package installation. Review also
found that a reboot-required state skipped the NVIDIA command but still ran the GPU
assertion, preventing the operator from reaching the reboot checkpoint. The assertion
now shares the same reboot and package-change condition as the command.

After installing the pinned Ansible environment into the project `.venv`,
`make gpu-ansible-validate` and `git diff --check` passed. These are syntax and static
checks only; no Ubuntu host, GPU, package installation, or check-mode execution was
used. PR CI must validate the updated source head. Manual installation, post-reboot
GPU checks, and idempotency remain open for the approved L4 batch.

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
`infrastructure/ansible/README.md`. PR #57 is
[open and ready for review](https://github.com/Bepoadewale/multi-tenant-ai-inference-platform/pull/57).
