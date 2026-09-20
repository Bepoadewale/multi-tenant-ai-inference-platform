# Validation

Run `make test lint demo`; add Redis and real-backend integration commands as they become executable. Record services started, versions, commands, results, integration evidence, failure demos, and environment assumptions. Record hardware, runtime, exact command and result for any benchmark; never infer GPU behavior from mock traffic or fabricate validation.

## Clean-Room Validation

Do not populate this section until executed. Record: date, commit SHA, OS/environment, Docker/kind/Kubernetes and key dependency versions where applicable; clean starting state; exact install/bootstrap/smoke/demo/failure/validation/cleanup commands; observed results; post-cleanup absence verification; and the second-bootstrap result. No prior local state or fabricated evidence is acceptable.
