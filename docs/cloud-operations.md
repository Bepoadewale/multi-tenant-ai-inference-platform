# Cloud Operations

The cloud pilot is designed to be safe, temporary, and Terraform-managed. It is not
started by default because it would create billable AWS resources.

## What has happened

An authenticated AWS Terraform plan review ran on 2026-10-08. It proposed the state
guardrails and private runtime, but did not apply anything. No AWS resource, state
bucket, cluster, image, or billing record was created by this repository.

## What an operator would do next

1. Review the Terraform plan and confirm the correct AWS account, region, tags, and budget.
2. Apply Terraform only after explicit approval.
3. Push an immutable container image, then deploy through the reviewed GitOps path.
4. Run a tenant success path and a bounded failure path.
5. Record metrics, traces, audit records, a dashboard, an alert, a short load sample,
   and a Cost Explorer query.
6. Run Terraform destroy and verify project resources are gone.

The exact commands, confirmation variables, failure drills, and evidence checklist are
in the [cloud-pilot runbook](cloud-pilot-runbook.md).

## Safety rules

- Terraform creates and destroys project resources. Do not use the AWS console for
  ad-hoc pilot changes.
- The expected AWS account is checked before plan, apply, or destroy.
- Apply and destroy require an exact confirmation value.
- Cloud services and data stores remain private. A browser route, if later enabled,
  must expose only the Console, API, and identity endpoints.
- Early Cost Explorer results are estimates. AWS billing commonly takes 24–48 hours
  to settle, so early values must never be described as final cost.
