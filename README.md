# Multi-Tenant AI Platform

A governed AI platform that lets applications, developers, and approved agents use
shared AI models without receiving direct access to model servers, Redis, GPUs,
Kubernetes, cloud accounts, or deployment controls.

**Delivery state:** **Local platform complete; AWS pilot ready.** The complete platform
has run twice from a clean local machine state. An authenticated AWS Terraform review
also produced a real no-apply plan. AWS infrastructure has **not** been created by
this repository, so this is not an AWS-pilot execution claim.

![Planned AWS pilot architecture](docs/assets/flagship-cloud-architecture.svg)

The diagram uses checked-in AWS icons and shows the planned cloud shape. Read the
[cloud architecture](docs/cloud-architecture.md) for the full trust boundary and
evidence status.

## What it allows—and prevents

| Caller | Allowed | Prevented |
| --- | --- | --- |
| Application team | Call an assigned model through one OpenAI-compatible API | Direct model-server, Redis, GPU, or infrastructure access; another team's model or quota |
| Platform operator | Review model evidence and approve an exact protected release | Approving a changed/stale release or bypassing release rules |
| Approved AI agent | Read its tenant's safe request evidence and prepare a rollback plan | Self-approval, release execution, routing changes, secret access, arbitrary shell or cloud access |
| Developer | Create a tenant-bound integration profile for an assigned model | Tenant override headers, rollout controls, platform-admin authority, or credential leakage |

Every inference request follows this control loop:

```text
signed identity → tenant and role check → Redis quota and bounded queue
→ capacity policy → model route → real CPU ONNX response
→ metadata-only usage → metrics and traces
```

A protected model release follows a second loop:

```text
MLflow artifact and evaluation → immutable release plan → independent approval
→ limited canary traffic → promote or restore the known-good model
→ durable audit and evidence
```

The gateway controls access to shared AI capacity. It does not give callers direct
infrastructure authority.

## What works locally

The local Docker stack uses two gateways, Redis, two real CPU ONNX Runtime targets,
MLflow, SQLite, OpenTelemetry Collector, Tempo, Prometheus, Grafana, and a scoped
Operator Console.

- Signed Ed25519 identities derive tenant and role on the server. Client tenant
  headers are not trusted.
- Redis shares request, token, concurrency, budget, and bounded-queue limits across
  two gateway replicas. One noisy tenant does not reset its quota by changing gateway.
- Real CPU ONNX models serve OpenAI-compatible and streaming requests. This is real
  inference, not a GPU-performance claim.
- MLflow stores local model artifacts, digests, evaluation results, champion/candidate
  aliases, canary plans, approval, promotion, stale-plan denial, and rollback.
- Metrics, traces, dashboards, metadata-safe request analysis, local SLO fixtures,
  and local token-cost estimates show what happened to a request.
- A bounded remediation service can restore only a known-good canary target after a
  separate approval. It cannot run arbitrary commands or access cloud credentials.
- Other bounded services demonstrate delegated agent tools, developer self-service,
  simulated edge routing, and hardened disposable sandbox tasks.

The simulated capacity pool is **not** physical GPU scheduling. GPU, vLLM, DCGM,
Kubernetes autoscaling, and cloud billing remain clearly outside local execution.

## Run it locally

Prerequisites: Docker Desktop, Docker Compose, Python 3.12, `curl`, and `jq`.
No cloud account, GPU, model download, or paid API is required.

```console
make install
make bootstrap-local
make smoke
make demo-flagship
make verify
make clean-local
```

`make demo-flagship` runs the connected success and failure story. The Operator Console
is available at [http://localhost:8091](http://localhost:8091). `make clean-local`
removes only this repository's containers, images, generated artifacts, and local state.

For focused drills, use `make demo-overload`, `make demo-release-control`,
`make demo-remediation`, `make demo-agent-tools`, `make demo-self-service`,
`make demo-edge-adapter`, or `make demo-sandboxed-agent`.

## What the AWS plan reviewed

The read-only plan was run against the approved account in `us-east-1`. It proposed:

- **7 state-guardrail resources:** an encrypted/versioned S3 state bucket, public
  access protections, DynamoDB lock table, and budget notifications.
- **36 runtime resources:** private VPC networking, EKS CPU nodes, RDS PostgreSQL,
  ElastiCache Redis, ECR repositories, Secrets Manager containers, and narrow IAM/IRSA roles.

Nothing was applied. The plan created no AWS resource and no Terraform state. The
[validation record](docs/governance/VALIDATION.md) contains the exact evidence.

## Cloud operations

The cloud pilot is off by default because it creates billable AWS resources. Terraform
is the only supported provisioning and teardown path.

```console
AWS_PROFILE=<operator-profile> EXPECTED_AWS_ACCOUNT_ID=<account-id> make pilot-guardrails-plan
AWS_PROFILE=<operator-profile> EXPECTED_AWS_ACCOUNT_ID=<account-id> make pilot-cloud-plan
AWS_PROFILE=<operator-profile> EXPECTED_AWS_ACCOUNT_ID=<account-id> PILOT_CLOUD_CONFIRM=apply make pilot-cloud-apply
AWS_PROFILE=<operator-profile> IMAGE_TAG=<immutable-tag> ECR_REPOSITORY=<repository-url> make pilot-cloud-push-image
AWS_PROFILE=<operator-profile> CLUSTER_NAME=<cluster-name> PILOT_CLOUD_CONFIRM=bootstrap make pilot-cloud-bootstrap-runtime
AWS_PROFILE=<operator-profile> CLUSTER_NAME=<cluster-name> make pilot-cloud-smoke
```

Run the complete sequence, failure drills, and account-guarded destroy from the
[cloud-pilot runbook](docs/cloud-pilot-runbook.md). Do not call the cloud pilot
complete until those steps have actual AWS evidence.

## Current boundary and next improvements

This repository does not claim AWS runtime execution, physical GPU execution,
enterprise identity-provider validation, public custom-domain TLS, sustained
error-budget evidence, disaster recovery, settled cloud billing, or a hosted SaaS.
Those are deliberate future claims with separate evidence requirements in
[Production evolution](docs/production-evolution.md).

## Documentation

- [Cloud architecture](docs/cloud-architecture.md) · [Cloud operations](docs/cloud-operations.md)
- [Security and privacy](docs/security/security.md) · [Operator Console](docs/operations/operator-console.md)
- [Observability and FinOps](docs/operations/observability-finops.md) · [Failure modes](docs/operations/failure-modes.md)
- [Validation evidence](docs/governance/VALIDATION.md) · [Implementation status](docs/governance/IMPLEMENTATION_STATUS.md)
- [System map and API reference](docs/architecture/flagship-system-map.md) · [Runnable clients](examples/README.md)

For governed Kubernetes environment creation, see the companion
[AI Platform Control Plane](https://github.com/Bepoadewale/ai-platform-control-plane).
