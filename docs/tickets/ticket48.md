# Ticket 48 — Prepare deterministic LLM evaluation

## Objective

Prepare a small, repeatable evaluation suite for the single-L4 model deployment before
the authorized GPU window. It must not make model calls during local validation or
store prompts and responses in public evidence.

## Current state

The repository has MLflow registration and governed release controls for its existing
ONNX demonstration models, but it has no evaluation suite for the planned Qwen/vLLM
runtime. No LLM evaluation has run.

## Research and decisions

- Use a versioned, synthetic JSON task suite rather than adding a third-party
  evaluation dependency.
- Prefer deterministic checks for exact arithmetic answers, JSON structure, list
  length, required terms, and malformed-request rejection.
- Mark summarization as requiring human review; do not use model-generated grading as
  the only release gate.
- Record model revision and suite digest, timing, token counts when returned, case
  status, and response hashes. Do not record request text, completions, or API keys.
- Put runtime reports outside public Git and set owner-only file permissions.
- Require an explicit model revision at execution time. The dry-run performs no network
  operation and may show the revision as unset.

## Changes

- Added six synthetic generation tasks and one malformed-JSON API case.
- Added a stdlib-only OpenAI-compatible evaluator with safe aggregate output, bounded
  per-request timeouts, no retries, a dry-run, and no prompt/completion logging.
- Added local Makefile and CI dry-run targets plus focused unit tests for deterministic
  checks and human-review behavior.
- Added an explicit interactive-only option to display the subjective summary; it is
  not stored in the report. Exit code 2 distinguishes “automatic checks pass, human
  review pending” from a fully clear evaluation.
- Documented runtime invocation and the checks that must be confirmed against the
  exact vLLM runtime before the authorized batch.
- Tightened exact-number matching so a signed token such as `-4` or `+4` cannot pass
  a check expecting the unsigned value `4`.
- Validate successful response completion and token-usage types before scoring. A
  malformed response now becomes a failed case in the report instead of raising an
  uncaught exception that discards prior case results.
- Documented and configured separate runnable paths for private vLLM access from the
  benchmark container and authenticated gateway access through loopback port 8081.
  The examples use the correct backend alias (`gpu-default`) and gateway model
  (`chat-default`). The evaluator source is mounted read-only into the benchmark
  service.

## Acceptance criteria

- Local dry-run reports the suite ID and case count with zero network requests.
- Unit tests cover the numeric boundary, exact JSON object, subjective review marker,
  and suite schema.
- CI runs the dry-run without AWS or a model service.
- No LLM response, GPU measurement, or release decision is claimed before actual
  runtime execution.

## Validation

- `make gpu-evaluation-plan` reported suite `single-l4-qwen-smoke-v1`, seven cases,
  and zero network requests.
- Five Python 3.12 unit tests passed. They cover suite version/case structure, numeric
  boundaries (including `4.5` not passing an expected `4`), exact JSON, and marking
  subjective summaries for human review.
- Ruff, Python bytecode compilation, JSON parsing, and `git diff --check` passed.
- The first numeric-boundary test caught an overly strict period boundary that rejected
  `4.`; the matcher now allows sentence punctuation while rejecting `14` and `4.5`.
- An initial Ruff run found one unused import; it was removed before the passing run.
- No GPU, model, or AWS resource is used. PR CI remains pending.
- Review follow-up on 2026-11-28: Ruff passed and the focused evaluation suite passed
  9 tests. New cases reject signed-number mismatches and verify that null/list
  completions, non-object usage, and non-integer token counts become failed report
  rows. `make gpu-evaluation-plan` reported seven cases and zero network requests;
  Docker Compose configuration validation and `git diff --check` passed. No model,
  container, AWS resource, or GPU was started. Updated PR CI is pending.
- The first mocked-HTTP test attempt failed because `MagicMock`'s context manager
  returned a separate mock instead of the configured response. The test double now
  returns itself from `__enter__`; the production code was not changed for that test
  harness issue.
- An additional attempt to run the full repository test target with the existing
  shared virtual environment failed during collection in 10 gateway modules because
  this isolated worktree had no generated `models/tiny-intent-classifier.onnx` file.
  `make install` normally creates that ignored local artifact. It was not run here, so
  no hidden local model files were generated. The benchmark/evaluation-focused tests
  and Ruff passed; the updated PR CI run remains the full-suite validation path.
- The code and status-document head `24b149c` passed all five required CI jobs in run
  `45996207684`. A follow-up documentation-only head `5af5562` is running through CI.

## Security and financial considerations

The optional signed bearer token is read only from `GPU_EVAL_BEARER_TOKEN` and is not
logged. Raw reports
are written outside the repository with owner-only permissions. The evaluator makes
seven small requests only when explicitly run; static and dry-run paths make none.
Do not include those runtime requests in a paid batch until the exact endpoint, model
revision, request count, time limit, and output location are reviewed.

## Outstanding work

- Validate response shape, token accounting, and malformed-JSON status with the exact
  pinned vLLM image on an authorized L4.
- Run the suite on a protected gateway with a tenant identity as part of a separate
  auth/quota test; this direct evaluator does not prove tenant isolation.
- Evaluate a candidate, record actual quality/performance evidence, and integrate the
  approved result with the existing immutable release plan and sequential rollback.

## Acceptance status

**Static preparation only. No model evaluation, GPU request, AWS operation, or release
decision has occurred.**
