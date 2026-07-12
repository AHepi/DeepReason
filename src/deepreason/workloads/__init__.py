"""Reasoning-first workload contracts and harness-owned compilation helpers."""

from deepreason.workloads.models import MandatoryInterface, compile_interface
from deepreason.workloads.registry import WORKLOADS, WorkloadRegistry
from deepreason.workloads.text import TEXT_WORKLOAD
from deepreason.workloads.website import WEBSITE_WORKLOAD

for _adapter in (TEXT_WORKLOAD, WEBSITE_WORKLOAD):
    try:
        WORKLOADS.register(_adapter)
    except ValueError:
        pass

__all__ = [
    "MandatoryInterface",
    "TEXT_WORKLOAD",
    "WEBSITE_WORKLOAD",
    "WORKLOADS",
    "WorkloadRegistry",
    "compile_interface",
]
