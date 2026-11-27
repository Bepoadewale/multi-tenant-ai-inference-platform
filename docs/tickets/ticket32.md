# Ticket 32 — Isolated single-L4 EC2 foundation

## Objective

Prepare a separate, static-only Terraform environment for one Ubuntu `g6.xlarge`
with a single NVIDIA L4. Add cost/runtime guards, reproducible plan and teardown
commands, and independent cleanup checks without changing the existing EKS contract
or local CPU inference path.

## Current state

- Branch: `codex/gpu-ec2-foundation`, based on PR #30 head `04cb564`.
- Phase: 2 of 12, static infrastructure preparation.
- Terraform describes the proposed environment; it has not been applied.
- AWS account identity was verified before the quota request. Applied On-Demand G/VT
  quota remains zero vCPUs (`L-DB2E81BA`); a requested increase to 4 vCPUs is pending.
- `g6.xlarge` is currently listed in `us-east-1a`, `1b`, `1c`, `1d`, and `1f`. This
  shows an offering, not available capacity. No instance was launched.
- AWS spend and GPU instance-hours remain zero for this goal.
- Exact-name read-only checks found the repository state bucket, lock table, and
  monthly budget absent; the bootstrap preview includes them as creates.

## Research and design

- Use Canonical Ubuntu 24.04 x86_64 from the official owner. Resolve the exact image
  during planning and retain the saved plan locally; the root does not pin a moving
  AMI alias as a permanent image ID.
- Reuse the repository-owned encrypted/versioned S3 state bucket and DynamoDB lock
  table, and use `gpu-ec2/us-east-1/terraform.tfstate` as this root's unique state
  key. Enable S3-native locking as well as the repository-required DynamoDB locking.
- Create a VPC, one public subnet and route, one no-ingress security group, a narrow
  Systems Manager instance profile, one `g6.xlarge`, and one encrypted 100 GiB gp3
  root volume tagged for the project and deleted on termination.
- Bound egress to TCP 443 and 80. Port 443 supports Systems Manager and artifacts;
  port 80 is retained for Ubuntu package mirrors and should be removed when all
  required sources use HTTPS. There is no NAT Gateway, endpoint, persistent load
  balancer, or managed monitoring service.
- Require IMDSv2. Use no SSH key and expose no inbound ports. The instance has a public
  address for outbound connectivity, which increases its network exposure and is
  documented as a lab trade-off.
- Enforce a 12-hour maximum expiry in Terraform input validation, a persistent
  `systemd` timer in cloud-init, and a one-time EventBridge Scheduler action scoped by
  IAM policy to this EC2 instance ARN. EC2 terminates after guest shutdown.
- Run a preflight for account, region, quota, AZ offering, existing tagged GPU
  instances, and repository state/budget guardrails. It is read-only and does not
  reserve capacity.
- Use a separate local-state preview plan only to inspect the exact proposed resource
  shape before repository backend bootstrap. It strips the S3 backend in a copy and
  must never be used to apply. The future apply path uses the repository's actual
  remote state and an exact SHA-256-reviewed saved plan.
- Routine destroy is limited to this GPU root. The independent verifier checks tagged
  EC2/network/storage and temporary IAM/Scheduler resources. It intentionally leaves
  the shared repository state bucket, lock table, and budget in place.

## Acceptance criteria

- [x] Separate root does not include EKS, databases, cache, NAT Gateway, or another
  accelerator family.
- [x] Root contains exactly one `aws_instance`, restricted to `g6.xlarge` for this
  first package; a later `g6.2xlarge` change requires measured justification and new
  cost review.
- [x] Account, region, expiry, and instance type have static guards.
- [x] IMDSv2, encrypted gp3, no-ingress security group, scoped IAM expiry policy, and
  two expiry paths are defined.
- [x] Plan/apply/destroy commands are separated. Apply and destroy require an explicit
  environment confirmation and an exact saved-plan checksum.
- [x] Cleanup verifier is read-only and scoped to this project environment.
- [x] Existing EKS and bootstrap roots still validate with backend disabled.
- [x] Inspect the AWS-backed read-only preview plan and record resource counts and
  the resolved AMI. The latest local GPU preview hash is recorded in the evidence
  manifest; the saved plan is not apply-ready.
