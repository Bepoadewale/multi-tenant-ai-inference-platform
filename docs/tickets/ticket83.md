# Ticket 83 — Bind the GPU expiry schedule to this project

**Status:** Implementation is prepared on `codex/gpu-expiry-binding-review`, stacked on PR #82. Focused tests pass locally; pull request and required CI are pending. No AWS operation.

## Objective

Make the saved-plan review verify that the one-time termination schedule uses the
project's expiry role and references the project's single GPU instance. A correct
schedule name and `TerminateInstances` action alone do not prove those bindings.

## Research and design

Terraform's official [JSON output format](https://developer.hashicorp.com/terraform/internals/json-format)
separates planned values from configuration expressions. EC2 IDs and generated role
ARNs are unknown before apply, so their values may be omitted from `change.after`.
The configuration section retains references to the resources used in each
expression. The validator now checks these references and refuses a plan with a
missing, malformed, or mismatched binding.

This check complements, rather than replaces, Terraform mock tests and human review
of the private saved plan. It does not prove AWS Scheduler delivery or actual
termination.

## Implementation

- Require the schedule's configured target ARN to be the EC2 `TerminateInstances`
  integration.
- Require the configured target role to reference `aws_iam_role.expiry`.
- Require the configured target input to reference `aws_instance.gpu.id` and no other
  resource.
- Require the expiry IAM policy's role and resource expressions to reference the
  matching project role and instance.
- Fail closed when Terraform configuration expressions are absent or ambiguous.
- Add fixture tests for a target bound to another role or instance.

## Acceptance criteria

- [x] The known-safe fixture passes, and saved-plan private user data stays out of
  the printed summary.
- [x] A schedule bound to another IAM role is rejected.
- [x] A schedule input bound to another instance is rejected.
- [x] An expiry policy expression bound to another instance is rejected.
- [x] Focused plan tests pass (24 tests), Ruff passes, and `git diff --check` passes.
- [ ] Validate the expression shape against a real AWS-provider plan when the
  authorized remote backend and GPU quota gates permit a plan.
- [ ] Publish the PR, pass all required CI, and receive owner review. No merge or
  AWS apply is authorized by this ticket.

## Validation commands and results

```bash
PYTHONPATH=.:gateway/src python -m pytest gateway/tests/test_gpu_ec2_plan_summary.py -q
ruff check scripts/gpu_ec2_plan_summary.py gateway/tests/test_gpu_ec2_plan_summary.py
git diff --check
```

The first local attempt used `python`, which is not installed as a command on this
workstation. `python3` is Python 3.14 but does not have pytest installed. The focused
suite then ran with a pre-existing local validation environment: **24 passed**;
Ruff and the diff check passed. No project-local virtual environment was created.

## Security, cost, and evidence limits

The fixture models Terraform's documented configuration-expression reference shape.
It does not contain an AWS account identifier, credential, real saved plan, or
provider response. The next authorized live plan should confirm this expression
shape before any apply. No AWS call, Terraform operation, GPU runtime, model download,
Docker build, or project spend occurred.
