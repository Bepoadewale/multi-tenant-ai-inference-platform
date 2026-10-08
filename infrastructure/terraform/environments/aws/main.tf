# This is the flagship's intended CPU-first AWS pilot. It is deliberately a
# Terraform contract until a separately authorized plan/apply/destroy exercise.
data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}

locals {
  prefix = "${var.project}-pilot"
  azs    = slice(data.aws_availability_zones.available.names, 0, 2)
  tags = {
    project     = var.project
    environment = "pilot"
    managed_by  = "terraform"
    owner       = var.owner
    cost_scope  = "pilot"
  }
  service_repositories = toset([
    "inference-gateway",
    "release-control",
    "operator-console",
  ])
}

check "expected_account" {
  assert {
    condition     = data.aws_caller_identity.current.account_id == var.expected_account_id
    error_message = "Refusing to plan or apply outside the expected AWS account."
  }
}

resource "aws_vpc" "pilot" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = { Name = "${local.prefix}-vpc" }
}

resource "aws_internet_gateway" "pilot" {
  vpc_id = aws_vpc.pilot.id

  tags = { Name = "${local.prefix}-igw" }
}

resource "aws_subnet" "public" {
  for_each = { for index, az in local.azs : az => index }

  vpc_id                  = aws_vpc.pilot.id
  availability_zone       = each.key
  cidr_block              = cidrsubnet(var.vpc_cidr, 4, each.value)
  map_public_ip_on_launch = false

  tags = {
    Name                     = "${local.prefix}-public-${each.value + 1}"
    "kubernetes.io/role/elb" = "1"
  }
}

resource "aws_subnet" "private" {
  for_each = { for index, az in local.azs : az => index }

  vpc_id            = aws_vpc.pilot.id
  availability_zone = each.key
  cidr_block        = cidrsubnet(var.vpc_cidr, 4, each.value + 8)

  tags = {
    Name                              = "${local.prefix}-private-${each.value + 1}"
    "kubernetes.io/role/internal-elb" = "1"
  }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.pilot.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.pilot.id
  }
}

resource "aws_route_table_association" "public" {
  for_each = aws_subnet.public

  subnet_id      = each.value.id
  route_table_id = aws_route_table.public.id
}

resource "aws_eip" "nat" {
  domain = "vpc"

  tags = { Name = "${local.prefix}-nat-eip" }
}

resource "aws_nat_gateway" "pilot" {
  allocation_id = aws_eip.nat.id
  subnet_id     = values(aws_subnet.public)[0].id

  depends_on = [aws_internet_gateway.pilot]

  tags = { Name = "${local.prefix}-nat" }
}

resource "aws_route_table" "private" {
  vpc_id = aws_vpc.pilot.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.pilot.id
  }
}

resource "aws_route_table_association" "private" {
  for_each = aws_subnet.private

  subnet_id      = each.value.id
  route_table_id = aws_route_table.private.id
}

data "aws_iam_policy_document" "eks_cluster_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["eks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "eks_cluster" {
  name               = "${local.prefix}-cluster"
  assume_role_policy = data.aws_iam_policy_document.eks_cluster_assume.json
}

resource "aws_iam_role_policy_attachment" "eks_cluster" {
  role       = aws_iam_role.eks_cluster.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
}

data "aws_iam_policy_document" "node_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "eks_node" {
  name               = "${local.prefix}-node"
  assume_role_policy = data.aws_iam_policy_document.node_assume.json
}

resource "aws_iam_role_policy_attachment" "node_worker" {
  role       = aws_iam_role.eks_node.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"
}

resource "aws_iam_role_policy_attachment" "node_cni" {
  role       = aws_iam_role.eks_node.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"
}

resource "aws_iam_role_policy_attachment" "node_ecr" {
  role       = aws_iam_role.eks_node.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryPullOnly"
}

resource "aws_eks_cluster" "pilot" {
  name     = var.cluster_name
  role_arn = aws_iam_role.eks_cluster.arn
  version  = var.kubernetes_version

  vpc_config {
    subnet_ids              = values(aws_subnet.private)[*].id
    endpoint_private_access = true
    endpoint_public_access  = false
  }

  access_config { authentication_mode = "API" }

  depends_on = [aws_iam_role_policy_attachment.eks_cluster]
}

data "tls_certificate" "eks_oidc" {
  url = aws_eks_cluster.pilot.identity[0].oidc[0].issuer
}

resource "aws_iam_openid_connect_provider" "eks" {
  url             = aws_eks_cluster.pilot.identity[0].oidc[0].issuer
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = [data.tls_certificate.eks_oidc.certificates[0].sha1_fingerprint]
}

locals {
  eks_oidc_issuer = trimprefix(aws_eks_cluster.pilot.identity[0].oidc[0].issuer, "https://")
}

data "aws_iam_policy_document" "gateway_irsa_assume" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.eks.arn]
    }

    condition {
      test     = "StringEquals"
      variable = "${local.eks_oidc_issuer}:aud"
      values   = ["sts.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "${local.eks_oidc_issuer}:sub"
      values   = ["system:serviceaccount:platform:inference-gateway"]
    }
  }
}

