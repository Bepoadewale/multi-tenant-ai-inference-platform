# Single-L4 GPU Batch Runbook

**Status:** prepared procedure; no host step or GPU command in this document has
been executed on an L4. **Last source review:** 2026-11-27. Recheck current prices,
quota, software artifacts, and model revision immediately before any paid session.

This runbook turns the prepared repository into one short, evidence-rich GPU work
window after AWS approves the quota. It groups paid work so the instance is not left
running while code, documents, CI, or reviews are handled. It is a plan, not approval
to create resources.

## Gates before any paid operation

All checks below must pass before the GPU root is applied.

1. **Quota:** verify the configured key profile with
   `AWS_PROFILE=ai-platform-pilot-key aws sts get-caller-identity`; check the applied
   On-Demand G/VT quota in `us-east-1` is at least four vCPUs. An email or request
   marked open is not approval. Check the selected AZ's G6 offering separately; an
   offering does not reserve capacity.
2. **Repository:** read the latest goal, execution journal, open PRs, and this
   runbook. Start only from a clean reviewable commit with the required static checks
   passing. Confirm the vLLM adapter, gateway behavior, Compose stack, benchmark
   harness, evaluation set, incident drill, and evidence export commands are already
   prepared. Avoid spending GPU time to edit scripts.
3. **Tools and state:** run `aws --version`, `terraform version`, `ansible --version`,
   `docker compose version`, and the project validation target. The current read-only
   baseline says the shared encrypted/versioned Terraform state bucket, DynamoDB lock
   table, and project budget are absent. Bootstrap those only through their own
   reviewed and authorized plan. The GPU Terraform root requires both lock mechanisms.
4. **Price and budget:** refresh the EC2 G6, public IPv4, 100-GiB gp3, object storage,
   state-lock, scheduler, data transfer, and tax/reserve estimates from current AWS
   sources. Calculate the whole experiment, not just instance runtime. The hard cap is
   **USD $25 total**. Stop if the full estimate or a reasonable overrun reserve cannot
   fit under $25. A budget alert is not a hard limit.
5. **Exact plan and expiry:** run the account/region/quota/AMI/availability preflight,
   save and review the exact remote-state plan, record its SHA-256, and independently
   count resources. Confirm the six-hour instance expiry is present in the reviewed
   plan, the guest shutdown timer is rendered, and the separate one-time AWS
   scheduled-termination path is configured. Record the run-monitor ID, root, PID,
   and log path for Terraform mutation. Do not run concurrent Terraform operations
   against this state.
6. **Approval:** obtain explicit owner approval for that exact plan, total estimated
   cost, maximum session runtime, resource list, and teardown procedure. Quota
   approval alone does not authorize apply. If any prerequisite fails, do static
   work only.

## Batch design

The allocation below is a planning ceiling, not a promise that each task will finish
within it. It leaves room within the requested 8–12 cumulative GPU-hour target for
recovery. Stop the instance between sessions and record actual instance-hours. Do not
start an optional experiment if a required acceptance gate or the $25 reserve is at
risk.

| Work block | Planned ceiling | Required output before moving on |
| --- | ---: | --- |
| Boot and inventory | 0.5 h | Real L4, Ubuntu, kernel, memory, disk, and SSM evidence |
| Manual driver, CUDA, Docker, and PyTorch | 1.5 h | Host driver plus synchronized host/container GPU computation |
| Manual vLLM and model validation | 1.5 h | Model artifact verification, server readiness, real streamed response |
| Gateway, Redis, tenant, and failure-path integration | 1.5 h | Authenticated tenant requests, quotas, and safe rejection evidence |
| Metrics, dashboards, and alert drill | 1.0 h | Live GPU/inference data, a correlated trace, one real controlled alert |
| Benchmarks and evaluation | 2.0 h | Raw measurements, metadata, deterministic evaluation output |
| Release/rollback and incident recovery | 1.0 h | Candidate gate and sequential rollback; a real recovery record |
| Evidence export, stop, destroy, independent cleanup verification | 1.0 h | Sanitized export, destroy record, scoped resource absence checks |
| **Total planned ceiling** | **10.0 h** | Stop early if all required evidence is complete. |

