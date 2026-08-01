"""Formal workloads keep kernel proof and informal adequacy separate.

The Lean theorem ``T`` and the proposed formalization relation ``R`` are
ordinary, attackable artifacts.  A kernel pass says only that the pinned
theorem was accepted under its recorded assumptions.  It creates no attack,
support, or status edge for an informal claim.  The claim depends on ``T`` and
``R`` only when the workload explicitly requests those dependence refs.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from deepreason.canonical import canonical_json, sha256_hex
from deepreason.ontology import Budget, Commitment, Interface, Provenance, Ref
from deepreason.ontology.artifact import Artifact, RefRole
from deepreason.rules.warrants import register_fail_warrant
from deepreason.verification.models import VerificationRequest, VerificationResult

_DIGEST_PATTERN = r"^[0-9a-f]{64}$"
_EXACT_LEAN_ID = r"^lean4@[0-9]+\.[0-9]+\.[0-9]+(?:[-+][0-9A-Za-z.-]+)?$"


class _FormalModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid", frozen=True, populate_by_name=True, serialize_by_alias=True
    )

    def model_dump(self, *args, **kwargs):
        kwargs.setdefault("by_alias", True)
        return super().model_dump(*args, **kwargs)

    def model_dump_json(self, *args, **kwargs):
        kwargs.setdefault("by_alias", True)
        return super().model_dump_json(*args, **kwargs)


class PinnedLeanRequest(VerificationRequest):
    """Lean-only request whose safety-relevant fields are explicit and pinned."""

    backend: Literal["lean4"] = "lean4"
    toolchain_id: str = Field(pattern=_EXACT_LEAN_ID)
    source_ref: str = Field(pattern=_DIGEST_PATTERN)
    allow_sorry: Literal[False] = False
    target_theorems: list[str] = Field(min_length=1)


class FormalClaim(_FormalModel):
    schema_: Literal["deepreason-formal-claim-v1"] = Field(
        default="deepreason-formal-claim-v1", alias="schema"
    )
    statement: str = Field(min_length=1)
    context: tuple[str, ...] = ()

    @field_validator("statement", "context")
    @classmethod
    def _nonblank(cls, value):
        values = (value,) if isinstance(value, str) else value
        if any(not item.strip() for item in values):
            raise ValueError("formal claim text must be nonblank")
        return value


class AssumptionMapping(_FormalModel):
    informal_assumption: str = Field(min_length=1)
    formal_assumption: str = Field(min_length=1)
    relation: Literal["equivalent", "stronger", "weaker"]


class FormalMismatchTest(_FormalModel):
    """A proposed falsifier for R, not a verifier verdict by itself."""

    id: str = Field(min_length=1)
    case: str = Field(min_length=1)
    expected_informal: str = Field(min_length=1)
    expected_formal: str = Field(min_length=1)


class FormalizationRelation(_FormalModel):
    """Refutable claim that Lean theorem ``theorem`` formalizes an informal target."""

    schema_: Literal["deepreason-formalization-relation-v1"] = Field(
        default="deepreason-formalization-relation-v1", alias="schema"
    )
    informal_target: str = Field(min_length=1)
    theorem: str = Field(min_length=1)
    assumption_mapping: tuple[AssumptionMapping, ...] = ()
    omitted_conditions: tuple[str, ...] = ()
    scope: str = Field(min_length=1)
    counterconditions: tuple[str, ...] = Field(min_length=1)
    mismatch_tests: tuple[FormalMismatchTest, ...] = Field(min_length=1)

    @field_validator("omitted_conditions", "counterconditions")
    @classmethod
    def _nonblank_conditions(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if any(not item.strip() for item in value):
            raise ValueError("formalization conditions must be nonblank")
        return value

    @model_validator(mode="after")
    def _unique_mismatch_tests(self):
        ids = [test.id for test in self.mismatch_tests]
        if len(ids) != len(set(ids)):
            raise ValueError("formalization mismatch test ids must be unique")
        return self


class FormalWorkloadSpec(_FormalModel):
    schema_: Literal["deepreason-formal-workload-v1"] = Field(
        default="deepreason-formal-workload-v1", alias="schema"
    )
    claim: FormalClaim
    request: PinnedLeanRequest
    relation: FormalizationRelation
    explicit_formal_dependence: bool = False

    @model_validator(mode="after")
    def _coherent_relation(self):
        if self.relation.informal_target != self.claim.statement:
            raise ValueError("formalization relation must name the exact informal claim")
        if self.relation.theorem not in self.request.target_theorems:
            raise ValueError("formalization theorem must be a pinned verification target")
        return self


class FormalWorkflowError(RuntimeError):
    """Pinned inputs or verifier receipts were unavailable or inconsistent."""


@dataclass(frozen=True)
class FormalWorkflowArtifacts:
    theorem: Artifact
    relation: Artifact
    claim: Artifact
    receipt: Artifact | None = None
    criticism: Artifact | None = None


def _request_commitment(request: PinnedLeanRequest) -> Commitment:
    request_digest = sha256_hex(canonical_json(request.model_dump(mode="json")))
    return Commitment(
        id=f"lean-kernel:{request_digest}",
        eval="program:lean_kernel",
        budget=Budget(
            steps=request.max_heartbeats,
            time_ms=None,
            extra={
                "max_rec_depth": request.max_rec_depth,
                "toolchain_id": request.toolchain_id,
            },
        ),
    )


def _validate_receipt(
    harness,
    request: PinnedLeanRequest,
    result: VerificationResult,
) -> None:
    if result.backend != "lean4":
        raise FormalWorkflowError("verifier receipt is not from the Lean backend")
    if result.fingerprint.get("backend") != "lean4":
        raise FormalWorkflowError("verifier fingerprint is not for the Lean backend")
    if result.source_sha256 != request.source_ref:
        raise FormalWorkflowError("verifier receipt is for different source bytes")
    if result.fingerprint.get("toolchain_id") != request.toolchain_id:
        raise FormalWorkflowError("verifier receipt is for a different toolchain")
    fingerprint_sha256 = sha256_hex(canonical_json(result.fingerprint))
    if result.toolchain_sha256 != fingerprint_sha256:
        raise FormalWorkflowError("verifier fingerprint digest is inconsistent")
    if result.verdict in {"pass", "fail"} and not result.fingerprint.get("available"):
        raise FormalWorkflowError("verifier claimed a verdict while unavailable")
    if result.verdict == "pass" and set(result.theorems) != set(request.target_theorems):
        raise FormalWorkflowError("verifier pass does not cover every pinned target")
    if result.diagnostics_ref is not None:
        try:
            harness.blobs.get(result.diagnostics_ref)
        except KeyError as error:
            raise FormalWorkflowError("verifier diagnostics are unavailable") from error


def register_formal_workflow(
    harness,
    spec: FormalWorkloadSpec,
    *,
    result: VerificationResult | None = None,
) -> FormalWorkflowArtifacts:
    """Register theorem T, relation R, claim, and an optional verifier receipt.

    A valid ``fail`` receipt creates an ordinary demonstrative criticism of T.
    A ``pass`` receipt is recorded but creates no warrant or graph edge.  No
    branch writes status directly; normal attack/dependence adjudication is the
    only route by which the informal claim's status can change.
    """

    try:
        source = harness.blobs.get(spec.request.source_ref)
    except KeyError as error:
        raise FormalWorkflowError("pinned Lean source is unavailable") from error
    if sha256_hex(source) != spec.request.source_ref:
        raise FormalWorkflowError("pinned Lean source digest mismatch")

    commitment = _request_commitment(spec.request)
    harness.register_commitment(commitment)
    theorem = harness.create_artifact(
        source,
        codec="code:lean4",
        interface=Interface(commitments=[commitment.id]),
        provenance=Provenance(role="user"),
    )
    relation = harness.create_artifact(
        canonical_json(spec.relation.model_dump(mode="json")),
        codec="json",
        interface=Interface(refs=[Ref(target=theorem.id, role=RefRole.MENTION)]),
        provenance=Provenance(role="user"),
    )
    refs = []
    if spec.explicit_formal_dependence:
        refs = [
            Ref(target=theorem.id, role=RefRole.DEPENDENCE),
            Ref(target=relation.id, role=RefRole.DEPENDENCE),
        ]
    claim = harness.create_artifact(
        spec.claim.statement,
        interface=Interface(refs=refs),
        provenance=Provenance(role="user"),
    )

    receipt = None
    criticism = None
    if result is not None:
        _validate_receipt(harness, spec.request, result)
        receipt = harness.create_artifact(
            canonical_json(result.model_dump(mode="json")),
            codec="json",
            interface=Interface(refs=[Ref(target=theorem.id, role=RefRole.MENTION)]),
            provenance=Provenance(role="critic"),
        )
        if result.fail_warrant_eligible:
            trace_ref = result.diagnostics_ref or harness.blobs.put(
                canonical_json(result.model_dump(mode="json"))
            )
            criticism = register_fail_warrant(
                harness,
                commitment_id=commitment.id,
                target_id=theorem.id,
                nu_content=(
                    f"nu: pinned {spec.request.toolchain_id} kernel rejection of "
                    f"{commitment.id} on {theorem.id} is sound and relevant"
                ),
                critic_content=(
                    f"critic: pinned Lean kernel rejected theorem artifact "
                    f"{theorem.id[:12]}"
                ),
                trace_ref=trace_ref,
                skip_if_on_record=True,
            )
    return FormalWorkflowArtifacts(
        theorem=theorem,
        relation=relation,
        claim=claim,
        receipt=receipt,
        criticism=criticism,
    )
