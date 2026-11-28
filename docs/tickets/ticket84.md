# Ticket 84 — Verify the single-L4 network topology in the saved plan

**Status:** Implementation is prepared on `codex/gpu-network-plan-review`, stacked on PR #83. The focused plan and wrapper suites pass 43 tests locally; CI and owner review remain pending. No AWS operation.

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
- [x] The focused plan and shell-wrapper suites pass (**43 tests**); Ruff and
  `git diff --check` pass.
- [ ] A real AWS-provider plan confirms the configuration-expression shape when the
  authorized backend and cost gates permit it.
- [ ] Publish PR, pass all required CI, and receive owner review. No merge or apply
  is authorized by this ticket.

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
address assignment, Systems Manager connectivity, or that AWS accepts the plan.

## Security, cost, and remaining work

No AWS API call, Terraform plan or apply, GPU instance, Docker build, model download,
or project spend occurred. Before applying, inspect the actual saved plan and verify
the route and references against the provider's output. The internet route allows
outbound package/model retrieval from the public subnet; inbound access remains
blocked and internal services remain loopback-bound.
