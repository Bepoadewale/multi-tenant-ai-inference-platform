# Documentation

Start with the [main README](../README.md). It explains what the platform does, what
has run locally, and what the AWS plan reviewed.

| If you want to know… | Read… |
| --- | --- |
| how the services fit together and which APIs exist | [Architecture](architecture/) |
| how to run, observe, or troubleshoot the local platform | [Operations](operations/) |
| how model releases and a future cloud pilot work | [Delivery](delivery/) |
| how identity, tenant limits, agent access, and privacy are protected | [Security](security/) |
| exactly what was tested and what remains only planned | [Governance](governance/) |
| how to discuss the project in an interview | [Portfolio](portfolio/) |
| why a major technical choice was made | [ADRs](adr/) |
| the single-L4 GPU project, progress, risks, and evidence | [GPU lab goal](goals/SINGLE_L4_GPU_INFRASTRUCTURE_GOAL.md) · [implementation backlog](gpu-lab/IMPLEMENTATION_BACKLOG.md) · [architecture](gpu-lab/ARCHITECTURE.md) · [repository audit](gpu-lab/REPOSITORY_AUDIT.md) · [cost report](gpu-lab/COST_REPORT.md) · [evidence manifest](gpu-lab/EVIDENCE_MANIFEST.md) · [GPU lab status](gpu-lab/IMPLEMENTATION_STATUS.md) · [quota appeal record](gpu-lab/QUOTA_APPEAL_DRAFT.md) · [AMI pinning ticket](tickets/ticket40.md) · [quota CLI follow-up](tickets/ticket41.md) · [Terraform preview ticket](tickets/ticket42.md) · [state-lock tests and appeal update](tickets/ticket43.md) · [validation](gpu-lab/VALIDATION.md) · [research notes](gpu-lab/RESEARCH_NOTES.md) |

The local Docker and CPU ONNX demonstration is executed evidence. Cloud/GPU documents
describe either a read-only plan review or future work unless they explicitly say an
AWS runtime action was executed.
