"""Typed append-only record of which registered modules built a run.

A registry pins a module's fingerprint at registration and re-checks it on
every resolve, but that pinning lives only in the process: nothing in the
run's record says which module answered.  Cross-run comparison therefore
cannot distinguish two runs that differ only in the module that produced
them.  This payload closes that gap by carrying the resolved fingerprint
into the append-only log.

The payload holds identity only.  It carries no wall-clock and no counter,
so two runs built by the same modules stamp byte-identical payloads and any
difference between two stamps is a difference in the modules themselves.
"""

from __future__ import annotations

from typing import Any, Literal, Mapping

from pydantic import ConfigDict, Field, field_validator

from deepreason.canonical import canonical_json, sha256_hex
from deepreason.frozen import FrozenDict, FrozenList, FrozenRecord


class ModuleFingerprintV1(FrozenRecord):
    """One registered module's identity, as its own registry reports it.

    ``fingerprint`` is the mapping the module's own ``fingerprint()`` returns
    and ``fingerprint_sha256`` is sha256 over its canonical JSON, so a reader
    can compare two runs without reimplementing the module's notion of
    identity.  ``registry`` names the registry that resolved it, so further
    registries can be stamped later without a schema change.
    """

    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)

    registry: str = Field(min_length=1)
    module_id: str = Field(min_length=1)
    fingerprint: Mapping[str, Any] = Field(default_factory=FrozenDict)
    fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @field_validator("fingerprint", mode="after")
    @classmethod
    def _freeze_mapping(cls, value):
        return FrozenDict(value)

    @classmethod
    def of(cls, registry: str, module_id: str, fingerprint: Mapping[str, Any]):
        """Build the record from a fingerprint mapping, digesting it here so
        no call site can record a digest that disagrees with its own value."""

        return cls(
            registry=registry,
            module_id=module_id,
            fingerprint=fingerprint,
            fingerprint_sha256=sha256_hex(canonical_json(dict(fingerprint))),
        )


class ModuleFingerprintsEventPayloadV1(FrozenRecord):
    """Every registered module that built one run, in one event.

    ``digest`` is sha256 over the canonical JSON of the module list, giving a
    reader one value to compare across runs instead of a structural walk.
    """

    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)

    schema_: Literal["module-fingerprints.v1"] = Field(
        "module-fingerprints.v1", alias="schema"
    )
    modules: list[ModuleFingerprintV1] = Field(min_length=1)
    digest: str = Field(pattern=r"^[0-9a-f]{64}$")

    @field_validator("modules", mode="after")
    @classmethod
    def _freeze_sequence(cls, value):
        return FrozenList(value)

    @classmethod
    def of(cls, modules):
        """Build the payload, digesting the module list here for the same
        reason ``ModuleFingerprintV1.of`` digests its mapping."""

        modules = list(modules)
        payload = [
            module.model_dump(mode="json", by_alias=True) for module in modules
        ]
        return cls(modules=modules, digest=sha256_hex(canonical_json(payload)))


def recorded_module_fingerprints(harness):
    """Every module-fingerprint payload in a run's log, oldest first.

    Absence is the valid answer, not a failure: every root recorded before
    this payload existed carries none, and an event predating the field has
    no attribute to read.  Both are tolerated by construction here so no
    caller has to remember to tolerate them.
    """

    return tuple(
        payload
        for event in harness.log.read()
        if (payload := getattr(event, "module_fingerprints", None)) is not None
    )
