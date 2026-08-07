"""Typed append-only record of which provider/model sat in which seat.

A `--seat` binding names a provider profile at `deepreason setup` time, and
`resolve_seat_bindings`/`resolve_seat_bindings_by_group` expand it into
routes at manifest-compile time, but that resolution lives only in the
files it touches: nothing in the run's own record says which model
actually sat in which role group. This payload closes that gap by
carrying the resolved group -> provider/model/profile-digest identity
into the append-only log.

The payload holds identity only. It carries no wall-clock and no counter,
so two runs bound to the same profiles stamp byte-identical payloads and
any difference between two stamps is a difference in the bindings
themselves.
"""

from __future__ import annotations

from typing import Literal

from pydantic import ConfigDict, Field

from deepreason.canonical import canonical_json, sha256_hex
from deepreason.frozen import FrozenList, FrozenRecord


class SeatBindingV1(FrozenRecord):
    """One role group's bound provider/model identity.

    Identity only, mirroring ``ModuleFingerprintV1``'s own shape: no
    wall-clock, no counter. Unlike a module fingerprint, a seat binding is
    already its own four scalar fields rather than an opaque mapping, so it
    needs no per-entry digest of its own -- the payload's single top-level
    ``digest`` covers the whole list.
    """

    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)

    group: str = Field(min_length=1)
    provider: str = Field(min_length=1)
    model_id: str = Field(min_length=1)
    profile_digest: str = Field(min_length=1)

    @classmethod
    def of(cls, group: str, profile) -> "SeatBindingV1":
        """Build the record from a resolved provider profile."""

        return cls(
            group=group,
            provider=profile.provider,
            model_id=profile.model_id,
            profile_digest=profile.profile_digest,
        )


class SeatBindingsEventPayloadV1(FrozenRecord):
    """Every bound role group's provider/model identity, in one event.

    ``digest`` is sha256 over the canonical JSON of the binding list,
    giving a reader one value to compare across runs instead of a
    structural walk.
    """

    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)

    schema_: Literal["seat-bindings.v1"] = Field("seat-bindings.v1", alias="schema")
    bindings: list[SeatBindingV1] = Field(min_length=1)
    digest: str = Field(pattern=r"^[0-9a-f]{64}$")

    @classmethod
    def of(cls, bindings) -> "SeatBindingsEventPayloadV1":
        """Build the payload, digesting the sorted binding list here for the
        same reason ``ModuleFingerprintsEventPayloadV1.of`` digests its own
        module list."""

        bindings = sorted(bindings, key=lambda binding: binding.group)
        payload = [
            binding.model_dump(mode="json", by_alias=True) for binding in bindings
        ]
        return cls(
            bindings=FrozenList(bindings), digest=sha256_hex(canonical_json(payload))
        )


def recorded_seat_bindings(harness) -> tuple[SeatBindingsEventPayloadV1, ...]:
    """Every seat-bindings payload in a run's log, oldest first.

    Absence is the valid answer, not a failure: every root recorded before
    this payload existed carries none, and an event predating the field has
    no attribute to read. Returns every stamp found -- never a single
    unpack -- because a continuation may legitimately carry more than one.
    """

    return tuple(
        payload
        for event in harness.log.read()
        if (payload := getattr(event, "seat_bindings", None)) is not None
    )
