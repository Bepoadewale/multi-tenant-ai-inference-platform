# GPU Lab Cost Report — Preliminary Estimate

**Status:** planning estimate only; no cloud resources have been created.  
**Pricing research date:** 2026-11-27 (recheck before any plan or apply).  
**Hard initial ceiling:** USD $25 for this project's AWS usage.  
**Current measured spend:** $0; GPU instance hours: 0.

## Read-only plan scope check

On 2026-11-26 at 23:41 UTC, AWS-backed preview plans were generated from local copies
with their S3 backend blocks removed. The bootstrap preview proposed **7 creates**:
the repository budget, DynamoDB lock table, S3 bucket, and S3 ownership, public-access,
encryption, and versioning controls. Its alert address was the non-routable
`example.invalid` placeholder, so it is not an apply-ready budget configuration.
The GPU preview proposed **14 creates** in `us-east-1c`, including exactly one
`g6.xlarge`, one 100 GiB encrypted gp3 root disk, VPC/subnet/routing/security, IAM, and
the two expiry controls. The resolved Canonical Ubuntu 24.04 image was
`ami-0a951420c495183dc`.

Together these previews show 21 proposed resource creates, but they are not remote-
state plans and are not suitable for apply. Their local plan files are ignored under
`.local/` and must not be committed. The estimate below still requires a final
remote-state plan after the repository bootstrap exists, current price/tax review,
and confirmation that the budget recipient is real and verified.

## What this estimate covers

This estimate models one `g6.xlarge` in `us-east-1` for no more than 12 cumulative
hours, one temporary public IPv4 address, one encrypted 100 GiB `gp3` volume, a
short-lived Terraform state bucket, one expiry schedule invocation, and 1 GiB of
internet data transfer out. It does not include any EKS, database, cache, NAT
Gateway, load balancer, managed monitoring, or DavDeploy resources.

The GPU Compose profile keeps vLLM model cache, Redis data, and MLflow's temporary
SQLite/artifact volume on the instance's existing encrypted root disk. MLflow adds no
separate AWS service or volume, but its artifacts consume part of the 100 GiB disk
allowance; monitor free space and export evidence before termination.

The VPC, subnet, route table, internet gateway, and security group have no hourly
charge by themselves. Systems Manager Session Manager has no additional connection
charge, but its interface endpoints do; the current design avoids both NAT and SSM
interface endpoints by using outbound internet connectivity from an instance with
no inbound service rules. One public IPv4 address is billed while allocated.

## Estimate table

| Resource / assumption | Formula | Planning amount |
| --- | --- | ---: |
| Linux shared `g6.xlarge`, 12 hours | 12 × $0.8048/hour (AWS Price List API lookup, 2026-11-26) | $9.6576 |
| In-use public IPv4, 12 hours | 12 × $0.005/hour | $0.0600 |
| 100 GiB `gp3`, 12 hours | $0.08/GiB-month × 100 × 12/(24×30) | $0.0133 |
| State bucket and versions, up to 1 GiB-month | $0.023/GB-month planning cap; verify exact regional rate | $0.0230 |
| S3 state/lock requests | Up to 1,000 write/list requests at $0.005/1,000; GET allowance | $0.0100 |
| DynamoDB lock requests | Small allowance for GPU-root lock requests against the repository's existing table; no second table | $0.0100 |
| EventBridge Scheduler expiry | Reserve one invocation even if account free tier applies | $0.0100 |
| AWS Budgets notification | Alert-only monthly cost budget with no action | $0.0000 |
| Internet data transfer out | Reserve 1 GiB at $0.90/GB, ten times the current $0.09/GB first-tier published rate; account aggregation and current rate must be checked | $0.9000 |
| **Estimated pre-tax subtotal** | Sum of listed items | **$10.6839** |
| Tax contingency | 25% of subtotal; conservative placeholder, not a tax determination | $2.6710 |
| General contingency | Fixed reserve for price changes and small unmodeled usage | $5.0000 |
| **Planning envelope** | Subtotal + contingency | **$18.3549** |
| **Headroom under $25** | $25 − envelope | **$6.6451** |

