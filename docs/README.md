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
| fundamental AI, GPU, inference, performance, and reliability concepts | [AI infrastructure handbook](gpu-lab/AI_INFRASTRUCTURE_HANDBOOK.md) |
| the single-L4 GPU project, progress, risks, and evidence | [GPU lab goal](goals/SINGLE_L4_GPU_INFRASTRUCTURE_GOAL.md) · [implementation backlog](gpu-lab/IMPLEMENTATION_BACKLOG.md) · [architecture](gpu-lab/ARCHITECTURE.md) · [repository audit](gpu-lab/REPOSITORY_AUDIT.md) · [cost report](gpu-lab/COST_REPORT.md) · [evidence manifest](gpu-lab/EVIDENCE_MANIFEST.md) · [GPU lab status](gpu-lab/IMPLEMENTATION_STATUS.md) · [local environment readiness](gpu-lab/LOCAL_ENVIRONMENT_READINESS.md) · [quota appeal record](gpu-lab/QUOTA_APPEAL_DRAFT.md) · [manual reproduction guide](gpu-lab/MANUAL_REPRODUCTION_GUIDE.md) · [GPU batch runbook](gpu-lab/GPU_BATCH_RUNBOOK.md) · [GPU host install manifest](gpu-lab/GPU_HOST_INSTALL_MANIFEST.md) · [Ansible host configuration](../infrastructure/ansible/README.md) · [sequential LLM release design](gpu-lab/SEQUENTIAL_LLM_RELEASE_DESIGN.md) · [single-GPU Compose profile](../deployments/single-gpu/README.md) · [CUDA performance preparation](../benchmarks/cuda_performance/README.md) · [CUDA preparation ticket](tickets/ticket49.md) · [GPU benchmark preparation ticket](tickets/ticket47.md) · [LLM evaluation preparation](../evaluations/gpu_llm/README.md) · [LLM evaluation ticket](tickets/ticket48.md) · [LLM release design ticket](tickets/ticket51.md) · [private MLflow evaluation integration](tickets/ticket52.md) · [container dependency lock ticket](tickets/ticket53.md) · [sequential LLM release record ticket](tickets/ticket54.md) · [authenticated LLM release API ticket](tickets/ticket55.md) · [host-side sequential release controller](tickets/ticket56.md) · [Ansible host configuration ticket](tickets/ticket57.md) · [manual guide ticket](tickets/ticket58.md) · [AMI pinning ticket](tickets/ticket40.md) · [quota CLI follow-up](tickets/ticket41.md) · [Terraform preview ticket](tickets/ticket42.md) · [state-lock tests and appeal update](tickets/ticket43.md) · [GPU batch preparation ticket](tickets/ticket44.md) · [single-L4 Compose profile ticket](tickets/ticket45.md) · [GPU observability preparation ticket](tickets/ticket46.md) · [validation](gpu-lab/VALIDATION.md) · [research notes](gpu-lab/RESEARCH_NOTES.md) |

The local Docker and CPU ONNX demonstration is executed evidence. Cloud/GPU documents
describe either a read-only plan review or future work unless they explicitly say an
AWS runtime action was executed.
