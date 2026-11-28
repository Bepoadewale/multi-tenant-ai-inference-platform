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

run "expiry_is_bounded_and_uses_two_independent_paths" {
  command = apply

  variables {
    expected_account_id = "123456789012"
    availability_zone   = "us-east-1a"
    ubuntu_ami_id       = "ami-0123456789abcdef0"
    expires_at          = timeadd(timestamp(), "6h")
  }

  assert {
    condition     = aws_instance.gpu.instance_initiated_shutdown_behavior == "terminate"
    error_message = "Guest shutdown must terminate the disposable EC2 instance."
  }

  assert {
    condition     = aws_instance.gpu.root_block_device[0].delete_on_termination
    error_message = "The encrypted root volume must be deleted with the instance."
  }

  assert {
    condition     = aws_instance.gpu.root_block_device[0].encrypted
    error_message = "The disposable root volume must be encrypted."
  }

  assert {
    condition     = aws_instance.gpu.metadata_options[0].http_tokens == "required"
    error_message = "The instance must require IMDSv2 tokens."
  }

  assert {
    condition     = aws_scheduler_schedule.expiry.schedule_expression == "at(${substr(var.expires_at, 0, 19)})"
    error_message = "The AWS schedule must use the exact approved one-time expiry."
  }

  assert {
    condition = (
      aws_scheduler_schedule.expiry.schedule_expression_timezone == "UTC" &&
      aws_scheduler_schedule.expiry.flexible_time_window[0].mode == "OFF" &&
      aws_scheduler_schedule.expiry.state == "ENABLED"
    )
    error_message = "The expiry schedule must be enabled, UTC, and have no flexible delivery window."
  }

  assert {
    condition = (
      aws_scheduler_schedule.expiry.target[0].arn == "arn:aws:scheduler:::aws-sdk:ec2:terminateInstances" &&
      jsondecode(aws_scheduler_schedule.expiry.target[0].input).InstanceIds == [aws_instance.gpu.id]
    )
    error_message = "The one-time AWS target must terminate only this instance."
  }

  assert {
    condition = (
      jsondecode(aws_iam_role_policy.expiry.policy).Statement[0].Action == ["ec2:TerminateInstances"] &&
      jsondecode(aws_iam_role_policy.expiry.policy).Statement[0].Resource == aws_instance.gpu.arn
    )
    error_message = "The scheduler role may terminate only this project instance."
  }

  assert {
    condition = (
      jsondecode(aws_iam_role.expiry.assume_role_policy).Statement[0].Principal.Service == "scheduler.amazonaws.com" &&
      jsondecode(aws_iam_role.expiry.assume_role_policy).Statement[0].Condition.StringEquals["aws:SourceAccount"] == var.expected_account_id &&
      jsondecode(aws_iam_role.expiry.assume_role_policy).Statement[0].Condition.ArnEquals["aws:SourceArn"] == aws_scheduler_schedule_group.gpu.arn
    )
    error_message = "Only EventBridge Scheduler from this account and schedule group may assume the expiry role."
  }

  assert {
    condition = (
      strcontains(aws_instance.gpu.user_data, "gpu-lab-expiry.timer") &&
      strcontains(aws_instance.gpu.user_data, "Persistent=true") &&
      strcontains(aws_instance.gpu.user_data, "shutdown --poweroff now") &&
      strcontains(aws_instance.gpu.user_data, "OnCalendar=") &&
      strcontains(aws_instance.gpu.user_data, formatdate("YYYY-MM-DD HH:mm:ss 'UTC'", var.expires_at))
    )
    error_message = "Cloud-init must install a persistent guest-side expiry timer."
  }
}

run "rejects_expiry_beyond_twelve_hours" {
  command = plan

  variables {
    expected_account_id = "123456789012"
    availability_zone   = "us-east-1a"
    ubuntu_ami_id       = "ami-0123456789abcdef0"
    expires_at          = timeadd(timestamp(), "13h")
  }

  expect_failures = [var.expires_at]
}

run "rejects_non_utc_expiry" {
  command = plan

  variables {
    expected_account_id = "123456789012"
    availability_zone   = "us-east-1a"
    ubuntu_ami_id       = "ami-0123456789abcdef0"
    expires_at          = replace(timeadd(timestamp(), "6h"), "Z", "+00:00")
  }

  expect_failures = [var.expires_at]
}
