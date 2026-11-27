# Single-GPU Compose profile

This profile runs the vLLM model server, two existing FastAPI gateway replicas, and
shared Redis on one EC2 host. It is separate from the local CPU Compose stack and the
future EKS contract. The two gateways share Redis state; they are not two independent
GPU servers or a high-availability deployment.

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
on loopback. The cloud security group must still have no inbound rules. Use Session
Manager port forwarding to reach the loopback gateway from an administrator's
workstation.

The vLLM server uses the stable served model alias `gpu-default`; the gateway passes
that alias in its OpenAI-compatible request. Model revision, BF16, 8,192-token
context, two sequences, and 85% vLLM memory utilization are conservative starting
settings, not verified safe values. Confirm model integrity and compatibility first,
then inspect GPU memory during real requests before changing limits.

## Static configuration check

From the repository root:

```bash
make gpu-compose-config
```

This parses the Compose document with the sample candidate pins. It does not pull the
image, connect to a GPU, check the runtime, download model weights, or run inference.

## Future EC2 run

Before starting this profile, generate the non-production local Ed25519 test identity
using the repository's documented workstation setup, make sure the public key is
available at `.local/identity/public.pem`, and connect to the EC2 host with Session
Manager. From the repository directory on that host, after driver and Docker GPU
access are independently verified:

```bash
make gpu-compose-config
docker compose --env-file deployments/single-gpu/.env.example \
  -f deployments/single-gpu/compose.yaml up --build --detach
docker compose --env-file deployments/single-gpu/.env.example \
  -f deployments/single-gpu/compose.yaml ps
```

Expected state is healthy Redis, vLLM, and both gateways. vLLM may take several
minutes to download model files and initialize; a running container is not ready
inference. Check `/health`, `/v1/models`, a non-streaming request, and a streamed
request through the gateway using a synthetic signed tenant identity. Keep the ports
on loopback and use Session Manager forwarding. Export sanitized logs and metrics
before stopping the stack:

```bash
docker compose --env-file deployments/single-gpu/.env.example \
  -f deployments/single-gpu/compose.yaml down
```

This command removes containers and the default network. It intentionally preserves
the named model-cache and Redis volumes. Do not delete those volumes without
reviewing whether evidence or model artifacts need to be retained; the Terraform
instance teardown deletes the encrypted root volume according to the reviewed plan.
The commands in this section are prepared instructions, not yet executed on AWS.
