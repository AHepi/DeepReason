"""The closed discriminated union of claim bodies.

CLOSED is the requirement, not a style: an open ``RelationClaim(predicate:
str)`` would let arbitrary prose predicates become quasi-ontology, and every
one of them would then need its own interaction with ``att``, ``dep``, replay
and status re-proven. The set of schema NAMES is closed here; a body is
implemented only where this rung has a producer for it.

Declared-and-unimplemented is deliberate and typed. Shipping body models with
no producers is the pattern `docs/ERRATA.md` E28 records — a mechanism nobody
triggers — so `decode` refuses a declared-but-unbuilt schema with a reason
rather than accepting it into a shape nothing can create.
"""

from __future__ import annotations

import json
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

# The closed name set. Adding a name here is an ontology change and belongs in
# the rung that supplies its producer, never in a convenience commit.
CLAIM_SCHEMAS: tuple[str, ...] = (
    "poietic.problem-subject.v1",
    "poietic.premise-attribution.v1",
    "poietic.derivation-manifest.v1",
    "poietic.reach-certificate.v1",
    "poietic.frame-assertion.v1",
    "poietic.problem-retirement.v1",
    "poietic.problem-translation.v1",
    "poietic.localization.v1",
    "poietic.succession.v1",
)

PROBLEM_SUBJECT_V1 = "poietic.problem-subject.v1"
DERIVATION_MANIFEST_V1 = "poietic.derivation-manifest.v1"
PREMISE_ATTRIBUTION_V1 = "poietic.premise-attribution.v1"
FRAME_ASSERTION_V1 = "poietic.frame-assertion.v1"
REACH_CERTIFICATE_V1 = "poietic.reach-certificate.v1"

# The names with a producer. The rest are declared above and refused below,
# with their names on the record so a reader sees the intended shape of the
# substrate rather than only the built part of it.
_IMPLEMENTED: tuple[str, ...] = (
    PROBLEM_SUBJECT_V1, PREMISE_ATTRIBUTION_V1, FRAME_ASSERTION_V1,
    DERIVATION_MANIFEST_V1, REACH_CERTIFICATE_V1,
)


class ClaimDecodeError(ValueError):
    """A typed decode refusal. Carries `code` so callers branch on a value
    rather than on message text."""

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


