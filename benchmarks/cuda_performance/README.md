# CUDA and GPU performance preparation

This folder contains a small CUDA C++ vector-add exercise and a PyTorch CPU/GPU
matrix-multiplication benchmark. It is prepared for the authorized single-L4 window;
there are no measurements from this code yet. The dry-run is safe on the workstation.

## What the experiments demonstrate

- **Vector addition:** one CUDA thread adds one pair of floats. A one-dimensional grid
  contains blocks of 256 threads; the final block can have unused threads, so the
  kernel checks the array bound. Threads access neighboring array positions, which
  allows the GPU to combine adjacent memory requests efficiently (coalescing).
- **Matrix multiplication:** PyTorch runs a square matrix multiply on CPU and on one
  L4. The operation count is approximately `2 × N³` floating-point operations. CUDA
  events measure queued GPU work, with explicit synchronization so the host does not
  mistake asynchronous launch time for full kernel time.
- **Host/device copies:** the vector program reports host-to-device and
  device-to-host transfer time separately from kernel time. The PyTorch program uses
  pinned host memory for its transfer sample and synchronizes around each sample.
- **Precision:** the PyTorch experiment tests FP32 and FP16 and includes BF16 only when
  PyTorch reports support. For correctness, each output is compared with an FP32
  multiply using the same values after they have been rounded to the test precision.
  This checks multiplication error without incorrectly counting input-quantization
  error as a broken GPU result. Unsupported precision is omitted, not silently
  replaced.

These are microbenchmarks. They do not represent LLM serving throughput, user latency,
multi-tenant contention, or production performance. The vector kernel is intentionally
simple and is not expected to beat an optimized library for all sizes.

## Triton kernel

The same CUDA/PyTorch learning environment includes Triton `3.8.0` in its hash-locked
dependency set. Triton expresses a GPU kernel in Python and compiles it for the target
GPU when first launched. The new vector-add exercise maps one Triton program to a
fixed-size block of elements, masks the last partial block, checks every result against
PyTorch, and measures only after warm-up with synchronized CUDA events. It reports an
**effective** byte-rate calculated as three FP32 values per element (two reads and one
write); this does not measure actual DRAM traffic because cache behavior is not counted.

Run the no-GPU plan from the local workstation:

```bash
make gpu-triton-plan
```

On the approved EC2 host through Systems Manager, the operator wrapper verifies exact
host identity and one visible L4, requires a separate confirmation, and limits the
kernel batch to at most 120 seconds:

```bash
GPU_EC2_TRITON_CONFIRM=run make gpu-ec2-triton
```

The command stores a private aggregate JSON file under
`/var/tmp/gpu-lab/cuda-performance/`. It imports neither Triton nor PyTorch in dry-run
mode, refuses to fall back to CPU, and has not been executed on an L4 yet.

## Nsight profiling

Nsight Systems shows a short timeline of host calls, CUDA launches, memory copies, and
kernel execution. Run the small, L4-guarded CUDA C++ vector program under it, with
sampling disabled to reduce unrelated data and collection overhead:

```bash
mkdir -p /var/tmp/gpu-lab/profiling
chmod 700 /var/tmp/gpu-lab/profiling
nsys --version
nsys profile --trace=cuda,nvtx --sample=none --cpuctxsw=none \
  --force-overwrite=true --stats=true \
  --output=/var/tmp/gpu-lab/profiling/vector-add \
  /tmp/gpu-lab-vector-add 1048576 5 20
nsys stats --report cuda_gpu_kern_sum --report cuda_api_sum \
  /var/tmp/gpu-lab/profiling/vector-add.nsys-rep
```

Nsight Compute examines one kernel in more detail. Its replay and counter collection
can change timings, so keep its result separate from normal benchmark data. NVIDIA
drivers may restrict hardware counters to administrators; if a non-privileged attempt
reports `ERR_NVGPUCTRPERM`, use the documented administrator path only for this
bounded sample. Do not change driver security settings to bypass the restriction.

```bash
ncu --version
sudo ncu --set basic --launch-count 1 --force-overwrite \
  --export /var/tmp/gpu-lab/profiling/vector-add \
  /tmp/gpu-lab-vector-add 1048576 5 20
```

Inspect the short report and record unavailable metrics. Do not profile DCGM hardware
counters at the same time; counter clients can conflict. Keep raw profiler files
outside Git, private, and short-lived. If `nsys` or `ncu` is absent from the reviewed
toolkit package set, record it as unavailable and confirm any extra package's version,
cost impact, and disk usage before installing it.

