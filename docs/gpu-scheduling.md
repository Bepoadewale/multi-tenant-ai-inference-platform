# GPU scheduling

Flagship context: the local serving path now executes a `simulated-l40s` capacity
policy. Redis atomically accounts for a pool of two slots and per-tenant allocations;
the gateway can admit, briefly queue, reject, or choose an explicitly allowed CPU
fallback. The policy is **SIMULATED HARDWARE quota accounting only**. Every successful
local inference still runs on ONNX Runtime `CPUExecutionProvider`; it does not prove
GPU placement, utilization, topology, memory, or performance.

The completed [GPU Scheduler Lab](https://github.com/Bepoadewale/gpu-scheduler-lab)
is the reference for real Kubernetes scheduler experiments with simulated extended
resources. A future flagship Kubernetes adapter may consume a placement decision, but
the gateway does not currently run Kueue, Volcano, or a physical device plugin.

GPU devices are requested as integer `nvidia.com/gpu` resources; GPU memory is not equivalent to Kubernetes CPU memory and is usually managed by the runtime. The GPU manifest applies selectors, taints/tolerations, bounded resources, long readiness, and graceful termination. Install NVIDIA GPU Operator or device plugin plus DCGM Exporter only on actual NVIDIA clusters. CPU local mode has no GPU telemetry.

Tensor parallel size must match available accelerators/topology. Use node labels/affinity for compatible GPU SKU and review NVLink/topology needs before multi-GPU serving.
