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
