# Ticket 84 — Verify the single-L4 network topology in the saved plan

**Status:** [PR #84](https://github.com/Bepoadewale/multi-tenant-ai-inference-platform/pull/84) is restacked on refreshed PR #83 head `142d0f3`. Published head `4a4f542` passed all six CI jobs in run `46172702249`. The branch passes 67 focused tests, 12 mocked Terraform cases, Ruff, documentation validation across 35 files, and `git diff --check`. Owner review remains pending. No AWS operation.

## Objective

Check that the resources in the initial GPU plan form the intended isolated network:
one project VPC, a single public subnet, one route through the project internet
gateway, one route-table association, and an instance attached only to that subnet
and security group.

## Research and design

HashiCorp's official [Terraform JSON output format](https://developer.hashicorp.com/terraform/internals/json-format)
shows planned resource values and parsed configuration expressions. Resource IDs are
often unknown until apply, so the validator checks known network settings in planned
values and exact resource references in configuration expressions. The existing
guard already checks that the security group has no ingress and only TCP 80/443
egress; this ticket closes the separate topology-binding gap.

## Implementation

- Require the project's reviewed VPC CIDR and DNS settings.
- Require the single subnet CIDR, selected availability zone, and public address
  assignment needed for the SSM-only no-NAT lab.
- Require the EC2 instance plan itself to enable a public IP, because enabling
  public addresses on the subnet does not prove this instance will receive one.
- Require one default route to the project internet gateway.
- Verify that the internet gateway, subnet, route table, and security group reference
  the GPU VPC.
- Verify that the route-table association references this subnet and route table.
- Verify that the GPU instance references this subnet and security group.
- Reject resource-reference substitutions in fixture tests.

## Acceptance criteria

- [x] The saved-plan fixture passes with the approved VPC and subnet topology.
- [x] Negative tests reject a changed subnet range and bindings to a different VPC,
  subnet, route table, or gateway.
- [x] The focused plan and shell-wrapper suites pass (**44 tests**); Ruff,
  `make gpu-docs-validate` (35 files), and `git diff --check` pass after the
  instance-level public-IP check.
- [x] All six required CI jobs passed on earlier implementation head `724c45a` in run
  `46147292091`.
- [ ] A real AWS-provider plan confirms the configuration-expression shape when the
  authorized backend and cost gates permit it.
- [x] Publish the public-IP follow-up and pass all required CI on earlier head `8349510` in run
  `46148953601`.
- [x] Publish the restacked branch and pass all required CI on head `798b2e8` in run
  `46171879043`.
- [ ] Receive owner review. No merge or apply is authorized by this ticket.

## Validation

```bash
PYTHONPATH=.:gateway/src python -m pytest \
  gateway/tests/test_gpu_ec2_plan_summary.py \
  gateway/tests/test_gpu_ec2_scripts.py -q
ruff check scripts/gpu_ec2_plan_summary.py \
  gateway/tests/test_gpu_ec2_plan_summary.py \
  gateway/tests/test_gpu_ec2_scripts.py
git diff --check
```

The tests validate fixture behavior only. They do not prove live routing, public
address assignment, Systems Manager connectivity, or that AWS accepts the plan. The
first follow-up test run exposed an omitted public-IP value in the separate fake CLI
fixture; that fixture now includes the same reviewed setting as the plan-summary
fixture, and the focused suite passes.

## Security, cost, and remaining work

During the original static validation, no AWS API call, Terraform plan or apply, GPU
instance, Docker build, model download, or project spend occurred. A later, separate
read-only AWS reconciliation is recorded below. Before applying, inspect the actual
saved plan and verify the route and references against the provider's output. The internet route allows
outbound package/model retrieval from the public subnet; inbound access remains
blocked and internal services remain loopback-bound.


## Current AWS gate reconciliation (2026-11-28 15:06 UTC)

A fresh read-only AWS CLI check confirms the existing quota request is closed with a
desired value of 4.0 vCPUs and the applied On-Demand G/VT quota is 4.0. It is enough
on paper for one `g6.xlarge`, but does not reserve availability-zone capacity. Exact
project-tag, EC2, state-bucket, lock-table, and project-Budget lookups found no matching
resources. The account has no Billing alternate contact. A different account Budget
was listed, but its coverage of this project is not established and it is not relied
upon. No Terraform plan/apply or resource change occurred.

The remaining gates are a valid private notification recipient, reviewed bootstrap
saved plan, remote state and lock, exact GPU-root saved plan, refreshed total cost and
capacity, expiry and teardown review, and separate apply authorization. This note is
read-only evidence and does not authorize cloud spending.

## Restack validation (2026-11-28 17:32 UTC)

PR #84 has been rebased onto refreshed PR #83 head `142d0f3`. On the resulting local
tree, the saved-plan, wrapper, benchmark-runner, language-model evaluation, and model
artifact tests pass (**67 tests**), Ruff passes for the changed Python files,
`make gpu-docs-validate` checks 35 Markdown files, and `git diff --check` passes.
Restacked head `798b2e8` passed all six required CI jobs in run `46171879043`. The
status follow-up head `4a4f542` also passed all six, including local-e2e, in run
`46172702249`. No AWS plan, apply, infrastructure, GPU operation, model download, or
spend occurred during this restack.
