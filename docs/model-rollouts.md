# Model rollouts

Flagship context: the existing weighted-routing core is preserved. A local MLflow
registry now stores real stable/candidate ONNX artifacts, SHA-256 digest tags, CPU
fixture evaluation metrics, and `champion`/`candidate` aliases. Governed approval,
promotion and rollback remain the next release-control slice.

Model v1 is stable and v2 candidate. Progress 5→25→50→100% only after infrastructure health and workload-specific latency/error gates. Rollback changes target weights to zero; it does not claim model quality validation. Quality evaluation belongs to a separate curated evaluation pipeline.

`PUT /platform/v1/rollouts/{alias}` requires the platform-admin role, validates a complete 100% target allocation, refuses unhealthy targets, and records a metadata-only administrative audit event. It is a local control-plane implementation; production persists this event and deploys weights through protected GitOps state.