resource "aws_iam_role" "gateway_irsa" {
  name               = "${local.prefix}-gateway"
  assume_role_policy = data.aws_iam_policy_document.gateway_irsa_assume.json
}

resource "aws_eks_node_group" "cpu" {
  cluster_name    = aws_eks_cluster.pilot.name
  node_group_name = "cpu-pilot"
  node_role_arn   = aws_iam_role.eks_node.arn
  subnet_ids      = values(aws_subnet.private)[*].id
  instance_types  = [var.node_instance_type]
  capacity_type   = "ON_DEMAND"

  scaling_config {
    desired_size = var.node_desired_size
    min_size     = var.node_min_size
    max_size     = var.node_max_size
  }

  update_config { max_unavailable = 1 }

  depends_on = [
    aws_iam_role_policy_attachment.node_worker,
    aws_iam_role_policy_attachment.node_cni,
    aws_iam_role_policy_attachment.node_ecr,
  ]
}

resource "aws_security_group" "data" {
  name        = "${local.prefix}-data"
  description = "PostgreSQL and Redis ingress from the pilot VPC only"
  vpc_id      = aws_vpc.pilot.id
}

resource "aws_vpc_security_group_ingress_rule" "postgres" {
  security_group_id = aws_security_group.data.id
  cidr_ipv4         = aws_vpc.pilot.cidr_block
  from_port         = 5432
  to_port           = 5432
  ip_protocol       = "tcp"
}

resource "aws_vpc_security_group_ingress_rule" "redis" {
  security_group_id = aws_security_group.data.id
  cidr_ipv4         = aws_vpc.pilot.cidr_block
  from_port         = 6379
  to_port           = 6379
  ip_protocol       = "tcp"
}

resource "aws_db_subnet_group" "pilot" {
  name       = "${local.prefix}-db"
  subnet_ids = values(aws_subnet.private)[*].id
}

resource "aws_db_instance" "postgres" {
  identifier                  = "${local.prefix}-postgres"
  engine                      = "postgres"
  engine_version              = "16"
  instance_class              = var.rds_instance_class
  allocated_storage           = 20
  max_allocated_storage       = 20
  db_name                     = "inference"
  username                    = "platform"
  manage_master_user_password = true
  publicly_accessible         = false
  storage_encrypted           = true
  deletion_protection         = false
  skip_final_snapshot         = true
  backup_retention_period     = 0
  multi_az                    = false
  apply_immediately           = true
  db_subnet_group_name        = aws_db_subnet_group.pilot.name
  vpc_security_group_ids      = [aws_security_group.data.id]
}

resource "aws_elasticache_subnet_group" "pilot" {
  name       = "${local.prefix}-cache"
  subnet_ids = values(aws_subnet.private)[*].id
}

resource "aws_elasticache_replication_group" "redis" {
  replication_group_id       = "${local.prefix}-redis"
  description                = "Shared admission and metadata cache for the pilot"
  engine                     = "redis"
  node_type                  = var.redis_node_type
  num_cache_clusters         = 1
  port                       = 6379
  automatic_failover_enabled = false
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  subnet_group_name          = aws_elasticache_subnet_group.pilot.name
  security_group_ids         = [aws_security_group.data.id]
}

resource "aws_s3_bucket" "model_artifacts" {
  bucket_prefix = "${var.project}-artifacts-"
  force_destroy = true
}

resource "aws_s3_bucket_public_access_block" "model_artifacts" {
  bucket                  = aws_s3_bucket.model_artifacts.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "model_artifacts" {
  bucket = aws_s3_bucket.model_artifacts.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "model_artifacts" {
  bucket = aws_s3_bucket.model_artifacts.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_ecr_repository" "services" {
  for_each             = local.service_repositories
  name                 = "${var.project}/${each.value}"
  image_tag_mutability = "IMMUTABLE"
  force_delete         = true

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_secretsmanager_secret" "runtime" {
  for_each                = toset(["application", "mlflow", "identity"])
  name                    = "${local.prefix}/${each.value}"
  recovery_window_in_days = 0
}

data "aws_iam_policy_document" "gateway_irsa" {
  statement {
    sid       = "ModelArtifacts"
    actions   = ["s3:GetObject", "s3:PutObject"]
    resources = ["${aws_s3_bucket.model_artifacts.arn}/gateway/*"]
  }

  statement {
    sid       = "RuntimeConfiguration"
    actions   = ["secretsmanager:GetSecretValue", "secretsmanager:DescribeSecret"]
    resources = [aws_secretsmanager_secret.runtime["application"].arn]
  }
}

resource "aws_iam_role_policy" "gateway_irsa" {
  name   = "artifact-and-runtime-configuration"
  role   = aws_iam_role.gateway_irsa.id
  policy = data.aws_iam_policy_document.gateway_irsa.json
}
