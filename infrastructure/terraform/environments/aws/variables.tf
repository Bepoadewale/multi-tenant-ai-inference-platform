variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "expected_account_id" {
  type        = string
  description = "Expected 12-digit pilot AWS account ID."
}

variable "project" {
  type    = string
  default = "multi-tenant-ai-inference-platform"
}

variable "owner" {
  type    = string
  default = "bepoadewale"
}

variable "cluster_name" {
  type    = string
  default = "multi-tenant-ai-platform-pilot"
}

variable "kubernetes_version" {
  type    = string
  default = "1.31"
}

variable "vpc_cidr" {
  type    = string
  default = "10.63.0.0/16"
}

variable "node_instance_type" {
  type    = string
  default = "t3.large"
}

variable "node_desired_size" {
  type    = number
  default = 2
}

variable "node_min_size" {
  type    = number
  default = 2
}

variable "node_max_size" {
  type    = number
  default = 2
}

variable "rds_instance_class" {
  type    = string
  default = "db.t3.micro"
}

variable "redis_node_type" {
  type    = string
  default = "cache.t3.micro"
}

variable "enable_gpu_nodes" {
  type        = bool
  default     = false
  description = "Reserved explicit cost switch. GPU infrastructure is not in this CPU pilot contract."
}
