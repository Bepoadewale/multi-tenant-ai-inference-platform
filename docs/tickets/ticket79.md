# Ticket 79 — Make GPU resource ownership tags explicit

## Objective

Make project resource ownership, expiry, cost scope, and data classification visible
and testable in the standalone GPU Terraform root before any infrastructure is created.

## Current state

The AWS provider configures default tags, but its mock provider does not merge those
defaults into each resource's configured `tags` field. The existing tests therefore
could not prove the full metadata each resource would receive. Explicit tag maps also
make the intent easier to inspect in the exact saved plan.

## Changes

- Create one shared explicit map with project, environment, management method, owner,
  cost scope, expiry, data class, and Name values.
- Apply it to every resource type in this GPU root whose pinned AWS provider schema
  exposes tags, including network resources, the host, root volume, IAM resources,
  and the Scheduler schedule group.
- Add a mocked-provider Terraform test that compares normalized tag values on all 11
  taggable resource blocks and checks the expected project values.
- Include this ticket in the existing local/CI documentation-link checker.

## Research and limitation

The locked AWS provider version is 5.100.0. Its resource schema rejects a `tags`
argument on `aws_scheduler_schedule`; the individual schedule cannot receive explicit
tags through this provider. The schedule group is tagged, the schedule uses the exact
project-specific name, and both remain managed by the dedicated GPU root. No AWS
mutation was performed to confirm tag propagation in a live account.

## Validation

Using Terraform 1.14.0 and the repository-locked AWS provider, GPU-root formatting and
`terraform validate` pass. `terraform test -no-color` passes all five cases: three
expiry tests, one network test, and the new resource-tag case. The tests use the
provider mock and make no AWS API calls. `git diff --check` and the GPU documentation
link checker are also required before publication. Full CI on the published PR head is
the remaining validation step.

## Failed approaches retained

- Adding `tags` directly to `aws_scheduler_schedule` failed validation because the
  pinned provider schema does not expose that argument; it was removed and recorded
  as a limitation.
- Directly comparing the provider's typed tag object with a `map(string)` local failed
  Terraform type equality. Comparing `jsonencode` output normalizes these equivalent
  values and the mocked test passes.

## Security and cost

This change improves ownership and cleanup discovery in source and planned resource
configuration. It does not change network access, grant permissions, create resources,
or prove live AWS cleanup. No credentials, cloud API calls, GPU hours, or project spend
were involved.

## Evidence and acceptance

Local evidence is static and mocked; it does not establish AWS tag propagation or
absence of untagged resources. Review the passing local validation and final PR checks
at [PR #79](https://github.com/Bepoadewale/multi-tenant-ai-inference-platform/pull/79)
when available.
