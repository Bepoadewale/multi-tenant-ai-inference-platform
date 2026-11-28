# Single-L4 vLLM benchmark preparation

This directory prepares one direct vLLM serving benchmark. It uses vLLM's official
`vllm bench serve` client inside the already pinned vLLM image. The client has no GPU
reservation; it sends requests over the private Compose network to the single vLLM
server. It measures inference-server behavior and **does not** include gateway,
Redis, tenant authorization, or full application cost.

## Planned matrix

`workloads.json` contains three synthetic request shapes and 100 measured prompts per
run, after five warm-up requests. Each case runs three times. The default plan includes
11 shape/concurrency cases and 33 runs:

- Short: 256 input tokens, 64 output tokens, concurrency 1, 2, 4, and 8.
- Medium: 1,024 input tokens, 128 output tokens, concurrency 1, 2, 4, and 8.
- Long context: 4,096 input tokens, 128 output tokens, concurrency 1, 2, and 4.
- Short concurrency 16 is held back until the operator explicitly allows it.

Each shape leaves a 128-token margin below the configured 8,192-token context. This
margin accounts for chat-template tokens and avoids a benchmark configuration that
fills the whole context by arithmetic alone. Actual tokenizer lengths and vLLM limits
must still be checked at runtime. Stop or reduce concurrency on memory pressure,
queue growth, errors, or a budget/runtime reserve problem.

## What is measured

The official benchmark reports time to first token (TTFT), time per output token
(TPOT), inter-token latency (ITL), end-to-end latency, request/token throughput, and
selected P50/P95/P99 values. It records aggregate results only; it does not use the
option that saves per-request response text. The run metadata records the source SHA,
region, instance type, GPU/driver, model revision, shape, concurrency, and repetition.
The workload and concurrency controls follow the [vLLM 0.34.0 `bench serve` CLI
reference](https://docs.vllm.ai/en/v0.34.0/cli/bench/serve/), including request
percentiles and `--max-concurrency`.

Use the actual run JSON plus Prometheus/DCGM samples to explain bottlenecks. A CPU
client clock measures request service timing; it does not measure an individual CUDA
kernel. `vllm bench serve` measures the serving API and token timing; use synchronized
PyTorch/CUDA experiments for kernel-level performance.

## Dry-run before the paid session

Run on the **local workstation** from the repository root:

```bash
make gpu-benchmark-plan
```

This validates the workload context bounds and prints the full commands without
contacting AWS, starting Docker, or connecting to an inference server. It omits the
concurrency-16 case by default.

## Real run after the separate GPU authorization

Only after the single-L4 instance and Compose profile are healthy, run on the **EC2
host** from the repository root. Set metadata from the verified host and approved
model revision; the command itself rejects a non-L4 GPU:

```bash
export AWS_REGION=us-east-1
export GPU_INSTANCE_TYPE=g6.xlarge
export GPU_MODEL_REVISION='replace-with-reviewed-model-revision'
python3 benchmarks/gpu_inference/run_vllm_matrix.py \
  --output-dir /var/tmp/gpu-lab/benchmark-results
```

Outputs are written outside the public repository, under the chosen evidence path.
The wrapper stops on the first failed run and preserves partial results. Export and
review the results before teardown. Do not upload raw results publicly without checking
for sensitive metadata. The wrapper checks the actual EC2 region and instance type
through IMDSv2, verifies one visible L4, and caps the benchmark batch at 120 minutes
by default; each individual command has a 10-minute timeout. These runtime guards do
not replace the independent EC2 expiry or exact-cost authorization. To include
short-prompt concurrency 16, first complete the
lower levels with adequate VRAM margin, then explicitly add:

```bash
python3 benchmarks/gpu_inference/run_vllm_matrix.py \
  --allow-concurrency-16 \
  --output-dir /var/tmp/gpu-lab/benchmark-results
```

Do not treat the dry-run or static matrix as benchmark evidence. No GPU measurement
has been recorded yet.

The current serving profile sets vLLM `--max-num-seqs=2`. Client concurrency above
two therefore measures the server's queueing and throughput at that engine limit; it
does not mean eight or sixteen sequences are running on the GPU at once. The runner
records the active vLLM sequence, context, and GPU memory-utilization settings for
each measured batch. Raising `--max-num-seqs` requires a separate model-memory check
and Compose configuration review before the next batch.

## Authenticated gateway comparison

`run_gateway_benchmark.py` compares a small direct-vLLM baseline with the authenticated
gateway, then sends a bounded concurrent request set across the customer-support,
internal-engineering, and research identities. It records status codes, request
latency, client-side semaphore wait, throughput, and runtime-reported token counts.
The prompts are fixed synthetic text; the report never stores request or response
content, bearer tokens, response bodies, or error details. Reports are written with
owner-only permissions below `.local/`.

On the **local workstation**, `make gpu-gateway-benchmark-plan` validates and prints
the plan. It does not read identities or make network requests. For an authorized L4
batch, run `make gpu-gateway-benchmark` on the **EC2 host** after both gateway ports
and vLLM are ready. This command requires IMDSv2 to report one approved `g6` instance
in `us-east-1` and exactly one visible L4. It uses the generated local identity file
and saves the sanitized result to `.local/gpu-lab/gateway-benchmark/`.

The report's direct-versus-gateway P50 difference is exploratory. The requests are not
perfectly isolated, and runtime cache state, model scheduling, and network timing can
change between them. It should not be called pure gateway overhead. The reported
semaphore wait is queueing in the load generator, not a measurement of the server's
internal queue. Status counts by synthetic tenant show observed admission behavior;
they do not prove a fixed rejection rate. The separate cancellation drill checks that
cancelled streams release reservations. Until a real L4 run completes, the tool and
its dry-run are preparation, not benchmark evidence. The runner limits the concurrent
phase to 60 requests, concurrency 2–16, and a 15-second per-request timeout; even if
all requests time out, the bounded request phases take about ten minutes or less.
