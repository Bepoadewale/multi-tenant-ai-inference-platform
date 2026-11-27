# Single-L4 language-model evaluation preparation

This folder contains a small, versioned evaluation suite and a Python runner for an
OpenAI-compatible chat endpoint. It is preparation only: no model is contacted by the
dry-run, and no model-quality result exists until the runner is used against a real
deployment.

## Why this suite exists

Latency and token throughput do not tell us whether a model followed an instruction
or returned valid structured data. This suite checks six generated responses with
simple, repeatable rules and sends one malformed JSON request to confirm that the API
rejects invalid input. The summary case is marked for human review because there is no
single objectively correct summary.

The checks are intentionally modest. Passing them does not prove general model
quality, factual reliability, safety, or readiness for production. The suite is a
smoke gate used alongside representative human review, gateway policy tests, runtime
health checks, and measured performance.

## Local dry-run

From the repository root, run:

```bash
make gpu-evaluation-plan
```

It parses the checked-in task file and prints the suite ID, case count, model alias,
and `network_requests: 0`. It does not start a service or contact AWS. The automated
tests exercise the deterministic scoring helpers without a model.

## Authorized runtime invocation

Only after the exact GPU deployment plan, cost, quota, expiry, and teardown gates have
been approved, run the prepared Compose evaluator on the EC2 host. It waits for vLLM
and MLflow readiness, sends the synthetic cases to the private vLLM endpoint, writes
the report to a temporary path, and uploads the sanitized report and metadata to the
local MLflow service:

```bash
docker compose --env-file deployments/single-gpu/.env \
  -f deployments/single-gpu/compose.yaml \
  --profile gpu-evaluation run --build --rm evaluator
```

The command prints the MLflow run ID. Review the run in the UI through a Systems
Manager port-forward to `127.0.0.1:15011`, then export the sanitized report before
teardown. The MLflow UI/API is not exposed through the instance's public interface.

For a separate trusted host that already has direct network access to an inference
endpoint, the standalone runner can also write a report outside the repository:

```bash
export GPU_EVAL_BASE_URL=http://127.0.0.1:8000/v1
export GPU_EVAL_MODEL=gpu-default
export GPU_EVAL_MODEL_REVISION=989aa7980e4cf806f80c7fef2b1adb7bc71aa306
python3.12 evaluations/gpu_llm/run_evaluation.py \
  --output /var/tmp/gpu-lab/evaluation/qwen-1.5b-results.json
```

To publish from that standalone invocation, set `MLFLOW_TRACKING_URI` to an
authorized MLflow server. The run fails if publication is configured but unavailable;
it does not silently discard the evidence.

The bearer token is optional for the direct local lab endpoint. If the protected
gateway is used, provide its signed tenant bearer token through
`GPU_EVAL_BEARER_TOKEN`; the program does not print or store that value. The runner
records case IDs, pass/fail, elapsed time, token
counts when the server returns them, the suite digest, and a digest of each generated
answer. It never saves prompts or generated text. The report file is restricted to
the current user on Unix-like systems.

By default, subjective response text is not printed or saved. For a controlled
interactive review, add `--show-subjective-response` and inspect it directly in the
terminal; do not redirect or retain that terminal output. The runner returns exit code
2 when automatic checks pass but human review is still outstanding, so an automated
release step cannot mistake this result for a fully approved candidate.

The automatic gate includes deterministic factual, JSON, instruction, reasoning,
technical-term, and malformed-request checks. A summary is marked as requiring human
review and is not scored by the automatic gate. An API or schema error is a failed
case. No retries are performed, so failures remain visible and request counts are
predictable.

## Known runtime checks

- Confirm that the chosen server returns the documented OpenAI chat completion
  schema and usage counts.
- Confirm the malformed-JSON status code is 400 or 422 for the pinned runtime.
- Check that model/template formatting does not break the deterministic assertions.
- Compare the report's model revision with the artifact digest verification record.
- Keep the separate gateway/authentication and tenant-quota tests; this direct suite
  does not establish multi-tenant isolation or authorization.
- Do not run until the paid execution batch is authorized. The default report path is
  outside Git, and raw reports must be reviewed before sharing.

## Release record preparation

`release_control.py` provides local, unit-tested helpers for binding a passing
evaluation report to the full model revision, model artifact digest, vLLM image
digest, serving configuration, and source commit. It also creates an immutable plan
digest and a SQLite approval record that requires an actor different from the plan
requester. A failed candidate, unpinned image, multi-GPU configuration, changed plan,
or stale champion/candidate manifest is rejected.

This is control logic, not a deployment command. The plan is not yet connected to an
authenticated HTTP endpoint or the actual MLflow run, and it does not restart vLLM.
The independent actor in the SQLite helper is a value passed by its caller; a future
API must derive that identity from a verified `release.approve` token. No model should
be switched based only on a local function call. These limits are recorded in the
[sequential release design](../../docs/gpu-lab/SEQUENTIAL_LLM_RELEASE_DESIGN.md).