The 12-hour runtime is a ceiling for all GPU instance time, not a planned target.
This estimate covers neither an authorization nor a promise that every requested
phase fits in 12 hours. Do not lengthen the run or add resources to use the headroom.
For a concise project-status summary, this estimate rounds to `$18.35`; retain the
unrounded arithmetic above when comparing it with the `$25` ceiling.

## Pricing sources and limitations

- The `g6.xlarge` rate was retrieved from AWS Price List API on 2026-11-26 for Linux,
  shared tenancy, and US East (N. Virginia). Refresh it with the same filters before
  every billable plan; the [EC2 On-Demand pricing page](https://aws.amazon.com/ec2/pricing/on-demand/)
  explains the pricing model but does not promise this instance rate.
- AWS's [EC2 On-Demand pricing page](https://aws.amazon.com/ec2/pricing/on-demand/)
  currently lists $0.09/GB for the first data-transfer-out tier after its shared
  100-GB monthly allowance. The planning line above deliberately reserves ten times
  that rate for one GB; account-wide free allowance may already be consumed, and the
  live regional rate still must be confirmed.
- AWS's [VPC pricing page](https://aws.amazon.com/vpc/pricing/) lists in-use public
  IPv4 at $0.005 per hour, billed in seconds with a 60-second minimum.
- AWS's [EBS pricing page](https://aws.amazon.com/ebs/pricing/) gives a gp3 example
  rate of $0.08 per GB-month and bills provisioned volume storage by time. The final
  plan must confirm the `us-east-1` rate and whether the console/API's GiB size maps
  to the quoted billable unit used in the estimate.
- AWS's [S3 pricing page](https://aws.amazon.com/s3/pricing/) charges for storage and
  requests. The $0.023 and request assumptions above are conservative planning
  values, not a locked regional quote. A versioned bucket retains prior Terraform
  state versions until explicitly cleaned up, so keep the bucket lifetime short and
  count retained object versions.
- AWS's [DynamoDB pricing page](https://aws.amazon.com/dynamodb/pricing/) charges
  on-demand tables by request units and storage. The `$0.01` line is a conservative
  project allowance for a small number of lock operations, not a quoted bill; verify
  current `us-east-1` rates and actual requests before the run.
- AWS says notification-only budgets are free ([AWS Budgets pricing](https://aws.amazon.com/aws-cost-management/aws-budgets/pricing/)). The bootstrap plan creates a `$10` monthly account-alert budget as an early warning; that figure is not the project's `$25` ceiling and does not stop an instance. Confirm this account's currently active budget count before apply.
- The [EventBridge pricing page](https://aws.amazon.com/eventbridge/pricing/) lists
  14 million Scheduler invocations per month in its free tier and $1 per million
  above it. The estimate reserves $0.01 for one invocation rather than relying on
  unused free-tier allowance.
- AWS's [global infrastructure FAQ](https://aws.amazon.com/about-aws/global-infrastructure/global-network/faqs/)
  describes a shared 100 GB/month internet data-transfer-out allowance across
  eligible services and regions. This estimate does not assume that allowance is
  unused: it reserves one GB at a planning rate. Recheck the live us-east-1 rate and
  account-level usage. Model, Docker-image, and package downloads are inbound to AWS;
  keep benchmark output and evidence upload small.
- AWS [Session Manager security guidance](https://docs.aws.amazon.com/prescriptive-guidance/latest/aws-startup-security-baseline/wkld-06.html)
  says Session Manager has no additional EC2 connection fee. Interface endpoints
  have hourly and data-processing charges, which are excluded because none are
  planned.

AWS pricing pages generally exclude taxes and duties. The 25% line is a planning
allowance only. The account billing profile and applicable tax must be reviewed before
the exact run is accepted. If tax or account-level data transfer makes the full plan
reach $25, the plan is not eligible to run.

The existing repository's budget pattern requires a notification recipient. AWS
requires a new direct email recipient to be verified before it receives alerts; do
not put the address in Git or claim the alert is active until AWS shows it as verified.
Use the supplied private input only at the later authorized apply. AWS Budgets can
notify after charges have already accrued, so this alert is an additional signal, not
a stop mechanism ([recipient verification](https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-email-recipients.html),
[budget delay and limits](https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-managing-costs.html)).

## Controls that make the estimate reviewable

1. Allow exactly one full L4 type (`g6.xlarge`) and one instance at once. Keep
   `g6.2xlarge` out of the first plan unless measured CPU or host-memory needs justify
   it and a new estimate remains within the ceiling.
2. Limit the EC2 root/data storage to one encrypted 100 GiB gp3 volume. Do not create
   snapshots, extra volumes, Elastic IPs, endpoints, or log archives by default.
3. Use a short-lived versioned S3 state bucket with server-side encryption, S3-native
  lock files and the repository's existing dedicated pay-per-request DynamoDB table.
  Give this root a unique `gpu-ec2/` key in that bucket. HashiCorp deprecates
  DynamoDB-based locking, so test the selected Terraform release's dual-lock behavior;
  do not create a second table or remove the repository table. State contents are
  sensitive; never commit state or saved plans. Destroy only the GPU workload root;
  do not destroy the shared repository state bucket, lock table, or budget as part of
  routine GPU teardown.
4. Set an exact UTC expiry in an EventBridge Scheduler one-time call that can
   terminate only this instance. Add a guest-side shutdown timer and set guest
   shutdown to terminate the EC2 instance. Both controls must be independently
   demonstrated before the paid run.
5. Restrict normal operation to the prepared execution batch. Do not leave the
   instance running during research, docs, CI, review, or overnight gaps. Record
   start/stop timestamps and cumulative runtime.
6. Omit CloudWatch ingestion by default. Keep local Prometheus/Grafana/Tempo data on
   the temporary encrypted volume, export only sanitized selected evidence, then
   terminate the host and delete the volume.
7. Independently verify the instance, volume, public IP, ENI, and project network
   resources after each batch. A budget alarm is only a notification; it is not a
   spending cap.

These controls reduce the likelihood and duration of cost overruns but cannot make an
AWS invoice mathematically hard-capped. In particular, AWS budgets do not stop an EC2
instance. If either independent expiry mechanism is not implemented or testable, do
not run the lab.

## Before any billable apply

- Recheck account identity, `us-east-1`, permission boundary, the exact On-Demand G/VT
  quota, G6 offerings, and current capacity. Current recorded quota is zero vCPUs
  (`L-DB2E81BA`), so no L4 launch is eligible now.
- Refresh every Price List input, the current tax profile, state retention, EBS size,
  data-transfer rate/aggregation, and Scheduler charges.
- Prepare and inspect one saved Terraform plan: exact resource count, tags, account,
  region, type, storage, public address, security rules, IAM scope, expiry, and
  teardown. Keep it out of Git.
- Confirm the full adjusted estimate is below $25 with the stated reserve. If required
  execution cannot fit under $25, stop cloud work, finish safe local work, and request
  more budget through the user's authorization process.
- On 2026-11-27, after the user explicitly asked to submit the quota request
  immediately, a request for 4 On-Demand G/VT vCPUs was submitted. AWS reports its
  status as `CASE_OPENED` (pending); the applied quota remains zero. No Terraform apply or infrastructure
  mutation has been made. Quota approval does not authorize paid provisioning.

## Current outcome

The first cost gate is prepared but not passed for launch: the estimate is provisional,
there is no final remote-state Terraform plan, and the quota increase request is still
pending while the applied quota remains zero. AWS spend recorded for this goal remains
`$0`.
