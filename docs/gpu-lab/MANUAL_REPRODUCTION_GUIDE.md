# Manual reproduction guide: single NVIDIA L4 inference lab

This guide is the operator's walk-through for rebuilding the lab. It is written so
you can understand each stage and check its result. Commands in this guide have not
all been run on AWS. A command is marked **future GPU execution** when it must wait
for applied quota, a reviewed cost estimate, the exact Terraform plan, and explicit
approval.

The project uses one `g6.xlarge` with one NVIDIA L4, standard Ubuntu 24.04 amd64,
Systems Manager Session Manager, Docker Compose, and a pinned vLLM image. The existing
CPU ONNX service and EKS deployment contract remain separate. The GPU runs one model
at a time; tenant quotas provide logical request controls, not hardware isolation.

## 0. Read the project state first

**Where:** local workstation, repository root.

```bash
git status --short --branch
git log -1 --oneline
gh pr list --state open
```

Read [the persistent goal](../goals/SINGLE_L4_GPU_INFRASTRUCTURE_GOAL.md),
[implementation status](IMPLEMENTATION_STATUS.md), [execution journal](EXECUTION_JOURNAL.md),
[cost report](COST_REPORT.md), [risk register](RISK_REGISTER.md), [host install manifest](GPU_HOST_INSTALL_MANIFEST.md),
and [GPU batch runbook](GPU_BATCH_RUNBOOK.md). The goal document is the source of the
project plan. The pull requests and execution journal establish the newest code and
validation state.

**Why:** quota approval, a successful Terraform plan, and a running service are three
different facts. Confirm current state before continuing, especially after a session
interruption.

**Expected:** the latest code commit and open PR state are visible; the current
infrastructure state is explicitly recorded. Do not infer AWS state from Git history.

**Stop if:** the goal, PRs, Terraform state, and AWS inventory disagree. Reconcile
them before any mutation.

## 1. Prepare the local tools and verify AWS identity

**Where:** local workstation, repository root.

Use Python 3.12 explicitly. The workstation may default to another Python version.
Set the exact variable names consumed by the repository wrappers. Replace the
placeholders locally; do not save the account ID in Git:

```bash
export AWS_PROFILE=ai-platform-pilot-key
export AWS_REGION=us-east-1
export EXPECTED_AWS_ACCOUNT_ID='<12-digit project account ID>'
python3.12 --version
aws --version
terraform version
docker compose version
actual_account="$(aws sts get-caller-identity \
  --query Account --output text)"
test "$actual_account" = "$EXPECTED_AWS_ACCOUNT_ID" \
  && echo 'Expected AWS account confirmed'
unset actual_account
```

Check the applied On-Demand G and VT quota in `us-east-1`:

```bash
AWS_PROFILE=ai-platform-pilot-key aws service-quotas get-service-quota \
  --service-code ec2 --quota-code L-DB2E81BA \
  --region us-east-1 --query Quota.Value --output text
```

The value must be at least 4 vCPUs for one `g6.xlarge`. A request or appeal being
open is not an approved applied quota. Do not submit another request if the existing
appeal is pending. The current recorded value is `0.0` vCPUs, so cloud provisioning
is blocked.

**Why:** this prevents work from reaching the wrong AWS account and checks the
specific capacity quota before planning a paid machine.

**Expected:** account check succeeds, region is `us-east-1`, quota is at least 4, and
AWS credentials remain in the local AWS profile. Never paste credentials into a
shell command, PR, screenshot, or repository file.

**If the SSO profile expired:** use `aws sso login --profile ai-platform-pilot`, then
repeat the identity check. The key profile is used for the required mutation preflight:

```bash
AWS_PROFILE=ai-platform-pilot-key aws sts get-caller-identity
```

Do not display the full output in public evidence; redact the account identifier.

## 2. Review cost, expiry, and the Terraform plan

**Where:** local workstation, repository root.

This section is a checklist, not authorization. The project spending ceiling is
USD $25 total. It includes the GPU instance, public IPv4 address if assigned, 100-GiB
encrypted gp3 disk, state/lock usage, scheduled termination, storage and network use,
tax uncertainty, and a contingency. A budget alert is not a hard cap.

The current environment inventory found no GPU instance or project-tagged GPU
resources. The Terraform state bucket, lock table, and budget alert must exist before
the GPU preflight can pass. This is a separate, small but billable bootstrap. Review
its scope and cost independently and obtain explicit approval before applying it; the
`$25` ceiling is not permission to apply. See the
[bootstrap instructions](../../infrastructure/terraform/bootstrap/README.md). A local
preview is available, but it contains a placeholder alert address and must never be
applied:

```bash
make gpu-ec2-bootstrap-preview-plan
```

For the actual bootstrap, create a private work directory and a variables file outside
the repository. Put the expected account, private budget-alert email, and approved
monthly alert threshold in that file; set its permissions to `0600`. Then initialize
without a remote backend, validate, and create a saved plan. These commands do not
create AWS resources:

```hcl
expected_account_id = "<12-digit project account ID>"
budget_alert_email  = "<private alert recipient>"
monthly_budget_usd  = 10
```

Save those values only in the private variables file. Do not set the real alert email
in a shell command or commit it.

