# AI Infrastructure Interview Preparation

This guide contains 106 questions with answers grounded in this repository. It is
designed for a DevOps engineer moving into AI infrastructure work. Explain the
reasoning in your own words; do not present a planned GPU experiment as experience
that has already happened.

## How to describe the evidence honestly

The repository has an executed CPU inference path, tenant authentication and
Redis-backed admission controls, local multi-gateway failure drills, and CI-checked
preparation for an isolated single-L4 environment. Terraform, Ansible, the GPU
Compose profile, vLLM model serving, GPU benchmarks, live GPU metrics, and rollback
are prepared or statically validated. They have not run on an AWS L4 because applied
On-Demand G/VT quota is zero. The user's appeal is pending; do not claim a GPU result,
AWS deployment, production incident, or measured cloud cost.

When answering a question about the L4, say what the prepared design intends to do,
what local/static evidence exists, and what exact observation is still needed on the
real host. Useful repository references include the [architecture](ARCHITECTURE.md),
[manual reproduction guide](MANUAL_REPRODUCTION_GUIDE.md), [GPU batch runbook](GPU_BATCH_RUNBOOK.md),
[benchmark preparation](../../benchmarks/gpu_inference/README.md),
[single-GPU deployment](../../deployments/single-gpu/README.md), and the real
[local Redis outage report](incidents/INCIDENT-LOCAL-REDIS-001.md).

## Linux

### 1. What does `nvidia-smi` prove?

It asks the NVIDIA driver for device and process information. A successful result
shows that the host driver can communicate with a visible GPU; it does not prove
that CUDA libraries, Docker GPU access, PyTorch, or a model server work. Check each
layer separately, then run a synchronized computation and verify its output.

### 2. Why check `uname -r` and kernel headers before installing a driver?

The NVIDIA kernel module must be built or selected for the running kernel. Headers
that do not match that kernel can prevent module installation or loading. Record the
kernel, install the matching headers, and reboot only through the documented recovery
path if the driver requires it.

### 3. How would you diagnose `nvidia-smi` reporting no devices?

First check that the EC2 instance is the expected `g6.xlarge`, inspect `lspci`, the
kernel log, installed NVIDIA packages, `lsmod`, and `dmesg` for module errors. Then
check kernel/header compatibility and whether the device nodes exist. Do not proceed
to vLLM until host discovery succeeds; container configuration cannot repair a host
driver that has not loaded.

### 4. Why are `free -h`, `df -h`, and `lsblk` useful in an inference lab?

Host random-access memory holds operating-system and container processes; disk holds
images, model files, logs, and caches; the block-device view confirms which disk backs
those filesystems. GPU memory is separate and must be checked with NVIDIA tools. A
model can fit in GPU memory while the image/model download exhausts the 100-GiB root
disk or host memory.

### 5. What is the difference between a process being alive and a service being ready?

A process can exist while it is still downloading weights, loading model layers, or
waiting for Redis. Liveness asks whether the process should be restarted; readiness
asks whether it can safely receive traffic. The prepared GPU profile checks the
selected inference backend and shared admission dependency, then still requires a
real synthetic inference request as a separate smoke test.

### 6. Why use Session Manager instead of opening SSH?

Systems Manager Session Manager can provide administrator access without an inbound
security-group rule or an exposed SSH key. The prepared network has no inbound rules
and the instance role is limited to management needs. Verify the agent is online and
use port forwarding for loopback-only operator services; this design still depends
on outbound access and correctly scoped IAM.

## AWS

### 7. Why is the GPU environment a standalone EC2 host?

The project is intended to teach the host-to-device stack directly: Ubuntu, the
kernel driver, CUDA, container GPU access, and one inference server. Kubernetes would
add a scheduler and cluster control plane before those foundations are understood.
The repository preserves its existing EKS contract, but this project does not deploy
it.

### 8. How do you decide whether an EC2 quota is sufficient?

Check the applied On-Demand G/VT quota in the target region and compare it with the
instance's vCPU requirement. A `g6.xlarge` needs four vCPUs of this quota. A pending
request, open case, or email appeal is not usable capacity; provisioning stays
blocked until the applied value is at least four and the exact instance type is
available in the selected Availability Zone.

### 9. What does an instance-type offering check tell you, and what does it not tell you?

It tells you that AWS lists the instance type in an Availability Zone. It does not
reserve capacity or promise that a launch will succeed. The runbook checks both the
regional quota and AZ offering before applying, then handles a capacity failure as a
stop condition rather than silently switching accelerator type.

