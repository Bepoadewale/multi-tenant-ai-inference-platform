# Ticket 77 — Test single-L4 expiry guardrails without AWS

## Objective

Test the infrastructure configuration that limits the GPU host's lifetime. A session
can end unexpectedly, so the host has two separate expiry paths: an Ubuntu timer and
an AWS EventBridge Scheduler task. This ticket checks the Terraform wiring before a
paid host exists.

## Current state

The GPU EC2 Terraform root defines a one-time UTC schedule, a scoped role that can
terminate one instance, a persistent `systemd` timer installed by cloud-init, EC2
shutdown-to-terminate behavior, encrypted root storage, and IMDSv2. The repository
had Terraform formatting and validation but no executable test for these expiry
relationships. A static assertion could miss HCL evaluation errors and a live apply
would be inappropriate for a cost-safety test.

## Design and changes

- Use Terraform's mocked AWS provider. The `terraform test` apply runs against
  in-memory mock resources and data; it does not use AWS credentials or create AWS
  resources.
- Assert the one-time schedule, exact UTC deadline, zero flexible window, target
  instance ID, least-privilege termination action and instance ARN, and restricted
  scheduler trust policy.
- Assert the host timer content, shutdown-to-terminate behavior, IMDSv2, encrypted
  storage, and delete-on-termination setting.
- Reject expiries more than 12 hours away or not expressed as an exact UTC `Z`
  timestamp.
- Run these tests through `make gpu-ec2-validate` and the existing CI Terraform
  validation path.

## Alternatives considered

- **Static text matching:** lower setup cost, but it does not evaluate HCL values or
  relationships among resources. Keep text checks only for rendered cloud-init text.
- **AWS apply and wait for the real deadline:** stronger runtime evidence, but it
  spends money and requires the unavailable/unauthorized project backend and host.
  Reserve this for the approved GPU batch.
- **Mocked Terraform test:** chosen because it evaluates the real configuration while
  avoiding cloud calls. It proves intended configuration only, not that AWS Scheduler
  executes at the deadline or that the Ubuntu timer runs after a reboot.

## Validation

`make gpu-ec2-validate` passes Terraform formatting, validation, and `terraform test
-no-color` (three tests). `make verify` passed Ruff, 202 repository tests (2 skipped),
the dependency audit, Compose/observability validation, GPU dry-run plans, and the
documentation-link checker. `make terraform-validate` passed bootstrap, EKS, and GPU
roots, including the mocked tests. `git diff --check` passed. The first full test
attempt in this new worktree could not collect gateway tests because the ignored
ONNX fixtures were absent; generating the normal tiny fixtures with
`scripts/create_model.py` resolved the setup issue. This was not a clean-room run.
The mocked apply creates no AWS resources. The official HashiCorp documentation says
provider mocking requires Terraform 1.7 or later; this root already requires
Terraform 1.10 or later. PR CI results will be recorded before acceptance.

## Security and financial boundary

The test uses fake account, instance, and role identifiers. Provider calls are mocked.
It contains no credentials and makes no network request at test time. No AWS resource,
GPU hour, model download, or project spend is involved.

## Remaining limitations

- Terraform tests do not prove EventBridge Scheduler's AWS-side delivery or IAM
  behavior.
- They do not prove cloud-init installs the unit on the selected Ubuntu AMI, the timer
  fires after reboot, or a guest shutdown terminates the EC2 instance.
- The real independent expiry and cleanup checks remain mandatory during the bounded
  authorized GPU batch.

## Acceptance status

Local mocked-provider coverage and full local verification pass. PR CI is pending. No
cloud or GPU result is claimed.

## References

- [Terraform provider mocking](https://developer.hashicorp.com/terraform/language/tests/mocking)
- [Terraform test language](https://developer.hashicorp.com/terraform/language/tests)
- [Terraform test command](https://developer.hashicorp.com/terraform/cli/commands/test)
