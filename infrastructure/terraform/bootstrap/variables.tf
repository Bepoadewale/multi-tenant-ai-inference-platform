variable "aws_region" {
  type        = string
  default     = "us-east-1"
  description = "Single approved region for the initial pilot."
}

variable "expected_account_id" {
  type        = string
  description = "AWS account allowed to receive this repository's state guardrails."

  validation {
    condition     = can(regex("^[0-9]{12}$", var.expected_account_id))
    error_message = "expected_account_id must be a 12-digit AWS account ID."
  }
}

variable "budget_alert_email" {
  type        = string
  sensitive   = true
  description = "Budget-notification recipient. Supply outside version control."
}

variable "monthly_budget_usd" {
  type        = number
  default     = 10
  description = "Monthly actual-cost alert threshold; an alert is not a hard spend cap."

  validation {
    condition     = var.monthly_budget_usd > 0 && var.monthly_budget_usd <= 25
    error_message = "Initial flagship pilot budget must be greater than zero and no more than USD 25."
  }
}

variable "project" {
  type        = string
  default     = "multi-tenant-ai-inference-platform"
  description = "Project-scoped state and resource prefix."
}

variable "owner" {
  type        = string
  default     = "bepoadewale"
  description = "Required ownership tag for pilot resources."
}
