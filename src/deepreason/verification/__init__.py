"""Pinned, bounded mechanical verifier backends.

Verification produces process receipts for ordinary commitments. It never
adds an ontology type or directly sets graph status.
"""

from __future__ import annotations

from importlib import import_module

__all__ = [
    "CheckResult",
    "CodeVerificationResult",
    "Lean4Backend",
    "LeanBackend",
    "SimulationBackend",
    "SimulationRequest",
    "SimulationVerificationResult",
    "TrustedCheckRunner",
    "UnknownVerifier",
    "VerificationRequest",
    "VerificationResult",
    "VerificationRunner",
    "VerifierBackend",
    "VerifierOperationalError",
    "VerifierRegistry",
    "VerifierRegistryError",
    "VerifierRunner",
    "verify_code_patch",
]

_EXPORTS = {
    "CheckResult": ("deepreason.verification.runner", "CheckResult"),
    "CodeVerificationResult": ("deepreason.verification.code", "CodeVerificationResult"),
    "Lean4Backend": ("deepreason.verification.lean", "Lean4Backend"),
    "LeanBackend": ("deepreason.verification.lean", "LeanBackend"),
    "SimulationBackend": ("deepreason.verification.simulation", "SimulationBackend"),
    "SimulationRequest": ("deepreason.verification.simulation", "SimulationRequest"),
    "SimulationVerificationResult": (
        "deepreason.verification.simulation",
        "SimulationVerificationResult",
    ),
    "TrustedCheckRunner": ("deepreason.verification.runner", "TrustedCheckRunner"),
    "UnknownVerifier": ("deepreason.verification.registry", "UnknownVerifier"),
    "VerificationRequest": ("deepreason.verification.models", "VerificationRequest"),
    "VerificationResult": ("deepreason.verification.models", "VerificationResult"),
    "VerificationRunner": ("deepreason.verification.runner", "VerificationRunner"),
    "VerifierBackend": ("deepreason.verification.models", "VerifierBackend"),
    "VerifierOperationalError": (
        "deepreason.verification.runner",
        "VerifierOperationalError",
    ),
    "VerifierRegistry": ("deepreason.verification.registry", "VerifierRegistry"),
    "VerifierRegistryError": (
        "deepreason.verification.registry",
        "VerifierRegistryError",
    ),
    "VerifierRunner": ("deepreason.verification.runner", "VerifierRunner"),
    "verify_code_patch": ("deepreason.verification.code", "verify_code_patch"),
}


def __getattr__(name: str):
    try:
        module_name, attribute = _EXPORTS[name]
    except KeyError as error:
        raise AttributeError(name) from error
    value = getattr(import_module(module_name), attribute)
    globals()[name] = value
    return value
