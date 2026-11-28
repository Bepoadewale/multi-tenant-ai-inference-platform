# Ticket 81 — Validate the exact saved GPU plan before apply

**Status:** implementation prepared in PR #81; no AWS operation.

## Objective

Make the Phase 2 plan review actionable and fail closed. The plan wrapper should
reject any saved plan outside the one-instance GPU scope, print a small summary that
does not expose plan contents, and apply should re-check the same saved plan bytes
before Terraform changes infrastructure.

## Current state

The Terraform wrapper previously printed a SHA-256 digest and left the operator to
inspect the binary saved plan. A matching digest protects against changing the file
after review, but does not itself prove the contents are within project boundaries.
The apply wrapper also did not repeat a structural review immediately before apply.

## Design and implementation

- `scripts/gpu_ec2_plan_summary.py` accepts Terraform's JSON rendering on standard
  input. It requires the exact 14 managed resource addresses and create-only actions.
- It verifies one `g6.xlarge`, the reviewed AMI and `us-east-1` availability zone,
  termination on guest shutdown, encrypted 100–120 GiB gp3 root storage, required
  IMDSv2 settings, SSM's managed policy, required project tags on every taggable
  resource, no inbound security-group rules, only TCP 80/443 IPv4 egress, and the
  exact one-time UTC expiry. Unexpected Terraform JSON shapes fail closed.
- It prints resource addresses and bounded facts only. Terraform JSON can contain
  user data and other private values; the wrapper pipes it directly into the validator
  and does not print or save the JSON output.
- `gpu-ec2-plan.sh` validates the newly created saved plan before printing its digest.
- `gpu-ec2-apply.sh` requires the same reviewed AMI/AZ/expiry inputs and revalidates
  the exact checksum-matched file after AWS preflight and before `terraform apply`.
- Fake Terraform integration tests exercise both wrappers. An unsafe plan must stop
  before apply, and a private sentinel in user data must not appear in wrapper output.

## Acceptance criteria

- [x] Reject extra or missing managed resources and non-create actions.
- [x] Reject a different accelerator, AMI, AZ shape, disk, metadata policy, tags,
  network rule, SSM attachment, or expiry.
- [x] Keep raw plan JSON and sensitive values out of command output.
- [x] Bind the apply operation to the reviewed plan digest and repeat structural
  validation before Terraform apply.
- [x] Cover safe and unsafe plans using unit tests and fake CLI wrapper tests.
- [ ] Pass final PR checks on the published head and receive owner review.

## Commands and validation

The initial local run used:

```bash
uv run --with pytest --with ruff --no-project --python 3.12 \
  pytest -q gateway/tests/test_gpu_ec2_plan_summary.py gateway/tests/test_gpu_ec2_scripts.py
```

The first wrapper integration attempt failed because the fake Terraform executable
looked only for `show` as its first argument, while the real command includes
`-chdir=<root>` before `show`. The test output was empty JSON input. The fake now
recognizes `show -json` anywhere in the argument vector, matching the actual wrapper.
A later failure was an expected-message mismatch after tag validation was broadened to
all taggable resources; the assertion was updated to the common, accurate message.
The corrected focused run first passed 28 tests. Negative cases were then added for
the IMDS hop limit, malformed AZ shape, and malformed Terraform JSON. One temporary
test-edit error placed a redaction assertion in the wrong test, producing a `NameError`;
the assertion was moved back to the test that owns the subprocess result. The final
focused run passed 33 tests.
Current validation results are recorded in the execution journal and evidence manifest.

Additional checks:

```bash
uv run --with ruff --no-project --python 3.12 ruff check \
  scripts/gpu_ec2_plan_summary.py \
  gateway/tests/test_gpu_ec2_plan_summary.py \
  gateway/tests/test_gpu_ec2_scripts.py
bash -n scripts/gpu-ec2-plan.sh scripts/gpu-ec2-apply.sh
git diff --check
make gpu-docs-validate
```

## Security, financial boundaries, and limitations

This validator reviews a saved plan locally; it does not create the missing remote
state backend or make an AWS plan apply-ready. Fake plans do not prove the live
provider emits identical JSON or that the account has capacity. A human must still
review the full exact plan and cost, and separate apply authorization remains
required. The apply-time JSON is kept in a process pipe; it is not committed or
retained as evidence. No credentials, prompts, private model artifacts, AWS resource,
GPU instance hour, or spend is part of this package.

## Evidence and outstanding work

- Unit tests reject unsafe fixture plans and ensure the CLI summary omits user data.
- Wrapper tests verify plan and apply profile propagation, summary privacy, saved-plan
  revalidation, and refusal to apply a plan with an unapproved instance type.
- Terraform's actual AWS JSON shape remains to be confirmed by a future exact saved
  plan after the backend, budget recipient, quota, capacity, and authorization gates
  are met.
- PR #81 must remain stacked on #80; neither this ticket nor its checks authorize a
  merge or cloud mutation.
