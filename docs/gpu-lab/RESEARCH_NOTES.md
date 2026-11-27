# GPU Lab Research Notes

Research was started on 2026-11-26 and updated on 2026-11-27. This remains a Phase 1 design record, not a final compatibility matrix. Recheck sources immediately before implementation because prices, quota, software releases, and model artifacts change.

## AWS hardware, region and quota

- AWS's [G6 product page](https://aws.amazon.com/ec2/instance-types/g6/) and [accelerated instance specification table](https://docs.aws.amazon.com/ec2/latest/instancetypes/ac.html) describe G6 as NVIDIA L4 based. The single-GPU `g6.xlarge` is listed with 4 vCPUs, 16 GiB host memory, one L4, and 22 GiB of listed GPU memory; `g6.2xlarge` has 8 vCPUs, 32 GiB, and one L4 with the same listed GPU memory. The GPU is commonly described as a 24 GB L4; AWS's table expresses the per-instance memory as 22 GiB. Capacity and runtime compatibility still need live validation.
- Read-only `describe-instance-type-offerings` in `us-east-1` listed `g6.xlarge` in `us-east-1a`, `1b`, `1c`, `1d`, and `1f`; it listed `g6.2xlarge` in `1a`, `1b`, `1c`, `1d`, and `1f`. Offering means the type is supported in that AZ, not that capacity can be launched.
- Read-only Service Quotas lookup returned `Running On-Demand G and VT instances = 0.0 vCPUs`, quota code `L-DB2E81BA`. AWS [EC2 instance quota documentation](https://docs.aws.amazon.com/ec2/latest/instancetypes/ec2-instance-quotas.html) says this quota is adjustable; AWS's [quota increase procedure](https://docs.aws.amazon.com/servicequotas/latest/userguide/request-quota-increase.html) notes increases require a request and may be reviewed. No increase has been requested. This is the current blocker for an On-Demand L4.
- A read-only AWS Price List API query on 2026-11-26, filtered for `g6.xlarge`, Linux, shared tenancy, `US East (N. Virginia)`, returned **$0.8048 per instance-hour**. This is the AWS catalog price, not a settled bill. Instance-only totals are `$6.4384` for 8 hours and `$9.6576` for 12 hours.
- [Amazon VPC pricing](https://aws.amazon.com/vpc/pricing/) currently lists an in-use public IPv4 address at `$0.005/hour`, billed per second with a 60-second minimum. If the public-subnet/no-inbound design needs one public IPv4 for outbound package/model downloads and SSM, add `$0.06` for a 12-hour window. Avoiding NAT Gateway is material to the small budget.
- [EBS pricing](https://aws.amazon.com/ebs/pricing/) documents gp3 per-second billing and gives an example regional rate of `$0.08/GiB-month`, with 3,000 baseline IOPS and 125 MiB/s included. At that example rate, 100 GiB for 12 hours is about `$0.0133`; confirm us-east-1's current rate and actual retained duration before apply.
- AWS [Session Manager](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager.html) avoids inbound SSH and key management. Check SSM Agent, instance role, endpoint reachability, and required IAM access. The instance still needs outbound HTTPS for package/model downloads. Recheck current Session Manager pricing and logging choices when finalizing the cost sheet.
- IMDSv2 is configured with `HttpTokens=required` per [EC2 metadata options](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/configuring-IMDS-new-instances.html). Docker/container access needs a deliberate hop-limit choice; do not increase it without a specific need.
- AWS's [EC2 NVIDIA driver guide](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/install-nvidia-driver.html) confirms G6 supports Tesla drivers; the [public driver matrix](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/public-nvidia-driver.html) identifies G6 as an L4 with minimum driver version 525.0. The current AWS guide includes manual Ubuntu 24.04 driver/CUDA installation instructions. NVIDIA's [Ubuntu driver guide](https://docs.nvidia.com/datacenter/tesla/driver-installation-guide/latest/ubuntu.html) documents header preparation, version pinning, compute-only install, and reboot. Candidate OS: standard Ubuntu 24.04 x86_64. The final driver/CUDA pair remains unresolved until a pinned vLLM build is selected and checked against the L4 and host kernel.
- NVIDIA's [Container Toolkit installation guide](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html) requires an installed NVIDIA driver first and then configures container runtime support. It documents a systemd cgroup reload caveat that can affect container GPU visibility; add this to the troubleshooting lab if the chosen Docker/runtime configuration is affected.

## Initial cost gate (not the final authorization estimate)

| Component | Current input | 12-hour planning amount |
| --- | --- | ---: |
| One Linux `g6.xlarge` | AWS Price List API, `$0.8048/hour` | `$9.6576` |
| One public IPv4, if used | AWS VPC pricing, `$0.005/hour` | `$0.0600` |
| 100 GiB gp3 | Example rate `$0.08/GiB-month`, 12/720 of a 30-day month | `$0.0133` |
| Subtotal above | Excludes state/lock, log ingestion, data transfer, taxes, and unexpected use | **`$9.7309`** |

This leaves about `$15.27` under the `$25` cap for all other charges, but it is not a complete total estimate or permission to apply. Confirm exact AMI/storage/billing dimensions, Terraform state and lock costs, CloudWatch/log choices, public IP duration, model download, data transfer, taxes, and resource cleanup. Prefer default EBS performance, avoid NAT and persistent endpoints, bound egress, and make state resources temporary where repository governance allows.

## vLLM and model starting point

- Current [vLLM GPU installation documentation](https://docs.vllm.ai/en/latest/getting_started/installation/gpu/) describes CUDA-specific prebuilt binaries, currently CUDA 13.0 in the `latest` view reached during research. Its [stable documentation](https://docs.vllm.ai/en/stable/getting_started/installation/gpu/) and version-specific release pages can represent a different current package matrix. The project must pin a specific vLLM release, wheel/container digest, Python, PyTorch/CUDA build, and driver, then test that combination on the L4. Do not use `latest` or infer compatibility just from `nvidia-smi`.
- The [Qwen/Qwen2.5-1.5B-Instruct model card](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct) identifies the model as Apache-2.0 licensed and documents its model family and usage. Verify the repository license file at the exact pinned model commit, artifact SHA-256, tokenizer, chat template, context requirements, and vLLM support before download. The browser page currently points at a moving `main`; it is not yet a pinned artifact.
- AWS lists 22 GiB per L4 on these instances (roughly the familiar 24 GB nominal figure). All usable GPU memory is shared by model weights, runtime/workspaces, CUDA graphs and attention KV cache. Start with the smallest model; measure context and concurrency before attempting 7B or quantized variants.

## Source list for later implementation research

Continue with current primary documentation before each phase: [AWS G6](https://aws.amazon.com/ec2/instance-types/g6/), [AWS EC2 accelerated specs](https://docs.aws.amazon.com/ec2/latest/instancetypes/ac.html), [EC2 public NVIDIA driver options](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/public-nvidia-driver.html), [AWS pricing calculator](https://calculator.aws/), [AWS Budgets](https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-managing-costs.html), [Terraform](https://developer.hashicorp.com/terraform/docs), [AWS Terraform provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs), [Ansible](https://docs.ansible.com/), [Ubuntu](https://documentation.ubuntu.com/), [NVIDIA driver install](https://docs.nvidia.com/datacenter/tesla/driver-installation-guide/), [CUDA](https://docs.nvidia.com/cuda/), [CUDA programming guide](https://docs.nvidia.com/cuda/cuda-c-programming-guide/), [Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/), [DCGM](https://docs.nvidia.com/datacenter/dcgm/), [DCGM Exporter](https://github.com/NVIDIA/dcgm-exporter), [Nsight Systems](https://docs.nvidia.com/nsight-systems/), [Nsight Compute](https://docs.nvidia.com/nsight-compute/), [Docker](https://docs.docker.com/), [PyTorch](https://docs.pytorch.org/), [PyTorch Profiler](https://docs.pytorch.org/docs/stable/profiler.html), [Triton](https://triton-lang.org/main/index.html), [Prometheus](https://prometheus.io/docs/), [Grafana](https://grafana.com/docs/), [OpenTelemetry](https://opentelemetry.io/docs/), [Redis](https://redis.io/docs/latest/), [MLflow](https://mlflow.org/docs/latest/), and [GitHub Actions](https://docs.github.com/en/actions).

## Decisions still open

- Whether the `$25` cap can cover the requested GPU-dependent validation with enough runtime to install the driver, download the model, integrate/observe/benchmark it, run safe incident drills, and export evidence. The instance-only estimate leaves room but time-consuming manual setup could use it quickly.
- How to raise the account's current zero On-Demand G/VT quota; no request submitted.
- Exact Ubuntu LTS point release/AMI, kernel, driver branch, CUDA compatibility, Docker Toolkit release, PyTorch build, vLLM release, and container image digest.
- Exact encrypted Terraform state/locking arrangement that follows repository governance without creating long-lived costs above the project cap.
- Which monitoring components can coexist on 16 GiB host memory without invalidating the inference experiment; measure before selecting `g6.2xlarge`.

## Compatibility research update (2026-11-26)

Current primary documentation provides a useful candidate stack, but exact package
versions and artifacts are not pinned yet and no GPU run has tested them:

- AWS's [EC2 public NVIDIA driver guide](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/public-nvidia-driver.html)
  documents manual installation on standard Ubuntu 24.04 x86_64. Its current example
  uses CUDA Toolkit 13.0 and NVIDIA driver package 580.65.06; it requires kernel
  headers matching `uname -r` before installation. This is an official installation
  path, not proof that that exact driver is available for the eventual AMI or that
  every vLLM wheel choice works on the selected kernel.
- NVIDIA's [CUDA compatibility matrix](https://docs.nvidia.com/deploy/cuda-compatibility/latest/minor-version-compatibility.html)
  lists a minimum driver family of 580 for CUDA 13.x and 525 for CUDA 12.x under
  minor-version compatibility. Newer drivers retain backward compatibility. The
  per-toolkit release notes still govern exact driver requirements and feature
  limits, so the broad family table alone is not enough to pin a deployment.
- vLLM's [stable GPU guide](https://docs.vllm.ai/en/stable/getting_started/installation/gpu/)
  lists L4 among supported CUDA GPUs, requires Linux and Python 3.11–3.14, and
  currently documents prebuilt CUDA 12.9 wheels by default, with CUDA 12.8 and 13.0
  alternatives. It warns that compiled CUDA kernels create binary compatibility
  constraints and recommends a fresh environment. The vLLM wheel bundles PyTorch;
  for serving, use the wheel's PyTorch rather than layering an independently resolved
  PyTorch build into the same environment. Pin a dated vLLM release and wheel/image
  digest at implementation time; current `stable` docs are not a reproducibility pin.
- The [PyTorch install guide](https://pytorch.org/get-started/locally/)
  recommends choosing an NVIDIA CUDA-enabled binary for CUDA-capable systems and
  verifying `torch.cuda.is_available()`. For a separate standalone CUDA/PyTorch lab,
  install the matching official binary in its own environment/container. This avoids
  changing vLLM's bundled dependency set.
- The [AWS EC2 accelerated-instance table](https://docs.aws.amazon.com/ec2/latest/instancetypes/ac.html)
  currently lists the selected G6 sizes as one NVIDIA L4 with 22 GiB. It also lists
  fractional L4 `g6f` instances; these do not satisfy the project's one full L4
  requirement and are explicitly excluded.

**Candidate, not final pin:** standard Ubuntu 24.04 x86_64; the AWS documented
CUDA 13.0/driver 580.65.06 manual path; vLLM from a dated release with a matching
published CUDA wheel or image; the PyTorch build supplied by that vLLM package.
Before a billable batch, verify the full exact compatibility tuple, model access and
download size, AMI/kernel, Docker/NVIDIA Container Toolkit support, current package
digests, and actual G6 capacity. The $25 cap and zero G/VT account quota remain
independent gates.

## State, access, and cost-control research update (2026-11-26)

- HashiCorp's [S3 backend guide](https://developer.hashicorp.com/terraform/language/backend/s3)
  supports native S3 lock files through `use_lockfile = true`, recommends bucket
  versioning, supports encryption, and marks DynamoDB-based locking deprecated. The
  repository's `AGENTS.md` requires repository-scoped state guardrails and unique key
  namespaces. The existing bootstrap defines that bucket and table. Reuse them for
  the GPU root with a unique `gpu-ec2/` state key, and configure an S3 lock file too;
  validate dual-lock compatibility. Do not silently remove the DDB requirement just
  because newer Terraform supports S3 locking. Exact Terraform minimum, state
  bootstrap, IAM access, and lifecycle still need implementation and validation.
- AWS [Session Manager guidance](https://docs.aws.amazon.com/prescriptive-guidance/latest/aws-startup-security-baseline/wkld-06.html)
  says Session Manager has no additional EC2 connection charge; interface VPC
  endpoints do incur hourly and data-processing charges. A public subnet with no
  inbound rules and outbound internet access avoids those endpoints and a NAT
  Gateway, but it still exposes a public IP and must be reviewed as an egress-only
  lab design. Package/model downloads flow out from the instance, so model and image
  pulls must be completed inside a bounded runtime.
- AWS documents SSM Agent as preinstalled on typical Ubuntu Server 24.04 AMIs and
  provides separate systemd service names for Snap and Debian packages ([Ubuntu
  setup](https://docs.aws.amazon.com/systems-manager/latest/userguide/agent-install-ubuntu.html),
  [AMI verification](https://docs.aws.amazon.com/systems-manager/latest/userguide/ami-preinstalled-agent.html)).
  The static root enables either known service and fails cloud-init if neither is
  present; real managed-instance registration still needs live validation.
- AWS's [S3 pricing page](https://aws.amazon.com/s3/pricing/) describes pay-for-use
  storage and requests and says internet ingress is not charged. It also lists the
  first 100 GB/month of internet egress across eligible AWS services as free; the
  project estimate should not rely on free-tier eligibility or omit any transfer.
  Final S3 state/version/object storage cost and lifecycle must be calculated at the
  real plan stage.
- The AWS [EC2 service-authorization reference](https://docs.aws.amazon.com/service-authorization/latest/reference/list_ec2.html)
  lists `ec2:TerminateInstances` for instance resources with resource-tag condition
  keys. The AWS [Scheduler universal-target guide](https://docs.aws.amazon.com/scheduler/latest/UserGuide/managing-targets-universal.html)
  allows an AWS SDK API operation as a target, and the [Terraform Scheduler resource](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/scheduler_schedule)
  supports one-time schedules and automatic deletion after invocation. Candidate
  independent expiry: exact UTC one-time `ec2:TerminateInstances` call, a Scheduler
  role limited to the one instance ARN and project tag, and `action_after_completion =
  "DELETE"`; pair it with a guest systemd shutdown timer and EC2 guest-shutdown-to-
  terminate behavior. AWS lists 14 million Scheduler invocations/month free and
  `$1`/million above that on its [pricing page](https://aws.amazon.com/eventbridge/pricing/);
  reserve a small positive amount rather than counting on account free tier. Test
  failure, retry, and teardown behavior before relying on either mechanism.

  Follow-up from the current AWS [one-time schedule documentation](https://docs.aws.amazon.com/scheduler/latest/UserGuide/schedule-types.html)
  (checked 2026-11-27): an `at(...)` schedule invokes once, but a completed schedule
  still counts against the account's schedule quota until it is deleted. Current
  AWS provider documentation describes `action_after_completion = "DELETE"`, but the
  repository's pinned AWS provider `5.100.0` schema rejected that argument during
  static validation. Therefore this lab keeps the schedule in Terraform state and
  requires normal Terraform destroy after the GPU batch; the read-only verifier must
  tolerate the schedule group already being absent. Do not claim expiry cleanup also
  removes the Scheduler schedule.

These findings refine the proposed cost architecture only; no AWS resources, budget,
VPC, or expiry mechanism have been created or tested. The current provisional
resource/runtime estimate and assumptions are recorded in [`COST_REPORT.md`](COST_REPORT.md).

## Container GPU and monitoring research update (2026-11-26)

- NVIDIA's [Container Toolkit installation guide](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)
  says to install the Linux NVIDIA driver first. Its current Ubuntu apt example
  documents a `1.20.2-1` package set and a signed package repository. It also calls
  out a systemd cgroup issue that can remove GPU access after `systemctl daemon reload`.
  The chosen host/runtime must pin one tested package version and include this failure
  in the runbook. No package was installed during this research.
- Docker's [Compose GPU guide](https://docs.docker.com/compose/how-tos/gpu-support/)
  requires `capabilities: [gpu]` for a service device reservation and supports a
  `count: 1` assignment. `count` and `device_ids` cannot be set together. This is
  device visibility to a container, not physical GPU isolation between tenants. A
  single L4 should be allocated only to the vLLM workload container; other services
  should not receive GPU access.
- NVIDIA's [DCGM Exporter releases](https://github.com/NVIDIA/dcgm-exporter/releases)
  list 4.8.4 as the current release at research time and report tested DCGM 4.6.1
  components. The [exporter release strategy](https://github.com/NVIDIA/dcgm-exporter/blob/main/RELEASE.md)
  distinguishes a versioned full image tag from mutable `latest`. The project should
  pin the complete exporter/image version and digest, inspect the metric field set,
  and run a live scrape before using any metric name or alert in a dashboard. The
  exporter is optional only if the selected single-host driver/DCGM compatibility is
  proven; no Kubernetes installation is implied.
- OpenTelemetry's [semantic-convention guidance](https://opentelemetry.io/docs/specs/semconv/how-to-write-conventions/)
  says sensitive, verbose, expensive, or unstable attributes should be opt-in and
  requirements should be explicit. The GenAI conventions now live in the separate
  [OpenTelemetry GenAI conventions repository](https://github.com/open-telemetry/semantic-conventions-genai);
  the former docs URL redirects to a moved notice. Pin a reviewed repository revision
  or document its schema version. Emit safe model and operation metadata only; never
  attach prompts, completions, bearer tokens, or sensitive tenant labels by default.

These are source-informed design inputs, not a tested container, exporter, metric,
trace, or alert configuration. All package versions and image digests must be checked
again before implementation and the paid run.

## 2026-11-27 — Monitoring, quota-state, model evaluation, and automation research

- [Prometheus overview](https://prometheus.io/docs/introduction/overview/) describes
  timestamped numeric time series with optional labels and a pull-based scrape model.
  It also warns that Prometheus is not an authoritative per-request billing ledger.
  Use it for operational trends; keep usage accounting in the gateway's durable
  request records and reconcile it separately.
- [Grafana dashboard documentation](https://grafana.com/docs/grafana/latest/visualizations/dashboards/build-dashboards/create-dashboard/)
  defines dashboards as panels backed by data-source queries. This supports the
  planned split between source metrics and dashboard views; expressions must be tested
  against actual metric names and labels before claiming a live dashboard.
- OpenTelemetry's [Python instrumentation guide](https://opentelemetry.io/docs/languages/python/instrumentation/)
  explains that an instrumented application uses the API and SDK, while a library
  should depend on the API. Python traces and metrics are stable; logs remain in
  development according to the [language status table](https://opentelemetry.io/docs/languages/).
  Keep existing gateway spans and export to the local Tempo stack; do not assume
  trace propagation into vLLM unless headers and spans are observed end to end.
- Redis's [Lua scripting guide](https://redis.io/docs/latest/interact/programmability/eval-intro/)
  states scripts execute atomically and block other server activity for their run.
  Current admission scripts are short and can preserve atomic reserve/settle semantics,
  but a request-id keyed lease/settlement protocol must keep each script bounded and
  idempotent. Do not use Redis metrics as exact accounting.
- MLflow's [Model Registry guide](https://mlflow.org/docs/latest/ml/model-registry/)
  documents model versioning, lineage, tags, and aliases; its [model registry workflow](https://mlflow.org/docs/latest/ml/model-registry/workflow/)
  says fixed model stages were deprecated in favor of aliases/tags. The repository's
  release-plan controls remain authoritative for protected deployment approval; do
  not confuse a mutable `champion` alias with an immutable approved release plan.
- MLflow's [GenAI evaluation guide](https://mlflow.org/docs/latest/genai/eval-monitor/)
  uses scorers and judges for LLM tasks, while [Promptfoo assertions](https://www.promptfoo.dev/docs/configuration/expected-outputs/)
  include deterministic string and JSON checks. Prefer local deterministic assertions
  for exact facts/schema constraints; treat model-graded quality as subjective,
  version the evaluator and prompts, and do not retain sensitive prompt contents.
- The Qwen 1.5B [model card](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct)
  currently displays Apache-2.0. The page is mutable; before download, fetch the
  license file and model metadata at an immutable commit and record file digests.
  This research does not authorize redistribution of model weights.
- Docker's [Compose GPU support guide](https://docs.docker.com/compose/how-tos/gpu-support/)
  requires GPU capability reservation and allows a count of one. Device visibility
  does not give tenant isolation or partition the L4; only vLLM should receive the
  device in the lab profile.
- Ansible's [playbook guide](https://docs.ansible.com/projects/ansible/latest/playbook_guide/playbooks_intro.html)
  describes desired-state modules as commonly idempotent but warns that not every
  playbook/module is. Run the configuration twice and inspect the second run for
  changes rather than assuming idempotency.
- HashiCorp's [Terraform provider requirements](https://developer.hashicorp.com/terraform/language/providers/requirements),
  [AWS create tutorial](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/aws-create),
  and [saved-plan guide](https://developer.hashicorp.com/terraform/tutorials/cli/plan)
  support pinning provider constraints, committing `.terraform.lock.hcl`, saving one
  reviewed plan, and applying that plan. Saved plans and state may contain sensitive
  values and must stay outside public Git.
- GitHub's [AWS OpenID Connect guide](https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-aws)
  explains short-lived federated tokens and requires trust conditions for repository
  identity. This project will not add cloud deploy to normal pull request workflows;
  any later manual workflow must have an explicit environment gate and narrowly scoped
  role.

These references inform design only. No monitoring stack, model evaluation, AWS
automation, GPU runtime, or model download was executed during this research.

## 2026-11-27 — GPU profiling and instrumentation boundaries

- NVIDIA's [CUDA programming guide](https://docs.nvidia.com/cuda/cuda-programming-guide/)
  separates CPU host code from GPU device kernels and organizes work in thread blocks
  and grids. The planned lab should time host-to-device copies, kernel work, and
  synchronization separately rather than treating one CPU wall-clock interval as GPU
  execution time.
- PyTorch's [profiler guide](https://docs.pytorch.org/docs/stable/profiler.html)
  can record CPU and CUDA activity, operator timing, memory, and traces. It warns that
  shape/stack capture can add overhead and retain tensor references; keep profiling
  captures short and report whether profiling was enabled during each benchmark.
- NVIDIA [Nsight Systems](https://docs.nvidia.com/nsight-systems/UserGuide/) provides
  a timeline across CPU threads, CUDA API calls, copies, and kernels; use it first to
  locate where time is spent. [Nsight Compute](https://docs.nvidia.com/nsight-compute/ProfilingGuide/)
  collects kernel-level metrics but can serialize launches, replay kernels, flush
  caches, or adjust clocks. Its reported duration is not directly comparable to
  ordinary unprofiled end-to-end timings. Keep workload timing and profiler diagnosis
  as separate records.
- NVIDIA's [DCGM feature overview](https://docs.nvidia.com/datacenter/dcgm/latest/user-guide/feature-overview.html)
  documents GPU telemetry and notes that profiling metrics can conflict with Nsight
  tools on supported hardware. Avoid running DCGM hardware-counter profiling and an
  Nsight capture at the same time; test each in a separate short run.
- Grafana's [alerting fundamentals](https://grafana.com/docs/grafana/latest/alerting/fundamentals/)
  describes periodic rule evaluation over data-source queries and multiple alert
  instances by time series. Bound label cardinality and verify rule queries against
  actual scrape data before inducing an alert.
- The active [OpenTelemetry GenAI convention repository](https://github.com/open-telemetry/semantic-conventions-genai)
  is separate from the former `opentelemetry.io` GenAI URL. Its current attribute
  registry warns that input-message and tool content may contain sensitive data.
  Do not attach content attributes by default; retain only metadata needed to trace
  request flow.

No profiler, exporter, alert, or live metric was executed during this source review.