- [ ] Review and merge through the normal pull-request process.
- [ ] Real account-side expiry behavior, GPU host, and cleanup are later phases and
  remain unverified.

## Validation performed

- `make terraform-validate`: passed for bootstrap, existing EKS, and GPU EC2 roots.
- `make gpu-ec2-validate`: passed Terraform backend-disabled initialization, format
  check, and validation for the new root.
- `bash -n scripts/gpu-ec2-*.sh`: passed for the preflight and guarded operations.
- `git diff --check`: passed.
- AWS read-only `sts get-caller-identity`, Service Quotas, and EC2 instance type
  offerings queries succeeded. The quota is zero; the offering list is not a capacity
  reservation.
- AWS-backed local-state previews reached terminal success: 7 bootstrap creates and
  14 GPU-root creates. The GPU preview resolved Canonical AMI
  `ami-0a951420c495183dc` and AZ `us-east-1c`. Plans are local and not suitable for
  apply; hashes are recorded in the evidence manifest and raw plans stay outside Git.
  The latest source-updated preview SHA-256 is
  `5a0574c21199d11e6af5ccbb8226240cf7a7b672ddd9ebbb5f6c64f6814658e1`.
- No AWS resource mutation or GPU operation was attempted.

## Issues and approaches

- Terraform validation initially rejected `action_after_completion` on the
  repository's pinned AWS provider `5.100.0`. The optional one-time-schedule cleanup
  field appears in newer provider documentation but not the pinned schema. Kept the
  repository provider version, removed that field, and documented that the schedule
  is removed by the normal Terraform destroy. The schedule does not repeat and still
  terminates the instance if the operator session ends.
- A multi-line Terraform boolean expression initially failed HCL parsing. Parentheses
  around the combined expiry condition fixed it; the final three-root validation
  passed.
- `terraform console` in the real root required backend initialization and stopped
  before rendering cloud-init. It did not contact AWS or modify state. Rendering from
  the backend-free preview copy succeeded and Ruby YAML parsing passed. Cloud-init
  execution, SSM registration, and live timer behavior remain explicit validation
  work. The first Ruby parser call used an unavailable `safe_load_file` method; using
  `YAML.safe_load(File.read(...))` succeeded.
- A first reading mistakenly treated the repository rule as requiring a separate
  lock table per root. Re-reading `AGENTS.md` and the existing bootstrap showed the
  rule is repository-scoped. The GPU root now reuses the repository bucket/table and
  uses a unique key namespace; it does not create duplicate shared guardrails.
- Terraform `check` assertions report failed checks as warnings and are not a strong
  apply boundary. The first account and AZ checks used that form. Replaced the account
  check with the AWS provider's `allowed_account_ids` enforcement in both the GPU and
  prerequisite bootstrap roots, and moved the AZ offering assertion into an EC2
  resource precondition so Terraform must stop before launch when the type is not
  offered in the selected zone.

## Security and financial considerations

- Hard project ceiling: USD $25. Preliminary 12-hour estimate: approximately $18.35
  including a 25% tax placeholder and $5 reserve. It remains provisional and must be
  refreshed against the exact full plan, tax profile, transfer, and state lifecycle.
- A 4-vCPU G/VT quota request for one `g6.xlarge` is pending following the user's
  direct instruction. This request alone does not authorize any paid provisioning.
- AWS Budgets is an alert only and does not stop the instance. The repository's
  recipient must be privately supplied and verified before treating notifications as
  active.
- Local plan files and raw Terraform state remain under ignored `.local/` or remote
  encrypted state; do not commit them. No credential is stored in source.
- No inbound path is configured. The public IP and broad destination set on egress
  ports 80/443 remain trade-offs requiring plan review.

## Outstanding work and next step

Update the execution journal and evidence manifest with the latest preview and rendered
template evidence, finish the final static review, and open this package as a focused
PR. Prepare the exact remote-state plan and full cost review while the quota request
is pending. No apply or GPU hours are part of this ticket's current work.