### 10. Why does a $25 budget alert not enforce the $25 project ceiling?

An alert reports spending after AWS observes it; it does not reliably stop a running
instance or every billable resource. The project controls exposure with one allowed
instance, a short approved runtime, a fixed expiry, a reviewed resource plan, and
teardown verification. Cost must include storage, public IPv4, state, egress, tax,
and other supporting resources, not just GPU hours.

### 11. Why require IMDSv2?

Instance Metadata Service version 2 requires a token for metadata requests, reducing
the risk of simple server-side request forgery paths reaching instance credentials.
The Terraform root requires tokens and uses hop limits appropriate to the host
design. IMDSv2 is one layer; least-privilege instance permissions and careful
application handling remain necessary.

### 12. How do you avoid damaging unrelated AWS resources during teardown?

Use a dedicated Terraform root, exact state key and reviewed destroy plan, project
tags, and resource-specific post-destroy queries. Never use broad account cleanup or
global Docker cleanup. The final evidence should distinguish resources that were
actually checked from possible untagged leftovers; the current project has not
provisioned its lab resources.

## GPU infrastructure

### 13. What is the NVIDIA L4 in this project?

It is the only accelerator type allowed for the lab, exposed by one `g6.xlarge` EC2
instance. The planned first experiment uses one GPU and a small instruct model. The
project does not claim bare-metal access, multi-GPU execution, Multi-Instance GPU
(MIG) partitioning, or physical tenant isolation.

### 14. How do the GPU driver, CUDA Toolkit, and CUDA runtime differ?

The host NVIDIA driver manages the device and exposes the driver API. The CUDA
Toolkit supplies development tools such as `nvcc` and libraries; an application or
container may carry its own CUDA runtime libraries. A container still relies on the
host driver and NVIDIA Container Toolkit to expose the device, so matching version
compatibility matters across these boundaries.

### 15. Why can `nvidia-smi` show a CUDA version different from `nvcc --version`?

`nvidia-smi` reports the maximum CUDA driver API level supported by the installed
driver, not necessarily the Toolkit installed on the host. `nvcc --version` reports
the compiler from a particular Toolkit installation. A container can use a third
runtime-library version, provided the host driver supports it.

### 16. What does NVIDIA Container Toolkit add?

It configures the container runtime so a container can receive GPU device nodes and
compatible driver interfaces from the host. It does not install a host driver or
make CPU-only application libraries GPU-enabled. Validate host discovery first, then
run a minimal CUDA container with explicit GPU access before testing PyTorch.

### 17. Why is one GPU instance at a time a hard boundary?

It limits cost and keeps the lab focused on shared single-device inference. Terraform
has one GPU instance resource and the preflight rejects a second active
project-tagged GPU host. Larger models or concurrent experiments must be scheduled
sequentially unless new capacity and spending are separately authorized.

### 18. How would you prove a container really computed on the L4?

Check that the container sees the named L4, allocate a CUDA tensor, run an operation,
synchronize before timing, verify the numerical result, and observe nonzero device
activity. A container starting successfully or importing PyTorch is not enough; a
silent CPU fallback must count as failure.

## CUDA

### 19. Why is a GPU useful for matrix multiplication?

Large matrix operations expose many independent multiply-and-accumulate operations
that can run at once. A GPU has many parallel execution units and specialized tensor
cores, so it can process these workloads efficiently when data is available. Small
workloads may lose to CPU work because launch and transfer overhead dominate.

### 20. What are a CUDA thread, block, and grid?

A thread performs an element of work, threads are grouped into a block that can
cooperate through shared memory, and blocks form the grid launched for a kernel.
The hardware schedules blocks onto streaming multiprocessors. Correct indexing must
handle a final partial block so it does not read or write beyond the input arrays.

### 21. Why must GPU timings synchronize?

CUDA launches are asynchronous: the CPU can return before the device finishes. A CPU
timer around only the launch measures submission overhead, not computation. Warm up,
synchronize before and after the measured region, repeat the workload, and report the
timing method.

### 22. What is the difference between host-to-device and device-to-host transfer?

Host-to-device copies input from system memory over the interconnect to GPU memory;
device-to-host returns results. Copies can dominate a small workload, so keeping data
on the device and batching operations may help. The performance lab separates
transfer time from kernel time rather than attributing both to arithmetic.

### 23. How do FP32, FP16, and BF16 differ in practical terms?

