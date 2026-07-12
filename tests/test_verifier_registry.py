from __future__ import annotations

from dataclasses import dataclass

import pytest

from deepreason import programs
from deepreason.verification.models import VerificationRequest, VerificationResult
from deepreason.verification.registry import (
    UnknownVerifier,
    VerifierRegistry,
    VerifierRegistryError,
)
from deepreason.verification.runner import VerificationRunner, VerifierOperationalError

_DIGEST = "a" * 64


@dataclass
class FakeBackend:
    revision: int = 1

    def fingerprint(self) -> dict:
        return {"backend": "fake", "revision": self.revision}

    def verify(self, request: VerificationRequest) -> VerificationResult:
        return VerificationResult(
            backend="fake",
            fingerprint=self.fingerprint(),
            verdict="pass",
            diagnostics_ref=_DIGEST,
            axioms_ref=_DIGEST,
            theorems=[],
            source_sha256=request.source_ref,
            toolchain_sha256=_DIGEST,
        )


def _request() -> VerificationRequest:
    return VerificationRequest(
        backend="fake",
        toolchain_id="lean4@4.19.0",
        source_ref=_DIGEST,
    )


def test_program_registry_values_carry_metadata_without_losing_callability():
    spec = programs.PROGRAMS["json-wf"]
    assert isinstance(spec, programs.ProgramSpec)
    assert spec.name == "json-wf"
    assert spec.class_ == "structural"
    assert spec("{}", None)[0] == programs.PASS

    for name in ("lean_parse", "lean_no_sorry", "lean_axiom_policy", "lean_kernel"):
        formal = programs.PROGRAMS[name]
        assert formal.class_ == "formal"
        assert formal.external_toolchain == "lean4"


def test_registry_pins_fingerprint_and_runner_checks_backend_contract():
    backend = FakeBackend()
    registry = VerifierRegistry()
    registration = registry.register(backend)
    assert registration.backend_id == "fake"
    assert registry.ids() == ("fake",)
    with pytest.raises(TypeError):
        registration.pinned_fingerprint["revision"] = 99
    assert VerificationRunner(registry).verify(_request()).verdict == "pass"

    backend.revision = 2
    assert not registry.fingerprint_is_pinned("fake")
    with pytest.raises(VerifierOperationalError, match="fingerprint changed"):
        VerificationRunner(registry).verify(_request())


def test_registry_rejects_duplicates_and_unknown_backends():
    registry = VerifierRegistry()
    registry.register(FakeBackend())
    with pytest.raises(VerifierRegistryError, match="already registered"):
        registry.register(FakeBackend())
    with pytest.raises(UnknownVerifier):
        registry.get("missing")


def test_request_rejects_unresolved_lean_toolchain_sentinels():
    with pytest.raises(ValueError, match="exact resolved coordinate"):
        VerificationRequest(
            backend="lean4",
            toolchain_id="lean4@4.x",
            source_ref=_DIGEST,
        )


def test_overrun_is_never_fail_warrant_eligible():
    result = VerificationResult(
        backend="lean4",
        fingerprint={"available": False},
        verdict="overrun",
        diagnostics_ref=_DIGEST,
        axioms_ref=_DIGEST,
        source_sha256=_DIGEST,
        toolchain_sha256=_DIGEST,
    )
    assert not result.fail_warrant_eligible