```bash
private_dir="$(mktemp -d)"
chmod 0700 "$private_dir"
export PRIVATE_TFVARS_FILE="$private_dir/bootstrap.tfvars"
export PRIVATE_PLAN_FILE="$private_dir/bootstrap.tfplan"
# Create PRIVATE_TFVARS_FILE with a local editor, then protect it before planning.
chmod 0600 "$PRIVATE_TFVARS_FILE"
terraform -chdir=infrastructure/terraform/bootstrap init -backend=false -input=false
terraform -chdir=infrastructure/terraform/bootstrap fmt -check
terraform -chdir=infrastructure/terraform/bootstrap validate
terraform -chdir=infrastructure/terraform/bootstrap plan -input=false \
  -var-file="$PRIVATE_TFVARS_FILE" -out="$PRIVATE_PLAN_FILE"
terraform -chdir=infrastructure/terraform/bootstrap show "$PRIVATE_PLAN_FILE"
```

Review the exact saved plan, state/lock/budget names, resource count, expiry strategy,
and cost with the owner. Only after that exact plan is authorized may it be applied.
Then deliberately migrate the new local bootstrap state to the encrypted S3 backend:

```bash
terraform -chdir=infrastructure/terraform/bootstrap apply -input=false "$PRIVATE_PLAN_FILE"
terraform -chdir=infrastructure/terraform/bootstrap init -migrate-state -force-copy \
  -input=false \
  -backend-config="bucket=multi-tenant-ai-inference-platform-tfstate-${EXPECTED_AWS_ACCOUNT_ID}" \
  -backend-config='key=bootstrap/terraform.tfstate' \
  -backend-config="region=${AWS_REGION}" \
  -backend-config='dynamodb_table=multi-tenant-ai-inference-platform-pilot-terraform-locks' \
  -backend-config='encrypt=true' \
  -backend-config='use_lockfile=true'
```

Applying the bootstrap is a separately approved billable action; it is not part of
the later GPU-instance apply. Keep the private variables, plan, and state out of
public Git and do not delete the shared backend or budget while the GPU root uses it.

Before the GPU preflight, select an offered Availability Zone and the reviewed
Canonical Ubuntu AMI. Set their exact wrapper inputs and one expiry no more than
12 hours away. Six hours is the planned maximum instance lifetime:

```bash
export GPU_EC2_AZ='<offered us-east-1 zone, for example us-east-1a>'
export GPU_EC2_UBUNTU_AMI_ID='<reviewed Canonical Ubuntu 24.04 amd64 AMI ID>'
export GPU_EC2_EXPIRES_AT="$(python3.12 -c 'from datetime import datetime, timedelta, timezone; print((datetime.now(timezone.utc) + timedelta(hours=6)).strftime("%Y-%m-%dT%H:%M:%SZ"))')"
```

The exact zone and AMI must be refreshed before use. Recreate the expiry and plan if
approval takes long enough for the expiry window to become stale.

```bash
make gpu-ec2-preflight
make gpu-ec2-validate
make gpu-ec2-plan
```

`gpu-ec2-preflight` checks account, region, quota, AMI and instance conditions.
`gpu-ec2-validate` checks the Terraform configuration without creating resources.
`gpu-ec2-plan` prepares a saved plan for review; it must not apply it automatically.
Plans and Terraform state may contain sensitive data. Keep them outside public Git.
The wrapper requires the exported `EXPECTED_AWS_ACCOUNT_ID`, `GPU_EC2_AZ`,
`GPU_EC2_UBUNTU_AMI_ID`, and `GPU_EC2_EXPIRES_AT` values above. The plan prints a
SHA-256 digest; record it privately as `GPU_EC2_PLAN_SHA256` after reviewing the
exact saved plan.

Before proceeding, inspect the exact saved plan and record:

- The expected account, region, and approved `g6.xlarge` type.
- Exactly one GPU instance, one VPC/subnet/network path, scoped IAM, encrypted gp3,
  IMDSv2, and no public inbound rule.
- The resource count and exact resources to create.
- The current line-item cost estimate, tax/reserve, maximum runtime, and spending cap.
- The plan SHA-256, six-hour expiry, separate scheduled termination, and guest timer.
- The project-only Terraform destroy plan and independent absence verifier.

**Future GPU execution — requires explicit approval:**

```bash
export GPU_EC2_PLAN_SHA256='<reviewed saved-plan SHA-256>'
GPU_EC2_CONFIRM=apply make gpu-ec2-apply
```

The apply wrapper must verify the saved plan digest and AWS account before Terraform
can change resources. Do not use plain `terraform apply`, do not regenerate an
uncertain plan, and do not run two Terraform mutations against one state at once.

**Expected:** one approved host and only the reviewed support resources are proposed.
The plan's estimated total remains below $25 with a reasonable reserve.

**Stop if:** quota is below 4, price has changed, any resource is unexpected, expiry is
missing, or the total cannot fit under the ceiling. Do non-billable work while blocked.

**Undo:** after an authorized session, run only the project-scoped destroy wrapper
against the reviewed GPU Terraform root. Independently verify absence. Do not remove
the shared state bucket/table or resources owned by another project.

## 3. Connect to the EC2 host without opening SSH

**Where:** local workstation.

Get the instance ID from the reviewed Terraform output or the project-scoped AWS
inventory. Never select an instance by guesswork.

```bash
AWS_PROFILE=ai-platform-pilot-key aws ssm start-session \
  --target '<approved-instance-id>' --region us-east-1
```

The Systems Manager agent must show Online. The instance role grants only the
permissions needed for Systems Manager. No SSH key or inbound port is needed.

**Where:** EC2 host through Session Manager.

```bash
sudo -s
id -u
pwd
```

