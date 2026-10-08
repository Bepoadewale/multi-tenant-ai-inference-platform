# Cloud-Pilot Operations Guide

This guide describes the operational shape of a future AWS pilot. **No cloud apply,
runtime bootstrap, ALB, or Terraform backend has been executed by this repository.**
It must not be read as a deploy-now runbook.

## Intended safe sequence

1. Create one dedicated, encrypted/versioned S3 state bucket and DynamoDB lock table
   for this repository; do not share either with another portfolio project.
2. Set account ID, region, mandatory resource tags, cost budget/alarm, and an explicit
   expected-account guard.
3. Review `terraform fmt`, backend-free initialization, `terraform validate`, and a
   non-applying plan before any owner-authorized apply.
4. Let Terraform create the private VPC, EKS, ECR, IAM/IRSA, and only the services
   required by the runtime. Use immutable image digests.
5. Bootstrap the cluster with restricted workloads, probes, resource bounds,
   NetworkPolicies, OTel/Prometheus/Tempo/Grafana, and GitOps delivery.
6. Run a tenant admission success path and a bounded failure path. Capture traces,
   metrics, audit, release/rollback, cost-query, and provider-side teardown evidence.
7. Review and execute Terraform destroy. Verify tagged resources, EKS, RDS, ECR,
   secrets, ALB/target groups, and workload state are absent afterward.

## Future command contract

When CP3–CP5 are implemented, commands should use a consistent, guarded form:

```console
AWS_PROFILE=<profile> make pilot-cloud-plan
AWS_PROFILE=<profile> make pilot-cloud-apply
AWS_PROFILE=<profile> make pilot-cloud-push-image
AWS_PROFILE=<profile> make pilot-cloud-bootstrap
AWS_PROFILE=<profile> make pilot-cloud-smoke
AWS_PROFILE=<profile> make pilot-cloud-validate
AWS_PROFILE=<profile> EXPECTED_AWS_ACCOUNT_ID=<account-id> make pilot-cloud-destroy
```

These names are future contracts only. They must not be added as commands until their
scripts do exactly what they promise with bounded timeouts and useful failure output.

## State bootstrap now present, but not applied

`infrastructure/terraform/bootstrap/` now defines the repository's separate S3 state
bucket, DynamoDB lock table, required tags, and actual-cost alert. It can be checked
without credentials or resource changes through `make terraform-validate`. It has not
been applied; a non-applying plan and owner-authorized bootstrap remain required.

## Delivery contract now present, but not connected

The Helm chart now renders an immutable-image field, IRSA annotation hook,
PodDisruptionBudget, and an opt-in ALB ingress. The checked-in Argo CD Application
describes a protected desired-state delivery path. `make cloud-delivery-validate`
renders and checks these files without contacting a cluster or AWS. It does not prove
Argo reconciliation, image delivery, IRSA assumption, ALB routing, or a smoke test.

## Required future evidence

- Provisioning: Terraform plan/apply summaries, account/region/required-tags check.
- Runtime: image digest, EKS readiness, tenant isolation, Redis shared admission,
  release approval/canary/rollback, and no public data-store/observability endpoint.
- Operations: traces, metrics, dashboards, at least one alert/failure drill, bounded
  load, and a Cost Explorer query labelled estimated until AWS settles billing.
- Teardown: reviewed destroy plan and provider-side absence checks.

Record exact results in [validation evidence](governance/VALIDATION.md) only after a
separately authorized pilot has run.
