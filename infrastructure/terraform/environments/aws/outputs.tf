output "cluster_name" {
  value = aws_eks_cluster.pilot.name
}

output "cluster_endpoint" {
  value = aws_eks_cluster.pilot.endpoint
}

output "rds_address" {
  value = aws_db_instance.postgres.address
}

output "redis_primary_endpoint" {
  value = aws_elasticache_replication_group.redis.primary_endpoint_address
}

output "artifact_bucket" {
  value = aws_s3_bucket.model_artifacts.bucket
}

output "ecr_repository_urls" {
  value = { for name, repo in aws_ecr_repository.services : name => repo.repository_url }
}

output "runtime_secret_arns" {
  value = { for name, secret in aws_secretsmanager_secret.runtime : name => secret.arn }
}

output "gateway_irsa_role_arn" {
  value       = aws_iam_role.gateway_irsa.arn
  description = "IRSA role bound only to the future platform/inference-gateway service account."
}
