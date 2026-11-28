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
| how the authenticated GPU gateway benchmark is prepared | [gateway benchmark ticket](tickets/ticket60.md) |
| how to prepare for AI infrastructure interviews using this project | [GPU lab interview preparation](gpu-lab/INTERVIEW_PREPARATION.md) · [ticket 61](tickets/ticket61.md) |
| how to diagnose GPU-lab failures and report benchmark results | [incident response handbook](gpu-lab/INCIDENT_RESPONSE_HANDBOOK.md) · [benchmark report framework](gpu-lab/BENCHMARK_REPORT.md) · [ticket 62](tickets/ticket62.md) |
| the current, evidence-labeled project report draft | [final report draft](gpu-lab/FINAL_PROJECT_REPORT.md) · [ticket 63](tickets/ticket63.md) |
| expanded learning chapters in the pre-GPU report draft | [final report draft](gpu-lab/FINAL_PROJECT_REPORT.md) · [ticket 72](tickets/ticket72.md) |
| latest AWS quota, capacity, and project-resource reconciliation | [implementation status](gpu-lab/IMPLEMENTATION_STATUS.md) · [cost report](gpu-lab/COST_REPORT.md) · [ticket 73](tickets/ticket73.md) |
| plain-English concepts for the single-L4 inference stack | [AI infrastructure handbook](gpu-lab/AI_INFRASTRUCTURE_HANDBOOK.md) · [ticket 75](tickets/ticket75.md) |
| validate relative links in the project goal, GPU guide, and lab documents | [`make gpu-docs-validate`](../Makefile) · [ticket 76](tickets/ticket76.md) |
| test the single-L4 expiry controls without AWS access | [`terraform test`](../Makefile) · [ticket 77](tickets/ticket77.md) |
| test that the GPU host has no inbound rules and bounded outbound ports | [mocked Terraform network test](tickets/ticket78.md) |
| verify project, owner, expiry, and cost tags on GPU-lab resources | [mocked Terraform tag test](tickets/ticket79.md) |
| prove GPU-root inputs reject unapproved hardware, regions, and storage sizes | [mocked Terraform input-constraint tests](tickets/ticket80.md) |
| guarded EC2 host configuration, deployment, smoke checks, incident drill, and evidence capture | [manual reproduction guide](gpu-lab/MANUAL_REPRODUCTION_GUIDE.md#use-the-guarded-host-operation-wrappers-after-the-manual-lesson) · [ticket 64](tickets/ticket64.md) |
| bounded Triton kernel and Nsight profiler preparation | [CUDA performance lab](../benchmarks/cuda_performance/README.md) · [ticket 65](tickets/ticket65.md) |
| reconciliation of model, quota, CI, and public-evidence facts | [ticket 66](tickets/ticket66.md) |
| live pull-request and backlog status reconciliation | [ticket 67](tickets/ticket67.md) |
| source and CI readiness for GPU host automation | [ticket 68](tickets/ticket68.md) |
| refreshed AWS Price List inputs and the $25 GPU-lab estimate | [cost report](gpu-lab/COST_REPORT.md) · [ticket 69](tickets/ticket69.md) |
| pinned GPU software candidates and their real-L4 validation boundary | [proposed architecture](gpu-lab/ARCHITECTURE.md) · [ticket 70](tickets/ticket70.md) |
| model-release source readiness versus real-host acceptance | [release backlog](gpu-lab/IMPLEMENTATION_BACKLOG.md) · [ticket 71](tickets/ticket71.md) |
| the single-L4 GPU project, progress, risks, and evidence | [GPU lab goal](goals/SINGLE_L4_GPU_INFRASTRUCTURE_GOAL.md) · [implementation backlog](gpu-lab/IMPLEMENTATION_BACKLOG.md) · [architecture](gpu-lab/ARCHITECTURE.md) · [repository audit](gpu-lab/REPOSITORY_AUDIT.md) · [cost report](gpu-lab/COST_REPORT.md) · [evidence manifest](gpu-lab/EVIDENCE_MANIFEST.md) · [GPU lab status](gpu-lab/IMPLEMENTATION_STATUS.md) · [local environment readiness](gpu-lab/LOCAL_ENVIRONMENT_READINESS.md) · [quota appeal record](gpu-lab/QUOTA_APPEAL_DRAFT.md) · [manual reproduction guide](gpu-lab/MANUAL_REPRODUCTION_GUIDE.md) · [AI infrastructure handbook](gpu-lab/AI_INFRASTRUCTURE_HANDBOOK.md) · [GPU batch runbook](gpu-lab/GPU_BATCH_RUNBOOK.md) · [GPU host install manifest](gpu-lab/GPU_HOST_INSTALL_MANIFEST.md) · [Ansible host configuration](../infrastructure/ansible/README.md) · [sequential LLM release design](gpu-lab/SEQUENTIAL_LLM_RELEASE_DESIGN.md) · [single-GPU Compose profile](../deployments/single-gpu/README.md) · [CUDA performance preparation](../benchmarks/cuda_performance/README.md) · [CUDA preparation ticket](tickets/ticket49.md) · [GPU benchmark preparation ticket](tickets/ticket47.md) · [LLM evaluation preparation](../evaluations/gpu_llm/README.md) · [LLM evaluation ticket](tickets/ticket48.md) · [LLM release design ticket](tickets/ticket51.md) · [private MLflow evaluation integration](tickets/ticket52.md) · [container dependency lock ticket](tickets/ticket53.md) · [sequential LLM release record ticket](tickets/ticket54.md) · [authenticated LLM release API ticket](tickets/ticket55.md) · [host-side sequential release controller](tickets/ticket56.md) · [manual guide ticket](tickets/ticket58.md) · [bootstrap guardrails ticket](tickets/ticket74.md) · [AI infrastructure handbook ticket](tickets/ticket75.md) · [AMI pinning ticket](tickets/ticket40.md) · [quota CLI follow-up](tickets/ticket41.md) · [Terraform preview ticket](tickets/ticket42.md) · [state-lock tests and appeal update](tickets/ticket43.md) · [GPU batch preparation ticket](tickets/ticket44.md) · [single-L4 Compose profile ticket](tickets/ticket45.md) · [GPU observability preparation ticket](tickets/ticket46.md) · [validation](gpu-lab/VALIDATION.md) · [research notes](gpu-lab/RESEARCH_NOTES.md) |

The local Docker and CPU ONNX demonstration is executed evidence. Cloud/GPU documents
describe either a read-only plan review or future work unless they explicitly say an
AWS runtime action was executed.