`id -u` must print `0`. The steps below use this root shell because Docker's Unix
socket gives root-level host control. Do not add the operator to the `docker` group
as a shortcut.

### Prepare the reviewed source tree

**Where:** EC2 host through Session Manager.

Use the exact reviewed repository commit recorded for the deployment. A commit SHA
is immutable; do not deploy a moving branch name such as `main`:

Replace `<reviewed-commit-sha>` with the full 40-character commit chosen during PR
review. Angle-bracket values in this guide are placeholders, not literal shell syntax.

```bash
cd /opt
git clone https://github.com/Bepoadewale/multi-tenant-ai-inference-platform.git
cd multi-tenant-ai-inference-platform
git checkout '<reviewed-commit-sha>'
git status --short --branch
git rev-parse HEAD
python3.12 -m venv .venv
.venv/bin/pip install --require-hashes -r requirements-container.lock
```

Verify that `git rev-parse HEAD` equals the approved deployment commit and that the
worktree is clean. This hash-locked environment supplies the identity-generation and
operator scripts. The Docker images independently install the same pinned container
dependencies. Do this before GPU workloads so dependency preparation does not use
the approved inference batch.

**Undo:** stop using this checkout after teardown; it is on the instance's encrypted
ephemeral project disk. Do not remove unrelated paths under `/opt`.

**Check the host:**

```bash
cat /etc/os-release
uname -a
lscpu
free -h
lsblk
lspci -nn | grep -i -E 'nvidia|3d controller|vga'
systemctl status amazon-ssm-agent --no-pager || \
  systemctl status snap.amazon-ssm-agent.amazon-ssm-agent --no-pager
systemctl list-timers gpu-lab-expiry.timer
```

The `lspci` program may be missing on a minimal AMI. If so, install only the
`pciutils` diagnostic package, then rerun the hardware listing. Do not continue unless
the OS is Ubuntu 24.04 amd64 and one L4 device is exposed.

**Common failures:** SSM Offline means check instance role permissions, the agent,
DNS, and outbound HTTPS. Missing GPU in `lspci` means the instance type or hardware
exposure is wrong; stop rather than installing a driver. A missing timer means the
expiry safeguard did not configure; stop and fix it before GPU setup.

## 4. Install the NVIDIA driver manually

This is a learning step. Perform it manually before using the Ansible role. The
version candidates below were researched on 2026-11-27; recheck the current NVIDIA
package metadata, signatures, kernel headers, and compatibility immediately before
the approved batch.

**Where:** EC2 host through Session Manager, root shell.

First identify the running kernel and install matching headers and package tools:

```bash
uname -r
apt-get update
apt-get install -y "linux-headers-$(uname -r)" build-essential dkms \
  ca-certificates curl gnupg pciutils python3-debian python3.12-venv
```

The kernel headers must match `uname -r`; the NVIDIA kernel module is built for that
kernel. Stop if the matching headers are unavailable.

Download and check the reviewed CUDA repository keyring package. The hash must be
rechecked from the official package index before use:

```bash
keyring=/var/tmp/cuda-keyring_1.1-1_all.deb
curl -fL \
  https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2404/x86_64/cuda-keyring_1.1-1_all.deb \
  -o "$keyring"
echo 'd2a6b11c096396d868758b86dab1823b25e14d70333f1dfa74da5ddaf6a06dba  '"$keyring" \
  | sha256sum -c -
dpkg -i "$keyring"
apt-get update
```

`dpkg` installs the repository's signing key configuration. `apt-get update` then
checks the repository metadata signature. A checksum mismatch or APT signature
warning is a stop condition.

Pin and install the headless compute driver and CUDA compiler toolkit:

```bash
apt-get install -y \
  nvidia-driver-pinning-580.196.11=580.196.11-1ubuntu1 \
  nvidia-headless-580=580.196.11-1ubuntu1 \
  nvidia-utils-580=580.196.11-1ubuntu1 \
  cuda-toolkit-13-0=13.0.3-1
```

The pin package selects the driver branch; the headless package avoids a desktop
stack; `nvidia-utils` provides tools such as `nvidia-smi`; the Toolkit supplies
`nvcc`. They are separate components. The driver is required for GPU access. The
host Toolkit is for compiling CUDA examples and is not needed merely to run the
vLLM image, which contains its own CUDA user-space libraries.

Do not install a CUDA meta-package that silently upgrades the driver. Do not use the
NVIDIA `.run` installer over APT-managed packages.

**Reboot:** the kernel module must load against the running kernel. Use the approved
Systems Manager reboot path, reconnect, and verify:

```bash
uname -a
lsmod | grep '^nvidia'
nvidia-smi
nvidia-smi -L
nvidia-smi -q
nvidia-smi topo -m
nvcc --version
```

`nvidia-smi` should show one NVIDIA L4 and a healthy driver. `nvcc --version` shows
the installed Toolkit compiler. Its CUDA version can differ from the version printed
by `nvidia-smi`: the latter describes the driver API capability, not the Toolkit on
disk.

**If it fails:** inspect `journalctl -k -b | grep -i nvidia`, `dkms status`,
`dpkg -l 'nvidia*'`, `/var/log/apt/term.log`, and the headers path. Do not change
driver branches until the exact package and kernel state is understood.

## 5. Install Docker and the NVIDIA Container Toolkit manually

The NVIDIA Container Toolkit passes GPU device nodes and driver libraries from the
host into containers. It does not install the host driver and does not create GPU
isolation.

