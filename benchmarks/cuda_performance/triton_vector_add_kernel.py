"""Triton JIT kernel kept separate so workstation plans do not import Triton."""

import triton
import triton.language as tl


@triton.jit
def vector_add(x_ptr, y_ptr, output_ptr, count, BLOCK_SIZE: tl.constexpr):
    offsets = tl.program_id(0) * BLOCK_SIZE + tl.arange(0, BLOCK_SIZE)
    mask = offsets < count
    x = tl.load(x_ptr + offsets, mask=mask, other=0.0)
    y = tl.load(y_ptr + offsets, mask=mask, other=0.0)
    tl.store(output_ptr + offsets, x + y, mask=mask)