class _Body(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class _Part(BaseModel):
    """A body's internal part. Not a claim: it carries no `schema` name and
    cannot be decoded on its own, so it never widens the closed set."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class KernelCheckV1(_Part):
    """One deterministic check a judgment rests on, and where to re-run it.

    `recorded_verdict` is what the judgment's author observed. It is kept for
    the record and is NEVER what a reader is told: `proof_debt.receipt` re-runs
    `program` against `target_ref` and reports the current verdict, because a
    recorded verdict that has stopped being true is the failure mode the whole
    receipt exists to catch. An empty `program` means the check is not
    re-runnable here, and the receipt says so rather than silently trusting it.
    """

    name: str
    program: str = ""
    target_ref: str = ""
    recorded_verdict: str = ""


class ProblemSubjectV1(_Body):
    """The companion artifact that makes a problem criticisable.

    Every field except `schema` is COPIED from the immutable `Problem` record,
    and recognition re-checks each copy against it. That is what stops a
    companion drifting from the problem it speaks for, which would leave
    criticism landing on a stale statement of the question.
    """

    schema_: Literal["poietic.problem-subject.v1"] = Field(
        default=PROBLEM_SUBJECT_V1, alias="schema"
    )
    problem_id: str
    description: str
    criteria: list[str] = Field(default_factory=list)
    trigger: str
    sources: list[str] = Field(default_factory=list)


class PremiseAttributionV1(_Body):
    """"This problem presupposes X."

    Three endpoints and NOT ONE of them names its own ref role — the compiler
    assigns those. The premise is MENTIONED, never depended on: an attribution
    that depended on its premise would be suspended by pass two at the exact
    moment the premise fell, erasing the relation needed to identify the orphan.
    """

    schema_: Literal["poietic.premise-attribution.v1"] = Field(
        default=PREMISE_ATTRIBUTION_V1, alias="schema"
    )
    problem_subject_ref: str
    premise_ref: str
    derivation_manifest_ref: str | None = None
    # The admitted-citation record this attribution rests on, when it cites
    # evidence at all. Optional because a run with no dossier bound has nothing
    # to cite and the all-configurations law forbids refusing it (R62).
    citation_ref: str | None = None


class FrameAssertionV1(_Body):
    """Def 9.2's frame claim: <subject b, scope sigma, validity v, departure>.

    An ORDINARY artifact carrying this body. There is no `kind` field and no
    event rule of its own, because the two axes are separated by EDGE ROLE
    rather than by a node type -- a frame layer with its own graph would need
    its interactions with att, dep, replay and status re-proven from scratch.

    Like every body here, not one field names its own ref role: the compiler
    assigns MENTION to the subject (Law 9.4) and DEPENDENCE to each reach
    record cited as the case, and that assignment is the whole separation.
    """

    schema_: Literal["poietic.frame-assertion.v1"] = Field(
        default=FRAME_ASSERTION_V1, alias="schema"
    )
    subject_ref: str
    # A `declarative-scope.v1` document (`calculus/scope.py`). Carried as data
    # rather than as a compiled object because it is artifact CONTENT: the
    # content address that names the assertion is taken over these bytes.
    scope: dict[str, Any]
    validity: Literal["universal", "bounded"] = "universal"
    validity_domain: str | None = None
    validity_tolerance: str | None = None
    departure_protocol: str
    reach_case_refs: list[str] = Field(default_factory=list)
    succeeded_wound_refs: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _bounded_is_content(self):
        """C3: instrument standing is not a third value. It is a consulted
        assertion whose validity reads `bounded`, and a bounded grant without
        its declared domain and tolerance would be an unqualified one wearing
        the word -- the tolerance is what a successor authors and attacks."""
        declared = self.validity_domain is not None and self.validity_tolerance is not None
        if (self.validity == "bounded") != declared:
            raise ValueError(
                "bounded validity requires both a domain and a tolerance, "
                "and universal validity permits neither"
            )
        if self.subject_ref in self.reach_case_refs:
            # A case that IS the subject is a dependence on the subject under
            # another name, which is exactly what Law 9.4 forbids.
            raise ValueError("a reach case may not be the subject itself")
        return self


class DerivationManifestV1(_Body):
    """The itemized bill a derived judgment rests on (E-1).

    Three kinds, and they differ in what a critic can DO about them, which is
    why they are three fields and not one list. `kernel_checks` are re-derived,
    so arguing with one means changing its input. `open_certificate_refs` are
    registered artifacts the judgment leans on but has not proved -- the
    compiler makes each a DEPENDENCE, which is what puts them inside
    `edges.py`'s evidence lineage and makes them the attackable half.
    `axiom_debt` names what is assumed and left unproved; an axiom has no
    attack surface by construction, so naming it IS the deliverable.

    The subject is a MENTION, never a dependence: a manifest that fell with its
    own subject would be unreadable at exactly the moment someone wanted the
    bill of materials.
    """

    schema_: Literal["poietic.derivation-manifest.v1"] = Field(
        default=DERIVATION_MANIFEST_V1, alias="schema"
    )
    subject_ref: str
    kernel_checks: list[KernelCheckV1] = Field(default_factory=list)
    open_certificate_refs: list[str] = Field(default_factory=list)
    axiom_debt: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _the_subject_is_not_its_own_certificate(self):
        """A certificate that IS the subject is a dependence on the subject
        under another name, which is what the mention law forbids here for the
        same reason it forbids it for a frame assertion."""
        if self.subject_ref in self.open_certificate_refs:
            raise ValueError("an open certificate may not be the subject itself")
        return self


class FrozenProblemV1(_Part):
    """A problem record as it stood at nomination.

    COPIED, never referenced: a criterion that read the live `Problem` would be
    reading graph state that can grow between nomination and evaluation, and
    two evaluations of one candidate could then disagree. `sources` and
    `lineage_root` travel with it so a reader can re-derive the span without
    the harness.
    """

    id: str
    description: str
    trigger: str
    sources: list[str] = Field(default_factory=list)
    criteria: list[str] = Field(default_factory=list)
    lineage_root: str = ""


class FrozenCommitmentV1(_Part):
    """A criterion's spec, frozen whole so a criterion program can re-evaluate
    it against a candidate without resolving anything through the harness.

    NO budget is carried. An earlier draft froze `Budget.steps`/`time_ms` here,
    and `DR-SEAM-evaluation-x-ontology` is why it does not: both are read by
    nothing in the tree, because neither is part of any spec digest, and a
    criterion's real bound lives in `extra["spec"]`. Freezing a number no
    consumer reads would put a second, authoritative-looking bound on the
    record beside the one that actually governs.
    """

    id: str
    eval: str
    observation_valued: bool = False


class FrozenSubjectV1(_Part):
    """One candidate subject as the record held it at nomination.

    This is the frozen candidate POOL, and its boundary is deliberate: a
    subject conjectured after nomination is absent, and a criterion asked about
    it answers `overrun` -- unobtainable -- rather than guessing. The
    alternative, reading the live graph, is what Rider 5 clause (4) forbids.

    `demarcation` carries §12.2's reading, and its three values are not a
    scale. `no-attack-surface` is a SETTLED failure -- `crit` is false, the
    interface declares nothing that could count against the subject, and no
    sample is needed to know it (Rung 2's rule, transferred). `declared-only`
    is the TYPED ABSTENTION: `crit` holds and the `load` half was never taken,
    because it needs the variator seat and one provider call per subject and
    nomination has no seat. `load-bearing` is both halves. A criterion reading
    the middle value answers `overrun`, never `fail`: "we could not check" must
    never look like "we checked and it was fine".
    """

    artifact_id: str
    registered_seq: int = 0
    commitments: list[str] = Field(default_factory=list)
    demarcation: Literal[
        "load-bearing", "declared-only", "no-attack-surface"
    ] = "declared-only"
    hv: float | None = None
    accounted: list[str] = Field(default_factory=list)
    wound_refs: list[str] = Field(default_factory=list)
    # The commitments registered criticism actually cites. Separate from
    # `wound_refs` because non-immunization asks a different question of them:
    # a wound identifies WHERE the subject was hurt, and a component nothing
    # cites is a component whose removal costs the record nothing.
    criticised_commitments: list[str] = Field(default_factory=list)


class ReachRecordV1(_Part):
    """One reach hit, with the LOG's own ordering attached.

    `subject_seq < measure_seq` is what reach-integrity checks, and it is the
    only novel-fact evidence the informal side can produce (§10.5): the log
    timestamps prove the artifact predates what it went on to survive.
    """

    problem_id: str
    lineage_root: str
    measure_seq: int
    subject_seq: int
    reveal_seq: int | None = None


class FrozenGrantV1(_Part):
    """A consulted frame assertion at nomination -- an incumbent's claim on a
    region of problem space, which is what a rival must not silently share."""

    assertion_id: str
    subject_ref: str
    scope: dict[str, Any] = Field(default_factory=dict)


class ReachCertificateV1(_Body):
    """The frozen, fence-stamped input every promotion criterion reads.

    Rider 5 clause (4): "programs consume frozen fence-stamped input artifacts
    ... never live graph state". This is that artifact. It is built ONCE, by
    nomination, from a pure fold over the log, and registered as an ordinary
    content-addressed artifact -- so "your certificate is wrong" has somewhere
    to land, which a reading that lived only inside a program would not.

    The subject is a MENTION and the certificate depends on NOTHING (compiler
    rule). A dependence would suspend the frozen input at exactly the moment a
    criterion needed to read it, and a certificate is a reading of the record
    rather than a claim resting on artifacts.
    """

    schema_: Literal["poietic.reach-certificate.v1"] = Field(
        default=REACH_CERTIFICATE_V1, alias="schema"
    )
    subject_ref: str
    scope: dict[str, Any]
    k_frame: int
    reach_records: list[ReachRecordV1] = Field(default_factory=list)
    problems: list[FrozenProblemV1] = Field(default_factory=list)
    commitments: list[FrozenCommitmentV1] = Field(default_factory=list)
    subjects: list[FrozenSubjectV1] = Field(default_factory=list)
    consulted: list[FrozenGrantV1] = Field(default_factory=list)
    # What the environment cap dropped. Present and empty rather than absent
    # when nothing was dropped: a silent cap reads as full coverage.
    truncated: list[str] = Field(default_factory=list)


_MODELS: dict[str, type[_Body]] = {
    PROBLEM_SUBJECT_V1: ProblemSubjectV1,
    PREMISE_ATTRIBUTION_V1: PremiseAttributionV1,
    FRAME_ASSERTION_V1: FrameAssertionV1,
    DERIVATION_MANIFEST_V1: DerivationManifestV1,
    REACH_CERTIFICATE_V1: ReachCertificateV1,
}


def encode(body: _Body) -> str:
    """Canonical JSON for a claim body: sorted keys, aliases, no nulls.

    Canonical because the artifact id is a content address over it — two
    encodings of one claim would be two artifacts, and idempotent registration
    would stop being idempotent.
    """
    payload = body.model_dump(mode="json", by_alias=True, exclude_none=True)
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def decode(text: str) -> _Body:
    """Parse a claim body, or refuse with a typed code."""
    try:
        payload = json.loads(text)
    except Exception as error:  # noqa: BLE001 - unparseable content is a refusal
        raise ClaimDecodeError("claim-not-json", str(error)) from None
    if not isinstance(payload, dict):
        raise ClaimDecodeError("claim-not-an-object", type(payload).__name__)
    schema = payload.get("schema")
    if schema not in CLAIM_SCHEMAS:
        raise ClaimDecodeError("claim-schema-unknown", repr(schema))
    if schema not in _IMPLEMENTED:
        raise ClaimDecodeError(
            "claim-schema-not-implemented",
            f"{schema} is declared in the closed set but has no producer yet",
        )
    try:
        return _MODELS[schema].model_validate(payload)
    except Exception as error:  # noqa: BLE001
        raise ClaimDecodeError("claim-body-invalid", str(error)) from None