**Where:** EC2 host, root shell. Refresh the signing-key checksums and APT package
versions before execution.

```bash
install -m 0755 -d /etc/apt/keyrings
curl -fL https://download.docker.com/linux/ubuntu/gpg \
  -o /var/tmp/docker-archive-key.asc
echo '1500c1f56fa9e26b9b8f42452a553675796ade0807cdce11975eb98170b3a570  /var/tmp/docker-archive-key.asc' \
  | sha256sum -c -
gpg --dearmor --yes -o /etc/apt/keyrings/docker.gpg \
  /var/tmp/docker-archive-key.asc
chmod 0644 /etc/apt/keyrings/docker.gpg
echo 'deb [arch=amd64 signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu noble stable' \
  > /etc/apt/sources.list.d/docker.list
```

Add NVIDIA's Container Toolkit repository with its separately verified key:

```bash
curl -fL https://nvidia.github.io/libnvidia-container/gpgkey \
  -o /var/tmp/nvidia-container-repo.asc
echo 'c880576d6cf75a48e5027a871bac70fd0421ab07d2b55f30877b21f1c87959c9  /var/tmp/nvidia-container-repo.asc' \
  | sha256sum -c -
gpg --dearmor --yes -o /etc/apt/keyrings/nvidia-container-toolkit.gpg \
  /var/tmp/nvidia-container-repo.asc
chmod 0644 /etc/apt/keyrings/nvidia-container-toolkit.gpg
echo 'deb [arch=amd64 signed-by=/etc/apt/keyrings/nvidia-container-toolkit.gpg] https://nvidia.github.io/libnvidia-container/stable/deb/amd64 /' \
  > /etc/apt/sources.list.d/nvidia-container-toolkit.list
apt-get update
```

Install the reviewed exact package set. Versions shown here are candidates that must
be refreshed immediately before the GPU batch:

```bash
apt-get install -y \
  docker-ce=5:29.9.3-1~ubuntu.24.04~noble \
  docker-ce-cli=5:29.9.3-1~ubuntu.24.04~noble \
  containerd.io=2.4.2-4~ubuntu.24.04~noble \
  docker-buildx-plugin=0.39.1-1~ubuntu.24.04~noble \
  docker-compose-plugin=5.8.0-1~ubuntu.24.04~noble \
  nvidia-container-toolkit=1.20.2-1 \
  nvidia-container-toolkit-base=1.20.2-1 \
  libnvidia-container-tools=1.20.2-1 \
  libnvidia-container1=1.20.2-1
nvidia-ctk runtime configure --runtime=docker
systemctl restart docker
systemctl enable docker
docker version
docker compose version
docker info
```

Use the vendor repository signatures through APT, and stop if the exact packages are
unavailable or a repository is unauthenticated. Do not pipe an unreviewed script into
a root shell.

## 6. Prove GPU access from a container

The immutable AMD64 digest below was read from the official NVIDIA CUDA image index
on 2026-11-27. Recheck it and the image publisher before pulling. This inspection did
not download image layers.

```bash
docker run --rm --gpus all \
  --entrypoint nvidia-smi \
  nvidia/cuda:13.0.2-base-ubuntu24.04@sha256:605fb0c8acf8674e164d822da8a8521f3a655056e569f0899e72ae940e1fe7dc
```

Expected output names one NVIDIA L4. This proves the container runtime can see the
GPU; it does not prove PyTorch or vLLM works. Check host and container output, and
record the digest and command.

**If the container reports no GPU:** verify host `nvidia-smi`, `docker info`,
`nvidia-ctk runtime list`, `/etc/docker/daemon.json`, Docker logs, and the
NVIDIA Container Toolkit package versions. Do not try an unpinned image or open a
public port as a workaround.

## 7. Install and run standalone PyTorch

This Python environment is for CUDA learning only. vLLM has its own pinned PyTorch
and CUDA stack inside its image; do not install this wheel into that image.

**Where:** EC2 host, root shell. Confirm free disk first.

```bash
df -h /
python3.12 -m venv /opt/gpu-lab/torch-venv
/opt/gpu-lab/torch-venv/bin/python -m pip install \
  --require-hashes \
  --index-url https://download.pytorch.org/whl/cu130 \
  --extra-index-url https://pypi.org/simple \
  -r benchmarks/cuda_performance/requirements-torch.lock
```

Run the synchronized matrix experiment:

```bash
/opt/gpu-lab/torch-venv/bin/python \
  benchmarks/cuda_performance/torch_matmul.py --dry-run
```

`--dry-run` prints the workload plan and performs no GPU operation. To execute the
bounded experiment, first review its timing and output-path options in the
[CUDA lab guide](../../benchmarks/cuda_performance/README.md), then run:

```bash
/opt/gpu-lab/torch-venv/bin/python \
  benchmarks/cuda_performance/torch_matmul.py \
  --sizes 256 512 1024 --warmups 3 --repeats 10 \
  --output /var/tmp/gpu-lab/cuda-performance/matmul.json
```

It performs warmups, synchronizes CUDA before timing, repeats measurements, and
checks numerical output. Do not time an asynchronous GPU call only with CPU wall time.

**Expected:** `torch.cuda.is_available()` is true, exactly one device is named
`NVIDIA L4`, a matrix is allocated and multiplied, `torch.cuda.synchronize()` returns,
and the result matches the expected value. Observe GPU activity during the workload.