If an experiment cannot finish within the approved window, preserve the real partial
result, stop the instance safely, and update the estimate before requesting another
GPU batch. Do not extend the window silently.

## Before launch: stage locally

Run these on the **local workstation**, from the focused branch that contains the
prepared scripts. They are static checks and do not launch AWS resources.

```bash
git status --short --branch
make verify
make terraform-validate
make gpu-ec2-validate
make gpu-ec2-preflight
```

`make verify` checks the local gateway, dependencies, and Compose syntax.
`make terraform-validate` checks Terraform roots without applying them.
`make gpu-ec2-validate` checks the dedicated EC2 environment's static configuration.
`make gpu-ec2-preflight` checks account, region, requested instance type, quota,
availability, and other implemented launch guards. Confirm the output does not print
credentials. Record failures; do not bypass a guard to keep the schedule.

Before the paid window begins, prepare and review:

- the exact Terraform saved plan and checksum;
- a current resource cost calculation with line items and cost assumptions;
- the exact maximum runtime and absolute expiry timestamp;
- the model revision, container image digest, package versions, and test workload;
- the benchmark matrix and evaluation inputs;
- commands to collect logs, metrics, traces, benchmark JSON, and sanitized screenshots;
- the post-destroy AWS verifier and a list of exactly scoped project resource filters.

Do not put the saved plan, Terraform state, AWS output containing identifiers, model
weights, private data, or credentials in public Git.

## Provision and secure access

On the **local workstation**, after the exact plan receives explicit approval:

```bash
make gpu-ec2-plan
# Review the exact plan and checksum with the owner before continuing.
make gpu-ec2-apply
```

The apply wrapper must verify the planned digest and the expected account before
Terraform can create resources. This creates one `g6.xlarge` only. Use Systems
Manager Session Manager from the local workstation for host administration; do not
open an SSH or application port to the internet. Confirm the instance is SSM-online
before running package installation. If the apply result is uncertain, inspect its
existing PID-based monitor and log; do not rerun Terraform or issue duplicate cloud
calls.

## Host inventory and manual GPU setup

Run on the **EC2 host through Session Manager**. Capture outputs to a sanitized local
evidence bundle. These are commands to execute during the future session, not results
already observed:

```bash
uname -a
lscpu
free -h
lsblk
lspci -nn | grep -i -E 'nvidia|3d controller|vga'
lsmod | grep -E '^nvidia'
nvidia-smi
nvidia-smi -L
nvidia-smi -q
```

Confirm Ubuntu 24.04 x86-64, one NVIDIA L4, expected memory, the encrypted root disk,
and an active NVIDIA kernel driver. An empty `lsmod`/failed `nvidia-smi` before driver
installation is expected; record it as the initial state. After the driver install,
an empty device list or a kernel-module error is a stop condition. Check the running
kernel and matching headers before changing packages.

Install the researched **compute-only/headless** NVIDIA driver using the supported
Ubuntu package method, with kernel headers for the running kernel. Pin the selected
driver branch/version only after checking the current NVIDIA package index and its
CUDA compatibility. Reboot through Session Manager's supported workflow, reconnect,
then verify `nvidia-smi`, `nvidia-smi -L`, and `nvidia-smi -q`. Do not install an old
`.run` file over distribution-managed packages. Avoid switching kernel or driver
branches mid-session unless the documented recovery path is available.

Install Docker Engine and the NVIDIA Container Toolkit from their signed official
repositories. Pin the toolkit package set. Run `nvidia-ctk runtime configure
--runtime=docker`, inspect the resulting daemon configuration, restart Docker, and
verify `docker info`. Do not assume a successful host `nvidia-smi` proves Docker GPU
access.

Run a minimal pinned CUDA base image with `--gpus all` and execute its device-query
or sample workload. Record the immutable image digest and output. Then run PyTorch
GPU validation: print `torch.__version__`, `torch.version.cuda`,
`torch.cuda.is_available()`, device name, and memory; allocate CUDA tensors; multiply
matrices; call `torch.cuda.synchronize()` before timing; verify the result and observe
nonzero GPU activity during the workload. A CPU fallback is a failed GPU check.

The current vendor docs recommend distribution packages on Ubuntu and describe a
headless driver path. The exact driver and Toolkit packages are deliberately not
hard-coded here: the checked project candidate set is dated and must be reconciled
with the image and driver compatibility matrix at launch time.

