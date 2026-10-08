# Multi-Tenant AI Inference Platform — Agent Guide

Mission: preserve the executed tenant-aware inference core, then evolve this repository
as the public flagship through small, independently validated integration slices. Keep
CPU fixtures explicitly non-GPU-performance evidence.

Stack: Python 3.12, FastAPI, Redis contracts, Prometheus, vLLM/Kubernetes contracts.

Commands: `make install`, `make bootstrap-local`, `make smoke`, `make demo-flagship`,
`make public-demo`, `make verify`, `make clean-local`, `make test`, `make lint`,
`make load-test`, `make helm-lint`, `make terraform-validate`.

Rules: never claim GPU/vLLM performance without execution; tenant identity is server-side; test cross-tenant limits and failure paths; no secrets/main pushes; update status/backlog and report exact validation. Do not copy other portfolio repositories wholesale: integrate through narrow APIs/events and preserve the working gateway path. Keep commercial/pricing/buyer strategy out of this public repository.

Future cloud infrastructure must be provisioned and torn down through Terraform. Do
not create or delete pilot cloud resources manually after account bootstrap; review
plans, use encrypted/locked state, run Terraform destroy for teardown, and record
post-destroy verification.

## Cloud-pilot readiness rule

The flagship is currently complete only for its local-first scope. The next delivery
phase is a **cloud-pilot readiness program**, not an AWS execution claim. Follow the
staged sequence in `docs/delivery/cloud-pilot-program.md` and preserve the local
proof while it is built. Each cloud repository must have its own encrypted/versioned
S3 Terraform state bucket, DynamoDB lock table, state key namespace, required tags,
and budget guardrail. Until an owner deliberately applies Terraform and records
provider-side evidence, label those resources `PLANNED / STATICALLY VALIDATED`.

Use `terraform init -backend=false`, `terraform fmt`, `terraform validate`, and a
reviewed non-applying plan while building the design. Do not place AWS credentials in
the repository or GitHub secrets. Future CI must use a least-privilege GitHub OIDC
role, and future browser access must expose only the Console/API/identity paths—not
Redis, MLflow, Prometheus, Grafana, Tempo, Kubernetes, or data stores.

Completion rule: do not mark this repository **PORTFOLIO COMPLETE — LOCAL-FIRST SCOPE** unless `DEFINITION_OF_DONE.md` has executed evidence for its repository-specific gate. Interfaces, mocks, manifests, architecture, unit tests, static validation, and documentation alone are insufficient. The tenant → admission → real inference → telemetry story must execute locally; unexecuted GPU/cloud integrations stay explicitly labeled.

## Clean-room reproducibility

Clean-room reproducibility is a mandatory completion criterion. Do not mark this repository
`PORTFOLIO COMPLETE — LOCAL-FIRST SCOPE` until a new engineer can reproduce the platform from a
clean project state using documented commands, execute the primary and required failure demos, run
validation, and safely tear down only this project's local resources. Do not infer reproducibility
from an existing developer environment; execute it after project-specific cleanup.

## Pull-request review rule

Do not certify any implementation PR as ready for human review until it includes executed,
project-scoped clean-room evidence for the change: clean state, bootstrap, smoke, the relevant
success and failure/security demos, validation, safe cleanup, and a second clean bootstrap/demo.
Record exact commands and outcomes in `docs/governance/VALIDATION.md`; if the sequence has not run or fails,
the PR remains draft. Documentation-only changes may state that clean-room execution is not
applicable, but must not imply implementation validation.
