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

run "network_is_closed_inbound_and_limited_outbound" {
  command = apply

  variables {
    expected_account_id = "123456789012"
    availability_zone   = "us-east-1a"
    ubuntu_ami_id       = "ami-0123456789abcdef0"
    expires_at          = timeadd(timestamp(), "6h")
  }

  assert {
    condition     = length(aws_security_group.gpu.ingress) == 0
    error_message = "The GPU host security group must not allow inbound connections."
  }

  assert {
    condition     = length(aws_security_group.gpu.egress) == 2
    error_message = "The GPU host should have only the two documented outbound rules."
  }

  assert {
    condition = alltrue([
      for rule in aws_security_group.gpu.egress :
      rule.protocol == "tcp" &&
      rule.from_port == rule.to_port &&
      contains([80, 443], rule.from_port) &&
      length(rule.cidr_blocks) == 1 &&
      contains(rule.cidr_blocks, "0.0.0.0/0") &&
      length(coalesce(rule.ipv6_cidr_blocks, [])) == 0 &&
      length(coalesce(rule.prefix_list_ids, [])) == 0 &&
      length(coalesce(rule.security_groups, [])) == 0 &&
      !coalesce(rule.self, false)
    ])
    error_message = "Outbound access must be limited to TCP 80 and 443."
  }

  assert {
    condition = (
      length([for rule in aws_security_group.gpu.egress : rule if rule.from_port == 80]) == 1 &&
      length([for rule in aws_security_group.gpu.egress : rule if rule.from_port == 443]) == 1
    )
    error_message = "Both package HTTP and TLS egress rules must exist exactly once."
  }

  assert {
    condition = contains(
      aws_instance.gpu.vpc_security_group_ids,
      aws_security_group.gpu.id
    ) && length(aws_instance.gpu.vpc_security_group_ids) == 1
    error_message = "The GPU instance must use the isolated project security group."
  }

  assert {
    condition = (
      aws_instance.gpu.instance_type == "g6.xlarge" &&
      aws_instance.gpu.availability_zone == var.availability_zone &&
      aws_instance.gpu.associate_public_ip_address &&
      aws_instance.gpu.subnet_id == aws_subnet.gpu.id
    )
    error_message = "The instance must remain one selected single-L4 host in the approved zone."
  }

}
