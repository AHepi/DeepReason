"""Canonical records for amendment epochs (docs/proposals/AMENDMENT_EPOCHS.md).

An amendment reshapes the question and injects evidence after a typed
terminal stop without editing anything.  The run manifest, the run input,
and the evidence dossier of every earlier epoch keep their exact canonical
bytes forever; a ``run-amendment.v1`` record chains one new epoch behind a
declared event fence, exactly the way a bridge terminal chains a successor
answer behind its parent.
"""

from __future__ import annotations

from typing import ClassVar, Literal

from pydantic import ConfigDict, Field, StrictInt, field_validator, model_validator

from deepreason.canonical import canonical_json, sha256_hex
from deepreason.frozen import FrozenRecord


_DIGEST = r"^[0-9a-f]{64}$"


def _canonical_digest(domain: str, payload: dict) -> str:
    return sha256_hex(domain.encode("utf-8") + b"\x00" + canonical_json(payload))


class _AmendmentRecord(FrozenRecord):
    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        populate_by_name=True,
        serialize_by_alias=True,
    )


class RunAmendmentV1(_AmendmentRecord):
    """One typed in-root epoch: a superseding question and/or new evidence.

    ``fence_seq`` is the first ledger sequence that belongs to the successor
    epoch.  Events below it were produced under the parent manifest, run
    input, and dossier and are validated against those; events at or above it
    belong to this epoch.  The record names both manifests explicitly so
    replay can validate each side of the fence against its own authority
    without ever rewriting either document.

    An amendment supersedes the question and the evidence, never the routing,
    policy, or budget authority: the controller's process state is bound to
    one manifest digest for the life of a root, so the successor manifest is
    the parent copied verbatim and the two digests are equal.  The fields stay
    distinct because the fence, not the equality, is what makes replay
    piecewise.
    """

    schema_: Literal["run-amendment.v1"] = Field("run-amendment.v1", alias="schema")
    amendment_digest: str = Field(pattern=_DIGEST)
    seq: StrictInt = Field(ge=1)
    parent_amendment_digest: str | None = Field(default=None, pattern=_DIGEST)
    parent_manifest_digest: str = Field(pattern=_DIGEST)
    successor_manifest_digest: str = Field(pattern=_DIGEST)
    parent_run_input_digest: str = Field(pattern=_DIGEST)
    successor_run_input_digest: str = Field(pattern=_DIGEST)
    parent_dossier_digest: str = Field(pattern=_DIGEST)
    successor_dossier_digest: str = Field(pattern=_DIGEST)
    # Dossiers this amendment introduces.  Empty when the amendment only
    # reshapes the question: the successor epoch then cites exactly the
    # dossier its parent did.
    supplemental_dossier_digests: tuple[str, ...] = Field(default=(), max_length=64)
    superseded_problem_id: str | None = Field(default=None, min_length=1, max_length=512)
    problem_id: str | None = Field(default=None, min_length=1, max_length=512)
    fence_seq: StrictInt = Field(ge=0)
    created_at: str = Field(min_length=1, max_length=64)

    IDENTITY_DOMAIN: ClassVar[str] = "run-amendment.v1"

    @classmethod
    def create(cls, **values) -> "RunAmendmentV1":
        provisional = cls.model_construct(amendment_digest="0" * 64, **values)
        payload = provisional.model_dump(
            mode="json", by_alias=True, exclude={"amendment_digest"}
        )
        return cls(
            amendment_digest=_canonical_digest(cls.IDENTITY_DOMAIN, payload),
            **values,
        )

    def identity_payload(self) -> dict:
        return self.model_dump(
            mode="json", by_alias=True, exclude={"amendment_digest"}
        )

    @field_validator("supplemental_dossier_digests")
    @classmethod
    def _canonical_supplements(cls, value):
        if len(value) != len(set(value)):
            raise ValueError("supplemental dossier digests must be unique")
        return tuple(value)

    @model_validator(mode="after")
    def _identity_and_shape(self):
        if self.problem_id is None and not self.supplemental_dossier_digests:
            raise ValueError(
                "an amendment must reshape the question or admit new evidence"
            )
        if (self.superseded_problem_id is None) != (self.problem_id is None):
            raise ValueError(
                "question supersession names both the old and the new problem"
            )
        if self.superseded_problem_id == self.problem_id and self.problem_id is not None:
            raise ValueError("a reshaped question must be a different problem")
        if self.supplemental_dossier_digests:
            if self.successor_dossier_digest != self.supplemental_dossier_digests[-1]:
                raise ValueError(
                    "the successor epoch cites its newest supplemental dossier"
                )
        elif self.successor_dossier_digest != self.parent_dossier_digest:
            raise ValueError(
                "an amendment without new evidence keeps its parent's dossier"
            )
        if self.successor_run_input_digest == self.parent_run_input_digest:
            raise ValueError("a successor run input is a distinct document")
        if self.seq == 1 and self.parent_amendment_digest is not None:
            raise ValueError("the first amendment has no parent amendment")
        if self.seq > 1 and self.parent_amendment_digest is None:
            raise ValueError("a later amendment names its parent amendment")
        expected = _canonical_digest(self.IDENTITY_DOMAIN, self.identity_payload())
        if self.amendment_digest != expected:
            raise ValueError("amendment digest does not match its canonical payload")
        return self


__all__ = ["RunAmendmentV1"]
