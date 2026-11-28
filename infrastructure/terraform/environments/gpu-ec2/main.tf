data "aws_caller_identity" "current" {}

data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }

  filter {
    name   = "architecture"
    values = ["x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

data "aws_ec2_instance_type_offerings" "selected" {
  filter {
    name   = "instance-type"
    values = [var.instance_type]
  }

  filter {
    name   = "location"
    values = [var.availability_zone]
  }

  location_type = "availability-zone"
}

locals {
  name = "${var.project}-gpu-ec2"

  required_tags = {
    project     = var.project
    environment = "gpu-ec2"
    managed_by  = "terraform"
    owner       = var.owner
    cost_scope  = "gpu-ec2"
    expires_at  = var.expires_at
    data_class  = "synthetic-only"
  }

  expiry_systemd = formatdate("YYYY-MM-DD HH:mm:ss 'UTC'", var.expires_at)
}

resource "aws_vpc" "gpu" {
  cidr_block           = "10.74.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = { Name = local.name }
}

resource "aws_internet_gateway" "gpu" {
  vpc_id = aws_vpc.gpu.id

  tags = { Name = local.name }
}

resource "aws_subnet" "gpu" {
  vpc_id                  = aws_vpc.gpu.id
  cidr_block              = "10.74.1.0/24"
  availability_zone       = var.availability_zone
  map_public_ip_on_launch = true

  tags = { Name = local.name }
}

resource "aws_route_table" "gpu" {
  vpc_id = aws_vpc.gpu.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.gpu.id
  }

  tags = { Name = local.name }
}

resource "aws_route_table_association" "gpu" {
  subnet_id      = aws_subnet.gpu.id
  route_table_id = aws_route_table.gpu.id
}

resource "aws_security_group" "gpu" {
  name        = local.name
  description = "No inbound access; outbound TCP 80/443 only for package and artifact retrieval."
  vpc_id      = aws_vpc.gpu.id

  egress {
    description = "TLS traffic for Systems Manager, package mirrors, container registries, and model artifacts."
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Ubuntu package mirrors may use HTTP; move package sources to HTTPS where supported."
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = local.name }
}

resource "aws_iam_role" "instance" {
  name = "${local.name}-ssm"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ssm_core" {
  role       = aws_iam_role.instance.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "gpu" {
  name = local.name
  role = aws_iam_role.instance.name
}

resource "aws_instance" "gpu" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = var.instance_type
  availability_zone           = var.availability_zone
  subnet_id                   = aws_subnet.gpu.id
  vpc_security_group_ids      = [aws_security_group.gpu.id]
  iam_instance_profile        = aws_iam_instance_profile.gpu.name
  associate_public_ip_address = true

  user_data                   = templatefile("${path.module}/cloud-init.yaml.tftpl", { expiry_systemd = local.expiry_systemd })
  user_data_replace_on_change = true

  instance_initiated_shutdown_behavior = "terminate"

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
  }

  root_block_device {
    volume_type           = "gp3"
    volume_size           = var.volume_size_gib
    encrypted             = true
    delete_on_termination = true
  }

  volume_tags = local.required_tags

  lifecycle {
    precondition {
      condition = (timecmp(var.expires_at, timestamp()) > 0 &&
      timecmp(var.expires_at, timeadd(timestamp(), "12h")) <= 0)
      error_message = "The exact expiry must be in the future and within 12 hours when applying."
    }

    precondition {
      condition     = contains(data.aws_ec2_instance_type_offerings.selected.instance_types, var.instance_type)
      error_message = "The selected single-L4 type is not offered in the selected availability zone."
    }
  }

  tags = { Name = local.name }
}

resource "aws_scheduler_schedule_group" "gpu" {
  name = local.name
}

resource "aws_iam_role" "expiry" {
  name = "${local.name}-expiry"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "scheduler.amazonaws.com" }
      Action    = "sts:AssumeRole"
      Condition = {
        StringEquals = { "aws:SourceAccount" = data.aws_caller_identity.current.account_id }
        ArnEquals    = { "aws:SourceArn" = aws_scheduler_schedule_group.gpu.arn }
      }
    }]
  })
}

resource "aws_iam_role_policy" "expiry" {
  name = "terminate-only-this-gpu-instance"
  role = aws_iam_role.expiry.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["ec2:TerminateInstances"]
      Resource = aws_instance.gpu.arn
    }]
  })
}

resource "aws_scheduler_schedule" "expiry" {
  name                         = local.name
  group_name                   = aws_scheduler_schedule_group.gpu.name
  schedule_expression          = "at(${substr(var.expires_at, 0, 19)})"
  schedule_expression_timezone = "UTC"
  state                        = "ENABLED"

  flexible_time_window {
    mode = "OFF"
  }

  target {
    arn      = "arn:aws:scheduler:::aws-sdk:ec2:terminateInstances"
    role_arn = aws_iam_role.expiry.arn
    input    = jsonencode({ InstanceIds = [aws_instance.gpu.id] })
  }

  depends_on = [aws_iam_role_policy.expiry]
}
