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

1. Copy `terraform.tfvars.example` outside source control and fill in the expected
   account and private budget-alert address.
2. Authenticate through a short-lived local profile; do not export long-lived keys.
3. Review a non-applying plan and the exact bucket/table/budget names.
4. Apply with `-backend=false` once approved.
5. Re-run init with the created S3 backend and DynamoDB lock configuration, migrating
   the bootstrap state deliberately.

The budget is an alert, not a guaranteed stop. The project must still use tagged,
time-boxed resources and an explicit Terraform destroy plan.
