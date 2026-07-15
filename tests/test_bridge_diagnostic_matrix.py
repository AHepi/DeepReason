"""C14 offline confabulation diagnostic matrix.

This module is deliberately a regression harness, not a runtime metric.  It
drives only scripted ``MockEndpoint`` instances, records where authored text
first appears, and never feeds a finding into formal status or scheduling.
The two-stage rows exercise the production bridge; the legacy rows exercise
the existing one-stage thesis output contract as the comparison baseline.
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from enum import Enum
from itertools import product

import pytest

from deepreason.bridge.compose import CompositionRequestV1
from deepreason.bridge.ledger import (
    ClaimLedgerCatalogItemV1,
    ClaimLedgerInputCatalogV1,
    build_claim_ledger_stage_a,
)
from deepreason.bridge.models import ClaimClass, SourceConflictV1
from deepreason.bridge.workflow import BridgeWorkflow
from deepreason.harness import Harness
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.contracts import ThesisOutput
from deepreason.llm.endpoints import MockEndpoint


class DiagnosticStage(str, Enum):
    INITIAL_CONJECTURE = "initial conjecture"
    SCRATCH_BLOCK = "scratch block"
    CLAIM_LEDGER = "claim ledger"
    BRIDGE_COMPOSITION = "bridge composition"
    SCHEMA_REPAIR = "schema repair"
    GROUNDING_REPAIR = "grounding repair"
    FINAL_RENDER = "final render"


class DiagnosticLabel(str, Enum):
    GROUNDED_FACTUAL_CLAIM = "grounded factual claim"
    VALID_INFERENCE = "valid inference"
    CLEARLY_LABELLED_CONJECTURE = "clearly labelled conjecture"
    CORRECT_ABSTENTION = "correct abstention"
    UNNECESSARY_ABSTENTION = "unnecessary abstention"
    UNSUPPORTED_FACTUAL_COMPLETION = "unsupported factual completion"
    CITATION_MISMATCH = "citation mismatch"
    SOURCE_DISTORTION = "source distortion"
    SCHEMA_ONLY_SUCCESS = "schema-only success"


_DENSE_ALLOY_CONJECTURE = "A dense alloy may explain the capsule's behaviour."
_MISTAKEN_WEIGHT = "The capsule weighs 19 kilograms."


@dataclass(frozen=True)
class MatrixCondition:
    scratchpad: bool
    allow_abstention: bool
    two_stage: bool

    @property
    def name(self) -> str:
        scratch = "scratch-on" if self.scratchpad else "scratch-off"
        abstention = "abstention-allowed" if self.allow_abstention else "abstention-disallowed"
        bridge = "two-stage" if self.two_stage else "one-stage-legacy"
        return f"{scratch}-{abstention}-{bridge}"


MATRIX = tuple(
    MatrixCondition(scratchpad, allow_abstention, two_stage)
    for scratchpad, allow_abstention, two_stage in product(
        (False, True), repeat=3
    )
)


@dataclass
class DiagnosticTrace:
    """Test-only first-appearance instrumentation for authored claims."""

    watched_claims: tuple[str, ...]
    checkpoints: set[DiagnosticStage] = field(default_factory=set)
    first_appearance: dict[str, DiagnosticStage] = field(default_factory=dict)
    labels: set[DiagnosticLabel] = field(default_factory=set)
    observations: dict[DiagnosticStage, list[str]] = field(default_factory=dict)
    prompts: list[str] = field(default_factory=list)

    def observe(self, stage: DiagnosticStage, authored_text: str = "") -> None:
        self.checkpoints.add(stage)
        self.observations.setdefault(stage, []).append(authored_text)
        for claim in self.watched_claims:
            if claim in authored_text and claim not in self.first_appearance:
                self.first_appearance[claim] = stage


class _StageScript:
    """Attach a diagnostic stage to each deterministic endpoint response."""

    def __init__(
        self,
        trace: DiagnosticTrace,
        responses: list[tuple[DiagnosticStage, str]],
    ) -> None:
        self.trace = trace
        self.responses = list(responses)

    def __call__(self, prompt: str) -> str:
        if not self.responses:
            raise RuntimeError("offline diagnostic script exhausted")
        self.trace.prompts.append(prompt)
        stage, response = self.responses.pop(0)
        self.trace.observe(stage, response)
        return response


@dataclass(frozen=True)
class DiagnosticAbstentionPolicy:
    """Test-only authoring policy used to vary the actual model-facing pack."""

    allow_unresolved: bool

    @property
    def directive(self) -> str:
        if self.allow_unresolved:
            return (
                "DIAGNOSTIC_ABSTENTION=allowed: unresolved terminal resolutions "
                "are valid answers when the bounded record is insufficient."
            )
        return (
            "DIAGNOSTIC_ABSTENTION=disallowed: this legacy comparison requires "
            "a positive filled answer even when the bounded record is insufficient."
        )

    def apply(self, target: str) -> str:
        return f"{target}\n{self.directive}"


class _LegacyPolicyScript:
    """Produce the legacy fixture response from the received prompt policy."""

    def __init__(self, trace: DiagnosticTrace) -> None:
        self.trace = trace

    def __call__(self, prompt: str) -> str:
        self.trace.prompts.append(prompt)
        allowed = DiagnosticAbstentionPolicy(True).directive
        disallowed = DiagnosticAbstentionPolicy(False).directive
        if allowed in prompt and disallowed not in prompt:
            response = _legacy_output(abstain=True)
        elif disallowed in prompt and allowed not in prompt:
            response = _legacy_output(abstain=False)
        else:
            raise RuntimeError("legacy diagnostic prompt has no unique abstention policy")
        self.trace.observe(DiagnosticStage.BRIDGE_COMPOSITION, response)
        return response


@dataclass(frozen=True)
class MatrixOutcome:
    condition: MatrixCondition
    trace: DiagnosticTrace
    final_text: str
    resolution: str
    process_status: str
    formal_state_unchanged: bool
    ledger_classes: tuple[ClaimClass, ...] = ()
    first_call_validity: tuple[bool, ...] = ()
    policy_directive: str = ""


def _catalog(
    *items: ClaimLedgerCatalogItemV1,
    policy: DiagnosticAbstentionPolicy | None = None,
) -> ClaimLedgerInputCatalogV1:
    output_target = "a calibrated answer"
    if policy is not None:
        output_target = policy.apply(output_target)
    return ClaimLedgerInputCatalogV1.create(
        problem_ref="diagnostic-problem",
        formal_seq=0,
        problem_text="What does the bounded record establish about the capsule's weight?",
        output_target=output_target,
        items=list(items),
    )


def _item(handle: str, kind: str, ref: str, excerpt: str) -> ClaimLedgerCatalogItemV1:
    return ClaimLedgerCatalogItemV1(
        handle=handle,
        kind=kind,
        ref=ref,
        excerpt=excerpt,
    )


def _request(
    policy: DiagnosticAbstentionPolicy | None = None,
) -> CompositionRequestV1:
    output_target = "a calibrated answer"
    if policy is not None:
        output_target = policy.apply(output_target)
    return CompositionRequestV1(
        output_target=output_target,
        formatting_profile="plain",
        desired_length_chars=8_192,
        maximum_sections=8,
    )


def _response(**values) -> str:
    return json.dumps(values, sort_keys=True)


def _adapter(
    harness: Harness,
    trace: DiagnosticTrace,
    *,
    summarizer: list[tuple[DiagnosticStage, str]] | None = None,
    thesis: list[tuple[DiagnosticStage, str]] | None = None,
    judge: list[tuple[DiagnosticStage, str]] | None = None,
) -> LLMAdapter:
    endpoints = {}
    for role, responses in (
        ("summarizer", summarizer),
        ("thesis", thesis),
        ("judge", judge),
    ):
        if responses is not None:
            endpoints[role] = MockEndpoint(
                _StageScript(trace, responses),
                name=f"offline-diagnostic-{role}",
                model="scripted-fixture",
            )
    return LLMAdapter(endpoints, harness.blobs, retry_max=2)


def _legacy_output(*, abstain: bool) -> str:
    if abstain:
        thesis = "The bounded record does not establish the capsule's weight."
        body = "The source records colour only, so the requested weight remains unknown."
    else:
        thesis = _MISTAKEN_WEIGHT
        body = f"The one-stage completion fills the required answer: {_MISTAKEN_WEIGHT}"
    return _response(
        thesis=thesis,
        argument=[{"heading": "Answer", "body": body, "citations": []}],
        rebuttals=[],
        rivals=[],
        overturn=["A source that directly records the capsule's weight."],
    )


def _stage_text(trace: DiagnosticTrace, stage: DiagnosticStage) -> str:
    return "\n".join(trace.observations.get(stage, ()))


def _label_initial_conjecture(trace: DiagnosticTrace) -> None:
    if (
        trace.first_appearance.get(_DENSE_ALLOY_CONJECTURE)
        == DiagnosticStage.INITIAL_CONJECTURE
        and "may" in _stage_text(trace, DiagnosticStage.INITIAL_CONJECTURE)
    ):
        trace.labels.add(DiagnosticLabel.CLEARLY_LABELLED_CONJECTURE)


def _run_legacy_matrix(tmp_path, condition: MatrixCondition) -> MatrixOutcome:
    harness = Harness(tmp_path / condition.name)
    formal_before = harness.state.model_dump_json()
    trace = DiagnosticTrace((_DENSE_ALLOY_CONJECTURE, _MISTAKEN_WEIGHT))
    trace.observe(
        DiagnosticStage.INITIAL_CONJECTURE,
        f"Conjecture: {_DENSE_ALLOY_CONJECTURE}",
    )
    scratch = ""
    if condition.scratchpad:
        scratch = f"Advisory scratch, not evidence: {_MISTAKEN_WEIGHT}"
        trace.observe(DiagnosticStage.SCRATCH_BLOCK, scratch)

    policy = DiagnosticAbstentionPolicy(condition.allow_abstention)
    adapter = LLMAdapter(
        {
            "thesis": MockEndpoint(
                _LegacyPolicyScript(trace),
                name="offline-diagnostic-thesis",
                model="scripted-fixture",
            )
        },
        harness.blobs,
        retry_max=2,
    )
    prompt = policy.apply(
        "SOURCE: The bounded source records that the capsule is blue.\n"
        "QUESTION: What is its weight?\n"
        f"{scratch}"
    )
    output, call = adapter.call("thesis", prompt, ThesisOutput, template_role="thesis")
    final_text = output.model_dump_json()
    trace.observe(DiagnosticStage.FINAL_RENDER, final_text)
    _label_initial_conjecture(trace)
    if _MISTAKEN_WEIGHT not in final_text:
        resolution = "insufficient_evidence"
        trace.labels.add(DiagnosticLabel.CORRECT_ABSTENTION)
    else:
        resolution = "answered"
        trace.labels.update(
            {
                DiagnosticLabel.UNSUPPORTED_FACTUAL_COMPLETION,
                DiagnosticLabel.SCHEMA_ONLY_SUCCESS,
            }
        )
    return MatrixOutcome(
        condition=condition,
        trace=trace,
        final_text=final_text,
        resolution=resolution,
        process_status="success",
        formal_state_unchanged=harness.state.model_dump_json() == formal_before,
        first_call_validity=tuple(item.valid for item in call.attempt_trace),
        policy_directive=policy.directive,
    )


def _run_two_stage_matrix(tmp_path, condition: MatrixCondition) -> MatrixOutcome:
    harness = Harness(tmp_path / condition.name)
    formal_before = harness.state.model_dump_json()
    trace = DiagnosticTrace((_DENSE_ALLOY_CONJECTURE, _MISTAKEN_WEIGHT))
    trace.observe(
        DiagnosticStage.INITIAL_CONJECTURE,
        f"Conjecture: {_DENSE_ALLOY_CONJECTURE}",
    )
    policy = DiagnosticAbstentionPolicy(condition.allow_abstention)

    source = _item(
        "S1",
        "source",
        "source-colour",
        "The bounded source records that the capsule is blue.",
    )
    items = [source]
    if condition.scratchpad:
        trace.observe(
            DiagnosticStage.SCRATCH_BLOCK,
            f"Advisory scratch, not evidence: {_MISTAKEN_WEIGHT}",
        )
        items.append(
            _item(
                "B1",
                "scratch",
                "sha256:" + "b" * 64,
                _MISTAKEN_WEIGHT,
            )
        )

    if condition.allow_abstention:
        stage_a = [
            (
                DiagnosticStage.CLAIM_LEDGER,
                _response(
                    entries=[
                        {
                            "entry_key": "K1",
                            "claim_class": "unknown",
                            "claim": "The capsule's weight is not established.",
                        }
                    ],
                    uncovered_requirements=[
                        {
                            "requirement": "A source recording capsule weight.",
                            "reason": "The bounded source records colour only.",
                        }
                    ],
                ),
            )
        ]
        composition = [
            (
                DiagnosticStage.BRIDGE_COMPOSITION,
                _response(
                    sections=[],
                    unresolved_items=[
                        {
                            "description": "The capsule's weight remains unknown.",
                            "ledger_entry_handles": ["E1"],
                        }
                    ],
                    resolution="insufficient_evidence",
                    resolution_reason="No weight measurement is grounded.",
                ),
            )
        ]
        judge: list[tuple[DiagnosticStage, str]] = []
    else:
        invalid_scratch_fact = _response(
            entries=[
                {
                    "entry_key": "K1",
                    "claim_class": "source_fact",
                    "claim": _MISTAKEN_WEIGHT,
                    "scratch_handles": ["B1"],
                }
            ]
        )
        source_laundered_fact = _response(
            entries=[
                {
                    "entry_key": "K1",
                    "claim_class": "source_fact",
                    "claim": _MISTAKEN_WEIGHT,
                    "source_handles": ["S1"],
                    **({"scratch_handles": ["B1"]} if condition.scratchpad else {}),
                }
            ]
        )
        stage_a = []
        if condition.scratchpad:
            stage_a.append((DiagnosticStage.CLAIM_LEDGER, invalid_scratch_fact))
            stage_a.append((DiagnosticStage.SCHEMA_REPAIR, source_laundered_fact))
        else:
            stage_a.append((DiagnosticStage.CLAIM_LEDGER, source_laundered_fact))
        composition = [
            (
                DiagnosticStage.BRIDGE_COMPOSITION,
                _response(
                    sections=[
                        {
                            "span_id": "S1",
                            "text": _MISTAKEN_WEIGHT,
                            "rendering_mode": "fact",
                            "ledger_entry_handles": ["E1"],
                        }
                    ],
                    resolution="answered",
                ),
            )
        ]
        judge = [
            (
                DiagnosticStage.GROUNDING_REPAIR,
                _response(
                    finding="citation_mismatch",
                    message="The colour source does not record weight.",
                ),
            ),
            (
                DiagnosticStage.GROUNDING_REPAIR,
                _response(action="remove_span"),
            ),
        ]

    adapter = _adapter(
        harness,
        trace,
        summarizer=stage_a,
        thesis=composition,
        judge=judge,
    )
    result = BridgeWorkflow(
        adapter,
        adapter,
        review_adapter=adapter,
        repair_adapter=adapter,
        policy={"max_grounding_repair_attempts": 2},
    ).run(
        _catalog(*items, policy=policy),
        _request(policy),
        materials={"source-colour": "The bounded source records that the capsule is blue."},
    )
    assert result.successful
    final_text = result.bridge_output.model_dump_json()
    trace.observe(DiagnosticStage.FINAL_RENDER, final_text)
    _label_initial_conjecture(trace)
    if (
        result.bridge_output.resolution.value == "insufficient_evidence"
        and _MISTAKEN_WEIGHT not in final_text
    ):
        trace.labels.add(DiagnosticLabel.CORRECT_ABSTENTION)
    pre_render = "\n".join(
        _stage_text(trace, stage)
        for stage in (
            DiagnosticStage.CLAIM_LEDGER,
            DiagnosticStage.SCHEMA_REPAIR,
            DiagnosticStage.BRIDGE_COMPOSITION,
        )
    )
    grounding_text = _stage_text(trace, DiagnosticStage.GROUNDING_REPAIR)
    first_call_validity = tuple(
        item.valid for item in result.model_calls[0].attempt_trace
    )
    if _MISTAKEN_WEIGHT in pre_render:
        trace.labels.add(DiagnosticLabel.UNSUPPORTED_FACTUAL_COMPLETION)
    if "citation_mismatch" in grounding_text:
        trace.labels.add(DiagnosticLabel.CITATION_MISMATCH)
        if any(
            entry.claim_class == ClaimClass.SOURCE_FACT
            and entry.claim == _MISTAKEN_WEIGHT
            and entry.source_refs
            for entry in result.claim_ledger.entries
        ):
            trace.labels.add(DiagnosticLabel.SOURCE_DISTORTION)
        if first_call_validity[-1]:
            trace.labels.add(DiagnosticLabel.SCHEMA_ONLY_SUCCESS)
    if not condition.allow_abstention:
        # The forced-fill test policy is present in every authoring prompt;
        # safety comes from the production ledger/review/repair path.
        assert any(policy.directive in prompt for prompt in trace.prompts)
    return MatrixOutcome(
        condition=condition,
        trace=trace,
        final_text=final_text,
        resolution=result.bridge_output.resolution.value,
        process_status=result.process_status,
        formal_state_unchanged=harness.state.model_dump_json() == formal_before,
        ledger_classes=tuple(entry.claim_class for entry in result.claim_ledger.entries),
        first_call_validity=first_call_validity,
        policy_directive=policy.directive,
    )


def _run_matrix_row(tmp_path, condition: MatrixCondition) -> MatrixOutcome:
    if condition.two_stage:
        return _run_two_stage_matrix(tmp_path, condition)
    return _run_legacy_matrix(tmp_path, condition)


def test_matrix_has_exactly_the_eight_directed_conditions():
    assert len(MATRIX) == 8
    assert {
        (row.scratchpad, row.allow_abstention, row.two_stage) for row in MATRIX
    } == set(product((False, True), repeat=3))


@pytest.mark.parametrize("condition", MATRIX, ids=lambda row: row.name)
def test_offline_diagnostic_matrix(tmp_path, condition):
    outcome = _run_matrix_row(tmp_path, condition)

    assert outcome.process_status == "success"
    assert outcome.formal_state_unchanged
    expected_stages = {
        DiagnosticStage.INITIAL_CONJECTURE,
        DiagnosticStage.BRIDGE_COMPOSITION,
        DiagnosticStage.FINAL_RENDER,
    }
    if condition.scratchpad:
        expected_stages.add(DiagnosticStage.SCRATCH_BLOCK)
    if condition.two_stage:
        expected_stages.add(DiagnosticStage.CLAIM_LEDGER)
    if condition.two_stage and not condition.allow_abstention:
        expected_stages.add(DiagnosticStage.GROUNDING_REPAIR)
    if condition.two_stage and condition.scratchpad and not condition.allow_abstention:
        expected_stages.add(DiagnosticStage.SCHEMA_REPAIR)
    assert outcome.trace.checkpoints == expected_stages
    expected_counts = Counter({stage: 1 for stage in expected_stages})
    if condition.two_stage and not condition.allow_abstention:
        expected_counts[DiagnosticStage.GROUNDING_REPAIR] = 2
    assert Counter(
        {
            stage: len(observations)
            for stage, observations in outcome.trace.observations.items()
        }
    ) == expected_counts
    assert any(
        outcome.policy_directive in prompt for prompt in outcome.trace.prompts
    )
    assert outcome.trace.first_appearance[_DENSE_ALLOY_CONJECTURE] == (
        DiagnosticStage.INITIAL_CONJECTURE
    )
    assert DiagnosticLabel.CLEARLY_LABELLED_CONJECTURE in outcome.trace.labels
    assert outcome.first_call_validity[-1]

    if condition.scratchpad:
        assert outcome.trace.first_appearance[_MISTAKEN_WEIGHT] == (
            DiagnosticStage.SCRATCH_BLOCK
        )
    elif not condition.allow_abstention:
        expected = (
            DiagnosticStage.CLAIM_LEDGER
            if condition.two_stage
            else DiagnosticStage.BRIDGE_COMPOSITION
        )
        assert outcome.trace.first_appearance[_MISTAKEN_WEIGHT] == expected
    else:
        assert _MISTAKEN_WEIGHT not in outcome.trace.first_appearance

    if condition.two_stage:
        # Even a forced-fill script becomes a safe unresolved terminal result.
        assert outcome.resolution == "insufficient_evidence"
        assert _MISTAKEN_WEIGHT not in outcome.final_text
        assert DiagnosticLabel.CORRECT_ABSTENTION in outcome.trace.labels
        if condition.scratchpad and not condition.allow_abstention:
            # The scratch-only fact failed the shared schema kernel.  Its retry
            # could use a source handle, but grounding review then rejected the
            # semantic mismatch; scratch alone never grounded the claim.
            assert outcome.first_call_validity == (False, True)
    elif condition.allow_abstention:
        assert outcome.resolution == "insufficient_evidence"
        assert _MISTAKEN_WEIGHT not in outcome.final_text
        assert DiagnosticLabel.CORRECT_ABSTENTION in outcome.trace.labels
    else:
        # The legacy schema accepts fluent required fields without testing
        # their epistemic content, locating this fixture's confabulation at
        # one-stage composition rather than transport or parsing.
        assert outcome.resolution == "answered"
        assert _MISTAKEN_WEIGHT in outcome.final_text
        assert DiagnosticLabel.SCHEMA_ONLY_SUCCESS in outcome.trace.labels


@dataclass(frozen=True)
class FixtureSpec:
    name: str
    catalog: ClaimLedgerInputCatalogV1
    materials: dict[str, str]
    stage_a: tuple[tuple[DiagnosticStage, str], ...]
    composition: tuple[tuple[DiagnosticStage, str], ...]
    judge: tuple[tuple[DiagnosticStage, str], ...] = ()
    watched_claims: tuple[str, ...] = ()
    initial_conjecture: str | None = None
    scratch_text: str | None = None
    expected_resolution: str = "answered"


def _fixture_specs() -> tuple[FixtureSpec, ...]:
    blue = _item("S1", "source", "source-blue", "The capsule is blue.")
    weight = _item(
        "S1",
        "source",
        "source-weight",
        "The capsule weighs 7 kilograms.",
    )
    scratch = _item(
        "B1",
        "scratch",
        "sha256:" + "c" * 64,
        _MISTAKEN_WEIGHT,
    )
    conflict = SourceConflictV1.create(
        conflicting_refs=["source-left", "source-right"],
        description="The two measurements disagree.",
    )
    return (
        FixtureSpec(
            name="insufficient-source-material",
            catalog=_catalog(),
            materials={},
            stage_a=(
                (
                    DiagnosticStage.CLAIM_LEDGER,
                    _response(
                        entries=[
                            {
                                "entry_key": "K1",
                                "claim_class": "unknown",
                                "claim": "The requested answer is not established.",
                            }
                        ],
                        uncovered_requirements=[
                            {"requirement": "A source establishing the answer."}
                        ],
                    ),
                ),
            ),
            composition=(
                (
                    DiagnosticStage.BRIDGE_COMPOSITION,
                    _response(
                        sections=[],
                        resolution="insufficient_evidence",
                        resolution_reason="The bounded catalog supplies no grounding.",
                    ),
                ),
            ),
            expected_resolution="insufficient_evidence",
        ),
        FixtureSpec(
            name="complete-source-material",
            catalog=_catalog(weight),
            materials={"source-weight": "The capsule weighs 7 kilograms."},
            stage_a=(
                (
                    DiagnosticStage.CLAIM_LEDGER,
                    _response(
                        entries=[
                            {
                                "entry_key": "K1",
                                "claim_class": "source_fact",
                                "claim": "The capsule weighs 7 kilograms.",
                                "source_handles": ["S1"],
                            },
                            {
                                "entry_key": "K2",
                                "claim_class": "supported_inference",
                                "claim": "The capsule's weight is known from the record.",
                                "premise_keys": ["K1"],
                            },
                        ]
                    ),
                ),
            ),
            composition=(
                (
                    DiagnosticStage.BRIDGE_COMPOSITION,
                    _response(
                        sections=[
                            {
                                "span_id": "S1",
                                "text": "The capsule weighs 7 kilograms.",
                                "rendering_mode": "fact",
                                "ledger_entry_handles": ["E1"],
                            },
                            {
                                "span_id": "S2",
                                "text": "Thus its weight is known from the record.",
                                "rendering_mode": "inference",
                                "ledger_entry_handles": ["E2"],
                            },
                        ],
                        resolution="partially_answered",
                        resolution_reason="The script abstains despite a complete answer.",
                    ),
                ),
            ),
            judge=(
                (DiagnosticStage.GROUNDING_REPAIR, _response(finding="supported")),
                (DiagnosticStage.GROUNDING_REPAIR, _response(finding="supported")),
            ),
            expected_resolution="partially_answered",
        ),
        FixtureSpec(
            name="conflicting-source-material",
            catalog=_catalog(
                _item("S1", "source", "source-left", "The value is 2."),
                _item("S2", "source", "source-right", "The value is 3."),
            ),
            materials={conflict.id: "One source says 2; the other says 3."},
            stage_a=(
                (
                    DiagnosticStage.CLAIM_LEDGER,
                    _response(
                        source_conflicts=[
                            {
                                "conflict_key": "C1",
                                "conflicting_handles": ["S1", "S2"],
                                "description": "The two measurements disagree.",
                            }
                        ],
                        entries=[
                            {
                                "entry_key": "K1",
                                "claim_class": "conflict",
                                "claim": "The reported value conflicts.",
                                "source_conflict_keys": ["C1"],
                            }
                        ],
                    ),
                ),
            ),
            composition=(
                (
                    DiagnosticStage.BRIDGE_COMPOSITION,
                    _response(
                        sections=[
                            {
                                "span_id": "S1",
                                "text": "The sources report conflicting values.",
                                "rendering_mode": "conflict",
                                "ledger_entry_handles": ["E1"],
                            }
                        ],
                        resolution="conflicting_evidence",
                    ),
                ),
            ),
            judge=((DiagnosticStage.GROUNDING_REPAIR, _response(finding="supported")),),
            expected_resolution="conflicting_evidence",
        ),
        FixtureSpec(
            name="tempting-unsupported-detail",
            catalog=_catalog(blue),
            materials={"source-blue": "The capsule is blue."},
            stage_a=(
                (
                    DiagnosticStage.CLAIM_LEDGER,
                    _response(
                        entries=[
                            {
                                "entry_key": "K1",
                                "claim_class": "source_fact",
                                "claim": "The capsule is blue.",
                                "source_handles": ["S1"],
                            }
                        ]
                    ),
                ),
            ),
            composition=(
                (
                    DiagnosticStage.BRIDGE_COMPOSITION,
                    _response(
                        sections=[
                            {
                                "span_id": "S1",
                                "text": _MISTAKEN_WEIGHT,
                                "rendering_mode": "fact",
                                "ledger_entry_handles": ["E1"],
                            }
                        ],
                        resolution="answered",
                    ),
                ),
            ),
            judge=(
                (
                    DiagnosticStage.GROUNDING_REPAIR,
                    _response(finding="citation_mismatch"),
                ),
                (DiagnosticStage.GROUNDING_REPAIR, _response(action="remove_span")),
            ),
            watched_claims=(_MISTAKEN_WEIGHT,),
            expected_resolution="insufficient_evidence",
        ),
        FixtureSpec(
            name="scratch-note-containing-mistaken-fact",
            catalog=_catalog(blue, scratch),
            materials={"source-blue": "The capsule is blue."},
            stage_a=tuple(
                (
                    stage,
                    _response(
                        entries=[
                            {
                                "entry_key": "K1",
                                "claim_class": "source_fact",
                                "claim": _MISTAKEN_WEIGHT,
                                "scratch_handles": ["B1"],
                            }
                        ]
                    ),
                )
                for stage in (
                    DiagnosticStage.CLAIM_LEDGER,
                    DiagnosticStage.SCHEMA_REPAIR,
                    DiagnosticStage.SCHEMA_REPAIR,
                )
            ),
            composition=(
                (
                    DiagnosticStage.BRIDGE_COMPOSITION,
                    _response(
                        sections=[],
                        resolution="insufficient_evidence",
                        resolution_reason="Scratch provenance supplies no grounding.",
                    ),
                ),
            ),
            watched_claims=(_MISTAKEN_WEIGHT,),
            scratch_text=_MISTAKEN_WEIGHT,
            expected_resolution="insufficient_evidence",
        ),
        FixtureSpec(
            name="repair-request-missing-required-field",
            catalog=_catalog(blue),
            materials={"source-blue": "The capsule is blue."},
            stage_a=(
                (
                    DiagnosticStage.CLAIM_LEDGER,
                    _response(
                        entries=[
                            {
                                "entry_key": "K1",
                                "claim_class": "source_fact",
                                "source_handles": ["S1"],
                            }
                        ]
                    ),
                ),
                (
                    DiagnosticStage.SCHEMA_REPAIR,
                    _response(
                        entries=[
                            {
                                "entry_key": "K1",
                                "claim_class": "unknown",
                                "claim": "The requested weight remains unknown.",
                            }
                        ]
                    ),
                ),
            ),
            composition=(
                (
                    DiagnosticStage.BRIDGE_COMPOSITION,
                    _response(
                        sections=[],
                        resolution="insufficient_evidence",
                        resolution_reason="Repair did not manufacture a positive answer.",
                    ),
                ),
            ),
            expected_resolution="insufficient_evidence",
        ),
        FixtureSpec(
            name="reviewer-finds-citation-mismatch",
            catalog=_catalog(
                _item(
                    "S1",
                    "source",
                    "source-approximate",
                    "The source reports approximately seven.",
                )
            ),
            materials={"source-approximate": "The source reports approximately seven."},
            stage_a=(
                (
                    DiagnosticStage.CLAIM_LEDGER,
                    _response(
                        entries=[
                            {
                                "entry_key": "K1",
                                "claim_class": "source_fact",
                                "claim": "The source reports approximately seven.",
                                "source_handles": ["S1"],
                            }
                        ]
                    ),
                ),
            ),
            composition=(
                (
                    DiagnosticStage.BRIDGE_COMPOSITION,
                    _response(
                        sections=[
                            {
                                "span_id": "S1",
                                "text": "The exact value is seven.",
                                "rendering_mode": "fact",
                                "ledger_entry_handles": ["E1"],
                            }
                        ],
                        resolution="answered",
                    ),
                ),
            ),
            judge=(
                (
                    DiagnosticStage.GROUNDING_REPAIR,
                    _response(finding="citation_mismatch", message="Too exact."),
                ),
                (
                    DiagnosticStage.GROUNDING_REPAIR,
                    _response(
                        action="correct_wording",
                        replacement_text="The source reports approximately seven.",
                    ),
                ),
                (DiagnosticStage.GROUNDING_REPAIR, _response(finding="supported")),
            ),
            watched_claims=("The exact value is seven.",),
            expected_resolution="answered",
        ),
    )


@dataclass(frozen=True)
class FixtureOutcome:
    spec: FixtureSpec
    result: object
    trace: DiagnosticTrace
    formal_state_unchanged: bool


def _label_fixture_trace(result, trace: DiagnosticTrace) -> None:
    """Classify only outcomes evidenced by parsed objects and recorded calls."""

    if result.bridge_output is None:
        return
    final_text = result.bridge_output.model_dump_json()
    modes = {section.rendering_mode.value for section in result.bridge_output.sections}
    if result.grounded_review is not None and result.grounded_review.passed:
        if "fact" in modes:
            trace.labels.add(DiagnosticLabel.GROUNDED_FACTUAL_CLAIM)
        if "inference" in modes:
            trace.labels.add(DiagnosticLabel.VALID_INFERENCE)

    source_weight_is_rendered = any(
        entry.claim_class == ClaimClass.SOURCE_FACT
        and "weighs 7 kilograms" in entry.claim
        for entry in result.claim_ledger.entries
    ) and "weighs 7 kilograms" in final_text
    if (
        source_weight_is_rendered
        and result.bridge_output.resolution.value == "partially_answered"
    ):
        trace.labels.add(DiagnosticLabel.UNNECESSARY_ABSTENTION)
    elif (
        result.bridge_output.resolution.value
        in {"underdetermined", "insufficient_evidence", "conflicting_evidence"}
        and not result.bridge_output.sections
    ):
        trace.labels.add(DiagnosticLabel.CORRECT_ABSTENTION)

    grounding_text = _stage_text(trace, DiagnosticStage.GROUNDING_REPAIR)
    if "citation_mismatch" in grounding_text:
        trace.labels.add(DiagnosticLabel.CITATION_MISMATCH)
    for claim, stage in trace.first_appearance.items():
        if stage in {
            DiagnosticStage.CLAIM_LEDGER,
            DiagnosticStage.SCHEMA_REPAIR,
            DiagnosticStage.BRIDGE_COMPOSITION,
        }:
            trace.labels.add(DiagnosticLabel.UNSUPPORTED_FACTUAL_COMPLETION)
        if (
            stage == DiagnosticStage.BRIDGE_COMPOSITION
            and "citation_mismatch" in grounding_text
            and claim not in final_text
        ):
            trace.labels.update(
                {
                    DiagnosticLabel.SOURCE_DISTORTION,
                    DiagnosticLabel.SCHEMA_ONLY_SUCCESS,
                }
            )


def _run_fixture(tmp_path, spec: FixtureSpec) -> FixtureOutcome:
    harness = Harness(tmp_path / spec.name)
    formal_before = harness.state.model_dump_json()
    trace = DiagnosticTrace(spec.watched_claims)
    if spec.initial_conjecture is not None:
        trace.observe(DiagnosticStage.INITIAL_CONJECTURE, spec.initial_conjecture)
    if spec.scratch_text is not None:
        trace.observe(DiagnosticStage.SCRATCH_BLOCK, spec.scratch_text)
    adapter = _adapter(
        harness,
        trace,
        summarizer=list(spec.stage_a),
        thesis=list(spec.composition),
        judge=list(spec.judge),
    )
    result = BridgeWorkflow(
        adapter,
        adapter,
        review_adapter=adapter,
        repair_adapter=adapter,
        policy={"max_grounding_repair_attempts": 4},
    ).run(spec.catalog, _request(), materials=spec.materials)
    if result.bridge_output is not None:
        trace.observe(
            DiagnosticStage.FINAL_RENDER,
            result.bridge_output.model_dump_json(),
        )
    _label_fixture_trace(result, trace)
    return FixtureOutcome(
        spec=spec,
        result=result,
        trace=trace,
        formal_state_unchanged=harness.state.model_dump_json() == formal_before,
    )


@pytest.mark.parametrize("spec", _fixture_specs(), ids=lambda spec: spec.name)
def test_scripted_failure_mode_fixtures_are_epistemically_safe(tmp_path, spec):
    outcome = _run_fixture(tmp_path, spec)
    result = outcome.result

    assert result.successful
    assert result.bridge_output.resolution.value == spec.expected_resolution
    assert result.validation_report.valid
    assert outcome.formal_state_unchanged
    expected_stages = {
        stage for stage, _ in (*spec.stage_a, *spec.composition, *spec.judge)
    }
    if spec.initial_conjecture is not None:
        expected_stages.add(DiagnosticStage.INITIAL_CONJECTURE)
    if spec.scratch_text is not None:
        expected_stages.add(DiagnosticStage.SCRATCH_BLOCK)
    if result.bridge_output is not None:
        expected_stages.add(DiagnosticStage.FINAL_RENDER)
    assert outcome.trace.checkpoints == expected_stages
    expected_counts = Counter(
        stage for stage, _ in (*spec.stage_a, *spec.composition, *spec.judge)
    )
    if spec.initial_conjecture is not None:
        expected_counts[DiagnosticStage.INITIAL_CONJECTURE] += 1
    if spec.scratch_text is not None:
        expected_counts[DiagnosticStage.SCRATCH_BLOCK] += 1
    if result.bridge_output is not None:
        expected_counts[DiagnosticStage.FINAL_RENDER] += 1
    assert Counter(
        {
            stage: len(observations)
            for stage, observations in outcome.trace.observations.items()
        }
    ) == expected_counts

    if spec.name == "insufficient-source-material":
        assert result.bridge_output.sections == []
        assert result.bridge_output.resolution.value == "insufficient_evidence"
    elif spec.name == "complete-source-material":
        assert "weighs 7 kilograms" in result.bridge_output.model_dump_json()
        assert [section.rendering_mode.value for section in result.bridge_output.sections] == [
            "fact",
            "inference",
        ]
        assert result.grounded_review.passed
        # This deliberate diagnostic fixture distinguishes valid content from
        # an unnecessarily weak overall resolution.
        assert result.bridge_output.resolution.value == "partially_answered"
    elif spec.name == "conflicting-source-material":
        assert result.bridge_output.sections[0].rendering_mode.value == "conflict"
        assert result.grounded_review.passed
    elif spec.name == "tempting-unsupported-detail":
        assert outcome.trace.first_appearance[_MISTAKEN_WEIGHT] == (
            DiagnosticStage.BRIDGE_COMPOSITION
        )
        assert result.bridge_output.sections == []
        assert result.grounded_review.findings[0].status.value == "citation_mismatch"
    elif spec.name == "scratch-note-containing-mistaken-fact":
        assert outcome.trace.first_appearance[_MISTAKEN_WEIGHT] == (
            DiagnosticStage.SCRATCH_BLOCK
        )
        assert all(
            not attempt.valid for attempt in result.model_calls[0].attempt_trace
        )
        assert [entry.claim_class for entry in result.claim_ledger.entries] == [
            ClaimClass.UNKNOWN
        ]
        assert result.claim_ledger.entries[0].scratch_refs is None
    elif spec.name == "repair-request-missing-required-field":
        assert [
            attempt.valid for attempt in result.model_calls[0].attempt_trace
        ] == [False, True]
        repaired = result.claim_ledger.entries[0]
        assert repaired.claim_class == ClaimClass.UNKNOWN
        assert repaired.source_refs is None
        assert repaired.evidence_refs is None
        assert repaired.premise_refs is None
    elif spec.name == "reviewer-finds-citation-mismatch":
        assert outcome.trace.first_appearance["The exact value is seven."] == (
            DiagnosticStage.BRIDGE_COMPOSITION
        )
        assert result.grounded_review.passed
        assert result.bridge_output.sections[0].text == (
            "The source reports approximately seven."
        )


def test_diagnostic_taxonomy_labels_all_scripted_outcomes(tmp_path):
    """The closed labels stay reporting-only and cover every directed class."""

    forced = _run_legacy_matrix(
        tmp_path / "forced",
        MatrixCondition(False, False, False),
    )
    allowed = _run_legacy_matrix(
        tmp_path / "allowed",
        MatrixCondition(False, True, False),
    )
    complete = _run_fixture(tmp_path / "complete", _fixture_specs()[1])
    assert complete.result.grounded_review.passed
    assert {
        section.rendering_mode.value
        for section in complete.result.bridge_output.sections
    } == {
        "fact",
        "inference",
    }
    assert complete.result.bridge_output.resolution.value == "partially_answered"
    mismatch = _run_fixture(tmp_path / "mismatch", _fixture_specs()[-1])
    assert mismatch.result.grounded_review.passed
    assert mismatch.trace.first_appearance["The exact value is seven."] == (
        DiagnosticStage.BRIDGE_COMPOSITION
    )

    # Every label is emitted by the evidence predicates in the corresponding
    # runner; the taxonomy assertion does not add labels of its own.
    observed = set().union(
        forced.trace.labels,
        allowed.trace.labels,
        complete.trace.labels,
        mismatch.trace.labels,
    )
    assert observed == set(DiagnosticLabel)


def test_actual_stage_observations_cover_the_instrumentation_taxonomy(tmp_path):
    traces = [
        _run_matrix_row(tmp_path / "matrix", condition).trace
        for condition in MATRIX
    ]
    traces.extend(
        _run_fixture(tmp_path / "fixtures", spec).trace
        for spec in _fixture_specs()
    )

    assert set().union(*(trace.checkpoints for trace in traces)) == set(DiagnosticStage)


def test_two_stage_composer_new_fact_is_removed_before_final_render(tmp_path):
    spec = next(
        item for item in _fixture_specs() if item.name == "tempting-unsupported-detail"
    )
    outcome = _run_fixture(tmp_path, spec)

    assert outcome.trace.first_appearance[_MISTAKEN_WEIGHT] == (
        DiagnosticStage.BRIDGE_COMPOSITION
    )
    assert _MISTAKEN_WEIGHT not in outcome.result.bridge_output.model_dump_json()
    assert outcome.result.bridge_output.resolution.value == "insufficient_evidence"


def test_scratch_presence_alone_cannot_ground_a_matrix_claim(tmp_path):
    outcome = _run_two_stage_matrix(
        tmp_path,
        MatrixCondition(True, False, True),
    )

    # The first fact authored with only B1 is rejected by Stage A.  A retry
    # that attaches the unrelated source is still caught by grounded review,
    # and neither form reaches final prose.
    assert outcome.first_call_validity == (False, True)
    assert _MISTAKEN_WEIGHT not in outcome.final_text
    assert outcome.resolution == "insufficient_evidence"


def test_repair_removes_or_downgrades_instead_of_filling_grounding(tmp_path):
    specs = {item.name: item for item in _fixture_specs()}
    missing = _run_fixture(
        tmp_path / "missing",
        specs["repair-request-missing-required-field"],
    ).result
    unsupported = _run_fixture(
        tmp_path / "unsupported",
        specs["tempting-unsupported-detail"],
    ).result

    repaired_entry = missing.claim_ledger.entries[0]
    assert repaired_entry.claim_class == ClaimClass.UNKNOWN
    assert repaired_entry.source_refs is None
    assert repaired_entry.evidence_refs is None
    assert repaired_entry.premise_refs is None
    assert unsupported.bridge_output.sections == []
    assert unsupported.bridge_output.resolution.value == "insufficient_evidence"


def test_allowing_unresolved_output_removes_forced_filling(tmp_path):
    disallowed = _run_legacy_matrix(
        tmp_path / "forced",
        MatrixCondition(False, False, False),
    )
    allowed = _run_legacy_matrix(
        tmp_path / "unresolved",
        MatrixCondition(False, True, False),
    )

    assert disallowed.policy_directive != allowed.policy_directive
    assert any(
        disallowed.policy_directive in prompt for prompt in disallowed.trace.prompts
    )
    assert any(allowed.policy_directive in prompt for prompt in allowed.trace.prompts)
    assert _MISTAKEN_WEIGHT in disallowed.final_text
    assert disallowed.resolution == "answered"
    assert _MISTAKEN_WEIGHT not in allowed.final_text
    assert allowed.resolution == "insufficient_evidence"


def test_all_endpoints_are_scripted_and_no_provider_route_is_used(tmp_path):
    condition = MatrixCondition(True, False, True)
    outcome = _run_two_stage_matrix(tmp_path, condition)

    assert outcome.process_status == "success"
    # The route identity retained on every call comes from MockEndpoint; a
    # network provider could not silently enter this offline regression suite.
    harness = Harness(tmp_path / "route-check")
    trace = DiagnosticTrace(())
    adapter = _adapter(
        harness,
        trace,
        summarizer=[
            (DiagnosticStage.CLAIM_LEDGER, _response(entries=[])),
        ],
    )
    stage_a = build_claim_ledger_stage_a(adapter, _catalog())
    call = stage_a.receipt.llm_call
    assert call.endpoint == "offline-diagnostic-summarizer"
    assert call.model == "scripted-fixture"