FP32 uses more bits and usually gives a broad numeric range with higher precision.
FP16 uses fewer bits and can improve throughput and reduce memory use, but its range
is smaller. BF16 has fewer precision bits than FP32 but a wider exponent range than
FP16; support and accuracy must be checked for the selected GPU and model.

### 24. What makes a workload compute-bound or memory-bound?

A compute-bound workload spends most of its time performing arithmetic; a
memory-bound workload waits for data movement. Compare synchronized timings, memory
traffic, and available profiler evidence. Optimizing arithmetic will not fix a
bandwidth bottleneck, and profiling permissions or counters may be limited in a
virtualized cloud GPU.

## Docker

### 25. Why use separate Compose profiles for CPU and GPU?

They preserve the already working CPU demonstration while isolating the single-host
GPU runtime, model, network ports, and observability choices. The GPU profile can be
validated statically without changing local defaults. Compose parsing is not proof
that images pull or that a GPU is present.

### 26. Why are vLLM and Grafana ports bound to loopback?

They are operator-facing services that should not be reachable from the public
internet. Loopback bindings allow access on the host and through a controlled Session
Manager tunnel. The security group also has no inbound rules, so an accidental host
listener does not by itself become a public service.

### 27. Why does the project avoid adding a user to the Docker group on the EC2 host?

Access to the Docker socket can start privileged containers and mount host files, so
Docker group membership is effectively root-level authority. The manual guide uses
a root shell only for the limited host-side Docker operations and calls out that
boundary. Production administration should use a reviewed privilege model and audit
who can reach the daemon.

### 28. Why pin container images by digest?

A mutable tag can point to different image bytes later. A digest identifies immutable
content and makes the deployment and release plan reproducible. Before launch, still
verify that the digest exists, supports the required architecture, has a compatible
runtime, and has an acceptable security status.

### 29. What does a healthy Compose container prove?

Only that its configured health check currently passes. It does not prove the model
answers correctly, streams properly, or stays within VRAM. Follow health checks with
`/v1/models`, authenticated gateway inference, stream completion, and live GPU
telemetry checks.

### 30. How do you preserve evidence when stopping Compose?

Export sanitized logs, metrics, traces, benchmark data, and evaluation results before
stopping the stack. The GPU profile uses memory-backed storage for some monitoring
data, so restart can erase it; model-cache and Redis volumes also have separate
lifecycle behavior. Do not delete a volume until its contents and retention need are
reviewed.

## Python

### 31. Why keep a standard-library benchmark client for the gateway test?

The host-side runner can execute with the Python already available on EC2 and does
not require installing the full project environment to issue measurements. It
creates bounded asynchronous request tasks and records aggregate metadata. It is a
client benchmark, not a CUDA kernel profiler.

### 32. How should an async inference request be cancelled safely?

Cancellation must propagate to the downstream stream and release request-scoped
admission and capacity leases in cleanup paths. Redis leases also expire if a process
dies, but expiry is a recovery bound rather than the normal release mechanism. Test
the cancelled stream across replicas and verify shared lease counts return to zero.

### 33. Why catch truncated HTTP responses in a benchmark client?

A server or proxy can close a connection after headers or partial content; the HTTP
library may raise an exception while reading the response. Treat it as one failed
sample, sanitize its details, and let the remaining bounded samples complete. An
unexpected exception must not silently erase the report or abort the entire run.

### 34. What should a privacy-safe benchmark report contain?

It can contain status, latency, throughput, token counts reported by the runtime,
concurrency, and environment metadata. It must exclude prompts, completions, bearer
tokens, response bodies, and raw error details. Unique output files need restrictive
permissions so reruns do not overwrite or expose earlier evidence.

### 35. How do you distinguish an application error from a dependency error?

Use a stable, generic service response for known dependency outages, retain sanitized
diagnostic context in controlled logs, and preserve the causal exception internally.
For example, loss of shared rollout state should return service unavailable rather
than look like an unclassified application crash. Never include secrets or prompt
content in error output.

### 36. What does a test fixture prove, and what does it not prove?

A fixture proves that code behaves as tested against the fixture's controlled input
and dependency behavior. It does not prove an actual model artifact, cloud driver,
GPU, or AWS permission works. Pair fixture tests with the relevant live validation
before claiming the real integration is verified.

## Distributed systems

### 37. Why use Redis for admission shared across gateway replicas?

Two gateway processes need to see the same request, token, concurrency, queue, and
lease state. Redis scripts make related updates atomic so both replicas make a
consistent admission decision. A local in-memory counter would allow aggregate use
to exceed a tenant limit across replicas.

### 38. Why use a Redis Lua script instead of several client commands?

