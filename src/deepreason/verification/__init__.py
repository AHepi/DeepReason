"""Mechanical verifier backends for ordinary program commitments.

Verifier results are traces.  They never set graph status directly.
"""

from deepreason.verification.code import CodeVerificationResult, verify_code_patch
from deepreason.verification.runner import CheckResult, TrustedCheckRunner

__all__ = [
    "CheckResult",
    "CodeVerificationResult",
    "TrustedCheckRunner",
    "SimulationBackend",
    "SimulationRequest",
    "SimulationVerificationResult",
    "verify_code_patch",
]


def __getattr__(name: str):
    """Load simulation exports lazily so ``python -m ...simulation`` is clean."""

    if name in {"SimulationBackend", "SimulationRequest", "SimulationVerificationResult"}:
        from deepreason.verification import simulation

        return getattr(simulation, name)
    raise AttributeError(name)
