variable "aws_region" {
  type        = string
  default     = "us-east-1"
  description = "Only the approved initial region."

  validation {
    condition     = var.aws_region == "us-east-1"
    error_message = "The initial L4 lab is restricted to us-east-1."
  }
}

variable "expected_account_id" {
  type        = string
  description = "AWS account permitted to own this isolated GPU environment."

  validation {
    condition     = can(regex("^[0-9]{12}$", var.expected_account_id))
    error_message = "expected_account_id must contain exactly 12 digits."
  }
}

variable "availability_zone" {
  type        = string
  description = "An us-east-1 availability zone where the selected G6 type is offered."

  validation {
    condition     = can(regex("^us-east-1[a-z]$", var.availability_zone))
    error_message = "availability_zone must be an us-east-1 zone name, such as us-east-1a."
  }
}

variable "instance_type" {
  type        = string
  default     = "g6.xlarge"
  description = "One single-L4 instance. Start with g6.xlarge; use g6.2xlarge only after documented evidence."

  validation {
    condition     = var.instance_type == "g6.xlarge"
    error_message = "This first GPU package is limited to one g6.xlarge; any later size change needs measured justification and a new cost review."
  }
}

variable "ubuntu_ami_id" {
  type        = string
  description = "Exact Canonical Ubuntu 24.04 amd64 AMI reviewed for this deployment. Update deliberately with matching evidence."

  validation {
    condition     = can(regex("^ami-[0-9a-f]{8,17}$", var.ubuntu_ami_id))
    error_message = "ubuntu_ami_id must be a valid lowercase EC2 AMI identifier."
  }
}

variable "volume_size_gib" {
  type        = number
  default     = 100
  description = "Encrypted gp3 root disk. Increase only after storage evidence and a new cost review."

  validation {
    condition     = var.volume_size_gib >= 100 && var.volume_size_gib <= 120
    error_message = "The initial disk must be between 100 and 120 GiB."
  }
}

variable "expires_at" {
  type        = string
  description = "Exact UTC expiry as RFC3339 ending in Z; the guest timer and AWS Scheduler both terminate the instance."

  validation {
    condition = (can(regex("^20[0-9]{2}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$", var.expires_at)) &&
      timecmp(var.expires_at, plantimestamp()) > 0 &&
    timecmp(var.expires_at, timeadd(plantimestamp(), "12h")) <= 0)
    error_message = "expires_at must be an exact future UTC RFC3339 timestamp, no more than 12 hours after the Terraform plan starts."
  }
}

variable "project" {
  type        = string
  default     = "multi-tenant-ai-inference-platform"
  description = "Project tag prefix; do not change it for this environment."

  validation {
    condition     = var.project == "multi-tenant-ai-inference-platform"
    error_message = "This root is restricted to the existing multi-tenant AI platform project."
  }
}

variable "owner" {
  type        = string
  default     = "bepoadewale"
  description = "Required resource ownership tag."
}