**If it fails:** print `torch.__version__`, `torch.version.cuda`,
`torch.cuda.is_available()`, `torch.cuda.device_count()`, device name, and allocated
memory. Compare them with `nvidia-smi`, driver output, and the locked requirements.
Do not interpret CPU fallback as success.

## 8. Serve the Qwen model manually with vLLM

The first model is `Qwen/Qwen2.5-1.5B-Instruct` at revision
`989aa7980e4cf806f80c7fef2b1adb7bc71aa306`. The recorded model-card license is
Apache-2.0; verify the immutable revision's license, artifact sizes, and file hashes
again before download. Model weights are several gigabytes and count against disk,
network, and the time budget. Download no 7B model during the first batch.

The recorded official AMD64 vLLM image digest is
`sha256:cf5b2fdd087eb4f6d261736967cc5cde974bd22ff4df50365f8fa419b6b4c484` for
`vllm/vllm-openai:v0.34.0`. Recheck the current image release, image digest,
supported L4 architecture, bundled CUDA/PyTorch versions, and Hugging Face library
version before use.

**Where:** EC2 host, root shell. Start with a short context and two sequences. The
model server binds to host loopback only:

```bash
docker volume create multi-tenant-ai-inference-platform-gpu-model-cache
docker run --name vllm-manual --gpus all --ipc=host \
  -p 127.0.0.1:8000:8000 \
  -v multi-tenant-ai-inference-platform-gpu-model-cache:/root/.cache/huggingface \
  vllm/vllm-openai@sha256:cf5b2fdd087eb4f6d261736967cc5cde974bd22ff4df50365f8fa419b6b4c484 \
  --model Qwen/Qwen2.5-1.5B-Instruct \
  --revision 989aa7980e4cf806f80c7fef2b1adb7bc71aa306 \
  --served-model-name gpu-default \
  --dtype bfloat16 --max-model-len 8192 --max-num-seqs 2
```

The command is foregrounded so logs remain visible. The named cache volume is the same
volume used by the later Compose profile, so the model is not downloaded twice. It
downloads only the pinned model; use the repository's full-snapshot digest command
after vLLM has populated the cache. Do not delete this cache before Compose starts. If
model download requires a token, do not put it in shell history; use the approved
secret-input mechanism.

**Where:** another EC2 shell (or a local SSM port forward). Check readiness and model
metadata before sending a prompt:

```bash
curl --fail --silent http://127.0.0.1:8000/health
curl --fail --silent http://127.0.0.1:8000/v1/models
```

For a short non-sensitive response, send:

```bash
curl --fail --silent http://127.0.0.1:8000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"gpu-default","messages":[{"role":"user","content":"Reply with OK."}],"max_tokens":8}'
```

For streaming, add `--no-buffer` and set `"stream":true` in the JSON body. The
server returns a sequence of `data:` records ending in `[DONE]`.

Send a short non-sensitive request and a streaming request using the documented
OpenAI-compatible API. Never put confidential prompts or responses in evidence. The
response should identify the requested served model and return generated text. Check
`nvidia-smi` before, during, and after the request to correlate GPU memory/utilization
with actual inference.

**Where:** EC2 host through a second Session Manager shell, after saving the manual
server's required logs and measurements. The manual container currently owns port
8000 and the L4. Stop and remove that container before the Compose deployment starts;
the named model-cache volume remains in place:

```bash
mkdir -p /var/tmp/gpu-lab/evidence
docker logs --timestamps vllm-manual \
  > /var/tmp/gpu-lab/evidence/vllm-manual.log 2>&1
docker stop vllm-manual
docker rm vllm-manual
test -z "$(docker ps -q --filter 'publish=8000')"
if ss -ltnH 'sport = :8000' | grep -q .; then
  echo 'Port 8000 is still in use; do not start Compose.' >&2
  exit 1
fi
nvidia-smi
docker volume inspect multi-tenant-ai-inference-platform-gpu-model-cache
```

Review and sanitize the saved log before exporting it. A stopped container releases
its GPU allocation and port; removing this container does not remove the named model
cache volume. Do not start the Compose model service until the port check passes.

**Common failures:** a model revision/hash mismatch means stop; a CUDA kernel error
means check driver, image CUDA, precision support, and GPU architecture; out-of-memory
means lower context or concurrency rather than adding a second model; no `/health`
means inspect container logs and `nvidia-smi`. Restore or terminate the service before
reconfiguring.

## 9. Deploy the existing gateway and observability stack

Only after manual vLLM works, use the prepared GPU Compose profile. The profile
includes two gateway containers, Redis, MLflow for private evaluation metadata,
Prometheus, Grafana, Alertmanager, OpenTelemetry Collector, Tempo, Node Exporter,
DCGM Exporter, and vLLM. It binds operator services to loopback and has no public
inbound ports.

**Where:** EC2 host, root shell, repository root.

```bash
cp deployments/single-gpu/.env.example deployments/single-gpu/.env
chmod 0600 deployments/single-gpu/.env
```

The digest command produces a value over every file in the cached model snapshot.
Save it in a shell variable and set it with the exact source commit in the private
`.env` file.
Create a random Grafana password without displaying it, then use this short Python
snippet to update only the three values. It does not print the password:

