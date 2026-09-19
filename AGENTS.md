# Multi-Tenant AI Inference Platform — Agent Guide

Mission: enforce tenant-aware inference admission, routing, metering and observability. Keep the current mock backend explicitly non-performance evidence.

Stack: Python 3.12, FastAPI, Redis contracts, Prometheus, vLLM/Kubernetes contracts.

Commands: `make install`, `make test`, `make lint`, `make demo`, `make load-test`, `make helm-lint`, `make terraform-validate`.

Rules: never claim GPU/vLLM performance without execution; tenant identity is server-side; test cross-tenant limits and failure paths; no secrets/main pushes; update status/backlog and report exact validation.
