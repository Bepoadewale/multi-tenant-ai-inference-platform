# Documentation

This repository keeps its local-first execution evidence separate from future cloud
adapters. Start with the [README](../README.md) for the runnable platform story.

| Area | Contents |
| --- | --- |
| [Architecture](architecture/) | System overview, flagship direction, tenant model, routing |
| [Operations](operations/) | Observability, FinOps, autoscaling, performance, benchmarks, failure modes, console |
| [Delivery](delivery/) | Model rollout, GPU scheduling, AWS adapter, real-workload pilot |
| [Security](security/) | Security model and controls |
| [Governance](governance/) | Implementation status and executed validation evidence |
| [Portfolio](portfolio/) | Interview guide and roadmap |
| [ADRs](adr/) | Architecture decisions |

Cloud/GPU instructions are planning or static validation unless a document explicitly
records executed evidence. The local Docker/CPU ONNX workflow remains the default
reproducible demonstration.
