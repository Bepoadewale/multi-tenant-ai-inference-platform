# What Is Needed for a Real Cloud Pilot

The repository is complete for its local-first story. It also has a reviewed AWS plan.
It is not yet an executed AWS pilot or a hosted SaaS.

## The next proof

A real cloud pilot must show all of these with recorded evidence:

1. Terraform creates the approved AWS foundation and later removes it.
2. The application runs on private EKS using immutable images, durable cloud stores,
   workload identity, and secret delivery.
3. A real tenant request passes identity, quota, route, and model-serving checks.
4. A protected model release requires approval and can safely roll back.
5. Metrics, traces, audit records, dashboards, an alert, and a bounded load sample
   explain what happened.
6. GitHub Actions uses short-lived OIDC access for plan/apply/destroy without stored
   AWS keys.

## Deliberately not claimed yet

- Physical GPU capacity, vLLM/Triton/SGLang compatibility, DCGM/KV-cache signals, or GPU benchmarks.
- Enterprise identity-provider validation, custom-domain HTTPS, multi-region high availability, or public SaaS operation.
- Sustained error-budget evidence, disaster recovery, settled AWS billing, or a commercial hosted control plane.

These are not hidden gaps. Each needs a named environment, a budget, and measured
evidence before it becomes a claim.
