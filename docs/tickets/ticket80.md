# Ticket 80 — Test GPU Terraform input limits

## Objective

Make the single-L4 environment's cost and architecture boundaries executable. A bad
input must fail during planning before Terraform can propose a broader deployment.

## Changes

Add mocked-provider Terraform plan cases that require the GPU root to reject:

- `g6.2xlarge`, which is outside the initial 4-vCPU experiment;
- `g5.xlarge`, which uses an unapproved accelerator family;
- root disks below 100 GiB or above the 120 GiB planning maximum;
- a region other than `us-east-1`;
- a project name outside the existing repository;
- a malformed AMI identifier.

The tests use fake identity/resource data and do not call AWS. They extend the existing
expiry, network, and tagging tests; the GPU root's full mocked suite now contains 12
cases.

## Failed approach and correction

The first wrong-region case also used a `us-west-2` Availability Zone. That correctly
failed the separate `availability_zone` validation before it reached the region check,
so Terraform reported an unexpected failure. The corrected test keeps a syntactically
valid `us-east-1a` zone while setting only `aws_region` to `us-west-2`; now the
`aws_region` validation is the sole expected failure. This preserves evidence about
the region guard rather than accidentally testing only the zone guard.

## Validation

Terraform 1.14.0 `fmt -check -recursive`, `validate`, and the 12-case `terraform test
-no-color` pass locally. The documentation link checker and CI remain to be run on the
published PR. The tests prove variable validation, not AWS capacity, instance type
availability, or any deployed resource state.

## Security and financial boundary

The package adds no resources or permissions. It uses mocked Terraform execution only;
no AWS credential, API call, GPU, Docker image, or spend is involved. The instance
family and storage bounds keep the planned initial experiment within its stated shape,
but the complete $25 cost gate and exact saved-plan review remain separately required.

## Acceptance status

On refreshed local head `a81c4ca`, Terraform formatting, validation, all 12 mocked
cases, `make gpu-docs-validate` across 31 Markdown files, and `git diff --check` pass.
The older remote PR #80 head `cf25f6d` passed all six jobs in run `46139054282`; that
run does not cover the refreshed branch. Publication and fresh CI are pending. This is
static/local evidence only; no AWS or GPU behavior is claimed.
