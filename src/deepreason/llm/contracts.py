"""Role output contracts (spec §9) — Pydantic models; the JSON schema shown
to the model is derived via model_json_schema().

The conjecturer contract is Verbalized Sampling (§11.6): a candidate
distribution with stated typicality estimates, never a single point.
"""

import json
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CandidateRef(BaseModel):
    target: str
    role: Literal["dependence", "mention"] = "dependence"


def discharge_kind_enum() -> list[str]:
    """The legal discharge kinds, read LIVE from the declaration registry.

    A literal here would make a declared kind legal in Python and invisible on
    the wire, which is worse than not declaring it: the model can only act on
    what the schema offers. Imported lazily -- `deepreason.discharge` is a
    consumer-facing interface and a module-level import would invert the
    dependency this file's own seam document states.
    """
    from deepreason.discharge import discharge_kind_names

    return list(discharge_kind_names())


class DischargeWireV1(BaseModel):
    """One criticism, answered (REBUILD F1).

    `handle` is the criticism's handle exactly as the pack listed it, and it is
    left a PLAIN STRING on purpose: its legal set has one authority --
    `deepreason.discharge.open_criticisms` -- and leaving the field open is what
    lets a menu renderer key on it by registering, without either side learning
    the other's subsystem. A private enum here would close that seam.

    NOTHING here is evidence. A discharge is a precondition on SUBMISSION; no
    field, kind or count may feed a label, a warrant, a rank or an admission
    decision (`DR-CON-discharge-channel`, the law line).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    handle: str = Field(min_length=1, max_length=256)
    kind: str = Field(min_length=1, json_schema_extra=lambda s: s.update(enum=discharge_kind_enum()))
    note: str = ""
    where: str | None = None


class EvidenceRefClaimV1(BaseModel):
    """One claimed grounding in an admitted dossier block (admission §4).

    ``block`` names a dossier block by id or by a unique hex prefix of at
    least 12 characters. ``quote``, when present, must reproduce a
    contiguous byte span of the block's canonical text exactly — the
    citation checker byte-verifies it and a mismatch is a durable finding,
    never a silent pass.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    block: str = Field(pattern=r"^[0-9a-f]{12,64}$")
    quote: str | None = Field(default=None, min_length=1, max_length=2_000)


class QuotedEvidenceRefV1(BaseModel):
    """A citation that cannot be made without reproducing the bytes.

    A SUBTYPE, not a stricter `EvidenceRefClaimV1`: the old contract's optional
    quote is load-bearing for the conjecturer channel that already ships, and
    tightening it globally would retroactively refuse citations that were legal
    when they were recorded. The calculus claim channel is new and can be born
    with the stronger rule (R62), so the requirement lives in the type rather
    than in a prompt asking nicely.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    block: str = Field(pattern=r"^[0-9a-f]{12,64}$")
    quote: str = Field(min_length=1, max_length=2_000)


class ConjectureCandidate(BaseModel):
    content: str
    # Stated probability/typicality estimate for this candidate (§11.6).
    typicality: float = Field(ge=0.0, le=1.0)
    # Born-connected (§7 L1): refs to neighbourhood artifacts where natural.
    refs: list[CandidateRef] = Field(default_factory=list)
    # Claimed groundings in admitted evidence blocks (admission §4); checked
    # deterministically after admission, never trusted on arrival.
    evidence_refs: list[EvidenceRefClaimV1] = Field(default_factory=list, max_length=8)

    @field_validator("content", mode="before")
    @classmethod
    def _coerce_object_content(cls, value):
        # Models asked for skeleton content often emit the skeleton as a JSON
        # object instead of an embedded string — accept it canonically.
        if isinstance(value, (dict, list)):
            return json.dumps(value, sort_keys=True)
        return value


class ConjecturerOutput(BaseModel):
    candidates: list[ConjectureCandidate] = Field(min_length=1)


class ArgumentativeCriticOutput(BaseModel):
    attack: bool
    case: str = ""  # the argument; becomes the critic artifact's content
    # Grounded recourse against an execution-backed target: a JSON list of
    # positional args for the target's entry point. The harness RUNS the
    # target on it and checks the declared property (oracle.py) — a violated
    # property becomes a DEMONSTRATIVE refutation; an invalid or passing
    # counterexample grounds nothing.
    counterexample: list | None = None
    # A presupposition of the PROBLEM that forbids nothing — filed only when
    # the pack carried the invitation, and never a substitute for the case
    # against the target. It becomes an ordinary premise artifact plus an
    # ordinary attribution artifact (premises.py), both attackable; the
    # harness reads the artifact's attack surface, so a presupposition with
    # nothing to forbid is what this field can honestly report.
    premise: str | None = None
    # Citations grounding that presupposition, each one quoted (R62). Optional
    # and absent-legal, exactly like `premise` and `counterexample` beside it: a
    # solo run with no dossier bound has nothing to quote, and the
    # all-configurations law forbids refusing it. What is impossible is an
    # UNQUOTED entry. None rather than [] so an uncited case canonicalises to
    # the same bytes it always did under `exclude_none`.
    premise_evidence: list[QuotedEvidenceRefV1] | None = Field(
        default=None, max_length=2
    )
    # A question the critic proposes should be asked NEXT, in its own words.
    # Optional and absent-legal like `premise` beside it, and additionally
    # UNREADABLE by anything that decides: no rank, admission or acceptance
    # path may consult it, so filling it earns nothing and leaving it empty
    # costs nothing (operator law, 2026-08-29; the absence is pinned by
    # tests/test_successor_law_line.py). None rather than "" so an unfilled
    # field canonicalises to the same bytes it always did under
    # `exclude_none`.
    successor_question: str | None = None


class BatchCase(BaseModel):
    """One target's entry in a batched criticism pass (§14 batching): the
    CALL is shared across targets, the case never is — each attacking entry
    becomes an ordinary per-target argumentative warrant with its own nu."""

    target: str  # must be an id listed in the pack; others are dropped
    attack: bool
    case: str = ""
    counterexample: list | None = None  # same semantics as the single contract
    premise: str | None = None          # same semantics as the single contract
    premise_evidence: list[QuotedEvidenceRefV1] | None = Field(
        default=None, max_length=2
    )
    successor_question: str | None = None  # same semantics as the single contract


class BatchCriticOutput(BaseModel):
    cases: list[BatchCase] = Field(default_factory=list)


class ExperimenterOutput(BaseModel):
    """Experiment designs (rules/experiment.py): each entry is the SOURCE of
    ``def gen(k)`` — a pure function from an index to one input for the
    property oracle in the pack. Adjudicated mechanically by generator_wf
    (compile, yield, novelty); a generator that designs no new experiment is
    refuted on arrival."""

    generators: list[str] = Field(min_length=1)


class VisionCriticOutput(BaseModel):
    """Visual judgment of RENDERED screenshots (rules/vision.py): attack=true
    with a concrete, visible fault tied to what the problem demands, or
    attack=false. screenshot_index names which provided image shows the
    fault (0-based; null when the fault spans all of them)."""

    attack: bool
    case: str = ""
    screenshot_index: int | None = None


class PropertyProposal(BaseModel):
    """One conjectured correctness property: ``claim`` states in one sentence
    what requirement of the PROBLEM STATEMENT the checker encodes (the
    relevance trial arbitrates exactly this claim); ``checker`` is the full
    source of ``def check(inp, out)``."""

    claim: str = Field(min_length=1)
    checker: str = Field(min_length=1)


class PropertyDesignerOutput(BaseModel):
    properties: list[PropertyProposal] = Field(min_length=1)


class EncoderTestCase(BaseModel):
    """One fixed {in, out} test pair. A bare ``dict`` cannot be an LLM-facing
    field here: the wire-contract firewall (``llm/wire.py::_reject_unknown_fields``)
    rejects every key inside an object whose schema declares no
    ``properties`` — exactly what an untyped ``dict`` produces."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    in_: list = Field(alias="in")
    out: Any = None