Several separate commands can interleave with another request and both pass a limit
before either records its reservation. Lua runs the admission decision and state
changes atomically on Redis. The script still needs bounded inputs, expiry behavior,
tests, and safe handling when Redis is unreachable.

### 39. What is a lease, and why does inference admission use one?

A lease represents a request's temporary reservation of shared capacity. The gateway
renews it while work is active and releases it on completion or cancellation. If the
process disappears, a deadline allows stale concurrency reservations to expire; token
ledgers remain conservative for their quota windows.

### 40. What is the difference between a tenant quota and GPU scheduling?

A tenant quota limits which requests the gateway admits based on policy. It does not
assign a GPU time slice, reserve VRAM, or stop another process from using the device.
The project’s Redis “GPU capacity” counters are logical admission controls, not a
hardware scheduler.

### 41. How does backpressure protect a shared model server?

It bounds how much work can wait or run, and rejects excess work before queue growth
causes unbounded latency or memory pressure. A bounded queue and explicit timeout
make overload visible. Queue depth, wait time, and rejection counts help distinguish
capacity saturation from a model error.

### 42. What happens if Redis fails during admission?

The gateway fails closed with a temporary service-unavailable response because it
cannot safely verify shared tenant limits. It must release any reservations it made
before the failure and recover readiness when Redis returns. The local outage report
documents a separate rollout-state path that originally escaped as HTTP 500 and was
fixed and verified in CI.

## vLLM

### 43. What responsibility belongs to vLLM and what belongs to the gateway?

vLLM executes model inference and manages serving concerns such as batching and GPU
memory. The gateway authenticates tenants, applies model permissions and quotas,
routes requests, and records metadata. Keeping those responsibilities separate lets
the model runtime serve requests without becoming the tenant security authority.

### 44. What is continuous batching?

It lets a serving engine add new sequences as other sequences finish, rather than
waiting for a fixed batch to complete. This can improve GPU use under varied request
lengths. It also makes scheduling and memory pressure depend on concurrent sequence
state, so maximum active sequences must be measured on the actual model and GPU.

### 45. What is the key/value (KV) cache?

Transformer attention derives key and value tensors for each input token and layer.
During autoregressive generation, previously computed entries can be reused instead
of recalculated at every new token. This reduces repeated work but consumes GPU
memory in proportion to layers, active tokens, precision, and concurrent sequences.

### 46. What is PagedAttention intended to improve?

It manages KV-cache memory in blocks so variable-length sequences can use memory
more flexibly than one large contiguous reservation per request. This reduces
fragmentation and can support higher serving throughput. It cannot create additional
VRAM; the cache still has a finite capacity.

### 47. What is the difference between prefill and decode?

Prefill processes the prompt and builds the initial attention state; it strongly
affects time to first token and often parallelizes across prompt tokens. Decode
generates tokens one at a time using cached state, so each token depends on the last
and is often measured as time per output token. Long prompts and long generations
stress these phases differently.

### 48. Why test `/tokenize` before forwarding a request?

The gateway needs an estimate of the rendered prompt length before reserving tenant
token capacity. The vLLM adapter calls the tokenizer endpoint with the chat messages
and generation prompt, then compares the result with the context limit. If the
tokenizer is unavailable, the gateway must fail safely rather than use an unreliable
word-count estimate for the GPU route.

### 49. Why use a stable served model alias?

The gateway can request a stable name such as `gpu-default` while the runtime
configuration and immutable release manifest identify the actual model revision.
This keeps routing separate from artifact identity. A release controller must still
verify the active manifest and model files before changing the alias.

### 50. What does the prepared `--max-num-seqs=2` setting mean?

It caps the number of active sequences handled by the engine at a time in the current
profile. A benchmark client concurrency of eight can therefore measure queueing around
that server limit; it does not prove eight GPU sequences execute simultaneously. The
value is a conservative candidate that must be checked against real L4 memory and
latency.

## Language models

### 51. What is a model parameter?

A parameter is a learned numeric value in the network, such as a weight used to
transform activations. A model with more parameters often needs more storage and
compute, though parameter count alone does not determine quality or serving capacity.
The selected first model is Qwen2.5-1.5B-Instruct, with the exact revision and license
to be rechecked before download.

### 52. What does a tokenizer do?

It maps text into token IDs the model was trained to process, and converts generated
IDs back to text. Tokens are not always whole words, so character or word counts are
not exact token counts. The gateway uses the serving tokenizer for its GPU-route
preflight and reports runtime token usage when available.

### 53. What is a context window?

