"""Reasoning-first workload contracts and harness-owned compilation helpers.

Workload models are process metadata around ordinary artifacts. They never add
ontology types or set status.
"""

from deepreason.workloads.formal import (
    FormalClaim,
    FormalizationRelation,
    FormalMismatchTest,
    FormalWorkloadSpec,
    PinnedLeanRequest,
    register_formal_workflow,
)
from deepreason.workloads.models import (
    MandatoryInterface,
    MandatoryRef,
    compile_interface,
    compile_interface_draft,
)
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
    "MandatoryRef",
    "FormalClaim",
    "FormalizationRelation",
    "FormalMismatchTest",
    "FormalWorkloadSpec",
    "PinnedLeanRequest",
    "TEXT_WORKLOAD",
    "WEBSITE_WORKLOAD",
    "WORKLOADS",
    "WorkloadRegistry",
    "compile_interface",
    "compile_interface_draft",
    "register_formal_workflow",
]
