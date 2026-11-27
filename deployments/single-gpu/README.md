# Single-GPU Compose profile

This profile runs the vLLM model server, two existing FastAPI gateway replicas, and
shared Redis on one EC2 host, with a prepared metrics and tracing stack. It is separate
from the local CPU Compose stack and the future EKS contract. The two gateways share
Redis state; they are not two independent GPU servers or a high-availability
deployment.

## Model routing

The profile sets `INFERENCE_VLLM_URL`. When that variable is present, the catalog
changes only `chat-default` to one 100%-weighted vLLM target and reads the API model
name from `INFERENCE_GPU_MODEL_ID`. Without this variable, the catalog retains the
existing ONNX CPU model ID, two weighted targets, and their current behavior. Tenant
authorization remains in the gateway.

The gateway `/healthz` response checks the selected inference backend and capacity
state. It returns HTTP 503 if vLLM or shared Redis admission state is unavailable.
This makes Docker's health check reflect the actual configured runtime; it does not
replace a real inference smoke request.

`SIMULATED_GPU_POOL` and the existing `SIMULATED_GPU_POOL_SLOTS` setting name a
Redis-backed **logical admission counter** retained from the local capacity feature.
It does not schedule CUDA work, measure VRAM, reserve physical GPU memory, or isolate
tenants at the device level. The vLLM server has one GPU and a configured sequence
limit; actual safe concurrency must be established from measured memory and runtime
behavior. The two gateway replicas share this counter because they use the same
Redis service.

## Configuration

`.env.example` contains the researched vLLM image digest and Qwen model revision as
provisional candidates. Recheck them before a paid run. Do not replace the immutable
image digest with a mutable tag. The Compose file requests exactly one NVIDIA GPU,
keeps Redis and vLLM off host-published ports, and publishes the gateway ports only
on loopback. Prometheus, Grafana, and Alertmanager also bind only to host loopback.
DCGM Exporter and the OpenTelemetry Collector (OTel Collector) have no published host
ports. Node Exporter shares the host network so it can observe host network counters;
it uses a read-only host-root mount, drops Linux capabilities, and publishes no Docker
port. The AWS security group must have no inbound rules. Use Systems Manager Session
Manager port forwarding to reach a loopback service from an administrator's
workstation.

The vLLM server uses the stable served model alias `gpu-default`; the gateway passes
that alias in its OpenAI-compatible request. Model revision, BF16, 8,192-token
context, two sequences, and 85% vLLM memory utilization are conservative starting
settings, not verified safe values. The selected v0.34.0 release changes KV-cache
sizing behavior and recommends letting the runtime size the cache in many cases. The
profile keeps an explicit 85% cap for the first bounded experiment; confirm the exact
meaning and behavior against the current release before starting, then inspect GPU
memory during real requests before changing limits. This setting is not a measured
capacity guarantee.

## GPU, host, and inference observability

This profile adds DCGM Exporter for GPU hardware, Node Exporter for Linux host
metrics, Redis Exporter for Redis health and usage, Prometheus for short-term metric
storage, Grafana dashboards, Alertmanager, a profile-specific OpenTelemetry Collector, and Tempo for
traces. The profile collector deletes known sensitive URL, authorization, cookie,
request/response-body, GenAI prompt/completion, and database-statement attributes
before export and does not log spans to stdout. This is defense in depth; operators
must still inspect emitted span attributes before relying on traces. Both vLLM and DCGM Exporter are
granted visibility to the same single L4 so vLLM can compute and DCGM can read
telemetry. That is shared device access, not GPU partitioning or tenant isolation.
DCGM uses a small non-profiling field list, so the container does not request
`SYS_ADMIN` for performance counters.

The dashboard uses DCGM Exporter 4.9 metric names and units: GPU busy time is a
0-to-1 ratio, and framebuffer memory is in bytes. vLLM V1 metric names use the
`vllm:` prefix. The Prometheus rule thresholds are laboratory diagnostics, not
production service-level objectives. Alertmanager shows alerts in its local UI and
sends no external notifications. Prometheus, Grafana, Alertmanager, and Tempo store
their short-lived data in memory-backed filesystems; a restart loses that data.
Export evidence before stopping the profile.

The exporter and observability image references are pinned to registry digests. The
profile-specific collector configuration is validated with the pinned Contrib image. The
digests were read from registry manifests without downloading the image layers. They
are static candidates, not proof that the images run correctly with the final NVIDIA
driver on an L4.

## Static configuration check

From the repository root:

```bash
make gpu-compose-config
```

This parses the Compose document with the sample candidate pins. It does not pull the
image, connect to a GPU, check the runtime, download model weights, or run inference.
It also does not execute Prometheus rules, create traces, check exporter metric
availability, or test a Grafana login.

## Future EC2 run

Before starting this profile, generate the non-production local Ed25519 test identity
using the repository's documented workstation setup, make sure the public key is
available at `.local/identity/public.pem`, and connect to the EC2 host with Session
Manager. From the repository directory on that host, copy the sample environment file,
replace its placeholder Grafana password with a fresh secret, and confirm model/image
pins against the current official sources. Keep `.env` out of Git. After driver and
Docker GPU access are independently verified:

```bash
cp deployments/single-gpu/.env.example deployments/single-gpu/.env
# Edit deployments/single-gpu/.env and replace the password placeholder.
docker compose --env-file deployments/single-gpu/.env \
  -f deployments/single-gpu/compose.yaml up --build --detach
docker compose --env-file deployments/single-gpu/.env \
  -f deployments/single-gpu/compose.yaml ps
```

Expected state is healthy Redis, vLLM, and both gateways. vLLM may take several
minutes to download model files and initialize; a running container is not ready
inference. Check `/health`, `/v1/models`, a non-streaming request, and a streamed
request through the gateway using a synthetic signed tenant identity. Keep the ports
on loopback and use Session Manager forwarding. Verify Prometheus targets at
`http://localhost:9090/targets`, dashboards at `http://localhost:3002`, and active
alerts at `http://localhost:9093`. Check the actual `/metrics` samples before relying
on a dashboard expression. Check traces in Grafana only after confirming an inference
request has a trace and that its span contains no prompt, response, token, or secret.
Export sanitized logs, metrics, traces, and screenshots before stopping the stack:

```bash
docker compose --env-file deployments/single-gpu/.env \
  -f deployments/single-gpu/compose.yaml down
```

This command removes containers and the default network. It intentionally preserves
the named model-cache and Redis volumes. Do not delete those volumes without
reviewing whether evidence or model artifacts need to be retained; the Terraform
instance teardown deletes the encrypted root volume according to the reviewed plan.
The commands in this section are prepared instructions, not yet executed on AWS.
