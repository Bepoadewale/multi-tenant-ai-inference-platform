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
   count resources. The work-block table totals a ten-hour planned batch; set the
   exact approved expiry to match that session plan, subject to the Terraform guard
   that rejects expiries more than 12 hours after planning. Verify the guest shutdown
   timer is rendered and the separate one-time AWS scheduled-termination path is
   configured. Record the run-monitor ID, root, PID, and log path for Terraform
   mutation. Do not run concurrent Terraform operations against this state.
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

Run `make gpu-benchmark-plan` locally to validate the context-safe vLLM workload
matrix and inspect the exact prepared command list. It does not contact AWS, start
Docker, or send inference requests. The paid run uses
`benchmarks/gpu_inference/run_vllm_matrix.py` and stores aggregate results outside
the public repository; it omits per-request response capture. Direct vLLM results
do not include gateway overhead or multi-tenant quotas.
The runner verifies EC2 instance type and region through IMDSv2, confirms an NVIDIA
L4 is visible, limits a batch to 120 minutes by default, and times out a single run
after 10 minutes. These checks supplement, but do not replace, the independent
instance expiry and exact-cost approval.

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

Session Manager's Ubuntu shell user can use `sudo`, but Docker's socket is a root-level
control interface. Do not add the login user to the `docker` group just to avoid
`sudo`; membership would grant root-equivalent control. For Docker, Compose, and the
private release files, start a root shell from the repository directory and verify
the identity before continuing:

```bash
sudo -s
cd /path/to/multi-tenant-ai-inference-platform
id -u
pwd
```

`id -u` should print `0`. Replace the repository path with the actual checkout path.
Run the following host-side Docker and release-controller commands in this shell, and
type `exit` to leave it. Do not copy AWS or model-service credentials into shell
history.

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
The isolated PyTorch wheel and its hash-locked install procedure are documented in
the [CUDA performance lab guide](../../benchmarks/cuda_performance/README.md). Check
free disk before installation; do not add these libraries to the vLLM container.

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
deployment in `deployments/single-gpu/` be started. It runs one vLLM server, Redis, and
the existing two gateway replicas. Its `.env.example` contains provisional pins and
must be reviewed before use. Keep Redis and vLLM on the private Compose network; the
gateway ports bind to loopback and should be reached only through Session Manager
port forwarding. The profile reuses Redis quota accounting and is not physical GPU
isolation. Test readiness, shutdown, and restart once, then continue to multi-tenant
work without leaving duplicate model servers active. GPU Compose parsing is checked
locally with `make gpu-compose-config`.

For release preparation, the host controller hashes every file in the exact pinned
Hugging Face model snapshot. From the repository root on the **EC2 host**, run:

```bash
python3 scripts/gpu_release_controller.py model-digest \
  Qwen/Qwen2.5-1.5B-Instruct 989aa7980e4cf806f80c7fef2b1adb7bc71aa306
```

The command reads the project's model-cache volume and prints a SHA-256 digest over a
sorted manifest of relative file paths, file sizes, and each file's SHA-256. It uses
the full snapshot (configuration, tokenizer files, and weight files), resolves Hub
cache symlinks, and rejects links escaping the model cache. The command does not
download weights. This is the digest that the evaluator will record; after evaluation,
compare the resulting MLflow metadata and report with this value. Set
`GPU_MODEL_ARTIFACT_SHA256` to the output and `GPU_SOURCE_COMMIT` to the exact source
commit before running the evaluator. `GPU_MODEL_ID` is the underlying
model repository; the evaluator records it separately from the served API alias.
The evaluator also records the pinned vLLM image and a digest of the exact runtime
settings passed to vLLM. The release API checks those values against the finished
sanitized MLflow run. Never fill a digest by hand or from an unverified source.

The single L4 cannot keep a champion and candidate model loaded together. During a
candidate evaluation, the gateway replicas must be stopped so tenants cannot receive
the unapproved candidate. After the evaluation is exported to MLflow, restore the
recorded champion before creating or approving a plan:

```bash
docker compose --env-file deployments/single-gpu/.env \
  -f deployments/single-gpu/compose.yaml stop gateway-1 gateway-2
# Temporarily set the candidate model, revision, image, and runtime settings in .env.
docker compose --env-file deployments/single-gpu/.env \
  -f deployments/single-gpu/compose.yaml up -d --no-deps --force-recreate vllm
GPU_MODEL_ID="$(sed -n 's/^GPU_MODEL_ID=//p' deployments/single-gpu/.env)"
GPU_MODEL_REVISION="$(sed -n 's/^GPU_MODEL_REVISION=//p' deployments/single-gpu/.env)"
MODEL_ARTIFACT_DIGEST="$(python3 scripts/gpu_release_controller.py model-digest \
  "$GPU_MODEL_ID" "$GPU_MODEL_REVISION")"
sed -i "s/^GPU_MODEL_ARTIFACT_SHA256=.*/GPU_MODEL_ARTIFACT_SHA256=$MODEL_ARTIFACT_DIGEST/" \
  deployments/single-gpu/.env
docker compose --env-file deployments/single-gpu/.env \
  -f deployments/single-gpu/compose.yaml --profile gpu-evaluation run --rm evaluator
# Only after an initial champion has been initialized:
python3 scripts/gpu_release_controller.py restore-active
```

This block is for later candidate evaluation after a champion has been initialized.
For the first model, leave vLLM running after evaluation, build and verify the initial
champion manifest below, then initialize active state. The first run must not call
`restore-active` because there is no recorded champion yet. Candidate evaluation
causes service downtime. Evaluation is not deployment approval.

