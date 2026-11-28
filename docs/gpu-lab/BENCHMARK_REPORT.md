# Single-L4 Inference Benchmark Report

**Status:** report framework prepared; no L4 measurements exist. This document must
be completed from real results after quota approval and an authorized GPU batch. The
empty result cells below are intentional; do not fill them with estimates, mock
responses, or results from CPU ONNX tests.

## Purpose

The lab measures whether one NVIDIA L4 can serve the selected model with useful
latency and throughput while the gateway enforces synthetic tenant controls. It
separates direct vLLM behavior from the full gateway path. It also captures the cost
and reliability trade-offs needed to decide what to optimize next.

The benchmark code and workloads are in:

- [`run_vllm_matrix.py`](../../benchmarks/gpu_inference/run_vllm_matrix.py) for the
  direct serving matrix.
- [`run_gateway_benchmark.py`](../../benchmarks/gpu_inference/run_gateway_benchmark.py)
  for authenticated tenant requests and the exploratory direct/gateway comparison.
- [`workloads.json`](../../benchmarks/gpu_inference/workloads.json) for the
  context-bounded synthetic workload shapes.
- [`CUDA performance lab`](../../benchmarks/cuda_performance/README.md) for
  synchronized PyTorch and vector-add experiments.

## Evidence boundary

The latest read-only AWS check reports 4.0 applied G/VT vCPUs, but no GPU instance
has run and the quota request record still says `CASE_OPENED`. Static dry-runs
validate command generation and bounds. Mock-transport tests
validate privacy and client behavior. CI validates repository behavior, including
the local CPU path. None of those results are L4 measurements.

| Result class | Current state | May be reported as |
| --- | --- | --- |
| Workload matrix | Static dry-run exists | Prepared commands and context checks |
| Gateway benchmark | Mocked/unit tested; L4 guard implemented | Client behavior and metadata safeguards |
| Direct vLLM serving | Not run | No model latency or throughput result |
| Authenticated GPU requests | Not run | No tenant benchmark result |
| GPU memory/utilization | Not run | No L4 capacity or utilization result |
| AWS cost | Estimate in `COST_REPORT.md`; no lab spend | Estimated cost only, not settled billing |

## Experiment questions

Complete the questions with evidence and an explanation after the real run.

1. How does request latency change between short, medium, and long input prompts?
2. How do time to first token and decode speed change as output length increases?
3. How does client concurrency affect throughput, P95/P99 latency, queueing, and
   failures when the engine sequence cap is two?
4. Does gateway admission and metering add measurable latency in this exploratory
   setup? What factors make the comparison imperfect?
5. How do CPU utilization, system memory, GPU activity, and framebuffer use change
   during model load and steady inference?
6. Which observed limit appears first: model execution, GPU memory, host resources,
   gateway queueing, Redis, network, or client generation?
7. What is the estimated whole-experiment cost per successful task and per million
   input/output tokens under the stated allocation method?
8. Which failure or overload condition was observed, and did the system recover
   without a leaked request or concurrency reservation?

## Fixed workload plan

The direct serving matrix prepares 100 measured prompts per run after five warm-up
requests, with three repetitions for each selected case. Its default is 11 cases:

| Shape | Input tokens | Output tokens | Concurrency levels |
| --- | ---: | ---: | --- |
| Short | 256 | 64 | 1, 2, 4, 8 |
| Medium | 1,024 | 128 | 1, 2, 4, 8 |
| Long context | 4,096 | 128 | 1, 2, 4 |

Concurrency 16 is opt-in after lower levels demonstrate adequate memory and error
margin. The profile currently sets vLLM `--max-num-seqs=2`; client concurrency above
two measures waiting and scheduling around that engine cap. It does not mean all
client requests run simultaneously on the GPU. The context window candidate is 8,192
tokens; actual rendered token counts must be checked before sending a workload.

The authenticated gateway benchmark uses three synthetic identities and a bounded
request set. Its 15-second request timeout and 60-request concurrent phase are hard
client bounds. It records status, latency, token usage, and client-side semaphore
wait, but not prompts, completions, bearer tokens, response bodies, or raw error
details.

## Method

Before the paid run:

1. Recheck the AWS account, applied quota, instance offering, signed package indexes,
   model revision/license/digest, vLLM image digest, Terraform state, and current
   all-in cost estimate.
2. Ensure the exact reviewed plan, expiry, $25 ceiling, and evidence-export steps are
   approved. The GPU batch must fit the current remaining budget and authorized
   runtime.
3. Run `make gpu-benchmark-plan` and `make gpu-gateway-benchmark-plan` on the local
   workstation. These commands do not contact AWS or an inference service.
4. On the authorized EC2 host, verify one L4, pinned software, and healthy vLLM,
   gateways, Redis, and monitoring before the benchmark.