The planned Nsight commands are based on NVIDIA's [Nsight Systems CLI guide](https://docs.nvidia.com/nsight-systems/UserGuide/), [Nsight Systems installation requirements](https://docs.nvidia.com/nsight-systems/InstallationGuide/), and [Nsight Compute profiling guide](https://docs.nvidia.com/nsight-compute/ProfilingGuide/). NVIDIA documents that Nsight Compute may require elevated permission for performance counters. CUDA Toolkit and its profiler contents still need to be confirmed on the selected Ubuntu host.

## Safe local dry-run

From the repository root:

```bash
make gpu-cuda-plan
```

This prints sizes, warmups, repetitions, and zero GPU/network operations. It does not
import PyTorch, invoke `nvcc`, or execute a CUDA kernel.

## Run on the EC2 host, after approval

Do not execute these commands until the account/quota, exact Terraform plan, full
cost, runtime, expiry, and teardown gates in `GPU_BATCH_RUNBOOK.md` have passed. Run
on the EC2 host through Systems Manager, not on the Apple Silicon workstation.

First confirm the compiler, driver, and hardware:

```bash
nvcc --version
nvidia-smi -L
nvidia-smi
```

Create the Python 3.12 environment and install the hash-locked PyTorch CUDA build.
These commands are for the **EC2 host through SSM**, after checking free disk space.
The lock targets Linux x86_64. It installs CUDA libraries into this virtual
environment; the host CUDA Toolkit separately provides `nvcc`.

```bash
python3.12 -m venv /opt/gpu-lab/torch-venv
/opt/gpu-lab/torch-venv/bin/python -m pip install \
  --require-hashes \
  --index-url https://download.pytorch.org/whl/cu130 \
  --extra-index-url https://pypi.org/simple \
  -r benchmarks/cuda_performance/requirements-torch.lock
```

The package index URLs are public vendor sources, not credentials. The hashes protect
the pinned artifacts. This dated lock is still a candidate; refresh and review it
before the authorized batch. Do not run this install against the workstation's Apple
Silicon Python.

Compile the CUDA C++ program into temporary storage and run it:

```bash
nvcc -O2 -std=c++17 -lineinfo \
  benchmarks/cuda_performance/vector_add.cu \
  -o /tmp/gpu-lab-vector-add
/tmp/gpu-lab-vector-add 1048576 5 20
```

Arguments are element count, warm-up count, and timed repetitions. The program checks
that exactly one visible GPU is an NVIDIA L4, checks every output against the CPU,
uses CUDA events for kernel and copy timing, and prints aggregate JSON only. The
maximum vector size is bounded. No per-element values are printed.

Run the PyTorch comparison and keep its result outside Git:

```bash
/opt/gpu-lab/torch-venv/bin/python benchmarks/cuda_performance/torch_matmul.py \
  --sizes 256 512 1024 --warmups 3 --repeats 10 \
  --output /var/tmp/gpu-lab/cuda-performance/matmul.json
```

The program refuses to fall back to CPU when CUDA is unavailable, rejects a non-L4 or
more than one visible GPU, checks numerical output, records driver/framework/device
metadata, and writes a mode-0600 aggregate report outside the repository. `median
GFLOP/s = 2 × N³ / median_seconds / 10⁹`; transfer latency is not included in this
compute formula. The total PyTorch run is capped at 600 seconds by default and cannot
be configured above that value. GPU utilization should be observed separately with
`nvidia-smi` and the live DCGM dashboard. The C++ vector sample also bounds elements,
warmups, and repetitions.

## Measurement discipline

- Keep the run inside the approved instance-hour and spending envelope.
- Do not time only a CUDA launch from the CPU clock. The script uses CUDA events and
  calls synchronization for each timed sample.
- Treat CPU and GPU timings as distinct device measurements. Record CPU thread count,
  GPU model, driver, PyTorch, CUDA runtime, size, dtype, warmups, and repetitions.
- Compare repeated medians and inspect samples. One measurement is not a stable
  performance claim.
- Correlate results with GPU utilization, clocks, temperature, and memory telemetry.
  This code does not sample every hardware counter itself.
- Export evidence, stop the instance promptly, and do not put raw output or compiled
  binaries in public Git.

## Limitations before runtime validation

The local workstation has no NVIDIA driver or `nvcc`. The `.cu` source therefore has
not been compiled or run. CUDA runtime behavior, timing numbers, FP16/BF16 numerical
error, and the exact PyTorch build must be checked on the pinned Linux/L4 environment.
Do not describe this preparation as CUDA execution evidence.
