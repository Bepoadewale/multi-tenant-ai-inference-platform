# Ticket 31: Repair audited Python dependencies

## Objective

Make the existing local install and gateway image install resolve versions that
address the dependency advisories found by the GPU-goal baseline audit.

## Current state

PR #31 is open as a draft on `codex/fix-baseline-dependency-audit`. The baseline
`make verify` run passed lint and 50 tests but failed at the dependency audit with 84
advisory records across seven transitive distributions.

## Relevant research

The audit was run with the repository's existing `pip-audit --skip-editable` target.
Each minimum in `constraints.txt` corresponds to the patched version identified by
that audit on 2026-11-26. These are resolver constraints, not direct application
dependencies or a fully locked dependency graph.

## Proposed architecture

Use one constraints file for both `make install` and the gateway Docker build. This
keeps local development and the container from resolving versions below the audited
minimums while leaving the application's declared dependency ranges intact.

## Implementation tasks

- [x] Add constraints for the seven affected transitive packages.
- [x] Apply constraints to local and container dependency installation.
- [x] Record baseline failure, fixes, validation, and known limitations.
- [x] Link install guidance and validation from the README and project status.
- [x] Build the gateway image with the constraints.
- [x] Complete two clean local validation cycles and project-scoped cleanup.

## Acceptance criteria

- `make install` succeeds from an empty local environment.
- `make verify` passes including dependency audit.
- Gateway Docker image build passes.
- The full CPU/local demo and smoke check pass from a clean bootstrap.
- No project containers, generated virtual environment, model directory, or test image
  remains after cleanup; preserve existing local user data.
- Do not use AWS or claim GPU validation.

## Commands executed

```console
make install
make bootstrap-local
make smoke
make demo-flagship
make verify
make clean-local
docker build -t inference-gateway:dependency-audit -f gateway/Dockerfile .
git diff --check
```

The install/build/validation sequence above passed. It was repeated from a clean
project state. On the final clean bootstrap, `make demo-flagship` exited 0. The audit
reported `No known vulnerabilities found`; Ruff and all 50 tests passed, with one
existing Starlette/httpx deprecation warning. Compose configuration validation
passed.

## Issues discovered and troubleshooting

The baseline audit failed with 84 advisory records. After applying the constraints,
a repeated flagship sequence on the same Redis state returned 429 in the agent-tools
demo because earlier demo traffic had consumed the fixture tenant's minute quota. A
fresh `make clean-local`, install, and bootstrap reset the quota state; the complete
flagship demo then passed. This behavior and the successful clean run are recorded in
`docs/governance/VALIDATION.md`.

## Security considerations

No credential, secret, or customer data was added. The package floors address the
known audit output but do not create a complete lock file or guarantee future
dependency resolution is immutable.

## Financial considerations

No AWS identity or cloud resource was used. No GPU or paid service was used.

## Evidence collected

- `docs/governance/VALIDATION.md`, “Dependency-audit baseline repair”.
- `make verify`: Ruff pass, 50 passed, no known vulnerabilities, Compose config pass.
- Local gateway image build completed; the temporary test image was removed.
- Two successful clean-room cycles; final project Compose containers, generated
  `.venv`, and generated `models/` absent.
- The pre-existing `.local/self-service/profiles.db` was restored and remains local.

## Outstanding work

- [ ] Review PR #31 and wait for GitHub checks.
- [ ] Merge only through the repository's approved PR workflow.
- [ ] Continue the separate single-L4 goal; AWS GPU work remains gated by the
  documented $25 ceiling and a currently zero G/VT vCPU quota.

## Final acceptance status

Implementation and local validation criteria are complete. PR review and CI checks
remain outstanding. No cloud or GPU acceptance criteria are claimed.