```bash
export MODEL_DIGEST="$(.venv/bin/python scripts/gpu_release_controller.py model-digest \
  Qwen/Qwen2.5-1.5B-Instruct 989aa7980e4cf806f80c7fef2b1adb7bc71aa306)"
export SOURCE_COMMIT="$(git rev-parse HEAD)"
export GRAFANA_ADMIN_PASSWORD="$(openssl rand -hex 32)"
python3 - <<'PY'
import os
from pathlib import Path

path = Path("deployments/single-gpu/.env")
values = {
    "GPU_MODEL_ARTIFACT_SHA256": os.environ["MODEL_DIGEST"],
    "GPU_SOURCE_COMMIT": os.environ["SOURCE_COMMIT"],
    "GRAFANA_ADMIN_PASSWORD": os.environ["GRAFANA_ADMIN_PASSWORD"],
}
lines = path.read_text().splitlines()
for key, value in values.items():
    if not value or "\n" in value or "\r" in value:
        raise SystemExit(f"invalid value for {key}")
    lines = [f"{key}={value}" if line.startswith(f"{key}=") else line for line in lines]
path.write_text("\n".join(lines) + "\n")
path.chmod(0o600)
PY
unset MODEL_DIGEST SOURCE_COMMIT GRAFANA_ADMIN_PASSWORD
```

Before startup, confirm the `.env` contains no `replace-` placeholders without
printing the password or full file:

```bash
if grep -q 'replace-' deployments/single-gpu/.env; then
  echo 'Replace all required placeholders before continuing' >&2
  exit 1
fi
make gpu-compose-config
make gpu-observability-validate
```

Edit only reviewed, non-secret values. Place tokens in a secret source approved for
the lab; never commit `.env`. Before startup, compare every image digest, port, volume,
profile, health check, and GPU device count with the reviewed configuration.

Before starting Compose, generate the lab's signed tenant identities so the gateway's
read-only public-key bind mount already exists. The tokens and private signing key
are sensitive, even though this is a disposable lab. Keep them on the EC2 host,
restrict file permissions, and never include their contents in command output or
evidence:

```bash
umask 077
.venv/bin/python scripts/generate_local_identity.py
stat -c '%a %n' .local/identity/private.pem .local/identity/tokens.json
test "$(stat -c '%a' .local/identity/private.pem)" = 600
test "$(stat -c '%a' .local/identity/tokens.json)" = 600
```

The script creates the signing key and public verification key locally on the host;
the GPU gateways mount only `public.pem`. In the preserved local CPU Compose stack,
the two simulated edge agents also read their device tokens from this directory.
Compose runs those two services with the `LOCAL_UID` and `LOCAL_GID` exported by
`bootstrap-local`, so they can read the owner-only file without making tokens
world-readable. The private key and short-lived tokens never need to be copied into a
container image.

**Future GPU execution — after manual vLLM validation, `.env` review, and identity
generation:**

```bash
docker compose --env-file deployments/single-gpu/.env \
  -f deployments/single-gpu/compose.yaml up -d
docker compose --env-file deployments/single-gpu/.env \
  -f deployments/single-gpu/compose.yaml ps
```

The three added lab identities are `customer-support`, `internal-engineering`, and
`research`. Each can call `chat-default`; their allowed model sets and quota limits
differ. For example, customer support cannot use `embeddings`, while engineering
can. These are application checks and shared Redis counters. All tenants still share
the same physical L4.

Make one bounded request through each gateway replica using the same signed
customer-support token. The shell reads the token directly from the protected file;
do not echo it. Use a short synthetic prompt and a small output limit:

```bash
support_token="$(jq -r '.customer_support' .local/identity/tokens.json)"
for port in 8081 8082; do
  curl --silent --show-error --fail-with-body --max-time 120 \
    "http://127.0.0.1:${port}/v1/chat/completions" \
    -H "Authorization: Bearer ${support_token}" \
    -H 'Content-Type: application/json' \
    -d '{"model":"chat-default","messages":[{"role":"user","content":"Reply with the word ready."}],"max_tokens":8}' \
    | jq '{model, usage, finish_reason: .choices[0].finish_reason}'
done
unset support_token
```

Then prove model authorization is enforced. Customer support is not allowed to call
`embeddings`; expect HTTP 403. The request is rejected by the gateway before model
execution:

```bash
support_token="$(jq -r '.customer_support' .local/identity/tokens.json)"
status="$(curl --silent --show-error --max-time 10 -o /tmp/gpu-tenant-denied.json \
  -w '%{http_code}' http://127.0.0.1:8081/v1/chat/completions \
  -H "Authorization: Bearer ${support_token}" \
  -H 'Content-Type: application/json' \
  -d '{"model":"embeddings","messages":[{"role":"user","content":"denied test"}],"max_tokens":1}')"
test "$status" = 403
unset support_token
```

The 403 proves model authorization, not separate GPU capacity. To test quota sharing,
use the existing bounded GPU overload drill after confirming its request count and
runtime fit the approved batch. Do not run unbounded loops.

**Where:** local workstation, repository root, before provisioning AWS resources.
Do not run this CPU-only exercise on the paid EC2 host: it needs no GPU, model
download, or AWS access, so completing it locally keeps the GPU window for hardware
work.

**Purpose and prerequisites:** exercise shared admission behavior and Redis failure
recovery in the existing CPU ONNX stack. Start the project's local services with
`make bootstrap-local` and confirm `make smoke` passes first. These drills stop and
restart only this project's Redis container; they preserve its named data volume.

Run:

```bash
make demo-gateway-cancellation
make demo-redis-outage
```

The first cancels ten streaming requests across both local gateways and checks that
each process's active-request gauge and Redis's shared active-lease count return to
zero. The second stops only the project's Redis container, expects both gateways to
reject requests with HTTP 503, then restarts Redis and checks both gateways become
ready again. The outage script has an exit trap that starts Redis if an assertion or
command fails; it preserves the named Redis volume.

