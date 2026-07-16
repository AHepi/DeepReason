"""Lightweight capability enums safe to import from ontology schemas."""

from enum import Enum


class CapabilityLifecycle(str, Enum):
    PROPOSED = "proposed"
    VALIDATED = "validated"
    GRANTED = "granted"
    DENIED = "denied"
    COMPILED = "compiled"
    DISPATCHED = "dispatched"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    RESULT_PACKAGED = "result_packaged"
    CONSUMED = "consumed"


__all__ = ["CapabilityLifecycle"]
