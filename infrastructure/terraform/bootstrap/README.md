# Flagship Terraform State Bootstrap

This root defines the **first future AWS apply only**: an encrypted/versioned S3
state bucket, DynamoDB state-lock table, required resource tags, and an actual-cost
budget alert for `multi-tenant-ai-inference-platform`. It is intentionally separate
from every other portfolio repository.

It has been statically validated only. Do not run `apply` without a separately
authorized cloud-pilot budget and account owner.

## Safe static validation

```console
terraform init -backend=false
terraform fmt -check
terraform validate
```

## Future, owner-authorized bootstrap flow

The scripts below prepare a private saved plan, require its SHA-256 digest for apply,
and keep Terraform logs and the first local state under `.local/` (ignored by Git).
They do not request an AWS change until the explicit apply command is run. The first
apply creates only these seven shared project resources: the state bucket, its
ownership/public-access/encryption/versioning controls, the lock table, and the
monthly cost alert. Do not use the example tfvars file for a real plan.

From the repository root, authenticate and set the reviewed account and a private
alert address. The `read -s` command hides the address while typing; it is kept only
in this shell environment and is not written to source files:

```bash
export AWS_PROFILE=ai-platform-pilot-key
export AWS_REGION=us-east-1
export EXPECTED_AWS_ACCOUNT_ID=<reviewed-12-digit-account>
read -r -s -p 'Private Budget alert email: ' GPU_EC2_BOOTSTRAP_BUDGET_EMAIL
printf '\n'
export GPU_EC2_BOOTSTRAP_BUDGET_EMAIL
```

Create and review the exact saved plan:

```bash
make gpu-ec2-bootstrap-plan
```

The script verifies the AWS account and that the exact bucket, lock table, and
Budget do not already exist. It creates a private local workspace, plans without
applying, validates that the plan contains exactly the seven reviewed resources,
and prints a SHA-256 digest. Review the printed summary and private plan/log files
locally; never commit them. If the recipient is wrong, stop and prepare a new plan.
AWS may require confirmation of Budget email delivery.

Only after the owner has reviewed the exact plan, confirmed the recipient, and
authorized this bootstrap apply, provide the run ID and digest printed by the plan:

```bash
export GPU_EC2_BOOTSTRAP_RUN_ID=<printed-run-id>
export GPU_EC2_BOOTSTRAP_PLAN_SHA256=<reviewed-64-character-digest>
export GPU_EC2_BOOTSTRAP_CONFIRM=apply
make gpu-ec2-bootstrap-apply
```

The wrapper rechecks identity, resource absence, local state absence, plan digest,
and allowed resource actions before applying that saved plan. If apply fails or its
outcome is uncertain, do not rerun it blindly: inspect the private log and reconcile
AWS resources and Terraform state first.

After success, migrate the exact seven-resource local state to the encrypted,
versioned S3 backend with DynamoDB locking and S3 lockfiles:

```bash
export GPU_EC2_BOOTSTRAP_CONFIRM=migrate
make gpu-ec2-bootstrap-migrate
```

The first local state copy remains in the private `.local/` workspace as a recovery
copy. Protect it and do not commit or remove it until the remote state and retention
requirements have been verified. The migration wrapper verifies bucket encryption,
versioning, lock-table status, account identity, and the exact local resource set
before moving state.

The AWS Budget is an alert, not a hard spending stop. A $25 alert configuration
does not guarantee total project spend stays below $25. Keep GPU runtime and resource
lifetimes bounded, review the exact GPU plan and cost separately, and follow the
project's authorized destroy and cleanup verification process.
