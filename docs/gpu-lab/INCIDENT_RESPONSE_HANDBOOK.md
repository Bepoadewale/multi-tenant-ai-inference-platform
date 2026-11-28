# GPU Inference Incident Response Handbook

This handbook is an operator procedure for the isolated, single-L4 lab. It combines
the failures already seen in local CI with diagnostic paths for future AWS and GPU
incidents. The driver, GPU, vLLM, and cloud scenarios below are prepared procedures;
they have not been injected on an L4. Do not report them as completed drills.

## Operating boundaries

- Confirm the current project goal, AWS account, region, quota, Terraform state, and
  resource inventory before touching infrastructure. The latest applied G/VT quota
  is `4.0` vCPUs, but request history still says `CASE_OPENED`; recheck quota and live
  capacity before any plan or apply. Do not treat the quota value as permission to
  launch.
- The project spending ceiling is USD $25. An alert is not a hard cap. Follow the
  approved run window and expiry in the [GPU batch runbook](GPU_BATCH_RUNBOOK.md).
- Use only the project Terraform root, exact reviewed plan, project tags, and
  Systems Manager (SSM) Session Manager. The planned security group has no ingress.
- Do not run global Docker cleanup, broad account cleanup, unbounded load, or an
  unreviewed driver/kernel change. Preserve useful output before stopping a service.
- Do not collect prompts, completions, bearer tokens, private keys, model access
  credentials, raw Terraform state, or unreviewed environment files in public
  evidence.

## Fast triage

Start by answering these in order:

1. **What failed?** Record the UTC time, request ID if available, affected tenant
   class (synthetic name only), service endpoint, status code, and whether the issue
   affects every request or one workload shape.
2. **Where did the request stop?** Check gateway logs and metrics, Redis health,
   vLLM readiness and model listing, then host/GPU signals. Follow the request path
   from client to gateway to admission to model server.
3. **Is it a dependency outage or an application defect?** Look for a connection or
   timeout at a service boundary and compare the response with the documented error
   mapping. Do not turn a known missing dependency into a misleading HTTP 500.
4. **Is capacity exhausted?** Check queue depth, active requests, GPU memory,
   vLLM waiting/running sequences, host memory, and disk. Do not raise concurrency
   or memory settings before collecting the current evidence.
5. **Can it be recovered safely?** Stop new work, preserve sanitized evidence, use
   the smallest scoped recovery, and verify readiness plus a synthetic inference
   request. Record start and recovery timestamps.

Record symptom and cause separately. “Gateway returned 503” is a symptom; “Redis
could not serve the shared admission read” is a cause only after logs or a controlled
test establish it.

## Safe evidence capture

Run host commands through SSM. Use exact project paths and retain output outside the
public repository when it contains account or host identifiers.

```bash
date -u +%FT%TZ
docker compose --env-file deployments/single-gpu/.env \
  -f deployments/single-gpu/compose.yaml ps
docker compose --env-file deployments/single-gpu/.env \
  -f deployments/single-gpu/compose.yaml logs --since 10m --tail 300 gateway-1 gateway-2 redis vllm
nvidia-smi
free -h
df -h
```

These commands show service state, recent container logs, host-visible GPU status,
host memory, and disk pressure. Review logs before exporting: redact IDs, addresses,
headers, prompt text, completion text, and secret values. Avoid `docker inspect` or
`env` output in public evidence unless sanitized first.

If the service stack is already stopped, do not start it merely to gather logs. Use
the existing Terraform run monitor and recorded evidence first. Never repeat a
Terraform apply or destroy whose outcome is uncertain; reconcile the existing log,
state, and AWS inventory.

## Decision tree: the L4 is not visible on the host

**Signals:** `nvidia-smi` fails, shows no GPU, or reports that it cannot communicate
with the driver.

1. Confirm the host is the approved `g6.xlarge` in `us-east-1` through the instance's
   IMDSv2 data and the project run record.
2. Inspect the PCI device and current kernel:

   ```bash
   uname -r
   lspci -nn | grep -i -E 'nvidia|3d controller|vga'
   lsmod | grep -E '^nvidia'
   dkms status
   journalctl -k -b --no-pager | grep -i -E 'nvidia|nvrm|xid'
   ```

3. If the PCI device is absent, stop: this points to instance/GPU exposure or an
   AWS host issue, not a container problem. Preserve the instance type and sanitized
   command results for the AWS case.
4. If the PCI device exists but the module is missing or failed, compare the running
   kernel, installed kernel headers, driver package, and driver build log. Do not
   install a second driver branch or run an NVIDIA `.run` installer over Ubuntu
   packages.
5. Reboot only through the prepared SSM procedure and only within the approved
   instance window. After reconnecting, recheck `nvidia-smi -L` and `nvidia-smi -q`.
6. If host discovery is still broken, stop the GPU batch and use the documented
   driver recovery path. Do not proceed to Docker, PyTorch, or model loading.

## Decision tree: the host sees the L4 but Docker does not

