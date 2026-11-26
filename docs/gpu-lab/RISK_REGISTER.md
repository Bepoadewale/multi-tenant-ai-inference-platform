# GPU Lab Risk Register

Initial risks from repository inspection and the project constraints. Update likelihood, impact, mitigation, owner, and evidence as research and implementation proceed.

| Risk | Impact | Initial mitigation / gate | Status |
| --- | --- | --- | --- |
| G6 capacity or L4 quota unavailable in `us-east-1` | GPU work cannot start or pushes project elsewhere | Read current quota/availability before planning; document any region change and cost before action. Initial On-Demand G/VT quota is 0 vCPUs; request not submitted. | Blocked pending quota |
| Existing dependency audit fails | PR CI may fail and known vulnerable dependencies remain in local environment | Treat as pre-existing baseline; identify direct/transitive packages and safe upgrades in a separate reviewable change, rerun validation | Open |
| Total AWS resources exceed the $25 ceiling | Unauthorized spend | Price all resources, cap runtime, use one instance, no NAT/managed services, gate exact plan, terminate after batch | Open; no spend |
| Session interruption leaves instance running | Continued spend | Independent expiry/cleanup safeguard, recorded run ID, bounded lifetime, immediate teardown after batch | Open |
| Existing/shared AWS resources mistaken for project-owned | Damage or cross-project impact | Read-only account/tag inventory, dedicated names/tags/state/root, exact plan and destroy only project root | Inventory pending |
| Standard Ubuntu driver/kernel/CUDA incompatibility | GPU unavailable or unstable | Pin a documented compatible stack; manual validation before Ansible; preserve recovery path | Open |
| L4 VRAM insufficient for model/runtime/context/concurrency | Startup failure or OOM | Begin with 1.5B model, measure; cap context and concurrency; don't co-load large models | Open |
| Mutable image/model artifact produces irreproducible results | Unknown code/model behavior | Pin image digest/version, model revision, download source and SHA-256 | Open |
| Gateway reports inaccurate token usage or leaks reservations | Tenant overrun, quota bypass, incorrect cost | Audit tokenizer/count/reconciliation, client cancellation, error and Redis failure paths; tests before live use | Open |
| Redis failure permits unbounded inference | Capacity overload and tenant impact | Preserve fail-closed admission; test dependency failure and reservation cleanup | Open |
| Prompt/completion or credentials leak through logs/evidence | Tenant privacy or account compromise | Metadata-only telemetry, redact outputs and headers, scan evidence before commit | Open |
| Single host is mistaken for HA or GPU isolation | Misleading engineering claims | Explicitly label single point of failure and logical-only tenancy everywhere | Open |
| Benchmark timing is asynchronous or under-repeated | False performance conclusions | Warm-up, device synchronization/events, repeated trials, record raw outputs and limitations | Open |
| Local validation regression while adding GPU path | Loss of proven CPU baseline | Run existing suite before/after; preserve CPU ONNX fallback and clean-room gate | Open |
| External model license or terms unsuitable | Reuse/redistribution issue | Verify current official model card/license before fetching; do not redistribute weights | Open |
| Evidence files expose sensitive values or bloat public Git | Security and repository maintainability | Sanitized manifest, no state/plans/credentials; keep bulky raw artifacts outside public repo | Open |