5. Record host and model metadata; perform warm-ups; synchronize CUDA kernel timing
   experiments; run the serving matrix with its fixed bounds; export sanitized
   results before teardown.
6. Stop or reduce load on GPU memory pressure, rising queue, repeated timeout, or
   budget/runtime reserve risk. Do not extend the instance window implicitly.

vLLM's serving client measures API-level request behavior, not individual CUDA kernel
duration. Kernel-level comparisons use the separate synchronized CUDA C++, PyTorch,
and Triton lab. Nsight Systems is reserved for one short CUDA timeline, and optional
Nsight Compute counters are kept out of normal timing runs because replay and counter
collection affect execution. No Triton or Nsight L4 result exists yet; the exact
commands and counter-permission limits are in the [CUDA lab guide](../../benchmarks/cuda_performance/README.md).
Direct-versus-gateway P50 differences are exploratory because requests can observe
different scheduling, cache, and network state; they are not a pure gateway-overhead
measurement. Client semaphore wait is generated by the benchmark client, not the
server's queue.

## Required run metadata

| Field | Value |
| --- | --- |
| Capture timestamp (UTC) | Pending real L4 run |
| Source commit | Pending real L4 run |
| AWS region and instance type | Pending real L4 run |
| GPU model and reported memory | Pending real L4 run |
| NVIDIA driver / CUDA driver API | Pending real L4 run |
| CUDA Toolkit / PyTorch | Pending real L4 run |
| vLLM image digest and version | Pending real L4 run |
| Model ID, revision, license, artifact digest | Pending real L4 run |
| Precision / context / sequence cap | Pending real L4 run |
| Warm-up and repetitions | Record actual command and output |
| Request shape / concurrency / duration | Record actual command and output |
| Instance start/stop and cumulative GPU hours | Pending real L4 run |
| Estimated full-batch cost and assumptions | Pending refreshed cost calculation |
| Actual settled billing | Pending AWS billing settlement |

## Results

No measurements have been collected. Replace this notice only after the authorized
GPU execution and evidence export.

| Shape | Concurrency | Successful requests | Failures | TTFT P50/P95/P99 | TPOT / ITL | Output tokens/s | Peak VRAM | GPU utilization |
| --- | ---: | ---: | ---: | --- | --- | ---: | ---: | ---: |
| Not measured | — | — | — | — | — | — | — | — |

Report each value with units, sample count, repetition count, and source artifact.
Include failed runs and partial results. Do not replace a failed sample with a
successful rerun without retaining the original result.

## Cost calculations

Record the complete batch cost estimate as:

```text
estimated batch cost = instance hours × current hourly rate
                     + public IPv4 cost
                     + gp3 storage/runtime charges
                     + Terraform state and lock storage requests
                     + scheduled expiry charges
                     + data transfer and image/model download allowance
                     + applicable tax and contingency
```

Use settled billing when it is available. If billing has not settled, label the
result “estimated” and show the assumption dates. Do not call AWS Budget alerts a
spending limit.

```text
estimated cost per successful request = full batch cost / successful requests
estimated cost per 1M input tokens    = allocated batch cost / measured input tokens × 1,000,000
estimated cost per 1M output tokens   = allocated batch cost / measured output tokens × 1,000,000
```

If the same shared GPU cost is divided by input tokens and then output tokens,
present those as two separate allocation views; do not add them as independent
charges. State the allocation method, include failed requests in full batch cost,
and report cost per successful evaluation task as a separate outcome metric.

## Analysis template

For every experiment, answer:

- **Question:** what operational decision was this run intended to inform?
- **Design:** what input shape, repetitions, warm-up, concurrency, and timing method
  were used?
- **Result:** what did the raw data show, with units and sample count?
- **Explanation:** why did the behavior occur? Which phase or resource was limiting?
- **Expectation:** did this match the prediction? What evidence supports that view?
- **Next change:** what single controlled variable should be tested next?
- **Limits:** what sample size, virtualization, cache, or measurement issue affects
  confidence?

## Evidence links to fill after execution

| Artifact | Status |
| --- | --- |
| Sanitized direct vLLM aggregate JSON | Pending |
| Sanitized authenticated gateway report | Pending |
| GPU/host telemetry samples | Pending |
| Benchmark charts generated from actual data | Pending |
| Exact commands and source SHA | Pending |
| Cost estimate and settled billing status | Pending |
| Evidence manifest entry and PR/commit | Pending |

## Current static evidence

- Direct vLLM benchmark command matrix and context checks: see the
  [benchmark preparation guide](../../benchmarks/gpu_inference/README.md).
- Authenticated client safety and bounds: see [ticket #60](../tickets/ticket60.md)
  and [interview preparation](INTERVIEW_PREPARATION.md).
- Current price assumptions and no-spend status: see [cost report](COST_REPORT.md).
- Actual L4 values: none. GPU execution awaits nonzero applied quota, exact
  authorization, and a reviewed bounded plan.
