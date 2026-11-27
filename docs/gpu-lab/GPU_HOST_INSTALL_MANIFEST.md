# GPU Host Installation Manifest

**Status:** researched installation plan; no package has been installed on an EC2
host. **Reviewed:** 2026-11-27. **Related:** [GPU batch runbook](GPU_BATCH_RUNBOOK.md),
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
| 0 | Local workstation | AWS CLI, Terraform, Git, Docker Compose, Python, GitHub CLI | Existing local versions are recorded in `LOCAL_ENVIRONMENT_READINESS.md`; Ansible controller version will be pinned before roles are written. | Review and provision the isolated host, validate configuration, and manage the repository. | Confirm the expected AWS account without printing credentials; run local static checks. |
| 1 | EC2 host | Standard Canonical Ubuntu Server 24.04 amd64 | Terraform pins AMI `ami-0a951420c495183dc`; verify owner, image name, architecture, availability, kernel, and region at preflight. | Provides a normal Linux host so driver and runtime setup is visible and teachable. | `lsb_release -a`, `uname -a`, `lscpu`, `free -h`, `lsblk`, `lspci`. |
| 2 | EC2 host | Systems Manager Agent and instance role | Prefer the agent supplied by the Canonical image; the scoped EC2 role must allow Systems Manager managed-instance operations. No inbound security-group rules. | Gives administrative access without SSH keys or open ports. | Confirm the agent service and the instance is Online in Systems Manager. |
| 3 | EC2 host | OS build and inspection tools | Install only required Ubuntu packages: matching `linux-headers-$(uname -r)`, compiler/build tools needed by the selected driver/toolkit, certificates, HTTPS/repository tools, `jq`, and Python virtual-environment support if a host-side script needs it. Resolve versions from the signed Ubuntu repository for the pinned image. | Matching headers enable driver modules; compiler tools build the CUDA sample; repository tools verify signed vendor repositories. | `dpkg-query`, `gcc --version`, `make --version`, and confirm header path matches `uname -r`. |
| 4 | EC2 host | NVIDIA Data Center compute driver | R580.196.11 candidate, compute/headless package set; the Ubuntu 24.04 NVIDIA repository exposes a matching pin package. Verify APT metadata signature and exact package names before install. | The kernel driver controls the physical L4 and makes it available to Linux and containers. | Reboot, reconnect with SSM, then `nvidia-smi`, `nvidia-smi -L`, and `nvidia-smi -q`; confirm one L4 and no driver error. |
| 5 | EC2 host | CUDA Toolkit and compiler | Toolkit-only package candidate `cuda-toolkit-13-0=13.0.3-1`. Do not install a meta-package that silently changes the driver. | `nvcc` compiles the CUDA C++ vector-add exercise. The toolkit is not needed just to run vLLM's container. | `nvcc --version`; compile the bounded sample; run it inside a GPU-enabled container or on the host. |
| 6 | EC2 host | Docker Engine, CLI, and Compose plugin | Install from Docker's signed Ubuntu repository; choose exact package versions and repository metadata during preflight, then record them. Do not use an unreviewed `curl | sh` installer. | Runs the single-GPU Compose application and observability stack. | `docker version`, `docker compose version`, `docker info`; verify the daemon is active. |
| 7 | EC2 host | NVIDIA Container Toolkit | Candidate package set `1.20.2-1`; verify all four package versions and signed repository metadata again. Configure Docker with `nvidia-ctk runtime configure --runtime=docker`, inspect the daemon change, then restart Docker. | Passes GPU device nodes and driver libraries into containers. | `docker info`; run a digest-pinned CUDA image with `--gpus all`, `nvidia-smi`, and a CUDA sample. |
| 8 | EC2 host or isolated container | Standalone PyTorch CUDA lab | Exact Python/PyTorch/CUDA wheel tuple is intentionally not pinned until the current official PyTorch selector is checked against the selected driver and CUDA runtime. Keep it isolated from vLLM's bundled Python/PyTorch. | Executes synchronized tensor allocation and matrix multiplication for GPU learning and benchmark comparisons. | Assert `torch.cuda.is_available()`, exactly one device named NVIDIA L4, allocate tensors, multiply, synchronize, and compare with CPU output. |
| 9 | EC2 host, Docker | vLLM OpenAI server | Candidate `vllm/vllm-openai:v0.34.0`; use only the freshly verified `linux/amd64` immutable image digest. Candidate CUDA 13.0 and bundled PyTorch 2.14.0. Never override its Torch libraries with an unrelated install. | Serves the model with a GPU-aware OpenAI-compatible API. | Confirm image digest, model revision, loaded CUDA model, `/health`, `/v1/models`, a real completion, and a streamed completion. |
| 10 | Model cache volume | Qwen model files | `Qwen/Qwen2.5-1.5B-Instruct`, revision `989aa7980e4cf806f80c7fef2b1adb7bc71aa306`, Apache-2.0 metadata, expected safetensors SHA-256 recorded in `RESEARCH_NOTES.md`. Recheck license and digest before download. | Provides the first small, open-weight model for measured L4 inference. | Verify the downloaded artifact digest before load; record the exact model revision. |
| 11 | Docker Compose network | Gateway (2 replicas), Redis, vLLM | Existing gateway image is built from this repository; Redis and vLLM image/model pins must match the reviewed Compose environment. Bind operator interfaces to loopback only. | Reuses existing authentication, tenant admission, shared quota, routing, and CPU/GPU runtime abstraction. | Health/readiness checks, authorized tenant request, denied tenant request, streaming, quota sharing across replicas. |
| 12 | Docker Compose network | DCGM Exporter, Node Exporter, Prometheus, Grafana, Alertmanager, OpenTelemetry Collector, Tempo, Redis exporter | Use the immutable image digests already in the single-GPU Compose profile; recheck registry manifests at preflight. | Measures GPU, host, gateway, Redis, vLLM, alert, and trace behavior without managed monitoring services. | Prometheus targets are healthy and real GPU/inference series move during a request; dashboard and alert drill use those series. |

## What does not belong on the host

- Do not install Kubernetes, kubelet, EKS components, or a multi-GPU scheduler. This
  project uses one standalone EC2 instance and Docker Compose.
- Do not install host Redis, MLflow, Prometheus, Grafana, Tempo, or vLLM if the pinned
  Compose containers provide those services. Avoid duplicate listeners and storage.
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
its own compatible CUDA libraries and PyTorch. This split avoids treating the host
Toolkit version as the same thing as the CUDA libraries inside the model image.

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
