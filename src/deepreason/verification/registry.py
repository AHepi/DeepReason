"""Deterministic verifier registry with fingerprint pinning."""

from __future__ import annotations

import copy
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from deepreason.canonical import canonical_json
from deepreason.ontology.frozen import FrozenDict
from deepreason.verification.models import VerificationResult, VerifierBackend


class VerifierRegistryError(ValueError):
    pass


class UnknownVerifier(VerifierRegistryError, KeyError):
    pass


@dataclass(frozen=True)
class VerifierRegistration:
    backend_id: str
    backend: VerifierBackend
    pinned_fingerprint: dict


class VerifierRegistry:
    """Resolve only trusted registered names; model output never routes tools."""

    def __init__(self, backends: Iterable[VerifierBackend] = ()) -> None:
        self._registrations: dict[str, VerifierRegistration] = {}
        for backend in backends:
            self.register(backend)

    def register(
        self,
        backend: VerifierBackend,
        *,
        backend_id: str | None = None,
    ) -> VerifierRegistration:
        if not hasattr(backend, "fingerprint") or not hasattr(backend, "verify"):
            raise TypeError("backend does not implement the verifier protocol")
        fingerprint = backend.fingerprint()
        resolved = backend_id or str(
            fingerprint.get("backend") or getattr(backend, "name", "")
        )
        if not resolved:
            raise VerifierRegistryError("backend fingerprint has no backend identifier")
        if resolved in self._registrations:
            raise VerifierRegistryError(f"verifier already registered: {resolved}")
        if fingerprint.get("backend") not in {None, resolved}:
            raise VerifierRegistryError("backend identifier disagrees with fingerprint")
        registration = VerifierRegistration(
            backend_id=resolved,
            backend=backend,
            pinned_fingerprint=FrozenDict(copy.deepcopy(fingerprint)),
        )
        self._registrations[resolved] = registration
        return registration

    def get(self, backend_id: str) -> VerifierRegistration:
        try:
            return self._registrations[backend_id]
        except KeyError as error:
            raise UnknownVerifier(f"unknown verifier: {backend_id}") from error

    resolve = get

    def ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._registrations))

    def names(self) -> tuple[str, ...]:
        return self.ids()

    def fingerprint(self, backend_id: str) -> dict[str, Any]:
        return self.get(backend_id).backend.fingerprint()

    def fingerprint_is_pinned(self, backend_id: str) -> bool:
        registration = self.get(backend_id)
        return canonical_json(registration.backend.fingerprint()) == canonical_json(
            registration.pinned_fingerprint
        )

    def verify(self, backend_id: str, request: Any, blobs: Any = None) -> VerificationResult:
        registration = self.get(backend_id)
        if not self.fingerprint_is_pinned(backend_id):
            raise VerifierRegistryError("verifier fingerprint changed after registration")
        if blobs is None:
            result = registration.backend.verify(request)
        else:
            result = registration.backend.verify(request, blobs)
        if result.backend != backend_id:
            raise VerifierRegistryError("verifier returned a different backend identifier")
        if canonical_json(result.fingerprint) != canonical_json(
            registration.pinned_fingerprint
        ):
            raise VerifierRegistryError("verifier result fingerprint is not pinned")
        return result
