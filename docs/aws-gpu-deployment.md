# Optional AWS/EKS GPU deployment

Use isolated AWS accounts, encrypted remote Terraform state/locking, EKS, CPU system nodes, explicit GPU node pools or Karpenter requirements, workload IAM, ECR, GPU Operator, DCGM, Prometheus, and protected GitOps deployment. `enable_gpu_nodes=false` by default. Review regional g5/p5 availability, quotas, on-demand/spot interruptions, and current price before apply. Destroy GPU nodes and model caches promptly after experiments.