It is the maximum number of tokens the model/runtime accepts across prompt and
generated response. Increasing context length can raise KV-cache memory use even when
the model weights do not change. The prepared 8,192-token limit is a candidate, not a
measured L4 capacity guarantee.

### 54. What is quantization?

Quantization stores or computes model values with fewer bits to reduce memory use and
sometimes increase throughput. It can change output quality, supported kernels, and
loading requirements. The project should attempt quantized variants only after the
baseline model is stable and the exact artifact, license, runtime, and quality are
checked.

### 55. What does temperature change during sampling?

Temperature rescales next-token probabilities before selection: lower values make
the distribution more concentrated, while higher values make less likely choices
more common. It changes output randomness, not model weights or factual ability. For
repeatable evaluation, keep it fixed and use deterministic checks where possible.

### 56. Why is an open-weight model not automatically unrestricted to use?

The model’s license and use conditions still apply, and model artifacts can have
separate provenance and integrity concerns. Record the exact revision, license
metadata, and artifact digest. A mutable repository name alone does not identify the
bytes used in a deployment.

## LLMOps

### 57. What should a model deployment record bind together?

The immutable record should identify model revision and artifact digest, license,
serving image digest, runtime configuration, evaluation suite/report digests, and
source commit. If one input changes, the plan should become stale or fail validation.
This makes a deployment reviewable and reproducible.

### 58. Why does the project use sequential single-GPU releases?

Two copies of even a small model may not fit safely alongside the active engine on one
L4. The prepared controller stops gateways, switches vLLM, checks readiness, and
restores the known-good configuration on failure. Until actually run on the L4, this
is a locally tested design, not evidence of zero downtime or successful GPU rollback.

### 59. Why require an independent approver?

The person who proposes a model change should not be the only person authorizing it.
The approval binds to the exact immutable plan, so changing the candidate or champion
after approval makes the plan stale. This is a governance control; it does not prove
the live host currently runs those bytes until the host controller checks them.

### 60. What can the authenticated release API verify?

It checks that a finished MLflow run and sanitized evaluation report match submitted
model, revision, source, image, runtime, and suite metadata, and requires a different
identity with the release-approval role. It stores plans in shared SQLite for two
gateways on the same host. It cannot itself inspect Docker or prove the live model
files; that belongs to the separate host-side controller.

### 61. Why hash the full model snapshot?

A revision string identifies a repository state, while a local snapshot digest checks
the bytes actually present on the host. Hashing every file lets the controller detect
corruption or an unexpected artifact before switching traffic. The hashing procedure
must include a stable path order and clear rules about symlinks and metadata.

### 62. Why avoid claiming a canary deployment here?

A canary usually sends a controlled portion of live traffic to a candidate while the
current version remains available. On one GPU, the two model copies may exceed safe
memory, and the current release plan is sequential. A multi-GPU production platform
could use separate candidate capacity and traffic weights, but that behavior is not
implemented or executed by this project.

## MLOps and evaluation

### 63. What makes an evaluation deterministic?

A deterministic check has an objective rule, such as whether a response parses as
valid JSON or contains a required field. It should specify normalization and edge
cases so the same input and output produce the same pass/fail result. Subjective
qualities such as helpfulness need a separate rubric and should not be disguised as
exact correctness.

### 64. Why version a synthetic evaluation set?

Changing prompts or expected outputs can change measured quality, so the suite needs
a stable identifier and digest. Bind that digest to each model result and release
plan. Synthetic examples avoid customer data but still need review for coverage and
possible leakage of test answers into development.

### 65. What should a candidate quality gate consider besides correctness?

It should include structured-output validity, instruction adherence, latency,
throughput, peak memory, and cost per successful task where these are measured. A
candidate that is slightly more accurate but cannot fit or serve within the resource
envelope may not be deployable. The one-L4 project must report real metrics only after
GPU execution.

### 66. What does MLflow contribute in this design?

MLflow stores run metadata, metrics, parameters, and a sanitized evaluation report
for the lab. It helps tie a candidate to its evidence, but the single-host local
SQLite and artifact directory are temporary lab storage, not a durable enterprise
registry. Model weights themselves remain in the model cache.

### 67. How should a failed candidate be handled?

Reject it before approval if deterministic evaluation fails or its manifest does not
match the run. If a candidate fails after deployment begins, restore the previous
known-good model configuration and verify health plus inference. Record the failed
result; do not edit history to make it look successful.

### 68. How would you detect stale evaluation evidence?

