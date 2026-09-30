# Contributing

Run `make lint`, `make test`, and `make helm-lint`. Preserve tenant isolation, prompt privacy, bounded retries, and explicit local-vs-GPU boundaries.

## Dependency and version policy

- Pin or constrain dependencies in `pyproject.toml`, Compose image references, and
  Terraform provider/module constraints where reproducibility materially depends on
  them.
- Upgrade one dependency family at a time, record the validation commands, and do not
  describe a runtime as supported until its local or pilot evidence is recorded.
- Security fixes take priority over feature work. If an upgrade changes an API,
  identity, model, or telemetry contract, document the migration and rollback path in
  `CHANGELOG.md`.
- `latest` is not a support statement. GPU/cloud/runtime compatibility must name the
  tested model, command, hardware, and environment.
