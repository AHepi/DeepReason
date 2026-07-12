"""Small deterministic registry for mechanical verifier backends."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from deepreason.verification.models import VerificationResult, VerifierBackend


class VerifierRegistry:
    """Resolve declared backends by exact name; no model-controlled routing."""

    def __init__(self, backends: Iterable[VerifierBackend] = ()) -> None:
        self._backends: dict[str, VerifierBackend] = {}
        for backend in backends:
            self.register(backend)

    def register(self, backend: VerifierBackend) -> None:
        if not isinstance(backend, VerifierBackend):
            raise TypeError("backend does not implement the verifier protocol")
        if backend.name in self._backends:
            raise ValueError(f"verifier backend already registered: {backend.name}")
        self._backends[backend.name] = backend

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._backends))

    def fingerprint(self, name: str) -> dict[str, Any]:
        return self._resolve(name).fingerprint()

    def verify(self, name: str, request: Any, blobs: Any = None) -> VerificationResult:
        return self._resolve(name).verify(request, blobs)

    def _resolve(self, name: str) -> VerifierBackend:
        try:
            return self._backends[name]
        except KeyError as error:
            raise KeyError(f"unknown verifier backend: {name}") from error
