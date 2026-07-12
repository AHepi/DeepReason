"""Reasoning-first workload contracts and harness-owned compilation helpers."""

from deepreason.workloads.models import MandatoryInterface, compile_interface
from deepreason.workloads.registry import WORKLOADS, WorkloadRegistry
from deepreason.workloads.website import WEBSITE_WORKLOAD

try:
    WORKLOADS.register(WEBSITE_WORKLOAD)
except ValueError:
    pass

__all__ = [
    "MandatoryInterface",
    "WEBSITE_WORKLOAD",
    "WORKLOADS",
    "WorkloadRegistry",
    "compile_interface",
]
