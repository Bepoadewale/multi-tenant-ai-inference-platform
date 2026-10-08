# Week 3 Goal — Multi-Tenant Inference

Starting maturity: `PORTFOLIO COMPLETE — LOCAL-FIRST SCOPE`.
Current target: preserve the completed flagship while evolving only through validated
P1 vertical slices; retain the completed model
release-control, simulated-capacity, operational-evidence, governed-remediation,
delegated-agent, developer-self-service, edge, and bounded-sandbox slices. Do not
claim physical GPU scheduling, full edge operations, gVisor/Firecracker, or production
adapters until each executes locally.

Clean-room objective: the weekly target is not merely a working current environment; it is an attempted `PORTFOLIO COMPLETE — LOCAL-FIRST SCOPE` outcome with clean bootstrap, demos, validation, safe teardown, and second bootstrap. Record blockers truthfully if unfinished.

Cloud-pilot objective: when cloud hardening is scheduled, complete one bounded CP
slice from `CODEX_BACKLOG.md` at a time. The sequence is architecture → Terraform
foundation → state/security → delivery/ingress → observability/recovery → OIDC
automation → separately authorized cloud execution. Do not call a static plan an AWS
pilot.