class EncoderOutput(BaseModel):
    """Commitment CODE for an ALREADY-ADMITTED conjecture's own prose (Item
    7, R38): ``source``/``entry``/``tests`` feed directly into the SAME
    ``checker_spec`` shape ``ForbiddenCase``/``Countercondition`` already
    carry (D2 rev 2) — the encoder never conjectures, it only authors the
    criticizable surface for a claim someone else already made."""

    source: str = Field(min_length=1)
    entry: str = Field(min_length=1)
    tests: list[EncoderTestCase] = Field(min_length=1)


class VariatorEdit(BaseModel):
    content: str


class VariatorOutput(BaseModel):
    """Bounded edits under mu / mu_struct (§6): role-level substitutions
    (mechanism, scope, causal link) for skeleton content, substantive local
    edits otherwise — never mere rewordings."""

    edits: list[VariatorEdit] = Field(min_length=1)


class SynthesizerOutput(BaseModel):
    """A proposed relation artifact (§9): content + the artifact ids it
    connects (rendered as dependence refs)."""

    relation: str
    connects: list[str] = Field(min_length=1)


class DefenderOutput(BaseModel):
    answer: str = Field(min_length=1)


class JudgeRuling(BaseModel):
    """Trial ruling (§3 guard): decisive_point MUST resolve to an actual
    element of the exchange — program-checked (referential integrity)."""

    verdict: Literal["fail", "pass"]
    decisive_point: str = Field(min_length=1)


class PairwiseRuling(BaseModel):
    """Pairwise discrimination (§10.2): A-beats-B-for-pi, never a global
    ranking. 'neither' registers nothing — the rivalry stands."""

    winner: Literal["A", "B", "neither"]
    decisive_point: str = ""


class ProseOutput(BaseModel):
    prose: str = Field(min_length=1)


class ThesisSection(BaseModel):
    """One section of a thesis argument; ``citations`` are pack artifact
    id prefixes (bracketed in the pack) — program-checked afterwards."""

    heading: str = Field(min_length=1)
    body: str = Field(min_length=1)
    citations: list[str] = Field(default_factory=list)


class ThesisRival(BaseModel):
    """A surviving rival position, stated fairly, with the concrete
    evidence or test that would discriminate it from the thesis."""

    artifact: str = ""  # pack id prefix ("" when positional)
    position: str = Field(min_length=1)
    discriminator: str = Field(min_length=1)


class ThesisOutput(BaseModel):
    """Committed thesis over a finished run's adjudicated record (§8 view):
    one defended position, argued from the pack ONLY."""

    thesis: str = Field(min_length=1)
    argument: list[ThesisSection] = Field(min_length=1)
    rebuttals: list[ThesisSection] = Field(default_factory=list)
    rivals: list[ThesisRival] = Field(default_factory=list)
    overturn: list[str] = Field(min_length=1)
