"""Section-allocated, digest-stable model packs."""

from deepreason.packs.allocate import AllocationResult, allocate_pack
from deepreason.packs.ir import PackIR, PackSection

__all__ = ["AllocationResult", "PackIR", "PackSection", "allocate_pack"]