## Manual vLLM model serving

First serve the model **manually**, before using Docker Compose. Confirm free disk and
GPU memory, then download only the pinned Qwen 1.5B model revision. The current
research record lists revision `989aa7980e4cf806f80c7fef2b1adb7bc71aa306`, Apache-2.0
metadata, and an expected weight-file digest; recheck the model card, file manifest,
license, and the repository artifact verifier before download. Do not expose or save
any Hugging Face token; this public model is expected to be retrievable without one,
but confirm current access requirements.

For the first pass, use the candidate pinned official `vllm/vllm-openai` image digest
recorded in `RESEARCH_NOTES.md`, after rechecking its architecture, release notes, L4
support, bundled PyTorch/CUDA versions, and host driver minimum. Never use `latest`.
The candidate startup settings should be conservative: one GPU, BF16 only if the live
runtime reports support, 8,192 token context, and a low maximum sequence count. Do
not increase context or concurrency until GPU memory telemetry proves the setting
fits with margin. Keep the manual server bound to loopback or an internal-only
container network.

```bash
docker run --rm --name vllm-manual --gpus all --ipc=host \
  -p 127.0.0.1:8000:8000 \
  -v /opt/model-cache:/root/.cache/huggingface \
  vllm/vllm-openai@sha256:<reviewed-image-digest> \
  --model Qwen/Qwen2.5-1.5B-Instruct \
  --revision <reviewed-model-revision> \
  --dtype bfloat16 --max-model-len 8192 --max-num-seqs 2
```

The digest and revision placeholders are intentionally unresolved until the final
preflight. Execute from the **EC2 host**, after exporting only non-secret variables
if the chosen model source needs them. For the approved artifact, use the existing
sanitized verifier before model load. Check `/health` and the OpenAI-compatible
`/v1/models` endpoint locally, send one deterministic non-sensitive prompt, then
send a short streamed prompt. Record first-token time, total response time, token
counts, server logs, and `nvidia-smi` before/during/after. Redact prompts and response
content from public evidence. A healthy HTTP process without a successful CUDA model
load is not a passing inference check.

Only after the manual request and stream work should the **single-GPU Docker Compose**
deployment be started. Keep Prometheus, Grafana, Tempo, Redis, gateway, and model
server on private Compose networks. Access operator views only through Session
Manager port forwarding. Test readiness, shutdown, and restart once, then continue to
multi-tenant work without leaving duplicate model servers active.

## Gateway, telemetry, measurements, and recovery

Use the prepared test tenants: customer support, internal engineering, and research.
For each, capture successful authenticated inference, unauthorized model denial,
invalid identity rejection, spoofed-header rejection, request/token/concurrency
quota rejection, and a short stream. Confirm Redis meters across both gateway
replicas and that failed/cancelled requests release concurrency reservations.
Simulate Redis loss and one gateway restart with the prepared bounded drill. Do not
record customer prompts or secrets.

Start DCGM Exporter, Node Exporter, Prometheus, Grafana, Alertmanager, and Tempo only
after the model and gateway are ready. Verify scrape targets and real series before
the benchmark. Capture utilization, framebuffer memory, temperature, power if
exposed, GPU clocks, CPU/memory/disk, vLLM queue/cache, gateway latency, request/token
counts, errors, and traces. Run one alert drill after checking the expression against
live samples; avoid concurrent Nsight/DCGM profiling-counter collection.

Run the prebuilt benchmark matrix in order: one warm single request; concurrency 1,
2, 4, 8 (and 16 only if capacity allows); a small set of context/output lengths;
then the prepared tenant-contention and overload cases. Warm up, use monotonic
clocks, synchronize GPU measurements, record repeated samples, and preserve raw
JSON outside public Git. Do not compare results when prompt/output shapes differ.
Stop a test on out-of-memory, runaway queue growth, disk pressure, or when remaining
runtime/cost reserve becomes insufficient.

Run deterministic model evaluations and release checks only after inference is
stable. Demonstrate candidate rejection and sequential known-good rollback. With one
L4, do not claim concurrent zero-downtime canary traffic. Perform the incident drills
only when their fault and recovery procedures are staged and reversible. Store each
real incident's failure and recovery evidence separately.

