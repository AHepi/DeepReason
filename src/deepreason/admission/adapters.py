"""The §3a admission adapter contract: plugins that mint canonical authority.

Adapters convert non-text sources into normalized blocks.  Because their
output binds into dossier digests, the contract is strict: version-bound
identity, sandboxed execution (resource limits plus seccomp network
denial — purity is enforced, not attested), declared span fidelity gating
tier eligibility, and closed wire schemas in both directions.  First-party
adapters use this exact path; the interface's first consumer is the
project itself.
"""

from __future__ import annotations

import json
import subprocess
import sys
from importlib import metadata

from pydantic import BaseModel, ConfigDict, Field

ENTRY_POINT_GROUP = "deepreason.admission.adapters"
_ADAPTER_ID = r"^[a-z][a-z0-9._-]{0,63}$"
_MAX_RESULT_BYTES = 32 * 1024 * 1024
_SANDBOX_CPU_SECONDS = 60
_SANDBOX_MEMORY_BYTES = 1_024 * 1024 * 1024


class AdapterManifestV1(BaseModel):
    """Closed-schema declaration one adapter registers under the group."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_: str = Field("admission-adapter-manifest.v1", alias="schema")
    adapter_id: str = Field(pattern=_ADAPTER_ID)
    adapter_version: str = Field(min_length=1, max_length=64)
    # Media claimed by content signature (hex-encoded byte prefix), never
    # by extension.
    content_signatures: tuple[str, ...] = Field(min_length=1, max_length=16)
    media_type: str = Field(min_length=1, max_length=256)
    span_fidelity: str = Field(pattern=r"^(exact_spans|approximate|none)$")
    requires: str | None = Field(default=None, max_length=256)
    extra_hint: str = Field(min_length=1, max_length=256)
    entry: str = Field(min_length=1, max_length=256)

    def claims(self, data: bytes) -> bool:
        return any(
            data.startswith(bytes.fromhex(signature))
            for signature in self.content_signatures
        )

    def available(self) -> bool:
        if self.requires is None:
            return True
        try:
            __import__(self.requires)
        except Exception:  # noqa: BLE001 - availability probe only
            return False
        return True


class AdapterBlockWireV1(BaseModel):
    """One extracted unit crossing the sandbox boundary."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    text: str = Field(min_length=1, max_length=8_192)
    title: str | None = Field(default=None, min_length=1, max_length=256)


class AdapterResultWireV1(BaseModel):
    """The complete closed result an adapter host may emit."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_: str = Field("admission-adapter-result.v1", alias="schema")
    adapter_id: str = Field(pattern=_ADAPTER_ID)
    adapter_version: str = Field(min_length=1, max_length=64)
    blocks: tuple[AdapterBlockWireV1, ...] = Field(max_length=4_000)


class AdapterError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


def registered_adapters(
    *, injected: tuple[AdapterManifestV1, ...] = ()
) -> tuple[AdapterManifestV1, ...]:
    """Entry-point-registered adapters plus explicitly injected ones (tests)."""

    manifests: list[AdapterManifestV1] = list(injected)
    try:
        entry_points = metadata.entry_points(group=ENTRY_POINT_GROUP)
    except Exception:  # noqa: BLE001 - registry probing is best-effort
        entry_points = ()
    for entry_point in entry_points:
        try:
            candidate = entry_point.load()
        except Exception:  # noqa: BLE001 - a broken plugin never crashes admit
            continue
        if isinstance(candidate, AdapterManifestV1):
            manifests.append(candidate)
    unique: dict[str, AdapterManifestV1] = {}
    for manifest in manifests:
        unique.setdefault(manifest.adapter_id, manifest)
    return tuple(unique.values())


def adapter_for(
    data: bytes, *, injected: tuple[AdapterManifestV1, ...] = ()
) -> AdapterManifestV1 | None:
    for manifest in registered_adapters(injected=injected):
        if manifest.claims(data):
            return manifest
    return None


def sandbox_available() -> bool:
    from deepreason.verification._sandbox import seccomp_available

    return seccomp_available()


def run_adapter(
    manifest: AdapterManifestV1,
    data: bytes,
    *,
    timeout_seconds: int = _SANDBOX_CPU_SECONDS * 2,
) -> AdapterResultWireV1:
    """Execute one adapter under the containment wrapper, bytes in, JSON out.

    The child process is the adapter host module inside the existing
    sandbox wrapper: CPU and memory rlimits apply and every network
    syscall is denied before the host imports anything.  A sandbox that
    cannot be established is a typed refusal — never a bare subprocess.
    """

    if not manifest.available():
        raise AdapterError(
            "ADMISSION_ADAPTER_DEPENDENCY_MISSING",
            f"adapter {manifest.adapter_id} requires {manifest.requires}; "
            f"install {manifest.extra_hint}",
        )
    if not sandbox_available():
        raise AdapterError(
            "ADMISSION_ADAPTER_SANDBOX_UNAVAILABLE",
            "adapter purity is enforced by the sandbox and no sandbox is "
            "available on this platform",
        )
    command = [
        sys.executable,
        "-m",
        "deepreason.verification._sandbox",
        "--cpu-seconds",
        str(_SANDBOX_CPU_SECONDS),
        "--memory-bytes",
        str(_SANDBOX_MEMORY_BYTES),
        "--",
        sys.executable,
        "-m",
        "deepreason.admission.adapter_host",
        manifest.entry,
    ]
    try:
        completed = subprocess.run(
            command,
            input=data,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        raise AdapterError(
            "ADMISSION_ADAPTER_TIMEOUT",
            f"adapter {manifest.adapter_id} exceeded {timeout_seconds}s",
        ) from error
    if completed.returncode != 0 or not completed.stdout:
        detail = completed.stderr.decode("utf-8", errors="replace")[:500]
        raise AdapterError(
            "ADMISSION_ADAPTER_FAILED",
            f"adapter {manifest.adapter_id} did not complete: {detail}",
        )
    if len(completed.stdout) > _MAX_RESULT_BYTES:
        raise AdapterError(
            "ADMISSION_ADAPTER_RESULT_TOO_LARGE",
            f"adapter {manifest.adapter_id} exceeded the result ceiling",
        )
    try:
        result = AdapterResultWireV1.model_validate(json.loads(completed.stdout))
    except ValueError as error:
        raise AdapterError(
            "ADMISSION_ADAPTER_RESULT_INVALID",
            f"adapter {manifest.adapter_id} returned an invalid result",
        ) from error
    if (
        result.adapter_id != manifest.adapter_id
        or result.adapter_version != manifest.adapter_version
    ):
        raise AdapterError(
            "ADMISSION_ADAPTER_IDENTITY_MISMATCH",
            "adapter result identity differs from its registered manifest",
        )
    return result