**Signals:** host `nvidia-smi` works, but a CUDA container sees no device or its
runtime cannot initialize CUDA.

1. Check Docker server configuration and NVIDIA runtime setup:

   ```bash
   docker info
   nvidia-ctk --version
   sudo cat /etc/docker/daemon.json
   ```

2. Confirm NVIDIA Container Toolkit configuration was applied to Docker, then
   restart only the Docker service using the Ansible role's documented handler.
3. Run the pinned minimal CUDA image with `--gpus all`; verify device discovery in
   that container before testing the larger vLLM image.
4. Compare container image CUDA requirements with the host driver support. The
   `nvidia-smi` CUDA field is a driver compatibility level, not proof of which
   Toolkit or runtime library is installed.
5. If the minimal container fails, do not diagnose vLLM yet. Preserve the Docker
   daemon configuration and sanitized runtime error, then restore the reviewed
   daemon configuration.

## Decision tree: CUDA or PyTorch runs on CPU or fails

**Signals:** `torch.cuda.is_available()` is false, device allocation fails, a
computation silently uses CPU, or synchronization raises an error.

1. Print `torch.__version__`, `torch.version.cuda`, the availability result, and the
   device name. Confirm the process runs inside the pinned CUDA-enabled environment.
2. Check device visibility from the same host/container and compare PyTorch's CUDA
   runtime with the host driver's supported API level.
3. Explicitly allocate tensors on `cuda`, perform matrix multiplication, call
   `torch.cuda.synchronize()`, and check both output values and device activity.
4. Treat any CPU fallback as a failed GPU check. Do not record CPU output as GPU
   evidence or use unsynchronized wall-clock timing.
5. If the test fails, preserve the smallest reproduction, versions, and complete
   sanitized error; do not reinstall packages until the compatibility matrix has
   been reviewed.

## Decision tree: vLLM does not become ready

**Signals:** the container starts but `/health` or `/v1/models` is not ready, the
gateway health check returns 503, or the model never becomes available.

1. Check vLLM startup logs for artifact download, revision, license or integrity
   errors, unsupported architecture, CUDA initialization, out-of-memory, or context
   configuration messages.
2. Check free root-disk space and model-cache mount before retrying downloads. Do
   not print Hugging Face credentials or copy model files into public Git.
3. Confirm the exact pinned model revision, serving image digest, served alias,
   configured context length, precision, and GPU memory setting agree across the
   release manifest and Compose environment.
4. Verify a real GPU is visible to vLLM and distinguish “container running” from
   model readiness. Check `/v1/models`, then perform one authenticated synthetic
   request through the gateway.
5. If startup failed from an incorrect setting, record the actual failure before
   applying a reviewed configuration correction. Do not alter several memory and
   concurrency settings at once.

## Decision tree: CUDA out of memory or growing latency

**Signals:** vLLM logs a CUDA out-of-memory error, GPU memory approaches capacity,
time to first token grows, queueing rises, or requests begin timing out.

1. Stop adding load. Save timestamps, model revision, request lengths, max output
   tokens, concurrency, vLLM sequence limit, and sanitized error details.
2. Compare GPU framebuffer use and utilization with vLLM running/waiting sequences,
   cache utilization, host CPU/RAM, and queue wait. A high queue with low GPU use
   may indicate another bottleneck.
3. Check whether the failure aligns with longer prompt/context, more output tokens,
   or more active sequences. The KV cache grows with active tokens, layers, precision,
   and concurrent sequences.
4. Recover by reducing the smallest relevant dimension (load, context, or permitted
   concurrency) through a reviewed configuration change, then restart only the
   service in scope and verify a short request.
5. Do not raise the vLLM memory-utilization percentage or assume quantization solves
   the issue without checking weight size, cache needs, kernels, quality, and startup
   headroom. Record an actual GPU memory failure only if it occurred on the L4.

## Decision tree: tenant requests fail or are throttled

**Signals:** HTTP 401/403/429/503, a queue rejection, or one synthetic tenant affects
the others.

1. Record only the synthetic tenant name and status/reason. Never capture the bearer
   token or full request in the incident record.
2. For 401, check token signature, issuer, expiry, and configured public key. For
   403, check server-derived tenant identity and model permission; ignore any
   caller-supplied tenant header.
3. For 429, inspect request/token/concurrency quota and queue decisions in shared
   Redis. Distinguish the tenant limit from the single engine's actual sequence cap.
4. For 503, check Redis, shared rollout state, tokenizer availability, selected
   backend health, and model readiness. The gateway should fail closed when it
   cannot establish policy or capacity state.
5. After recovery, verify active leases, queue counters, and a request through each
   gateway replica. Do not claim physical GPU isolation from a successful logical
   quota test.

## Decision tree: Redis or one gateway replica fails

**Signals:** one or both gateways return 503, readiness fails, or tenant limits
appear inconsistent.

1. Check Redis `PING`, both gateway `/healthz` endpoints, and recent logs. Do not
   infer shared-state health from only one replica.
