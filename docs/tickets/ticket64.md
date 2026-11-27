# Ticket 64 — guarded single-L4 host operations

## Objective

Prepare the remaining repeatable host commands before quota approval. After the
manual installation and first manual deployment lessons, an operator should be able
to configure the exact L4 host, deploy the isolated Compose profile, check real tenant
inference, run bounded evaluation/benchmark and a reversible Redis drill, and collect
sanitized evidence. No AWS provisioning or GPU execution is part of this ticket.

## Current state

Terraform and the GPU stack are prepared, but there were no single-command wrappers
for most post-provisioning host operations. The current AWS applied On-Demand G/VT
quota is recorded as zero, and the owner's appeal outcome is not confirmed. No L4
host or project AWS resource has been created.

## Research and design

- Follow the repository's single-host Docker Compose profile and local Ansible
  connection. Run these operations through Systems Manager Session Manager on the
  EC2 host; do not open public service ports or give CI AWS credentials.
- Validate the host against IMDSv2 identity, the expected account and exact instance
  ID, `us-east-1`, `g6.xlarge`, and exactly one visible NVIDIA L4 before host actions.
- Keep tenant tokens mode `0600`; never print prompt, response, token, `.env`, or raw
  logs in operator output or evidence.
- Bound configure (90 minutes), Compose build/start (45 minutes), readiness (20 minutes), evaluation (20
  minutes), benchmark (1–120 minutes, 60 by default), and each HTTP request. The
  Terraform expiry remains the independent limit if the session is interrupted.
- Keep host snapshots under a private path outside the repository. Record only
  sanitized hardware/software/service/readiness metadata.

## Implementation tasks

- [x] Add an IMDSv2/account/instance/region/type/L4 guard.
- [x] Add a bounded authenticated smoke for readiness, tenant spoof, identity/model
  denial, three short tenant requests, and one streamed request.
- [x] Add separately confirmed host wrappers for Ansible, Compose deploy, evaluation,
  and bounded direct/gateway benchmarks.
- [x] Add a reversible Redis outage drill that verifies the baseline, checks both
  gateways fail closed, restores Redis in an exit trap, and checks recovery.
- [x] Add private sanitized host evidence output and fake-based unit tests.
- [x] Validate the deployment `.env` file is a regular mode-`0600` file with unique
  keys, verified-format model digest/source commit, and a sufficiently long password.
- [x] Document the manual-to-automated handoff, confirmations, locations, timeouts,
  evidence limits, and Terraform-only teardown in the reproduction and batch guides.
- [x] Align Ansible validation with the hash-locked local environment and keep a CI
  fallback for the workflow that installs those same locked dependencies.
- [x] Run focused local fake-based tests, Ruff, shell parsing, static command previews,
  and documentation/link checks.
- [ ] Pass required pull request CI and resolve any findings.
- [ ] Obtain human review; do not merge without owner authorization.

## Acceptance criteria

- Local tests prove the host identity guard rejects mismatched account/instance,
  wrong GPU count/type, and insecure tenant token permissions.
- Smoke tests prove only synthetic traffic is sent and that output excludes tokens
  and response content.
- Evidence tests prove private permissions and repository-path refusal.
- Shell wrappers parse and refuse absent explicit confirmations. Static checks do not
  contact AWS, Docker, a model endpoint, or a GPU host.
- Operator guides accurately state the timeouts and limits and label host execution as
  pending until real L4 evidence exists.
- Existing CPU ONNX, EKS contract, Terraform destroy protections, and local clean-room
  validation remain unchanged.

## Validation and commands

Planned local-only checks:

```bash
.venv/bin/ruff check scripts/gpu_ec2_host_guard.py scripts/gpu_ec2_smoke.py \
  scripts/gpu_ec2_evidence.py gateway/tests/test_gpu_ec2_operator.py
PYTHONPATH=.:gateway/src .venv/bin/python -m pytest -q gateway/tests/test_gpu_ec2_operator.py
bash -n scripts/gpu-ec2-host-action.sh scripts/gpu-ec2-redis-outage.sh
make -n gpu-ec2-configure gpu-ec2-deploy gpu-ec2-smoke gpu-ec2-benchmark \
  gpu-ec2-evaluate gpu-ec2-incident-drills gpu-ec2-evidence
git diff --check
```

Pull request CI remains responsible for the repository's normal required checks.
Do not launch a separate manual clean-room cycle for this package; record the
workflow's local-E2E result and do not claim that it exercised EC2/GPU operations.

## Security and financial considerations

No AWS operation, model download, GPU request, or spend is required. Confirmation
variables only guard accidental invocation and do not authorize cloud spend. Host
identity is checked before actions. The Redis drill changes only the project Compose
service and restores it on exit. No Docker-wide cleanup is added. AWS teardown remains
the exact-plan, project-scoped Terraform process from the local workstation.

## Evidence collected

Sixteen focused tests passed; Ruff passed for all new Python files; both shell scripts
passed `bash -n`; Make previews showed only the intended wrapper commands; a local
negative check confirmed host configuration stops before metadata access without its
confirmation; `git diff --check` passed. Seventy-eight local Markdown links across
seven updated documentation files resolve. The first Ansible syntax attempt found
the executable absent. The Make target now prefers the hash-locked host venv;
installing `infrastructure/ansible/requirements.lock` with `--require-hashes` into
that ignored local venv allowed `make gpu-ansible-validate` to pass. GitHub CI is
pending. These results are local/static only. No L4 screenshot, metric, benchmark,
cost, inference result, or incident is claimed. The initial PR head passed all six
required checks in run `46081589301`, including one local E2E cycle; the later
deployment-preflight follow-up is not yet pushed and therefore needs updated-head CI.

## Outstanding work

- Complete required PR CI and address automated review.
- Obtain human review; do not merge without owner authorization.
- Await human review/merge authorization.
- Execute these commands only after quota is applied, a separate exact-plan/budget
  approval exists, and the user-authorized GPU batch begins.
