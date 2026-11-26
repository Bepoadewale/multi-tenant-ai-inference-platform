# GPU Lab Research Notes

Research was started on 2026-11-26. This is an initial Phase 1 record, not a final compatibility matrix. Recheck sources immediately before implementation because prices, quota, software releases, and model artifacts change.

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
  versioning, supports encryption, and marks DynamoDB-based locking deprecated. This
  project should use the S3 lock file so it does not add a DynamoDB table just for
  Terraform locking. The exact Terraform minimum, backend bootstrap, permissions, and
  lifecycle still need implementation and validation.
- AWS [Session Manager guidance](https://docs.aws.amazon.com/prescriptive-guidance/latest/aws-startup-security-baseline/wkld-06.html)
  says Session Manager has no additional EC2 connection charge; interface VPC
  endpoints do incur hourly and data-processing charges. A public subnet with no
  inbound rules and outbound internet access avoids those endpoints and a NAT
  Gateway, but it still exposes a public IP and must be reviewed as an egress-only
  lab design. Package/model downloads flow out from the instance, so model and image
  pulls must be completed inside a bounded runtime.
- AWS's [S3 pricing page](https://aws.amazon.com/s3/pricing/) describes pay-for-use
  storage and requests and says internet ingress is not charged. It also lists the
  first 100 GB/month of internet egress across eligible AWS services as free; the
  project estimate should not rely on free-tier eligibility or omit any transfer.
  Final S3 state/version/object storage cost and lifecycle must be calculated at the
  real plan stage.
- The AWS [EC2 service-authorization reference](https://docs.aws.amazon.com/service-authorization/latest/reference/list_ec2.html)
  lists `ec2:TerminateInstances` for instance resources with resource-tag condition
  keys. That allows a tightly scoped self-expiry mechanism if needed; a simpler
  design candidate is an instance-boot systemd shutdown timer combined with EC2
  `instance_initiated_shutdown_behavior = "terminate"`, which needs no persistent
  Lambda or broad terminate role. Validate the boot timer, termination behavior,
  restart policy, and teardown independently before relying on it.

These findings refine the proposed cost architecture only; no AWS resources, budget,
VPC, or expiry mechanism have been created or tested.
