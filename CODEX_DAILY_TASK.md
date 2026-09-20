# Daily Engineering Task

Read the control files, fetch and inspect the Codex branch/PR, run the quick baseline, then ask: “What is the highest-value remaining blocker preventing PORTFOLIO COMPLETE — LOCAL-FIRST SCOPE?” Continue it. Do not select cosmetic refactors, documentation polish, or P2 work while P0 blockers remain. Use `make test lint` and the relevant local backend/Redis integration test. Update factual status/backlog, commit and push only the Codex branch, then report exact validation and gaps.

As the project approaches completion, clean-room reproducibility becomes P0. Before declaring completion: tear down Project-owned infrastructure; verify teardown; bootstrap clean; smoke; run primary and failure/security demos; validate; clean again; bootstrap a second time; and record evidence. If either rebuild fails, fix it before cosmetic work.