## Evidence export and teardown

Before ending the paid window, copy sanitized outputs to the reviewed evidence
location and update the manifest with date, commit, instance/GPU/software/model
metadata, and what each file proves. Uploading evidence to a paid external service is
not assumed; include storage and transfer in the cap. Confirm no sensitive prompt,
token, IP, account ID, private key, raw Terraform state, or saved plan is public.

Then stop the Compose stack, export logs/metrics/traces, stop or terminate the
instance through the reviewed project teardown wrapper, and use the project-only
read-only cleanup verifier. A termination request is not cleanup proof: verify
instance termination, delete-on-termination volume handling, and scoped project
network, IAM, Scheduler, and address resources. Do not remove the shared backend or
other projects' resources. Record estimated runtime cost and retrieve actual billing
evidence when available. Until billing settles, label it as an estimate.

## Current research set and compatibility decision

The 2026-11-27 research record contains provisional candidates: Ubuntu 24.04 amd64;
NVIDIA driver package branch/version candidate R580; CUDA Toolkit candidate 13.0.3;
NVIDIA Container Toolkit `1.20.2-1`; and an official vLLM OpenAI image candidate
`v0.34.0` with an AMD64 digest. These are **not final pins** and no compatibility has
been proven on the L4. vLLM's current official Docker guide says CUDA 13 images need
an R580-or-newer host driver normally and describe an explicit compatibility mode
for selected older driver branches; prefer a compatible native driver instead of
enabling compatibility implicitly. PyTorch should be installed from the official
selector for the chosen CUDA build. The standalone container provides its own CUDA
user-space libraries, so the host CUDA Toolkit is needed for `nvcc`/CUDA C++ labs but
not merely to run that container.

Before launch, recheck these official sources and update the compatibility record:

- [AWS G6 instances](https://aws.amazon.com/ec2/instance-types/g6/) and [EC2 accelerated instance guide](https://docs.aws.amazon.com/ec2/latest/instancetypes/ac.html): L4 model, vCPU/RAM/VRAM, storage/network capabilities, and supported region/AZ.
- [NVIDIA Ubuntu driver installation guide](https://docs.nvidia.com/datacenter/tesla/driver-installation-guide/latest/ubuntu.html): running-kernel headers, signed repository, driver pinning, headless packages, reboot and verification.
- [NVIDIA CUDA Linux installation guide](https://docs.nvidia.com/cuda/cuda-installation-guide-linux/): supported Ubuntu/kernel/compiler matrix and toolkit installation without an unintended driver replacement.
- [NVIDIA Container Toolkit install guide](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html): supported host driver, signed apt repository, pinned packages, Docker runtime setup.
- [PyTorch install selector](https://docs.pytorch.org/get-started/locally/) and [CUDA availability check](https://docs.pytorch.org/docs/stable/generated/torch.cuda.is_available.html): matching wheel and actual device validation.
- [vLLM GPU install guide](https://docs.vllm.ai/en/stable/getting_started/installation/gpu/), [Docker guide](https://docs.vllm.ai/en/latest/deployment/docker/), [engine arguments](https://docs.vllm.ai/en/latest/configuration/engine_args/), and [Qwen2.5-1.5B-Instruct model card](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct): supported runtime, image and model constraints.
- [NVIDIA DCGM Exporter](https://github.com/NVIDIA/dcgm-exporter) and [Prometheus getting started](https://prometheus.io/docs/prometheus/latest/getting_started/): metric collection and target validation.

## Failure stop conditions

Stop and preserve diagnostics if the AWS account/region differs, applied quota is
below four, the exact plan differs, the price envelope exceeds the cap, the expiry
mechanism is absent, SSM is unavailable, the host image/architecture differs, the L4
is missing, the driver fails to load, Docker cannot see the GPU, model integrity
fails, vLLM reports incompatible kernels, GPU memory approaches exhaustion, prompts
appear in telemetry, shared tenant accounting fails, a reservation leaks, or teardown
verification finds a project resource left behind. Investigate without rerunning
mutations until current state is known.

## Evidence status

This document is static preparation. It does not demonstrate quota approval,
availability/capacity, infrastructure, installed software, model download, GPU
execution, inference, benchmark measurements, alert behavior, incidents, or teardown.
