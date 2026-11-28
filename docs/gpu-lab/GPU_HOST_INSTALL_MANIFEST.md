# GPU Host Installation Manifest

**Status:** researched installation plan and statically checked Ansible role; no package has been installed on an EC2
host. **Reviewed:** 2026-11-28. **Related:** [GPU batch runbook](GPU_BATCH_RUNBOOK.md),
[compatibility research](RESEARCH_NOTES.md), and [local environment readiness](LOCAL_ENVIRONMENT_READINESS.md).

This document answers what will be installed and where. It keeps the host operating
system small: GPU drivers and the CUDA compiler live on Ubuntu; the model server,
gateway, Redis, and monitoring services run in pinned containers. Package versions
below are researched candidates. Recheck sources and the exact Ubuntu kernel before
the paid session; none has been proven on a live L4.

## Installation order

The order matters because later layers depend on earlier ones. For example, the
NVIDIA Container Toolkit exposes an already working host driver to Docker; it cannot
repair a missing or broken driver.

| Order | Install on | Component | Candidate / policy | Why it is needed | Minimum verification |
| --- | --- | --- | --- | --- | --- |
| 0 | Local workstation | AWS CLI, Terraform, Git, Docker Compose, Python, GitHub CLI | Existing local versions are recorded in `LOCAL_ENVIRONMENT_READINESS.md`. The host-side Ansible controller is pinned separately in `infrastructure/ansible/requirements.lock` and is not installed on this Mac. | Review and provision the isolated host, validate configuration, and manage the repository. | Confirm the expected AWS account without printing credentials; run local static checks. |
| 1 | EC2 host | Standard Canonical Ubuntu Server 24.04 amd64 | Terraform pins AMI `ami-0a951420c495183dc`; verify owner, image name, architecture, availability, kernel, and region at preflight. | Provides a normal Linux host so driver and runtime setup is visible and teachable. | `lsb_release -a`, `uname -a`, `lscpu`, `free -h`, `lsblk`, `lspci`. |
| 2 | EC2 host | Systems Manager Agent and instance role | Prefer the agent supplied by the Canonical image; the scoped EC2 role must allow Systems Manager managed-instance operations. No inbound security-group rules. | Gives administrative access without SSH keys or open ports. | Confirm the agent service and the instance is Online in Systems Manager. |
| 3 | EC2 host | OS build and inspection tools | Install only required Ubuntu packages: matching `linux-headers-$(uname -r)`, compiler/build tools needed by the selected driver/toolkit, certificates, HTTPS/repository tools, `jq`, and Python virtual-environment support if a host-side script needs it. Resolve versions from the signed Ubuntu repository for the pinned image. | Matching headers enable driver modules; compiler tools build the CUDA sample; repository tools verify signed vendor repositories. | `dpkg-query`, `gcc --version`, `make --version`, and confirm header path matches `uname -r`. |
| 4 | EC2 host | NVIDIA Data Center compute driver | R580.196.11 candidate, compute/headless package set; the Ubuntu 24.04 NVIDIA repository exposes a matching pin package. Verify APT metadata signature and exact package names before install. | The kernel driver controls the physical L4 and makes it available to Linux and containers. | Reboot, reconnect with SSM, then `nvidia-smi`, `nvidia-smi -L`, and `nvidia-smi -q`; confirm one L4 and no driver error. |
| 5 | EC2 host | CUDA Toolkit and compiler | Toolkit-only package candidate `cuda-toolkit-13-0=13.0.3-1`. Do not install a meta-package that silently changes the driver. | `nvcc` compiles the CUDA C++ vector-add exercise. The toolkit is not needed just to run vLLM's container. | `nvcc --version`; compile the bounded sample; run it inside a GPU-enabled container or on the host. |
| 6 | EC2 host | Docker Engine, CLI, and Compose plugin | 2026-11-28 Ubuntu 24.04 amd64 repository candidates: Engine/CLI `5:29.9.3-1~ubuntu.24.04~noble`, containerd `2.4.2-4~ubuntu.24.04~noble`, Buildx `0.39.1-1~ubuntu.24.04~noble`, Compose `5.8.1-1~ubuntu.24.04~noble`. Hashes are in `RESEARCH_NOTES.md`. Install from Docker's signed repository; recheck package metadata and signature before use. | Runs the single-GPU Compose application and observability stack. | `docker version`, `docker compose version`, `docker info`; verify the daemon is active. |
| 7 | EC2 host | NVIDIA Container Toolkit | Candidate package set `1.20.2-1`; verify all four package versions and signed repository metadata again. Configure Docker with `nvidia-ctk runtime configure --runtime=docker`, inspect the daemon change, then restart Docker. | Passes GPU device nodes and driver libraries into containers. | `docker info`; run a digest-pinned CUDA image with `--gpus all`, `nvidia-smi`, and a CUDA sample. |
| 8 | EC2 host Python 3.12 virtual environment | Standalone PyTorch CUDA lab | Official wheel candidate: Linux x86_64 `torch==2.14.0+cu130`; the 29-package transitive lock is `benchmarks/cuda_performance/requirements-torch.lock`. It has hashes and targets CPython 3.12 / x86_64 Linux. The Ansible role installs this lock in `/opt/gpu-lab/torch-venv`; recheck sources before use. Keep it isolated from vLLM's bundled Python/Torch libraries. | Executes synchronized tensor allocation and matrix multiplication for GPU learning and benchmark comparisons. | Assert `torch.cuda.is_available()`, exactly one device named NVIDIA L4, allocate tensors, multiply, synchronize, and compare with CPU output. |
| 9 | EC2 host, Docker | vLLM OpenAI server | Candidate `vllm/vllm-openai:v0.34.0`; the observed OCI index is `sha256:20fdb089454afbb324efa4110a2c025ff7b27cc1a086e07aa580b18df8ad1ce1`, with `linux/amd64` child `sha256:cf5b2fdd087eb4f6d261736967cc5cde974bd22ff4df50365f8fa419b6b4c484`. Candidate CUDA 13.0 and bundled PyTorch 2.14.0. Never override its Torch libraries with an unrelated install. | Serves the model with a GPU-aware OpenAI-compatible API. | Recheck the registry manifest, image provenance and digest; inspect `huggingface_hub` is at least 2.0.0 in the image; confirm model revision, loaded CUDA model, `/health`, `/v1/models`, a real completion, and a streamed completion. |
| 10 | Model cache volume | Qwen model files | `Qwen/Qwen2.5-1.5B-Instruct`, revision `989aa7980e4cf806f80c7fef2b1adb7bc71aa306`, Apache-2.0 metadata, expected safetensors SHA-256 recorded in `RESEARCH_NOTES.md`. Recheck license and digest before download. | Provides the first small, open-weight model for measured L4 inference. | Verify the downloaded artifact digest before load; record the exact model revision. |
| 11 | Docker Compose network | Gateway (2 replicas), Redis, vLLM | Existing gateway image is built from this repository; Redis and vLLM image/model pins must match the reviewed Compose environment. Bind operator interfaces to loopback only. | Reuses existing authentication, tenant admission, shared quota, routing, and CPU/GPU runtime abstraction. | Health/readiness checks, authorized tenant request, denied tenant request, streaming, quota sharing across replicas. |
| 12 | Docker Compose network | DCGM Exporter, Node Exporter, Prometheus, Grafana, Alertmanager, OpenTelemetry Collector, Tempo, Redis exporter | Use the immutable image digests already in the single-GPU Compose profile; recheck registry manifests at preflight. | Measures GPU, host, gateway, Redis, vLLM, alert, and trace behavior without managed monitoring services. | Prometheus targets are healthy and real GPU/inference series move during a request; dashboard and alert drill use those series. |
| 13 | Docker Compose network / encrypted instance disk | Private, single-host MLflow tracking server | PR #52 adds MLflow 3.18.0 using SQLite and a named artifact volume on the encrypted 100-GiB root disk. It is an evaluation evidence store, not a durable production registry. Its host port is loopback-only; there is no inbound security-group rule. | Records model version metadata, evaluation aggregates, release evidence, and rollback results within the disposable host. | Check health, write a sanitized evaluation report, verify no prompt/completion text is logged, export required artifacts, and confirm the named volume is removed with the host. Include image size, disk, and memory in the fit check. |
| 14 | Docker Compose network / encrypted instance disk | Shared gateway LLM release-plan SQLite state | PR #55 prepares a SQLite volume mounted by both gateway containers on the same EC2 host. Write-ahead logging handles local concurrent requests; it is not a distributed database or cross-host lock. | Preserves release plans, manifests, approvals, and approver identity across gateway restarts on this disposable host. | Create a plan through an authenticated gateway request, read it through the other replica, verify self-approval is denied, export sanitized state, and confirm the named volume is removed with the host. Include SQLite/WAL files in disk monitoring. |

