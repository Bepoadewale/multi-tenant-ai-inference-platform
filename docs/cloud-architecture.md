# Intended AWS Cloud Architecture

This is the flagship's **planned cloud-pilot topology**. It is a design and
static-validation target, not evidence that AWS resources or cloud workloads have
run. The completed local-first platform remains the only executed deployment scope.

![Intended AWS cloud-pilot topology](assets/flagship-cloud-architecture.svg)

## In plain English

Teams and approved agents call the gateway instead of receiving direct access to a
model runtime, Redis, Kubernetes, or AWS. The gateway verifies identity, derives the
tenant, enforces a shared limit, routes a request, records only safe usage metadata,
and emits evidence. Release, remediation, developer, edge, and sandbox functions
remain bounded services; they do not become an all-powerful platform administrator.

For a future pilot, Terraform would create the AWS foundation. Kubernetes would run
the CPU-first application services privately. A deliberately narrow ALB would expose
only the Operator Console, API, and identity route for browser review. It would never
make Redis, MLflow artifacts, Prometheus, Grafana, Tempo, databases, or Kubernetes
administration public.

## Planned component responsibilities

| Area | Intended responsibility | Evidence status |
| --- | --- | --- |
| S3 + DynamoDB | Encrypted, versioned, locked Terraform state for this repository only. | 📐 Architecture / contract only |
| VPC + EKS | Private application/data workloads with bounded public ingress. | 📐 Architecture / contract only |
| ECR | Immutable images for the platform services. | 📐 Architecture / contract only |
| RDS PostgreSQL | Durable cloud control, release, remediation, and audit records. | 📐 Architecture / contract only |
| ElastiCache Redis | Shared admission, routing, and usage-metadata state. | 📐 Architecture / contract only |
| S3 artifacts | MLflow/model artifacts with integrity evidence. | 📐 Architecture / contract only |
| IAM/IRSA + Secrets Manager | Workload identity and secret delivery without source-controlled credentials. | 📐 Architecture / contract only |
| GitHub OIDC + GitOps | Short-lived delivery identity and reviewed desired-state reconciliation. | 📐 Architecture / contract only |
| ALB | Narrow browser route to Console/API/identity only; public TLS needs a controlled domain and ACM. | 📐 Architecture / contract only |

## Important boundaries

- The existing CPU ONNX runtime is a real local execution path. It is not a cloud
  throughput or GPU-performance claim.
- The simulated capacity pool is not a physical GPU scheduler. Any GPU node group is
  disabled by default and needs a separately budgeted experiment.
- Cloud Terraform must be the only provisioning and teardown authority after account
  bootstrap. No ad-hoc console changes or long-lived keys in GitHub.
- A future GitHub Actions workflow must use a repository-bound OIDC role and explicit
  confirmation for apply or destroy.
- A future browser path must not turn the Console into a direct cloud-credential or
  Kubernetes-credential holder.

See [cloud-pilot program](delivery/cloud-pilot-program.md) for the staged work and
[security architecture](security/security.md) for the corresponding trust model.
