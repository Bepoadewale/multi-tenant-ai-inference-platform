# Security and privacy

Flagship context: remediation, agent-tool, developer-self-service, and narrow edge
adapters are executed locally; each extends—not bypasses—the existing signed identity,
tenant authorization and privacy boundary.

The gateway authenticates before resolving tenant and fails closed for unknown credentials/models. It does not trust tenant headers or expose Kubernetes/GPU credentials. Kubernetes templates use non-root, read-only root filesystem, dropped capabilities, seccomp, NetworkPolicy, ServiceAccount, limits, and secret references. Model registry tokens belong in external secrets, never Git.

Prompts/responses are sensitive and are not logged or metered as content. Retain metadata only, minimize access, define controlled debugging opt-in with retention/audit, and protect traces/logs accordingly.

The remediation controller has a deliberately smaller authority boundary than the
gateway. It reads an existing metadata-only request record, accepts only a failed
canary request, and can execute only `ROLLBACK_CANARY_TO_STABLE`. It requires a signed
`platform.admin` requester plus a different signed `remediation.approve` principal;
the requester cannot self-approve. The exact release plan and weights are preconditions
checked immediately before execution. Stale state is rejected, while cooldown and
action-budget guards prevent retry loops. The controller has no generic shell,
Kubernetes, Docker, cloud, registry, or tenant-inference credential.

The developer-self-service service is also deliberately bounded. It validates the
same signed JWT issuer/audience/expiry/signature controls as the gateway, derives the
tenant server-side, requires `developer.self_service`, and rejects delegated agent
principals. It accepts only tenant-assigned aliases, isolates profile reads by tenant,
and makes repeated calls safe through tenant-scoped idempotency fingerprints. Generated
starter files contain no bearer token or tenant override header; the local demo supplies
an already-issued fixture token only at client execution time. Production identity/token
issuance remains an external identity-provider adapter.

The edge adapter has a separate identity class. Its device tokens contain
`principal_type=device` and `edge.connect`; a human/tenant token cannot register a
device, while a device token cannot call platform administration, release, or
remediation APIs. The device agent validates the original signed tenant token before
inference and evaluates privacy before any central fallback. Its control-plane SQLite
registry stores device/profile/model/network/telemetry metadata—not inference inputs
or outputs. Profiles are simulation inputs, not attestation or physical hardware proof.
