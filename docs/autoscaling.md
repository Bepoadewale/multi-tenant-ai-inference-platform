# Autoscaling

HPA/KEDA scales pods; Karpenter/EKS node groups scale GPU capacity. They solve different delays. The included KEDA contract scales on active inference demand rather than CPU alone. Queue depth, active requests, token rate, GPU/KV pressure, and latency are candidates; select per model/workload. Latency-sensitive production models use minimum warm replicas. Scale-to-zero is a development cost optimization with cold-start consequences.
