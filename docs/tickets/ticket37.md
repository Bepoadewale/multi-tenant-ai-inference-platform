# Ticket 37 — Pin the first L4 runtime candidates

## Objective

Research a reproducible candidate for the first GPU execution batch: Ubuntu,
NVIDIA driver and CUDA, NVIDIA Container Toolkit, vLLM, and the required Qwen model.
Record the exact artifacts that are already identifiable, the unresolved package
checks, and the distinction between official compatibility claims and real L4
execution. This documentation-only package must not launch cloud resources or
download the multi-gigabyte model.

## Current state

- Phase: Phase 1 research supporting Phase 3; Phase 2 infrastructure work and
  reviews continue independently.
- Branch: `codex/gpu-software-compatibility`, based on the open PR #32 foundation
  head `da2567e`.
- Pull request: planned as PR #37 against `codex/gpu-ec2-foundation`; not yet opened.
- AWS G/VT On-Demand quota remains applied at 0 vCPUs. The existing increase request
  is `CASE_OPENED`; this ticket authorizes no mutation.
- No EC2, GPU, model download, or cloud spend occurred. Local Docker registry
  manifest metadata and public Hugging Face metadata were read only.

## Research and findings

- Candidate host: standard Ubuntu Server 24.04 x86_64, with the exact Canonical AMI
  ID and kernel resolved at a reviewed plan. No GPU-ready AMI is used.
- Candidate NVIDIA branch: Data Center R580, point release 580.196.11, compute-only.
  NVIDIA release notes dated 2026-11-23 list CUDA 13.x and Ubuntu 24.04.4 support;
  the R580 branch is LTS through June 2028. The exact signed Ubuntu package and
  dependencies must be checked before finalizing manual commands and Ansible pins.
- Candidate host CUDA Toolkit: 13.0 for the `nvcc` learning exercises. The vLLM
  container supplies its own CUDA user-space libraries; the host toolkit is not
  required merely to run this container.
- NVIDIA Container Toolkit must follow the host driver. Pin its exact package after
  checking the NVIDIA apt repository during the bounded preflight; current static
  documentation does not establish a package installed on the target AMI.
- Candidate inference image: `vllm/vllm-openai:v0.34.0`, CUDA 13.0, PyTorch 2.14.0.
  `docker buildx imagetools inspect` returned OCI index digest
  `sha256:20fdb089454afbb324efa4110a2c025ff7b27cc1a086e07aa580b18df8ad1ce1` and
  `linux/amd64` image digest
  `sha256:cf5b2fdd087eb4f6d261736967cc5cde974bd22ff4df50365f8fa419b6b4c484` on
  2026-11-27. A fresh check is required before the execution package; the image was
  not pulled or run.
- vLLM's published GPU guide names L4 among GPUs with compute capability 7.5 or
  higher, and the v0.34.0 supported-model table lists `Qwen2ForCausalLM`.
- Hugging Face Hub API on 2026-11-27 reports the Qwen model revision as
  `989aa7980e4cf806f80c7fef2b1adb7bc71aa306`, license `apache-2.0`, architecture
  `Qwen2ForCausalLM`, BF16 weights, and 3,087,467,144 bytes for `model.safetensors`.
  The Hub's LFS SHA-256 is
  `dd924a11b4c220f385b51ffa522daea7c9f3d850e31b162bb5661df483c6d3ee`. The model
  files were not downloaded.
- The model config says 32,768 positional embeddings, while tokenizer metadata says
  131,072 maximum length. The pinned config's RoPE settings and the runtime-supported
  limit need review. Begin with a conservative context such as 8,192 and do not copy
  the tokenizer limit directly into the vLLM config.
- These sources establish a version-family candidate, not actual host, container,
  CUDA, PyTorch, or model behavior on EC2 L4 hardware.

## Proposed architecture

