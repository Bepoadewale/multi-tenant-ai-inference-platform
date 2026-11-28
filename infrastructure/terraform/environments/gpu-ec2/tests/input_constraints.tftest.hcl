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

run "rejects_larger_single_gpu_instance" {
  command = plan

  variables {
    expected_account_id = "123456789012"
    availability_zone   = "us-east-1a"
    ubuntu_ami_id       = "ami-0123456789abcdef0"
    expires_at          = timeadd(timestamp(), "6h")
    instance_type       = "g6.2xlarge"
  }

  expect_failures = [var.instance_type]
}

run "rejects_non_l4_accelerator_instance" {
  command = plan

  variables {
    expected_account_id = "123456789012"
    availability_zone   = "us-east-1a"
    ubuntu_ami_id       = "ami-0123456789abcdef0"
    expires_at          = timeadd(timestamp(), "6h")
    instance_type       = "g5.xlarge"
  }

  expect_failures = [var.instance_type]
}

run "rejects_disk_above_initial_cost_limit" {
  command = plan

  variables {
    expected_account_id = "123456789012"
    availability_zone   = "us-east-1a"
    ubuntu_ami_id       = "ami-0123456789abcdef0"
    expires_at          = timeadd(timestamp(), "6h")
    volume_size_gib     = 121
  }

  expect_failures = [var.volume_size_gib]
}

run "rejects_disk_below_documented_initial_size" {
  command = plan

  variables {
    expected_account_id = "123456789012"
    availability_zone   = "us-east-1a"
    ubuntu_ami_id       = "ami-0123456789abcdef0"
    expires_at          = timeadd(timestamp(), "6h")
    volume_size_gib     = 99
  }

  expect_failures = [var.volume_size_gib]
}

run "rejects_unapproved_region" {
  command = plan

  variables {
    expected_account_id = "123456789012"
    availability_zone   = "us-east-1a"
    aws_region          = "us-west-2"
    ubuntu_ami_id       = "ami-0123456789abcdef0"
    expires_at          = timeadd(timestamp(), "6h")
  }

  expect_failures = [var.aws_region]
}

run "rejects_unapproved_project_name" {
  command = plan

  variables {
    expected_account_id = "123456789012"
    availability_zone   = "us-east-1a"
    ubuntu_ami_id       = "ami-0123456789abcdef0"
    expires_at          = timeadd(timestamp(), "6h")
    project             = "unrelated-project"
  }

  expect_failures = [var.project]
}

run "rejects_malformed_ami_identifier" {
  command = plan

  variables {
    expected_account_id = "123456789012"
    availability_zone   = "us-east-1a"
    ubuntu_ami_id       = "not-an-ami"
    expires_at          = timeadd(timestamp(), "6h")
  }

  expect_failures = [var.ubuntu_ami_id]
}
