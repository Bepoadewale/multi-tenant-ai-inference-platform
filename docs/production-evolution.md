# Production Evolution Boundary

The repository is **PORTFOLIO COMPLETE — LOCAL-FIRST SCOPE**. That means its central
multi-tenant inference and integrated vertical-slice story has been run, tested, and
clean-room reproduced locally. It does not mean an AWS, GPU, or public SaaS deployment
has been proven.

## What the next cloud phase must prove

1. Terraform-managed foundation with repository-specific state, locking, tags, and
   budget safeguards.
2. Private EKS runtime with image delivery, durable cloud stores, least-privilege
   workload identity, and secure secret delivery.
3. A governed tenant request through real cloud runtime components, with cloud metrics,
   traces, audit, release rollback, and provider-side teardown.
4. GitHub Actions OIDC plan/apply/destroy controls without stored AWS credentials.
5. A narrow ALB only if browser review is needed; trusted public HTTPS remains a later
   domain-and-ACM decision.

## Explicitly outside a first CPU cloud pilot

- Physical GPU capacity, GPU scheduling performance, vLLM/Triton/SGLang compatibility,
  DCGM/KV-cache telemetry, and real GPU benchmarks.
- Enterprise identity-provider validation, public custom-domain TLS, multi-region HA,
  and settled cloud-billing claims.
- A commercial hosted-control-plane, customer support, or buyer/pricing strategy.

Those are not omissions from the local platform. They are separate claims requiring
named environments, measured evidence, cost approval, and their own acceptance gates.

The authoritative delivery order is the [cloud-pilot program](delivery/cloud-pilot-program.md).
