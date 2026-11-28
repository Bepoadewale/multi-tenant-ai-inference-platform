# Standalone single-L4 EC2 environment

This Terraform root is a separate, static-only design for one Ubuntu EC2 instance
with one NVIDIA L4. It does not deploy EKS, Kubernetes, Redis, databases, or managed
monitoring. It has not been applied to AWS.

## What the root plans

- One VPC, one public subnet in a selected `us-east-1` availability zone, one
  internet gateway, one route table, and one security group.
- No inbound security-group rules. The instance has outbound TCP 443 for Systems
  Manager, images, and model downloads, plus TCP 80 because Ubuntu package mirrors
  may use HTTP. Prefer HTTPS package sources where available. There is no NAT
  Gateway and no interface endpoint. The public address increases exposure if a
  future rule is added; inspect the exact plan and security group before applying.
- One initial instance, restricted to `g6.xlarge`, with IMDSv2 required and
  an encrypted 100 GiB `gp3` root disk deleted on termination.
- A narrow instance role for Systems Manager. The role used by EventBridge Scheduler
  can terminate only this instance ARN.
- Every resource type that the pinned AWS provider exposes as taggable carries explicit
  project, environment, owner, cost-scope, data-class, expiry, and Name tags. Terraform
  tests assert these values directly; they do not rely only on provider `default_tags`.
- Two independent expiry controls: a persistent Ubuntu `systemd` timer installed by
  cloud-init and a one-time EventBridge Scheduler call. Both use the same exact UTC
  expiry. EC2 terminates the instance after the guest shuts down.

The Terraform source contains exactly one `aws_instance` resource and no `count` or
`for_each` for GPU machines. A read-only preflight also rejects an existing,
non-terminated GPU instance with the project's tags. This does not provide physical
GPU isolation between application tenants.
The later `g6.2xlarge` option is intentionally not enabled in this first package; it
requires measured CPU or host-memory evidence and a fresh cost review.

The root takes an exact `ubuntu_ami_id`; it does not ask Terraform for `most_recent`.
The example pins Canonical Ubuntu Server 24.04 amd64 AMI
`ami-0a951420c495183dc`, named
`ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-20261120`. A read-only
`DescribeImages` check on 2026-11-27 returned Canonical owner ID `099720109477`,
`x86_64`, and `available`. The guarded preflight checks these properties before plan
and apply and passes the same ID to Terraform. Review a new Canonical AMI and update
the recorded ID deliberately; the saved plan then contains that exact image ID. If
the image is later deregistered, the destroy plan uses the AMI ID from the project
configuration and does not need to query Canonical's catalog.

The image is expected to include the Systems Manager Agent. Cloud-init enables either
its Snap or Debian systemd service and fails visibly if neither service exists. AWS
documents this as common for Ubuntu Server AMIs; verify the instance is online before
relying on Session Manager.

The planned backend uses the repository's private, versioned state bucket and
DynamoDB lock table managed by `infrastructure/terraform/bootstrap/`, with a separate
key such as `gpu-ec2/us-east-1/terraform.tfstate`. The bootstrap design has not been
applied: the latest exact-name AWS reads found no bucket, lock table, or budget. Apply
the separately reviewed bootstrap plan before initializing this root with remote
state. The S3 backend is configured to use both its native lock file and the
repository's DynamoDB locking contract. Never put state or saved plans in Git.

The Scheduler one-time schedule remains in the Terraform state after firing with the
repository's currently pinned AWS provider. The normal Terraform destroy removes it;
it has no repeat rule. If a Codex or operator session ends early, its target still
terminates the instance at the exact deadline.
The pinned AWS provider does not expose tags on an individual Scheduler schedule, so
the schedule itself is not tagged. Its schedule group is project-tagged, and the
schedule uses the exact project name and remains managed through this dedicated root.

The expiry timestamp is part of cloud-init user data. Changing it after deployment
forces a replacement so the guest timer and cloud schedule cannot silently drift.
The default replacement order terminates the existing instance before creating the
next one; inspect this ordering in any later plan.

After an expiry has passed, the destroy-plan helper supplies a temporary future
timestamp to satisfy the root's input validation. It always calls `terraform plan
-destroy`; review that the plan contains only destroys before approving its checksum.
The temporary timestamp is not used to extend a running host.

The bootstrap root owns the repository budget alert. An alert is only a notification;
it does not stop spending. Its recipient must be verified in AWS before treating the
alert as active. The $25 project ceiling remains enforced by the approved resource
scope, runtime, expiry, and teardown process, not by a budget alert.

## Static validation

From the repository root:

```bash
terraform -chdir=infrastructure/terraform/environments/gpu-ec2 init -backend=false
terraform -chdir=infrastructure/terraform/environments/gpu-ec2 fmt -check -recursive
terraform -chdir=infrastructure/terraform/environments/gpu-ec2 validate
make gpu-ec2-validate
```

`-backend=false` validates configuration without connecting to the remote state
bucket. It does not prove an AWS account has quota, capacity, permissions, or working
SSM/GPU access. `make gpu-ec2-validate` also runs the mocked-provider Terraform tests
in `tests/expiry.tftest.hcl`; these assert configuration relationships without AWS
API calls. They do not prove Scheduler delivery or the guest timer on a real host.
Do not use a normal apply during static validation.

## Eventual operator sequence

The detailed goal and runbook are in `docs/goals/SINGLE_L4_GPU_INFRASTRUCTURE_GOAL.md`
and `docs/gpu-lab/`. Before a paid operation, the owner must complete the repository's
cloud-pilot authorization sequence, refresh the estimate, verify the account and
quota, select an offered AZ, record a future expiry, review the exact saved plan, and
confirm teardown. A read-only check on 2026-11-28 returned an applied G/VT quota of
4 vCPUs, enough on paper for one `g6.xlarge`; the owner reports approval, while the
quota-request history still reads `CASE_OPENED`. Five us-east-1 AZ offerings appeared
in the CLI query, but an offering is not a capacity reservation. No GPU resource or
Terraform apply exists.
The exact remote-state plan, verified budget-alert recipient, full cost, expiry, and
apply-authorization gates still prevent launch.

After an authorized apply, use Session Manager to verify the instance and timer,
configure the GPU manually, export sanitized evidence, then review a Terraform
destroy plan for this root only. The Scheduler and guest expiry are safeguards, not a
substitute for planned teardown.
