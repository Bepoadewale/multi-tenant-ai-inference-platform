# Cloud-Pilot Runbook

This is the future CP6 operational sequence. It is deliberately **not executed
evidence**. The local platform remains the verified proof until this runbook is used
in an authorized AWS pilot and exact results are recorded.

## Preconditions

- A dedicated AWS account, expected-account guard, budget alert, state bucket, and
  DynamoDB lock table exist through Terraform bootstrap.
- A branch-bound GitHub OIDC role and a protected `aws-pilot` GitHub Environment have
  been reviewed. No AWS access keys are stored in GitHub.
- The operator can reach the private EKS endpoint through an approved private path.
- Immutable image digest, runtime configuration, and service-account IRSA annotation
  are reviewed in a desired-state PR.

## Intended command sequence

```console
AWS_PROFILE=<profile> EXPECTED_AWS_ACCOUNT_ID=<account-id> make pilot-guardrails-plan
AWS_PROFILE=<profile> EXPECTED_AWS_ACCOUNT_ID=<account-id> make pilot-cloud-plan
AWS_PROFILE=<profile> IMAGE_TAG=<immutable-tag> ECR_REPOSITORY=<terraform-output> make pilot-cloud-push-image
AWS_PROFILE=<profile> CLUSTER_NAME=<terraform-output> PILOT_CLOUD_CONFIRM=bootstrap make pilot-cloud-bootstrap-runtime
AWS_PROFILE=<profile> CLUSTER_NAME=<terraform-output> make pilot-cloud-smoke
AWS_PROFILE=<profile> CLUSTER_NAME=<terraform-output> make pilot-cloud-validate
AWS_PROFILE=<profile> EXPECTED_AWS_ACCOUNT_ID=<account-id> PILOT_CLOUD_CONFIRM=destroy make pilot-cloud-destroy
```

`apply` is intentionally not in the ordinary chain. It requires a reviewed plan,
explicit `PILOT_CLOUD_CONFIRM=apply`, and a separate authorization.

## Required CP6 evidence

1. Tenant A and Tenant B share Redis-backed admission without cross-tenant leakage.
2. A release requires independent approval; a canary succeeds or safely rolls back.
3. A policy, quota, backend, or release-failure scenario is observable and bounded.
4. Prometheus metrics, OTel/Tempo traces, Grafana evidence, audit records, and one
   alert are captured from the cloud runtime.
5. A bounded load sample is recorded with environment, duration, concurrency, and
   exact observed outcomes. It is not a benchmark unless measured as one.
6. A Cost Explorer query is recorded as estimated until AWS billing data settles—often
   24–48 hours later. Do not call early values measured billing.
7. Terraform destroy is reviewed and run; provider-side checks confirm EKS, RDS,
   ElastiCache, ECR, secrets, VPC resources, ALB/target groups if enabled, and tagged
   pilot resources are absent.

## Reliability design

- Gateway replicas: two or more; PDB keeps at least one available during voluntary
  disruption.
- Admission state: Redis is shared; loss fails closed for distributed admission.
- Durable release/remediation/audit state: RDS PostgreSQL; test restart recovery before
  calling the pilot successful.
- Release safety: immutable artifact digest, independent approval, stale-state check,
  bounded canary, and known-good rollback.
- Public exposure: if enabled, ALB routes only Console/API/identity. Data stores,
  observability, and Kubernetes administration stay private.
