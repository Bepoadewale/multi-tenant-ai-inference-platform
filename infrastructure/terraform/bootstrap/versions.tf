terraform {
  required_version = ">= 1.8.0"

  # Bootstrap initially runs with `-backend=false`. After this bucket and lock table
  # exist, operators explicitly migrate local bootstrap state to this backend.
  backend "s3" {}

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = local.required_tags
  }
}