**Expected:** the cancellation command reports ten cancelled streams with no active
leases left. During the outage, both gateways return HTTP 503; after Redis restarts,
both readiness checks pass. These checks validate the local gateway and shared-state
path only. They do not validate vLLM, GPU behavior, or production recovery.

**If Redis does not recover:** run `docker compose -f docker-compose.yml start redis`
and check `docker compose ps redis` and `docker compose logs --tail=100 redis`. The
drill's exit trap attempts this recovery automatically. Do not delete the volume or
run global Docker cleanup. When finished with the local exercise, stop the project
through the repository's project-scoped local cleanup instructions; do not run those
cleanup commands against AWS or unrelated Docker projects.

Then verify:

- Both gateway replicas are ready and can reach the vLLM service over the internal
  Compose network.
- Authenticated tenants can infer only from models they are authorized to use.
- Tenant limits and concurrency are shared through Redis across both replicas.
- Invalid identities, tenant-header spoofing, unauthorized models, exhausted quota,
  saturation, timeout, and cancellation behave as expected.
- Prometheus targets are up; Grafana dashboards show live GPU and vLLM data; a
  request can be followed through available gateway traces.
- Logs, traces, metrics, MLflow records, and screenshots omit prompts, outputs,
  authorization tokens, account IDs, and sensitive endpoints.

Use `make gpu-benchmark-plan` and `make gpu-evaluation-plan` before real workloads.
These commands are safe dry runs. Real benchmarks use the bounded workload runner,
aggregate-only result files, explicit duration, and project metadata. Real evaluation
uses the versioned synthetic suite. Do not make performance or quality claims from
dry-run output.

### Use the guarded host-operation wrappers after the manual lesson

The commands below automate repeated host work only after the matching manual steps
above have been understood and verified. They have not run on an EC2 host. They fail
closed unless the host's Instance Metadata Service v2 identity matches the expected
AWS account, exact GPU instance ID, `us-east-1`, and one `g6.xlarge` with one visible
L4. Get the exact instance ID from the reviewed Terraform output and keep it in the
Session Manager shell only; do not add it to public evidence. These commands run in
the EC2 host's **root shell** from the repository root. They do not provision AWS.

Set the two identity checks in that shell, using the account value from the approved
deployment record and the exact instance ID:

```bash
export EXPECTED_AWS_ACCOUNT_ID='<approved AWS account ID>'
export GPU_EC2_INSTANCE_ID='<exact project g6.xlarge instance ID>'
```

First repeat the host configuration. Before applying it, review Ansible check mode as
described in [the Ansible guide](../../infrastructure/ansible/README.md). The pinned
Ansible environment must exist at `infrastructure/ansible/.venv`:

```bash
GPU_EC2_CONFIGURE_CONFIRM=apply make gpu-ec2-configure
```

The command can run for at most 90 minutes. It uses the local Ansible playbook and
does not reboot automatically. If the NVIDIA driver changed, follow the manual SSM
reboot procedure, reconnect, and rerun it. Save both real Ansible summaries privately
so the second run's `changed=0` can be checked.

The earlier manual Compose start is the first deployment. To build and deploy the
reviewed profile again, the root shell must have a reviewed `.env` with exact mode
`0600`, the owner-only tenant identity file, a verified 64-character model artifact
SHA-256, the current checkout's exact 40-character source commit, and a unique Grafana
password at least 32 characters long:

```bash
GPU_EC2_DEPLOY_CONFIRM=deploy make gpu-ec2-deploy
```

The preflight rejects symlinks, duplicate keys, placeholders, invalid or stale
provenance, and weak passwords without printing values. This gives the Compose
image build/start operation a 45-minute limit, then waits for
vLLM and both gateways for at most 20 minutes. If build/start fails or readiness does
not arrive, it stops vLLM and both gateways and exits with failure. The script does
not print `.env`, model responses,
or identity tokens; it reads no more than 256 KiB from any response. A failed start still needs operator inspection and the planned
Terraform expiry remains the final protection against an abandoned instance.

Run the short synthetic authenticated check only after readiness. It exercises the
three named tenants, header-spoof resistance, invalid identity, model denial, and a
small streamed response through both gateway replicas. It issues four short model
requests, reads at most 256 KiB per response, and reports only statuses and token
counts:

```bash
GPU_EC2_SMOKE_CONFIRM=run make gpu-ec2-smoke
```

Collect a private host snapshot outside the checkout. The tool refuses to write
under the public repository and creates a new mode-`0700` directory with a mode-`0600`
JSON file. It records versions, one-line GPU status, service states, readiness codes,
and source commit; it does not collect logs, prompts, completions, or tokens:

```bash
make gpu-ec2-evidence
```

The optional scripts have separate confirmations and limits. Evaluation is limited
to 20 minutes. The direct vLLM benchmark defaults to 60 minutes and may be set from
1 to 120 minutes; the authenticated gateway benchmark then runs its fixed 18-request
synthetic workload. Results are written to the reviewed private output locations.
The Redis drill first checks current readiness, stops only the Compose Redis service,
requires both gateways to return HTTP 503, restarts Redis in an exit trap, and checks
both gateways recover. It does not destroy volumes or other Docker resources:

