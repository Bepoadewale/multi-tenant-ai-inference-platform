# Compose VPC/EKS/GPU modules only in a reviewed, remote-state-backed environment.
output "gpu_nodes_enabled" {
  value = var.enable_gpu_nodes
}
