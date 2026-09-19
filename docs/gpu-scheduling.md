# GPU scheduling

GPU devices are requested as integer `nvidia.com/gpu` resources; GPU memory is not equivalent to Kubernetes CPU memory and is usually managed by the runtime. The GPU manifest applies selectors, taints/tolerations, bounded resources, long readiness, and graceful termination. Install NVIDIA GPU Operator or device plugin plus DCGM Exporter only on actual NVIDIA clusters. CPU local mode has no GPU telemetry.

Tensor parallel size must match available accelerators/topology. Use node labels/affinity for compatible GPU SKU and review NVLink/topology needs before multi-GPU serving.