Compare the candidate’s model revision, artifact digest, runtime image, runtime
configuration, suite digest, and source commit with the finished evaluation run. If
any material input differs, reject the plan rather than reusing old scores. The
release API implements those metadata checks; live artifact verification remains a
host-side task.

## Observability

### 69. What is time to first token (TTFT)?

TTFT is the elapsed time from a request entering the measured path until its first
generated token is available. It includes prompt processing and serving overhead, so
long prompts can raise it. State where the timer starts and ends before comparing
measurements from different tools.

### 70. What is time per output token (TPOT)?

TPOT estimates the time spent producing each output token after the first token.
It describes decode cadence, while TTFT captures the initial wait. Report the exact
tool formula and output-token count because runtimes may define aggregate values
differently.

### 71. What do P50, P95, and P99 tell an operator?

They are latency percentiles: the median, a value at or below which 95% of samples
fall, and the corresponding 99% value. Tail percentiles show slow experiences that
an average can hide. Small sample sets make P99 unstable, so include sample count and
repeat count.

### 72. How can GPU and gateway metrics be correlated without storing prompts?

Use request IDs and trace context plus bounded labels such as model and synthetic
tenant, while excluding prompts, completions, credentials, and high-cardinality user
data. Correlate request rate, latency, queueing, vLLM activity, and DCGM utilization
by time window. Verify actual emitted spans and metric labels before relying on a
dashboard.

### 73. Why should tenant IDs be handled carefully in metrics?

Tenant labels can create high cardinality as tenants grow, increasing monitoring
storage and query cost. They can also reveal business relationships. The lab has a
few synthetic tenants, but a larger system may use aggregates or controlled tenant
views rather than exposing each tenant as a global time-series label.

### 74. What does DCGM Exporter provide?

It exposes selected NVIDIA Data Center GPU Manager (DCGM) metrics to Prometheus, such
as device busy time, framebuffer memory, temperature, and power when available. The
profile uses a pinned non-profiling field list. Metrics, names, permissions, and
device visibility still need validation on the real L4; configuration alone is not
live telemetry.

## Reliability

### 75. What is the difference between an SLI, SLO, and SLA?

A service-level indicator (SLI) is a measured signal such as successful-request
ratio. A service-level objective (SLO) is an internal target for that signal over a
defined window. A service-level agreement (SLA) is a customer-facing commitment and
may have contractual consequences. The lab's alert thresholds are diagnostic and
should not be called production SLOs.

### 76. What is an error budget?

It is the allowed unreliability implied by an SLO over a time window. If an objective
allows 0.1% failures, the corresponding 0.1% is the error budget. The project must
first define and measure a meaningful service objective before an error budget can
guide release decisions.

### 77. Why are retries dangerous for inference?

Retries can multiply load during an overload and duplicate expensive generation after
a client timeout. Retry only errors that are safe to retry, use bounded attempts and
backoff, and preserve an idempotency or request identity strategy where possible.
For streaming, a partial response cannot usually be restarted invisibly.

### 78. How should timeouts be layered?

The client timeout should leave time for gateway processing and downstream model
execution, and each layer should have a finite bound. A shorter upstream timeout can
cancel work downstream and trigger lease cleanup. Measure actual cold-start and
request behavior before choosing values; defaults are not production evidence.

### 79. Why is a single EC2 host a single point of failure?

The model, gateways, Redis, and local monitoring share one machine and its network,
disk, and lifecycle. Two gateway containers on that host do not provide host or
availability-zone redundancy. The lab demonstrates software behavior on one node,
not high availability.

### 80. What should recovery verification include?

Check that the failed dependency is healthy, service readiness has returned, and a
representative authenticated request succeeds. Also verify that counters, leases,
and queues did not remain stuck. Record timestamps so recovery duration is based on
observations, not recollection.

## Security

### 81. Why must tenant identity come from verified credentials rather than a header?

A client controls its request headers, so a claimed tenant header can be spoofed.
The gateway verifies a signed identity and derives tenant and role from trusted
claims, then checks access to the requested model. The client may request a model but
cannot choose its authorization identity.

### 82. What is the difference between authentication and authorization?

Authentication establishes which identity presented a valid credential. Authorization
decides what that identity may do, such as use a model or approve a release. A valid
signature does not automatically grant permission to every route or tenant resource.

### 83. Do Redis quotas isolate tenants at the GPU hardware layer?

No. They control which requests the gateway admits and how much logical usage is
allowed. All admitted requests still share one L4 and the same model process. The
project makes no claim of memory partitioning or hardware isolation.

