# GPU host Ansible configuration

This playbook prepares the one approved Ubuntu 24.04 L4 host after the manual
installation lesson has been completed. It installs a headless NVIDIA driver,
CUDA Toolkit compiler, Docker Engine, and NVIDIA Container Toolkit. It does not
provision AWS resources, download a model, start inference, change the security
group, or reboot the machine. It also installs the project's hash-locked PyTorch CUDA
environment into an isolated Python 3.12 virtual environment.

The play runs against the local machine. Run it from an EC2 shell opened through
AWS Systems Manager Session Manager after checking that you are on the project
host. Do not run it on the Mac workstation: the `local` connection would configure
the workstation running Ansible.

## What it changes

- Checks Ubuntu 24.04 amd64 and exactly one L4 device exposed by `lspci`.
- Installs matching kernel headers, build tools, and repository helpers.
- Adds the official NVIDIA CUDA and NVIDIA Container Toolkit repositories using
  pinned key checksums and package versions.
- Adds the official Docker repository and installs pinned Engine and Compose
  packages.
- Configures Docker's NVIDIA runtime and restarts Docker only if its daemon file
  changed.
- Checks the driver, `nvcc`, Docker runtime, and pending reboot state.
- After reboot, runs a small synchronized matrix multiplication through the separate
  PyTorch environment and confirms exactly one L4 is visible.

Package and repository key values are dated candidates, not a promise that those
versions will still be available. Before any paid batch, refresh the package index,
verify signatures and compatibility, then review the exact changes. The role does
not automatically reboot; the operator must use the documented Session Manager
reboot step and rerun the playbook.

## Validate without a GPU

From the repository root, in a Python 3.12 environment with the locked Ansible
dependencies installed:

```bash
cd infrastructure/ansible
ANSIBLE_CONFIG=ansible.cfg ansible-playbook playbooks/configure-gpu-host.yml --syntax-check
```

Syntax checking parses the playbook but does not run tasks, fetch packages, access
AWS, or prove the packages work with an L4. CI runs this check.

## Run on the EC2 host after manual setup

First complete the manual steps in `docs/gpu-lab/GPU_BATCH_RUNBOOK.md`. Then copy the
repository checkout and run the following through Session Manager, as root:

```bash
cd /path/to/multi-tenant-ai-inference-platform/infrastructure/ansible
python3 -m venv .venv
.venv/bin/python -m pip install --require-hashes -r requirements.lock
ANSIBLE_CONFIG=ansible.cfg .venv/bin/ansible-playbook \
  playbooks/configure-gpu-host.yml --check --diff
```

Review the check-mode report. If the proposed changes match the reviewed package
matrix, run it once without `--check`, reboot manually if the play reports a pending
reboot, reconnect, and run it again. The second run should report no package or
configuration changes. `--check` is not a complete simulation for every APT or
external command, so it does not replace review or the cost/runtime gates.

Ansible's return to `changed=0` is necessary but not sufficient: verify `nvidia-smi`,
`nvcc --version`, `docker info`, and a digest-pinned CUDA container as described in
the runbook. The playbook includes a small PyTorch GPU computation, but it has not yet
run on an EC2 host.
