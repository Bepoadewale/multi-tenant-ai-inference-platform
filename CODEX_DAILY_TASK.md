# Daily Engineering Task

Read the control files, fetch and inspect the Codex branch/PR, run the quick baseline,
then ask: “What is the highest-value remaining flagship-integration blocker?” Continue
it. Preserve the authenticated gateway, Redis admission, ONNX inference, metering and
observability before adding any slice. Do not select cosmetic refactors or copy another
repository wholesale; integrate through a narrow contract and prove it locally.

As the project approaches completion, clean-room reproducibility becomes P0. Before declaring completion: tear down Project-owned infrastructure; verify teardown; bootstrap clean; smoke; run primary and failure/security demos; validate; clean again; bootstrap a second time; and record evidence. If either rebuild fails, fix it before cosmetic work.

Before certifying any implementation PR as ready for human review, apply the same
project-scoped clean-room sequence to that change and record exact evidence in
`docs/governance/VALIDATION.md`. A PR without it remains draft; only documentation-only PRs may
state that runtime evidence is not applicable.

For future cloud work, Terraform is the required provision/teardown authority. Keep
cloud work outside the local evidence boundary until a reviewed Terraform plan, applied
resources, Terraform destroy, and provider-side post-destroy verification are recorded.
