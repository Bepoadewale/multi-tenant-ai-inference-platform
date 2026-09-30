# Autoscaling

Flagship context: the Redis-backed `simulated-l40s` capacity slice is executed locally
and proves bounded admission, queueing, rejection, and explicitly allowed CPU fallback.
It is policy/accounting evidence only: HPA, KEDA, Karpenter, Kubernetes placement, and
physical GPU scale-out remain future adapters.

HPA/KEDA scales pods; Karpenter/EKS node groups scale GPU capacity. They solve different delays. The included KEDA contract scales on active inference demand rather than CPU alone. Queue depth, active requests, token rate, GPU/KV pressure, and latency are candidates; select per model/workload. Latency-sensitive production models use minimum warm replicas. Scale-to-zero is a development cost optimization with cold-start consequences.