2. If Redis is unavailable, preserve the fail-closed 503 and stop new benchmark
   traffic. Do not temporarily switch to process-local quota state.
3. If one gateway is unhealthy but the other is healthy, record the host/container
   failure and route the synthetic smoke request to the healthy loopback endpoint
   only while the approved test procedure permits it.
4. Restore Redis or the affected gateway, then verify both gateway readiness
   endpoints and shared lease accounting.
5. The recorded [local Redis incident](incidents/INCIDENT-LOCAL-REDIS-001.md) was a
   CI fault-injection incident. It is not an AWS or GPU failure. Its root cause was
   an uncaught Redis error in the shared rollout-state read, which occurred before
   the admission error handler.

## Decision tree: missing GPU or inference metrics

**Signals:** Prometheus target is down, panels are empty, DCGM has no L4 series, or
traces do not show a gateway-to-model request.

1. Check Prometheus target state and scrape error, then the exporter container and
   its device visibility. A syntactically valid config does not prove that a metric
   exists on this device.
2. Inspect raw `/metrics` output and confirm metric names, units, and labels before
   editing a dashboard. DCGM busy time in this profile is a 0–1 ratio; framebuffer
   memory is bytes.
3. Check whether the workload actually ran during the metric window and whether the
   selected exporter field list contains the requested metric.
4. For a missing trace, check propagation headers and the collector pipeline; inspect
   span attributes to confirm prompt, completion, credentials, and request bodies
   have been removed.
5. Capture the actual target error and a sanitized sample. Do not create a synthetic
   screenshot or report a dashboard as live evidence from its configuration alone.

## Decision tree: disk or host memory pressure

**Signals:** image/model download fails, container restarts, the host becomes
unresponsive, or Docker reports no space left.

1. Check `df -h`, `lsblk`, `free -h`, container exit status, and the most recent
   system and service logs.
2. Determine whether the space is used by images, model cache, logs, or temporary
   benchmark reports before removing anything.
3. Do not run global image, volume, or system-prune commands. Export evidence and
   identify exact project-owned artifacts first.
4. If the 100-GiB root disk is genuinely insufficient, stop the batch, update the
   estimate and Terraform design, and obtain review before replacement. Do not
   silently resize or attach persistent storage.

## Controlled fault-injection plan

The only incident drill with an execution result currently recorded is the local
Redis outage and recovery check. Once the GPU environment is authorized, use the
runbook's batch window and prepare recovery before each fault:

| Scenario | Safe test boundary | Recovery verification | Current evidence |
| --- | --- | --- | --- |
| Redis outage | Stop only the project Redis service after confirming its restore trap | Redis `PING`, both gateway readiness checks, one synthetic request | Local CI incident and recovery report; no L4 run |
| Gateway cancellation | Cancel bounded synthetic streams through both local replicas | Redis lease and active-request counters return to zero | Local CI cancellation drill; no vLLM-backed stream |
| vLLM request timeout | One synthetic request with a short controlled client timeout | Confirm downstream cancellation and no leaked lease | Prepared test; no L4 execution |
| Model startup failure | Invalid candidate configuration in an isolated candidate file, with the champion recorded | Restore the last known-good configuration and verify readiness | Fake-based controller tests only |
| GPU memory pressure | Increase one bounded request dimension only after measuring baseline headroom | Stop load, let sequences drain, verify service recovers | Not yet executed; require real L4 and budget window |
| Prometheus scrape failure | Stop only the project exporter or use a local invalid target | Restore the target and confirm scrape resumes | Static config validation only |

Do not deliberately break a host driver or fill the EC2 disk without a proven
recovery path and separate review. A controlled incident is useful only when failure
and recovery are both observed and retained.

## Incident report template

For each real exercise, copy the template into `docs/gpu-lab/incidents/` with a new
unique identifier:

1. Title, identifier, timestamp, environment, phase, and commit.
2. Affected components and expected behavior.
3. Exact bounded fault procedure and safety boundary.
4. Observed response, logs, metrics, alert, trace, and evidence references.
5. Detection method and time to detect.
6. Symptom, root cause, and alternative hypotheses considered.
7. Investigation commands and failed troubleshooting attempts.
8. Successful fix and why it worked.
9. Recovery verification and measured recovery time.
10. Preventive work and production limitations.
11. Evidence classification: local, simulated, static, AWS, or real GPU execution.

Do not fabricate missing times or outputs; mark them unavailable and explain why.

## References

- [GPU batch runbook](GPU_BATCH_RUNBOOK.md)
- [Manual reproduction guide](MANUAL_REPRODUCTION_GUIDE.md)
- [Single-GPU Compose profile](../../deployments/single-gpu/README.md)
- [GPU observability preparation](../../deployments/single-gpu/compose.yaml)
- [Authenticated gateway benchmark](../../benchmarks/gpu_inference/README.md)
- [Local Redis outage incident](incidents/INCIDENT-LOCAL-REDIS-001.md)
- [Implementation status and evidence boundaries](IMPLEMENTATION_STATUS.md)
