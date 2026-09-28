# Security and privacy

Flagship context: remediation is executed locally; later agent-tool and edge adapters
must extend—not bypass—the existing signed identity, tenant authorization and privacy
boundary.

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
