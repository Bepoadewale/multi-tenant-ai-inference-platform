output "state_bucket" {
  value       = aws_s3_bucket.terraform_state.bucket
  description = "Encrypted/versioned Terraform state bucket for this repository only."
}

output "lock_table" {
  value       = aws_dynamodb_table.terraform_locks.name
  description = "DynamoDB table used to lock this repository's Terraform state."
}

output "monthly_budget_name" {
  value       = aws_budgets_budget.monthly_pilot.name
  description = "Actual-cost alert budget; it is not an automatic spend stop."
}
