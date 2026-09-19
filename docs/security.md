# Security and privacy

The gateway authenticates before resolving tenant and fails closed for unknown credentials/models. It does not trust tenant headers or expose Kubernetes/GPU credentials. Kubernetes templates use non-root, read-only root filesystem, dropped capabilities, seccomp, NetworkPolicy, ServiceAccount, limits, and secret references. Model registry tokens belong in external secrets, never Git.

Prompts/responses are sensitive and are not logged or metered as content. Retain metadata only, minimize access, define controlled debugging opt-in with retention/audit, and protect traces/logs accordingly.
