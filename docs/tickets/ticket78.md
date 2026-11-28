# Ticket 78 — Test single-L4 network boundaries without AWS

## Objective

Keep the GPU instance unreachable through unsolicited inbound network traffic and
limit its internet egress to the package and artifact ports this lab requires. Test
these boundaries in Terraform without launching AWS resources.

## Current state

The dedicated EC2 root has a security group with no ingress rules and two outbound
TCP rules: port 443 for Systems Manager, registries, and artifact download, and port
80 for Ubuntu mirrors that do not offer TLS. The EC2 host has a public address to
avoid a NAT Gateway; the security group accepts no incoming connection, and operator
access is intended to use Systems Manager Session Manager. The Terraform root had no
executable assertion that guarded this shape.

## Design and changes

- Add a mocked-provider Terraform test for the real GPU EC2 configuration.
- Require zero ingress rules and exactly two outbound rules.
- Require the rules to be TCP 80 and TCP 443, each with the documented public IPv4
  destination; reject other protocol/port combinations.
- Verify that the single `g6.xlarge` resource uses the project security group and
  selected availability zone.
- Run the test in the existing `make gpu-ec2-validate` path used by Terraform CI.

## Alternatives considered

- A text search in HCL would not verify the evaluated resource fields or that the
  instance references this security group.
- A live AWS scan would be stronger evidence of deployed behavior, but there is no
  approved infrastructure to scan and this package must remain non-billable.
- The selected mock test validates configuration only. A real security-group review
  and Session Manager check remain required after authorized provisioning.

## Validation

The previous PR #78 implementation head `5c3bd12` passed six CI jobs in run
`46135887060`; this is historical after the current restack. PR #78's intermediate
head `179240c` also passed all six jobs in run `46168796270`. The branch is now
restacked onto PR #77 follow-up head `58165d1`, which records the local cancellation
demo isolation fix after the earlier local-e2e failure. On the refreshed stack, the
network test and three expiry tests pass with
`terraform test -no-color` using the AWS mock provider. `make gpu-docs-validate`
checked 29 Markdown files after restacking, and `git diff --check` passed. Before this restack,
`make verify` passed Ruff, 202 repository tests (2 skipped),
the dependency audit, Compose and observability validation, GPU dry-run plans, and
Markdown-link validation. `make terraform-validate` passed the bootstrap, EKS, and GPU
roots, including all four mocked Terraform tests. `git diff --check` passed. The
observability validator pulled four digest-pinned images; they were pruned after the
run, and no containers or image tags remained locally. This was not a clean-room run.
Fresh CI for this restacked head is pending. No new AWS operation or GPU validation
occurred.

AWS documents that security groups begin with no inbound rules, are stateful, and
allow return traffic for connections initiated by the instance. The chosen policy
therefore needs no inbound ephemeral-port rules for package or model downloads. See
[EC2 security groups](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-security-groups.html)
and [VPC security group rules](https://docs.aws.amazon.com/vpc/latest/userguide/security-group-rules.html).

## Security and financial boundary

The test uses fake identifiers and the AWS provider is mocked. It does not contact
AWS or require credentials. No resource, GPU hour, model download, or project spend
is involved.

## Limitations

- This checks Terraform's planned security-group and instance configuration, not the
  effective AWS network after provisioning.
- Egress remains open to any public IPv4 address on TCP 80 and 443. The environment
  avoids a NAT Gateway, and package/model hosts are not a fixed allowlist.
- A public address is not an inbound access path by itself; the zero-ingress rule is
  the boundary. Session Manager and the instance role still require live verification.

## Acceptance status

Four mocked Terraform tests pass on the refreshed source. Prior PR #78 CI passed, but
that result predates the updated base; current-head CI remains pending. No cloud or GPU
result is claimed.
