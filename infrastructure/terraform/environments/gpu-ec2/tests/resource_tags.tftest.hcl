mock_provider "aws" {
  mock_data "aws_caller_identity" {
    defaults = {
      account_id = "123456789012"
    }
  }

  mock_data "aws_ec2_instance_type_offerings" {
    defaults = {
      instance_types = ["g6.xlarge"]
    }
  }

  mock_resource "aws_instance" {
    defaults = {
      id  = "i-0123456789abcdef0"
      arn = "arn:aws:ec2:us-east-1:123456789012:instance/i-0123456789abcdef0"
    }
  }

  mock_resource "aws_iam_role" {
    defaults = {
      arn = "arn:aws:iam::123456789012:role/gpu-ec2-expiry"
    }
  }
}

run "all_tagged_resources_carry_complete_project_metadata" {
  command = apply

  variables {
    expected_account_id = "123456789012"
    availability_zone   = "us-east-1a"
    ubuntu_ami_id       = "ami-0123456789abcdef0"
    expires_at          = timeadd(timestamp(), "6h")
  }

  assert {
    condition     = jsonencode(aws_vpc.gpu.tags) == jsonencode(local.resource_tags)
    error_message = "The VPC must carry the complete GPU-lab tags."
  }

  assert {
    condition     = jsonencode(aws_internet_gateway.gpu.tags) == jsonencode(local.resource_tags)
    error_message = "The internet gateway must carry the complete GPU-lab tags."
  }

  assert {
    condition     = jsonencode(aws_subnet.gpu.tags) == jsonencode(local.resource_tags)
    error_message = "The subnet must carry the complete GPU-lab tags."
  }

  assert {
    condition     = jsonencode(aws_route_table.gpu.tags) == jsonencode(local.resource_tags)
    error_message = "The route table must carry the complete GPU-lab tags."
  }

  assert {
    condition     = jsonencode(aws_security_group.gpu.tags) == jsonencode(local.resource_tags)
    error_message = "The security group must carry the complete GPU-lab tags."
  }

  assert {
    condition     = jsonencode(aws_iam_role.instance.tags) == jsonencode(local.resource_tags)
    error_message = "The instance role must carry the complete GPU-lab tags."
  }

  assert {
    condition     = jsonencode(aws_iam_instance_profile.gpu.tags) == jsonencode(local.resource_tags)
    error_message = "The instance profile must carry the complete GPU-lab tags."
  }

  assert {
    condition     = jsonencode(aws_instance.gpu.tags) == jsonencode(local.resource_tags)
    error_message = "The EC2 instance must carry the complete GPU-lab tags."
  }

  assert {
    condition     = jsonencode(aws_instance.gpu.volume_tags) == jsonencode(local.resource_tags)
    error_message = "The root volume must carry the complete GPU-lab tags."
  }

  assert {
    condition     = jsonencode(aws_scheduler_schedule_group.gpu.tags) == jsonencode(local.resource_tags)
    error_message = "The expiry schedule group must carry the complete GPU-lab tags."
  }

  assert {
    condition     = jsonencode(aws_iam_role.expiry.tags) == jsonencode(local.resource_tags)
    error_message = "The expiry role must carry the complete GPU-lab tags."
  }

  assert {
    condition = (
      local.resource_tags.project == "multi-tenant-ai-inference-platform" &&
      local.resource_tags.environment == "gpu-ec2" &&
      local.resource_tags.managed_by == "terraform" &&
      local.resource_tags.owner == "bepoadewale" &&
      local.resource_tags.cost_scope == "gpu-ec2" &&
      local.resource_tags.data_class == "synthetic-only" &&
      local.resource_tags.expires_at == var.expires_at &&
      local.resource_tags.Name == "${var.project}-gpu-ec2"
    )
    error_message = "Required ownership, cost, data-class, expiry, and resource-name tags must use the configured project values."
  }
}
