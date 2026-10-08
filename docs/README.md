# Documentation

This repository keeps its local-first execution evidence separate from future cloud
adapters. Start with the [README](../README.md) for the runnable platform story.

| Area | Contents |
| --- | --- |
| [Architecture](architecture/) | [Full system map/API reference](architecture/flagship-system-map.md), flagship integration direction, and [intended AWS topology](cloud-architecture.md) |
| [Operations](operations/) | Observability, FinOps, performance, failure modes, console |
| [Delivery](delivery/) | Model rollout, the staged [cloud-pilot program](delivery/cloud-pilot-program.md), [cloud operations](cloud-operations.md), and hardware/runtime pilot guidance |
| [Security](security/) | Security model, architecture diagram, and threat controls |
| [Governance](governance/) | Implementation status and executed validation evidence |
| [Portfolio](portfolio/) | Interview guide and roadmap |
| [ADRs](adr/) | Architecture decisions |

Cloud/GPU instructions are planning or static validation unless a document explicitly
records executed evidence. The local Docker/CPU ONNX workflow remains the default
reproducible demonstration.

[Production evolution](production-evolution.md) states the exact evidence required
before a cloud or enterprise claim can replace that local-first boundary.

For a low-level client walkthrough, use the token-free source in
[`examples/`](../examples/README.md); it calls the executed inference API rather than
inventing a parallel interface.
