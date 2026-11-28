# Ticket 82 — Validate the GPU expiry schedule target

**Status:** [PR #82](https://github.com/Bepoadewale/multi-tenant-ai-inference-platform/pull/82) is open on PR #81; implementation head `3c50b00` passed all six required jobs in run `46143239396`. This documentation follow-up needs CI; no AWS operation.

## Objective

Verify the saved Terraform plan schedules the exact project-scoped one-time action
that terminates the single GPU EC2 instance. A matching deadline alone does not prove
that the schedule will shut the host down.

## Current state

PR #81's validator checked the schedule's UTC expression, enabled state, one-time
flexible window, and date. It did not inspect the saved plan's schedule group or
target action. A plan could therefore pass the summary while invoking a different AWS
operation.

## Design and implementation

- Require the schedule name and group to match the project's exact GPU environment.
- Require the target ARN to be EventBridge Scheduler's AWS SDK integration for
  `ec2:TerminateInstances`.
- Keep the exact UTC deadline, enabled state, and flexible time window disabled.
- Print the operation in the summary so a human reviewer can see what the expiry does.
- Add negative fixtures for an unrelated group and a Lambda invocation target.

## Acceptance criteria

- [x] Accept a plan with the project group and EC2 termination action.
- [x] Reject a schedule in an unrelated group.
- [x] Reject a schedule invoking a different AWS action.
- [x] Keep the exact reviewed deadline and one-time schedule checks.
- [x] Pass the focused plan and wrapper tests, Ruff, and diff checks.
- [x] Publish PR #82 on top of #81 and pass all six checks on implementation head `3c50b00`.
- [ ] Pass CI on the final documentation head.
- [ ] Receive owner review; no merge or AWS apply is authorized by this ticket.

## Validation and troubleshooting

```bash
uv run --with pytest --with ruff --no-project --python 3.12 \
  pytest -q gateway/tests/test_gpu_ec2_plan_summary.py gateway/tests/test_gpu_ec2_scripts.py
uv run --with ruff --no-project --python 3.12 ruff check \
  scripts/gpu_ec2_plan_summary.py \
  gateway/tests/test_gpu_ec2_plan_summary.py \
  gateway/tests/test_gpu_ec2_scripts.py
git diff --check
```

The initial edit to the schedule condition missed a boolean `or`; the syntax review
found it before the test run, and it was fixed. The focused suite then passed 35 tests
and Ruff reported no issues.

## Security, cost, and evidence limits

The checked fixture represents the expected Terraform JSON shape, and the project's
Terraform mock test separately checks the configured expiry role and one-time
schedule. These tests do not prove the actual AWS provider's plan JSON shape, that
EventBridge Scheduler fires, or that an EC2 instance terminates. A real plan and
controlled expiry drill remain part of the approved GPU lifecycle. No AWS calls,
Terraform mutations, GPU execution, model downloads, or spend occurred.