```bash
GPU_EC2_EVALUATE_CONFIRM=run make gpu-ec2-evaluate
GPU_EC2_BENCHMARK_CONFIRM=run GPU_EC2_BENCHMARK_MAX_MINUTES=60 make gpu-ec2-benchmark
GPU_EC2_INCIDENT_CONFIRM=redis-outage make gpu-ec2-incident-drills
```

The confirmation values prevent accidental invocation; they are not substitutes for
the separate cost, quota, and exact-plan authorization gates. Run benchmarks and
incident drills only within the approved instance window. Save their raw outputs
privately and add only reviewed, sanitized summaries to Git. Teardown remains a
separate, locally reviewed Terraform operation from the workstation, after evidence
export; never use Docker-wide cleanup.

## 10. Re-run the host configuration with Ansible

Finish the manual installation and initial GPU validation before this section. The
Ansible role is prepared at `infrastructure/ansible/`; its Python dependencies are
hash-locked. It runs locally on the EC2 host through Session Manager, not on the Mac.

```bash
cd infrastructure/ansible
python3 -m venv .venv
.venv/bin/python -m pip install --require-hashes -r requirements.lock
ANSIBLE_CONFIG=ansible.cfg .venv/bin/ansible-playbook \
  playbooks/configure-gpu-host.yml --syntax-check
ANSIBLE_CONFIG=ansible.cfg .venv/bin/ansible-playbook \
  playbooks/configure-gpu-host.yml --check --diff
```

Read the complete diff. The playbook pins versions and repository keys, installs the
hash-locked PyTorch environment, configures Docker GPU support, and runs a small
synchronized matrix check. It does not reboot automatically. If the driver changed,
use SSM to reboot, reconnect, and rerun the playbook. The second actual run should
report no package/configuration changes; retain both outputs. A syntax check or
check-mode run is not proof of idempotency.

**Expected:** one L4, working `nvidia-smi`, `nvcc`, Docker NVIDIA runtime, successful
PyTorch matrix check, and `changed=0` on the second run.

**Undo:** use the documented project Terraform teardown after exporting evidence.
Do not globally remove Docker images or volumes; do not delete another project's
resources.

## 11. Reproduce and troubleshoot one controlled failure

Choose only a staged, reversible incident from
[the GPU batch runbook](GPU_BATCH_RUNBOOK.md). Examples include a bounded tenant
quota rejection, vLLM readiness failure, Redis failure, invalid model config, or a
limited GPU memory test. Avoid host-level driver removal, unrestricted stress, disk
filling, or network exposure.

For each incident, record the planned fault, preconditions, exact start/end time,
affected service, expected signal, observed logs and metrics, diagnosis, recovery, and
independent success check. Clearly label it a controlled laboratory incident, not a
production incident. Never fabricate an alert or error to make the report look
complete.

## 12. Export evidence and tear down

Before stopping the GPU, export sanitized command output, benchmark aggregates,
evaluation summaries, dashboards, alerts, traces, release/rollback records, and
screenshots to the approved evidence location. Update the evidence manifest with
commit, PR, time, GPU/driver/runtime/model metadata, and exactly what each file proves.
Keep raw Terraform plans/state, secrets, model weights, prompts, response text, and
credential-bearing logs out of public Git.

**Where:** EC2 host, root shell, repository root. Stop only the project Compose
profile. This preserves named volumes long enough to finish the evidence export. Then
leave the Session Manager shell; Terraform administration is performed from the
authorized local workstation, where the AWS profile, Terraform backend, plan files,
and destroy guards are configured:

```bash
docker compose --env-file deployments/single-gpu/.env \
  -f deployments/single-gpu/compose.yaml down
exit
```

**Where:** authorized local workstation, repository root. Restore the expected
account, AWS profile, region, Availability Zone, and exact AMI ID from the deployment
record. The destroy wrapper requires those inputs to reconstruct and inspect the
project-scoped plan:

```bash
export AWS_PROFILE=ai-platform-pilot-key
export AWS_REGION=us-east-1
export EXPECTED_AWS_ACCOUNT_ID='<12-digit project account ID>'
export GPU_EC2_AZ='<Availability Zone recorded at apply>'
export GPU_EC2_UBUNTU_AMI_ID='<Canonical Ubuntu AMI recorded at apply>'
make gpu-ec2-destroy-plan
```

Review that plan and the printed SHA-256 digest. Only after the exact project-only
destroy plan is authorized, set its digest and confirmation literal, then run the
destroy and independent absence verifier:

```bash
export GPU_EC2_DESTROY_PLAN_SHA256='<reviewed destroy-plan SHA-256>'
GPU_EC2_CONFIRM=destroy make gpu-ec2-destroy-apply
make gpu-ec2-verify-clean
```

Review the exact destroy plan before applying it. The independent verifier must check
the one instance, its volume, network interfaces, security group, subnet, route table,
internet gateway, VPC, scoped role/profile, expiry schedule, and any project logs or
addresses. A termination request is not proof of absence. Never delete shared state
or other project resources. Record estimated and settled billing separately; billing
may settle later.

## 13. What success means

The lab is reproducible only after the authorized AWS/GPU steps have actually run and
supporting evidence exists for the L4, driver, CUDA computation, container GPU access,
PyTorch, vLLM inference, tenant enforcement, observability, performance, evaluation,
release/rollback, recovery, and teardown. Static Terraform validation, Ansible syntax,
local CPU tests, metadata lookups, or a running container do not prove those results.

For concept explanations and troubleshooting examples, read the
[GPU batch runbook](GPU_BATCH_RUNBOOK.md) and [research notes](RESEARCH_NOTES.md).
