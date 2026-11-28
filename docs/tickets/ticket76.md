# Ticket 76 — Validate links in GPU project documentation

## Objective

Check the local links and heading fragments in the goal, README, GPU lab documents,
and current tickets from both local verification and GitHub Actions. A broken link in
the manual guide or persistent goal can make a correct implementation difficult to
reproduce.

## Current state

Recent documentation packages used a temporary local checker. The repository CI
validated Terraform, Ansible, Compose, tests, and observability, but had no reusable
relative-link check for the GPU project documentation. The handbook, bootstrap
guardrails, and quota corrections are already in open PRs #74 and #75.

## Design and changes

- Add a standard-library-only Python checker for relative Markdown file links and
  heading fragments, including duplicate GitHub heading slugs and fenced-code blocks.
- Cover the README, project goal, all `docs/gpu-lab/*.md` documents, and the current
  implementation tickets. Do not create a repository-wide migration of
  unrelated historical docs.
- Run the check in `make verify` and in the existing `manifests` CI job.
- Add focused tests for valid links, duplicate heading fragments, missing files,
  missing fragments, and code examples.

## Alternatives considered

An external Markdown package or hosted link service would add a dependency and may
require network access during CI. The selected checker uses Python's standard
library and validates only local targets. It intentionally does not validate remote
URL availability, reference-style link definitions, or complex nested Markdown
syntax.

## Validation

Three focused tests passed. Ruff passed for the checker and tests. `make gpu-docs-validate` checked all 27 README/goal/GPU-lab/current-ticket documents. Full `make verify` passed Ruff, 202 tests (2 skipped), dependency audit, Compose, observability, benchmark/evaluation/CUDA dry runs, and the link target. `make terraform-validate` passed all three roots; `git diff --check` passed. The previous PR #76 head `777335c` passed all six required jobs in run `46131623135`; this is historical after the current restack. On the refreshed local stack, the documentation validator again checked 27 files, all 3 focused tests and Ruff passed, and `git diff --check` passed. Fresh PR CI remains pending. No manual clean-room cycle or cloud/GPU operation was run.

## Security and financial boundary

The checker reads repository documentation only. It makes no network request, changes
no AWS resource, downloads no model or image, and cannot print credentials. No project
cost is incurred.

## Outstanding work

- Obtain owner review for PR #76, which is stacked on PR #75.

## Acceptance status

**Current local documentation checks pass; fresh PR CI and owner review remain pending.** No AWS/GPU validation is claimed.