### 84. How should model prompts be handled in logs and traces?

Treat them as potentially sensitive user data. The prepared profile removes known
prompt/completion and credential attributes before export, and the benchmark omits
request and response content. Inspect actual spans, exporter behavior, and error logs
before enabling broader telemetry; filtering configuration is not proof by itself.

### 85. Why keep inference services private if requests are authenticated?

Authentication is not a reason to expose every internal endpoint to the internet.
Private networking reduces the attack surface for vLLM, Redis, MLflow, and monitoring.
Only the controlled operator path and intended gateway entry point should be reachable,
with TLS and identity checks appropriate to that path.

### 86. How should an application use EC2 role credentials?

The AWS SDK should retrieve short-lived credentials from the instance role through
IMDSv2 instead of embedding long-lived keys in files or images. Grant only the
permissions needed for the host's actual task. The prepared GPU instance role is
limited to Systems Manager access; model serving should not need broad AWS privileges.

## Performance engineering

### 87. Why compare throughput with tail latency?

Increasing concurrency can raise completed requests per second while making some
users wait much longer. A serving system needs both throughput and latency percentiles
to show the trade-off. The benchmark records these separately and keeps concurrency
bounded.

### 88. What does client-side semaphore wait measure?

It measures time a request waited for a slot in the benchmark client before it was
sent. It is not server queue time. Labeling it accurately prevents operators from
mistaking load-generator behavior for vLLM or gateway scheduling.

### 89. What can cause low GPU utilization while requests are slow?

The workload may be too small, the model may be waiting on CPU tokenization or data
movement, or a low request rate may not feed the GPU. It could also be queueing in a
different dependency or a measurement error. Correlate GPU, CPU, queue, request, and
token metrics and inspect traces before tuning batch limits.

### 90. Why warm up a benchmark before collecting results?

Startup includes model loading, kernel initialization, compilation or cache setup,
and cold filesystem effects. Warm-up samples separate some startup effects from
steady serving behavior. Report both cold-start time and steady-state results rather
than discarding cold starts entirely.

### 91. How do input length and output length affect different costs?

Input length increases prompt prefill work and initial cache state. Output length
increases repeated decode work and retains more KV-cache entries during generation.
Concurrent requests combine these memory demands, so benchmark shape and concurrency
must remain within the configured context and observed VRAM limit.

### 92. What does the prepared benchmark matrix tell you about a concurrency limit?

It explores short, medium, and long prompts at increasing concurrency, with
concurrency 16 withheld until lower levels show adequate memory and error margin. The
serving engine is prepared with a two-sequence limit, so higher client concurrency
mostly tests waiting and throughput around that constraint. Only a real L4 run can
establish useful safe values.

## FinOps

### 93. How do you calculate estimated cost per million output tokens?

Divide total estimated experiment cost by measured output tokens, then multiply by
one million. State whether the cost includes instance runtime, IPv4, disk, state,
egress, tax assumptions, and failed requests. It is an estimate until billing settles
and must not be described as actual billed cost.

### 94. Why measure cost per successful task as well as cost per token?

A model can produce many tokens that fail a task's correctness criteria. Cost per
successful task connects compute spending to useful outcomes. It requires a defined
evaluation set, measured runtime, and transparent success rule.

### 95. What is the most direct cost control in this lab?

Shorten the time the GPU instance exists and keep the execution in one prepared
batch. Stop it whenever work does not require the L4, install and benchmark from
scripts prepared in advance, and use independent instance expiry. This does not
replace checking all supporting-resource charges.

### 96. How should spot capacity be considered?

Spot may lower compute price but can interrupt the instance, wasting setup time and
complicating a narrow evidence window. The project prefers predictable On-Demand
execution and has no approved quota today. Consider Spot only after comparing actual
savings with interruption risk and ensuring evidence checkpoints survive.

## Incident response

### 97. Describe an actual failure investigated in this project.

In the local CI Redis outage drill, stopping Redis caused gateway 1 to return HTTP 500
instead of the expected 503. The shared rollout-state read raised before the later
admission error handler ran. The fix maps that dependency failure to a sanitized 503
and persists shared rollout state before updating local weights; the corrected
two-gateway drill passed CI.

### 98. What is the difference between a symptom and a root cause in that incident?

The HTTP 500 was the symptom visible to the test client. The root cause was an
uncaught Redis connection error in the rollout-state lookup that ran before admission
handling. Changing only the response assertion would have hidden the failure instead
of making the gateway fail safely.

### 99. Give a STAR-format example based on the local Redis incident.

