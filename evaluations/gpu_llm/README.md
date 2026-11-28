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

Run these only after the exact GPU deployment plan, cost, quota, expiry, and teardown
gates are approved. The vLLM API is private to the Compose network; port 8000 is not
published on the EC2 host. The benchmark image has a read-only copy of this evaluator
so it can call vLLM by its private Compose service name. From the repository root on
the EC2 host, set the verified model revision and a host directory outside the repo:
replace the angle-bracket placeholder with the verified 40-character model commit
before running the command.

```bash
export GPU_MODEL_REVISION=<verified-40-character-model-commit>
export GPU_EVAL_OUTPUT_DIR=/var/tmp/gpu-lab/evaluation
mkdir -p "$GPU_EVAL_OUTPUT_DIR"
docker compose --env-file deployments/single-gpu/.env \
  -f deployments/single-gpu/compose.yaml run --rm --no-deps \
  --entrypoint python \
  --volume "$GPU_EVAL_OUTPUT_DIR:/results:rw" \
  benchmark /opt/gpu-evaluation/run_evaluation.py \
  --base-url http://vllm:8000/v1 \
  --model gpu-default \
  --model-revision "$GPU_MODEL_REVISION" \
  --output /results/vllm-results.json
```

This runs the evaluator inside the benchmark container, where Compose DNS resolves
`vllm`; it does not publish the inference API to the network. The report is written
to the host directory `/var/tmp/gpu-lab/evaluation`.

For an end-to-end check through tenant authentication and gateway routing, run the
evaluator on the EC2 host against the gateway's loopback-only port. The gateway's
client-facing model name is `chat-default` (the backend-only vLLM alias is
`gpu-default`). Obtain a signed tenant token through the tenant identity workflow and
keep it in the host environment; do not put it in shell history or a file committed
to Git. Replace the model-revision placeholder with the verified 40-character
commit before running the command; `read -s` accepts the token without echoing it or
putting its value in shell history:

```bash
export GPU_EVAL_BASE_URL=http://127.0.0.1:8081/v1
export GPU_EVAL_MODEL=chat-default
export GPU_EVAL_MODEL_REVISION=<verified-40-character-model-commit>
read -rsp 'Tenant token: ' GPU_EVAL_BEARER_TOKEN; printf '\n'; export GPU_EVAL_BEARER_TOKEN
python3 evaluations/gpu_llm/run_evaluation.py \
  --output /var/tmp/gpu-lab/evaluation/gateway-results.json
```

The token is read from the environment and is not printed or stored in the report.
The runner records case IDs, pass/fail, elapsed time, token counts when returned, the
suite digest, and a digest of each generated answer. It never saves prompts or
generated text. The report file is restricted to the current user on Unix-like
systems.

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