## What does not belong on the host

- Do not install Kubernetes, kubelet, EKS components, or a multi-GPU scheduler. This
  project uses one standalone EC2 instance and Docker Compose.
- Do not install host Redis, Prometheus, Grafana, Tempo, or vLLM when the pinned Compose
  containers provide those services. Avoid duplicate listeners and storage.
- The single-GPU Compose profile has a private, disposable MLflow service from PR #52.
  It uses SQLite and the encrypted root disk; export evidence before teardown. Do not
  treat this single-host store as a durable production model registry.
- The GPU release-plan SQLite volume is shared only between gateway replicas on this
  one EC2 host. It is not a multi-host coordination store. The approval API has no
  Docker access and cannot restart vLLM.
- Do not install a second independent PyTorch into vLLM's environment. The server
  image owns its Python and CUDA user-space dependencies.
- Do not install a desktop driver or graphical display stack on this headless host.
- Do not download multiple models or keep larger models loaded concurrently on the
  single L4. The first run uses the pinned 1.5B model and one GPU.
- Do not expose model, Redis, metrics, Grafana, or gateway ports to the internet.

## Expected host state after the base installation

The OS should show one NVIDIA L4. The host driver owns the kernel interface. The CUDA
Toolkit supplies `nvcc` for the C++ lab. Docker runs the application containers. The
NVIDIA Container Toolkit connects Docker to the host driver. The vLLM image supplies
its own compatible CUDA libraries and PyTorch. The standalone PyTorch CUDA build and
its CUDA library packages are installed in a separate Python 3.12 virtual environment
for the CUDA experiment. The host Toolkit separately provides `nvcc`. This split
avoids changing vLLM's libraries or treating the host Toolkit version as the same
thing as the CUDA libraries inside the model image. Check free disk before downloads:
the model, vLLM image, and standalone CUDA packages all consume space on the 100-GiB
root volume.