**Situation:** the local two-gateway outage drill expected a safe 503 but observed
500. **Task:** make the gateway fail closed when shared routing state is unavailable.
**Action:** traced the request ordering, added dependency-error handling, made the
shared write precede process-local mutation, and extended the recovery drill.
**Result:** CI verified 503 behavior on both replicas, Redis recovery, and readiness
after recovery. This is local CI evidence, not a production outage.

### 100. How do you approach an unfamiliar GPU out-of-memory incident?

Capture the exact request shape, model revision, active sequence count, context,
precision, and GPU memory before changing settings. Check vLLM logs, DCGM memory
metrics, and whether memory returns after requests finish; then reduce concurrency or
context as a controlled test. Preserve the failure and recovery data and do not claim
the OOM was reproduced until it actually occurs on the L4.

## System design

### 101. Design a safe request path for three tenants sharing one L4.

Verify a signed identity, derive the tenant server-side, check model permission,
estimate prompt and output budget, reserve request/token/concurrency capacity in
shared Redis, and then route to vLLM. Reconcile reported usage and release leases on
success, error, timeout, or cancellation; reject overload with a bounded response.

### 102. What changes when the service grows to several GPUs?

Add a capacity and placement layer that knows GPU type, memory, model residency,
and available sequence slots. Keep tenant policy in the gateway, but do not confuse
its quota with placement. Measure per-device utilization and add capacity only when
traffic, availability, or model fit justifies the cost.

### 103. When is tensor parallelism appropriate?

Tensor parallelism splits portions of model computation across multiple GPUs so a
large model or workload can use their combined capacity. It introduces communication
and topology costs, often through NVIDIA Collective Communications Library (NCCL).
This lab has one L4 and does not execute tensor-parallel or distributed inference.

### 104. Why might Kubernetes be useful later, and why is it out of scope here?

Kubernetes can schedule containers, replace failed processes, and coordinate a GPU
fleet when capacity and operational scale justify a control plane. It also adds
cluster networking, node lifecycle, GPU scheduling, and more cloud cost. This project
uses one EC2 host to learn the driver and serving stack first, while preserving the
repository's existing EKS plan without deploying it.

### 105. How would you keep a future multi-region inference service reliable?

Use regional cells with local model capacity, durable global identity and policy,
regional quota enforcement, and explicit failover criteria. Replicate model artifacts
and benchmark each region independently; do not assume a healthy API endpoint means
GPU capacity is available. This is a design discussion, not an implemented feature.

### 106. What evidence would you require before calling this a working L4 platform?

At minimum, verify the authorized account, approved quota, one tagged L4 instance,
driver and CUDA host/container computation, real PyTorch execution, real vLLM output,
authenticated tenant behavior, live GPU/inference telemetry, measured benchmarks,
evaluation and rollback, and verified teardown. Keep the evidence tied to a commit and
include failure cases; static files and CI mocks alone do not satisfy this gate.

## STAR examples grounded in this repository

Use these only as frameworks. Adjust the wording to your actual contribution and do
not add business impact that the records do not contain.

### Fail-closed Redis behavior

Use question 99. The evidence is the [incident report](incidents/INCIDENT-LOCAL-REDIS-001.md)
and the passing local E2E job in PR #58. Be explicit that it ran in CI with the CPU
stack, not on AWS.

### Single-host model release trade-off

**Situation:** the project has one GPU and cannot assume two model copies fit at once.
**Task:** make release evidence reviewable without claiming a concurrent canary.
**Action:** prepare an immutable plan, independent approval, host-side checks of the
active manifest and model snapshot, sequential vLLM restart, readiness verification,
and restoration on failure. **Result:** local fake-based tests and CI cover the
controller logic; actual Docker/L4 deployment and rollback remain a quota-gated
validation task.

### Cost and privacy boundaries

**Situation:** real model calls can spend money and expose sensitive text. **Task:**
prepare a benchmark that is bounded and produces useful evidence without retaining
prompt or completion content. **Action:** cap requests, concurrency, timeout and
instance runtime; send synthetic tenant identities; store only sanitized metrics in
owner-only output files. **Result:** the runner is locally tested and CI-checked; no
real GPU request or measured cloud cost is claimed.

## Follow-up prompts for a technical interview

For any answer, be ready to explain the trade-off, what could fail, the metric that
would reveal the failure, and the next safe diagnostic. For project claims, identify
the artifact, commit, CI run, and whether it is source code, static validation, local
execution, simulated behavior, or real AWS/GPU evidence.