Use the R580 driver on the Ubuntu host; install the CUDA 13.0 Toolkit separately for
CUDA C++ practice; configure Docker with the NVIDIA Container Toolkit; run the pinned
vLLM CUDA 13.0 image with the L4 exposed; mount only a cache directory and serve the
pinned Qwen revision. Run standalone PyTorch checks in a separate environment or use
the exact PyTorch bundled in the vLLM image. Do not replace vLLM's Torch libraries
with a separately resolved build.

## Implementation tasks

- [x] Check current official NVIDIA driver lifecycle, Ubuntu instructions, and CUDA
  compatibility for R580 and CUDA 13.
- [x] Check official vLLM release artifacts, GPU requirements, and supported model
  architecture.
- [x] Resolve the current Qwen revision, license metadata, configuration, size, and
  published LFS SHA-256 without downloading the weights.
- [x] Query the registry for the vLLM OCI index and AMD64 child digests.
- [x] Record one-run clean-room policy remains unchanged; no extra local clean-room
  cycle is part of this research package.
- [ ] Recheck exact Ubuntu packages, signing keys, CUDA toolkit package, Docker and
  Container Toolkit versions, and image digests in the GPU preflight.
- [ ] Validate the full software matrix on one authorized L4 during a consolidated
  paid execution batch after all spending and quota gates pass.

## Commands and validation

- `git status --short --branch`, repository docs/source inspection: research branch
  was clean at start and is based on PR #32's `da2567e` head.
- `docker buildx imagetools inspect vllm/vllm-openai:v0.34.0`: returned the OCI index
  and platform-specific digests above. This fetched registry metadata only; no image
  layers were downloaded or executed.
- A metadata query was first invoked as `python` and returned `command not found` on
  this workstation. Re-running the same read-only Hugging Face Hub query with
  `python3` succeeded and returned the revision/license/config/LFS fields above.
- Official docs checked: NVIDIA R580.196.11 release notes, NVIDIA driver/CUDA
  support matrix and Ubuntu install guide, vLLM v0.34.0 release and model/GPU docs,
  and the Hugging Face model card and pinned revision.
- No GPU tests, local clean-room cycle, AWS calls that mutate state, or inference
  tests were performed as part of this ticket.

## Issues and troubleshooting

- The moving `stable`/`latest` documentation can disagree with the newest dated
  release. This ticket therefore uses version-specific vLLM v0.34.0 release/model
  documentation and records the publication date.
- The Hugging Face `blobId` is a Git blob identifier, not the model's file checksum.
  The Hub API's LFS `sha256` field is the checksum to verify after an authorized
  download.
- The image tag is not an immutable reference. Use the platform-specific digest and
  recheck it before use.
- The tokenizer's 131,072 limit conflicts with the model config's 32,768 positional
  embeddings. Resolve the model's RoPE details before increasing the conservative
  runtime context.

## Security and financial considerations

- Public model metadata and image manifests were queried without credentials.
- Model weights were not downloaded, and no AWS resources were created.
- The initial authorized AWS ceiling remains USD $25; this package creates no
  additional authorization and no GPU instance-hours have been consumed.
- Pin the Hub revision and verify the actual file digest before inference. Do not
  store credentials, prompts, raw Terraform plans/state, or model weights in Git.

## Evidence

- Updated `docs/gpu-lab/RESEARCH_NOTES.md` with the dated candidate matrix and
  limitations.
- The manifest digests came from Docker registry metadata; the model metadata and
  LFS digest came from Hugging Face Hub API. Both are public metadata checks, not
  workload execution.
- Official source links are in the research notes; no screenshot was captured.

## Outstanding work and acceptance

- Status: **research recorded; hardware compatibility not yet validated**.
- The exact AMI/kernel/package versions and container digest need fresh preflight
  checks. Quota approval, complete bounded cost estimate, exact-plan review, expiry,
  and teardown safeguards remain separate prerequisites.
- Ticket is accepted when the dated matrix and its limitations are reviewed in PR
  #37. It does not close the broader Phase 3 acceptance gate.