vLLM v0.34.0 release notes describe automatic KV-cache sizing from free GPU memory
after warm-up and recommend removing `gpu_memory_utilization` in many configurations.
The Compose profile currently sets this value to `0.85` as a deliberate initial
capacity bound. Validate that it still behaves as intended with this release and
model; do not raise it based only on release-note claims. The same release requires
Hugging Face Hub 2.0.0 or newer. The image's bundled Python environment must be
checked directly before loading the model.

For example, `nvidia-smi` reports the maximum CUDA driver API level supported by the
installed driver; `nvcc --version` reports the separately installed compiler toolkit.
Those versions can differ without being an error. Check the exact compatibility table
and vLLM image requirements instead of trying to make the version strings identical.

## Stop conditions and recovery

Stop before continuing if the Ubuntu image, account, region, instance type, or GPU is
wrong; matching headers are unavailable; the driver fails after reboot; `nvidia-smi`
does not identify one L4; the CUDA and driver compatibility check fails; Docker cannot
see the GPU; an image digest or model hash differs; or the cost/runtime reserve is
threatened. Capture sanitized logs and metadata before troubleshooting. Do not repeat
package installation or infrastructure mutation until the current host state is
known. Use the SSM recovery route and the runbook's teardown safeguards.

## Evidence boundary

The AMI, driver, Toolkit, vLLM, model, and observability references in
[`RESEARCH_NOTES.md`](RESEARCH_NOTES.md) are metadata and documentation evidence.
They do not prove that packages were installed, a model was downloaded, or the L4
worked. The paid execution batch must record actual versions and outputs, confirm
package and model integrity, and update this manifest if live results require a
different compatible version.