The authenticated gateway exposes `POST /gpu-release/v1/plans` for an operator with
the `platform.admin` role and `POST /gpu-release/v1/plans/{plan_id}/approve` for a
different identity with the `release.approve` role. Send no bearer token to shell
history or logs. The API records the plan, its champion/candidate manifests, and the
approver in a shared single-host SQLite volume. The API itself does not inspect the
running process or restart Docker. The host controller requires the exact target
environment `single-l4-lab`, an approved plan, and two distinct actors. It compares
the plan champion with a private active-release record, the live container command and
image, the model-cache volume, and a fresh digest of the full model snapshot. It
checks vLLM at host loopback port 8000 and each gateway replica at loopback ports 8081
and 8082. Compose maps these ports only to `127.0.0.1`; the security group has no
inbound rules. The controller updates only model-serving values in `.env`, restarts
only the `vllm` Compose service, starts the gateway replicas, and restores the previous
model if readiness fails. It checks service readiness, not an authenticated inference
request; perform the separate tenant smoke test after deployment.
It does not create a traffic-weighted canary or promise zero downtime. These controls
are locally fake-tested but have not run on EC2 or an L4.

For the initial model, after vLLM has loaded the pinned snapshot, calculate its digest
as shown above and set `GPU_MODEL_ARTIFACT_SHA256` in `.env` before evaluation. Run the
evaluator, then download the sanitized MLflow report to
`.local/gpu-release/initial-report.json` through the loopback-only MLflow UI. Create a
runtime configuration file that matches `.env` exactly, for example:

```json
{
  "served_model_name": "gpu-default",
  "dtype": "bfloat16",
  "max_model_len": 8192,
  "max_num_seqs": 2,
  "max_num_batched_tokens": 8192,
  "gpu_memory_utilization": 0.85,
  "tensor_parallel_size": 1
}
```

Create a champion manifest from that report and the digest just computed:

```bash
VLLM_IMAGE="$(sed -n 's/^VLLM_IMAGE=//p' deployments/single-gpu/.env)"
GPU_SOURCE_COMMIT="$(sed -n 's/^GPU_SOURCE_COMMIT=//p' deployments/single-gpu/.env)"
MODEL_ARTIFACT_DIGEST="$(python3 scripts/gpu_release_controller.py model-digest \
  Qwen/Qwen2.5-1.5B-Instruct 989aa7980e4cf806f80c7fef2b1adb7bc71aa306)"
python3 scripts/gpu_release_controller.py manifest-from-report \
  .local/gpu-release/initial-report.json \
  --model-id Qwen/Qwen2.5-1.5B-Instruct \
  --model-revision 989aa7980e4cf806f80c7fef2b1adb7bc71aa306 \
  --model-license Apache-2.0 \
  --model-artifact-sha256 "$MODEL_ARTIFACT_DIGEST" \
  --vllm-image "$VLLM_IMAGE" \
  --runtime-config .local/gpu-release/runtime-config.json \
  --source-commit "$GPU_SOURCE_COMMIT" \
  --alias champion \
  --output .local/gpu-release/champion.json
```

For the initial model, start both loopback-only gateway replicas so the controller can
verify their health endpoints, then initialize the active champion. For later model
changes, apply only an approved plan:

```bash
docker compose --env-file deployments/single-gpu/.env \
  -f deployments/single-gpu/compose.yaml up -d --no-deps gateway-1 gateway-2
python3 scripts/gpu_release_controller.py initialize /path/to/champion-manifest.json
python3 scripts/gpu_release_controller.py apply <approved-plan-uuid>
```

The apply command prompts for a short-lived `platform.admin` token without echoing or
storing it. If the process or instance stops during replacement, first run
`python3 scripts/gpu_release_controller.py recover`; it reapplies the last private
active manifest, verifies the model snapshot, and starts the gateway replicas. These
commands are prepared and fake-tested only; their first real execution requires the
authorized L4 batch.

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

The static direct-server matrix is defined in `benchmarks/gpu_inference/workloads.json`.
It starts with 256/64, 1,024/128, and 4,096/128 input/output token shapes; uses 100
measured prompts after five warm-ups and three repetitions; and holds short-prompt
concurrency 16 behind an explicit operator flag. Check measured GPU memory and actual
tokenizer/context behavior before enabling that level. A separate authenticated
gateway benchmark is still required to measure gateway overhead and tenant admission.

Run deterministic model evaluations only after inference is stable and MLflow/vLLM
health checks pass. Use the one-shot `evaluator` Compose profile to send the versioned
synthetic tasks to vLLM and upload the suite digest, model revision, aggregate gate
metrics, and sanitized report to the private MLflow tracking server. The MLflow
service uses SQLite and a local artifact directory on the encrypted instance volume;
its host port is loopback-only and reachable for review through Session Manager
forwarding. It is disposable, so export the evaluation artifact and run metadata before
teardown. Check that no prompt or completion text was logged. Demonstrate candidate
rejection and sequential known-good rollback. With one L4, do not claim concurrent
zero-downtime canary traffic. Perform incident drills only when their fault and
recovery procedures are staged and reversible. Store each real incident's failure and
recovery evidence separately.

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
NVIDIA driver R580.196.11; CUDA Toolkit 13.0.3; NVIDIA Container Toolkit `1.20.2-1`;
Docker Engine 29.9.3 and Compose plugin 5.8.0; PyTorch `2.14.0+cu130` for CPython
3.12; and the vLLM OpenAI image `v0.34.0` with an AMD64 digest. These are **not final
pins** and no compatibility has been proven on the L4. vLLM's current official Docker guide says CUDA 13 images need
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
