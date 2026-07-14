"""Replay-derived signals for the jolt-trigger feasibility pilot.

This module is an analysis view plus typed Measure receipts.  It never calls a
model, creates an artifact or warrant, adds a graph edge, or changes status.
Hard refuted-attractor orbiting and soft repertoire exhaustion intentionally use
different windows and different conjunctions; neither diagnosis is a truth or
acceptance signal.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from enum import Enum
from statistics import median
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from deepreason.canonical import canonical_json, sha256_hex
from deepreason.llm.embedder import distance
from deepreason.ontology import Rule, Status
from deepreason.scheduler.scheduler import problem_family_key


FUNCTIONAL_SIGNAL = "jolt-functional-observation"
TRIGGER_SIGNAL = "jolt-trigger"


class JoltSignalError(ValueError):
    """A pilot signal cannot be derived under its frozen evidence contract."""


class StatusSource(str, Enum):
    EXECUTION = "execution"
    DETERMINISTIC = "deterministic"
    FORMAL = "formal"
    BROWSER = "browser"
    PROPERTY = "property"
    FUZZ = "fuzz"
    SIMULATION = "simulation"
    EXTERNAL_EVIDENCE = "external_evidence"


class VerifierMetricKind(str, Enum):
    COVERAGE = "coverage"
    OBJECTIVE = "objective"
    TEST_SCORE = "test_score"
    COUNTEREXAMPLE = "counterexample"
    PROOF_OBLIGATION = "proof_obligation"
    OTHER = "other"


class VerifierMetric(BaseModel):
    """A domain evaluator normalises ``delta`` so positive means improvement."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(min_length=1, max_length=120)
    kind: VerifierMetricKind
    before: float
    after: float
    delta: float
    unit: str = Field(min_length=1, max_length=80)
    source_receipt: str = Field(pattern=r"^[0-9a-f]{64}$")


class FunctionalObservation(BaseModel):
    """Deterministic evaluator output recorded as a status-inert Measure."""

    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)

    schema_id: Literal["deepreason-functional-observation-v1"] = Field(
        default="deepreason-functional-observation-v1", alias="schema"
    )
    candidate_id: str = Field(min_length=1)
    problem_id: str = Field(min_length=1)
    problem_family: str = Field(min_length=1)
    domain: Literal["code", "finite", "simulation", "formal", "browser"]
    evaluator_id: str = Field(min_length=1, max_length=160)
    evaluator_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    admitted: bool
    functional_novelty: bool
    mechanism_class: str | None = Field(default=None, min_length=1, max_length=160)
    verifier_metric: VerifierMetric | None = None
    new_commitment: bool = False
    new_counterexample_class: bool = False
    # Optional report field only. Trigger geometry is recomputed from the
    # replay-visible artifact stream under the exact stamped embedder.
    semantic_novelty: float | None = Field(default=None, ge=0.0)
    status_source: StatusSource

    @model_validator(mode="after")
    def _admission_contract(self):
        if not self.admitted and (
            self.functional_novelty
            or self.mechanism_class is not None
            or self.verifier_metric is not None
            or self.new_commitment
            or self.new_counterexample_class
        ):
            raise ValueError("a non-admitted candidate cannot claim functional progress")
        return self

    @property
    def digest(self) -> str:
        return sha256_hex(canonical_json(self.model_dump(mode="json", by_alias=True)))


class ObservationReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    event_seq: int = Field(ge=0)
    observation: FunctionalObservation


class PilotSignalPolicy(BaseModel):
    """Frozen candidate thresholds; calibration hypotheses, not production rules."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    hard_window_calls: int = Field(default=10, gt=0)
    hard_min_gate_blocks: int = Field(default=5, gt=0)
    hard_min_concentration: float = Field(default=0.60, gt=0.0, le=1.0)
    early_novelty_n: int = Field(default=8, gt=1)
    recent_admissions_n: int = Field(default=8, gt=1)
    soft_late_early_ratio_max: float = Field(default=0.85, gt=0.0)
    soft_gate_blocks_max: int = Field(default=1, ge=0)


class HardOrbitSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    sufficient_data: bool
    completed_conjecturer_calls: int = Field(ge=0)
    gate_block_count: int = Field(ge=0)
    gate_block_rate: float = Field(ge=0.0)
    empty_cycle_count: int = Field(ge=0)
    no_register_rate: float = Field(ge=0.0, le=1.0)
    tokens_per_admitted_candidate: float | None = Field(default=None, ge=0.0)
    blocked_target_concentration: float = Field(ge=0.0, le=1.0)
    blocked_lineage_concentration: float = Field(ge=0.0, le=1.0)
    time_since_last_admission_calls: int = Field(ge=0)
    time_since_last_verifier_improvement_calls: int = Field(ge=0)
    refuted_attractor_present: bool
    same_problem_family_block_share: float = Field(ge=0.0, le=1.0)
    concentrated_target_id: str | None = None
    verifier_improvement_count: int = Field(ge=0)
    trigger: bool
    source_event_seqs: tuple[int, ...] = ()


class SoftExhaustionSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    sufficient_data: bool
    problem_family: str
    early_novelty_median: float | None = Field(default=None, ge=0.0)
    recent_novelty_median: float | None = Field(default=None, ge=0.0)
    within_run_normalised_semantic_novelty: tuple[float, ...] = ()
    late_early_novelty_ratio: float | None = Field(default=None, ge=0.0)
    mechanism_class_discovery_rate: float = Field(ge=0.0, le=1.0)
    new_executable_commitment_rate: float = Field(ge=0.0, le=1.0)
    verifier_coverage_delta: float = 0.0
    best_objective_or_test_score_delta: float = 0.0
    new_counterexample_rate: float = Field(ge=0.0, le=1.0)
    semantic_cluster_growth_without_functional_growth: float = Field(
        ge=0.0, le=1.0
    )
    admissions_since_last_verifier_improvement: int = Field(ge=0)
    problem_age: int = Field(ge=0)
    recent_gate_block_count: int = Field(ge=0)
    verifier_improvement_count: int = Field(ge=0)
    trigger: bool
    source_event_seqs: tuple[int, ...] = ()


class Diagnosis(str, Enum):
    HARD_ORBIT = "hard_orbit"
    SOFT_EXHAUSTION = "soft_exhaustion"
    AMBIGUOUS = "ambiguous"
    HEALTHY = "healthy"
    INSUFFICIENT_DATA = "insufficient_data"


class DiagnosisResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    diagnosis: Diagnosis
    hard_trigger: bool
    soft_trigger: bool
    hard_sufficient: bool
    soft_sufficient: bool
    source_event_seqs: tuple[int, ...]

    @property
    def digest(self) -> str:
        return sha256_hex(canonical_json(self.model_dump(mode="json")))


class _GateBlock(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    event_seq: int
    reason: str
    candidate_id: str | None
    problem_id: str | None
    target_id: str | None


class _ConjecturerCall(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    event_seq: int
    problem_id: str | None
    tokens: int = Field(ge=0)
    no_register: bool
    admitted_ids: tuple[str, ...]
    gate_blocks: tuple[_GateBlock, ...]


def record_functional_observation(harness, observation: FunctionalObservation):
    """Append a typed process receipt without creating any epistemic object."""
    if observation.admitted and observation.candidate_id not in harness.state.artifacts:
        raise JoltSignalError("JOLT_OBSERVATION_CANDIDATE_MISSING")
    if observation.problem_id not in harness.state.problems:
        raise JoltSignalError("JOLT_OBSERVATION_PROBLEM_MISSING")
    if (
        problem_family_key(harness.state, observation.problem_id)
        != observation.problem_family
    ):
        raise JoltSignalError("JOLT_OBSERVATION_PROBLEM_FAMILY_MISMATCH")
    payload = json.dumps(
        observation.model_dump(mode="json", by_alias=True),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return harness.record_measure(inputs=[FUNCTIONAL_SIGNAL, payload])


def functional_observations(harness) -> tuple[ObservationReceipt, ...]:
    """Parse only append-only Measure receipts; malformed records fail closed."""
    out: list[ObservationReceipt] = []
    seen: set[str] = set()
    for event in harness.log.read():
        if (
            event.rule != Rule.MEASURE
            or len(event.inputs) != 2
            or event.inputs[0] != FUNCTIONAL_SIGNAL
        ):
            continue
        try:
            observation = FunctionalObservation.model_validate_json(event.inputs[1])
        except ValueError as error:
            raise JoltSignalError(
                f"JOLT_FUNCTIONAL_RECEIPT_INVALID:event={event.seq}"
            ) from error
        key = observation.candidate_id
        if key in seen:
            raise JoltSignalError(f"JOLT_FUNCTIONAL_RECEIPT_DUPLICATE:{key}")
        seen.add(key)
        out.append(ObservationReceipt(event_seq=event.seq, observation=observation))
    return tuple(out)


def require_embedder_fingerprint(embedder, expected: dict[str, str]) -> dict[str, str]:
    """Evidence mode accepts no fallback and no partial identity match."""
    if embedder is None or not callable(getattr(embedder, "fingerprint", None)):
        raise JoltSignalError("JOLT_EMBEDDER_UNAVAILABLE")
    actual = embedder.fingerprint()
    required = {"model", "version", "sentinel"}
    if set(expected) != required or any(not expected.get(key) for key in required):
        raise JoltSignalError("JOLT_EXPECTED_EMBEDDER_FINGERPRINT_INVALID")
    if any(actual.get(key) != expected[key] for key in required):
        raise JoltSignalError("JOLT_EMBEDDER_FINGERPRINT_MISMATCH")
    return {key: str(actual[key]) for key in sorted(required)}


_REFUTED_PATTERNS = (
    re.compile(r"to refuted ([0-9a-f]{8,64})"),
    re.compile(r"^gate:hash: ([0-9a-f]{8,64}) is a refuted artifact$"),
)


def _resolve_prefix(prefix: str | None, artifact_ids) -> str | None:
    if not prefix:
        return None
    if prefix in artifact_ids:
        return prefix
    matches = [artifact_id for artifact_id in artifact_ids if artifact_id.startswith(prefix)]
    return matches[0] if len(matches) == 1 else None


def _gate_block(event, harness) -> _GateBlock:
    reason = str(event.inputs[0])
    target_prefix = None
    for pattern in _REFUTED_PATTERNS:
        match = pattern.search(reason)
        if match:
            target_prefix = match.group(1)
            break
    return _GateBlock(
        event_seq=event.seq,
        reason=reason,
        candidate_id=str(event.inputs[1]) if len(event.inputs) > 1 else None,
        problem_id=str(event.inputs[2]) if len(event.inputs) > 2 else None,
        target_id=_resolve_prefix(target_prefix, harness.state.artifacts),
    )


def _conjecturer_calls(harness) -> tuple[_ConjecturerCall, ...]:
    """Segment gate receipts by valid completed conjecturer call.

    Transport/schema drops are process failures, not evidence of repertoire
    exhaustion, and therefore do not enter either candidate trigger window.
    """
    calls: list[_ConjecturerCall] = []
    pending_gates: list[_GateBlock] = []
    current_problem: str | None = None
    for event in harness.log.read():
        signal = str(event.inputs[0]) if event.inputs else ""
        if event.rule == Rule.MEASURE and signal == "cycle":
            pending_gates = []
            current_problem = (
                str(event.inputs[2])
                if len(event.inputs) > 2 and event.inputs[2] != "-"
                else None
            )
        if event.rule == Rule.MEASURE and signal.startswith("gate:"):
            pending_gates.append(_gate_block(event, harness))
        if event.llm is None or event.llm.role != "conjecturer":
            continue
        if signal == "dropped-call":
            pending_gates = []
            continue
        problem_id = (
            str(event.inputs[0])
            if event.rule == Rule.CONJ and event.inputs
            else current_problem
        )
        admitted = tuple(
            output
            for output in event.outputs
            if output in harness.state.artifacts
            and harness.state.artifacts[output].provenance.role.value == "conjecturer"
        )
        calls.append(
            _ConjecturerCall(
                event_seq=event.seq,
                problem_id=problem_id,
                tokens=max(0, event.llm.tokens),
                no_register=signal == "conj-noregister",
                admitted_ids=admitted,
                gate_blocks=tuple(pending_gates),
            )
        )
        pending_gates = []
    return tuple(calls)


def _max_share(values: list[str | None], denominator: int) -> tuple[float, str | None]:
    counts = Counter(value for value in values if value is not None)
    if not counts or denominator <= 0:
        return 0.0, None
    winner = min(counts, key=lambda value: (-counts[value], value))
    return counts[winner] / denominator, winner


def _calls_since(calls: tuple[_ConjecturerCall, ...], predicate) -> int:
    for offset, call in enumerate(reversed(calls)):
        if predicate(call):
            return offset
    return len(calls)


def hard_orbit_snapshot(
    harness,
    *,
    policy: PilotSignalPolicy | None = None,
    observations: tuple[ObservationReceipt, ...] | None = None,
) -> HardOrbitSnapshot:
    policy = policy or PilotSignalPolicy()
    all_calls = _conjecturer_calls(harness)
    calls = all_calls[-policy.hard_window_calls :]
    blocks = [block for call in calls for block in call.gate_blocks]
    n_blocks = len(blocks)
    admitted_n = sum(len(call.admitted_ids) for call in calls)
    tokens = sum(call.tokens for call in calls)

    target_share, target_id = _max_share(
        [block.target_id for block in blocks], n_blocks
    )
    lineages = [
        harness.state.artifacts[block.target_id].provenance.school
        if block.target_id in harness.state.artifacts
        else None
        for block in blocks
    ]
    lineage_share, _ = _max_share(lineages, n_blocks)

    target_families: list[str | None] = []
    proposal_families: list[str | None] = []
    addressed = {}
    for artifact_id, problem_id in harness.state.addr:
        addressed.setdefault(artifact_id, problem_id)
    for block in blocks:
        target_problem = addressed.get(block.target_id or "")
        target_families.append(
            problem_family_key(harness.state, target_problem) if target_problem else None
        )
        proposal_families.append(
            problem_family_key(harness.state, block.problem_id)
            if block.problem_id in harness.state.problems
            else None
        )
    same_family = sum(
        1
        for target_family, proposal_family in zip(target_families, proposal_families)
        if target_family is not None and target_family == proposal_family
    )
    family_share = same_family / n_blocks if n_blocks else 0.0

    receipts = observations if observations is not None else functional_observations(harness)
    first_seq = calls[0].event_seq if calls else harness._next_seq
    recent_improvements = [
        receipt
        for receipt in receipts
        if receipt.event_seq >= first_seq
        and receipt.observation.verifier_metric is not None
        and receipt.observation.verifier_metric.delta > 0
    ]
    improvement_seqs = {receipt.event_seq for receipt in receipts if (
        receipt.observation.verifier_metric is not None
        and receipt.observation.verifier_metric.delta > 0
    )}
    improvement_calls = {
        index
        for index, call in enumerate(all_calls)
        if any(
            call.event_seq <= seq < (
                all_calls[index + 1].event_seq if index + 1 < len(all_calls) else harness._next_seq
            )
            for seq in improvement_seqs
        )
    }
    last_indices = range(max(0, len(all_calls) - len(calls)), len(all_calls))
    since_improvement = len(calls)
    for offset, index in enumerate(reversed(tuple(last_indices))):
        if index in improvement_calls:
            since_improvement = offset
            break

    sufficient = len(calls) == policy.hard_window_calls
    refuted = bool(
        target_id is not None
        and harness.state.status.get(target_id) == Status.REFUTED
    )
    concentration = max(target_share, lineage_share, family_share)
    trigger = bool(
        sufficient
        and n_blocks >= policy.hard_min_gate_blocks
        and concentration >= policy.hard_min_concentration
        and refuted
        and not recent_improvements
    )
    source_seqs = sorted(
        {call.event_seq for call in calls}
        | {block.event_seq for block in blocks}
        | {receipt.event_seq for receipt in recent_improvements}
    )
    return HardOrbitSnapshot(
        sufficient_data=sufficient,
        completed_conjecturer_calls=len(calls),
        gate_block_count=n_blocks,
        # Blocks per completed call is intentionally not a probability; it can
        # exceed one when VS_K > 1.
        gate_block_rate=n_blocks / len(calls) if calls else 0.0,
        empty_cycle_count=sum(call.no_register and bool(call.gate_blocks) for call in calls),
        no_register_rate=(sum(call.no_register for call in calls) / len(calls)) if calls else 0.0,
        tokens_per_admitted_candidate=(tokens / admitted_n) if admitted_n else None,
        blocked_target_concentration=target_share,
        blocked_lineage_concentration=lineage_share,
        time_since_last_admission_calls=_calls_since(calls, lambda call: bool(call.admitted_ids)),
        time_since_last_verifier_improvement_calls=since_improvement,
        refuted_attractor_present=refuted,
        same_problem_family_block_share=family_share,
        concentrated_target_id=target_id,
        verifier_improvement_count=len(recent_improvements),
        trigger=trigger,
        source_event_seqs=tuple(source_seqs),
    )


def _novelty_rows(harness, receipts: tuple[ObservationReceipt, ...], embedder):
    prior: list[tuple[str, list[float]]] = []
    rows = []
    for receipt in receipts:
        observation = receipt.observation
        if not observation.admitted or observation.candidate_id not in harness.state.artifacts:
            continue
        vector = harness.embed_artifact(embedder, observation.candidate_id)
        candidates = [
            distance(vector, old_vector)
            for family, old_vector in prior
            if family == observation.problem_family
        ]
        rows.append((receipt, min(candidates) if candidates else None))
        prior.append((observation.problem_family, vector))
    return rows


def soft_exhaustion_snapshot(
    harness,
    *,
    problem_family: str,
    embedder,
    expected_embedder_fingerprint: dict[str, str],
    policy: PilotSignalPolicy | None = None,
    observations: tuple[ObservationReceipt, ...] | None = None,
) -> SoftExhaustionSnapshot:
    policy = policy or PilotSignalPolicy()
    require_embedder_fingerprint(embedder, expected_embedder_fingerprint)
    receipts = observations if observations is not None else functional_observations(harness)
    family_receipts = tuple(
        receipt
        for receipt in receipts
        if receipt.observation.problem_family == problem_family
        and receipt.observation.admitted
    )
    rows = _novelty_rows(harness, family_receipts, embedder)
    nonnull = [(receipt, value) for receipt, value in rows if value is not None]
    early = nonnull[: policy.early_novelty_n]
    baseline_end_seq = early[-1][0].event_seq if len(early) == policy.early_novelty_n else None
    after_baseline = [
        (receipt, value)
        for receipt, value in nonnull
        if baseline_end_seq is not None and receipt.event_seq > baseline_end_seq
    ]
    recent = after_baseline[-policy.recent_admissions_n :]
    sufficient = (
        len(early) == policy.early_novelty_n
        and len(recent) == policy.recent_admissions_n
    )
    early_median = median(value for _, value in early) if early else None
    recent_median = median(value for _, value in recent) if recent else None
    ratio = (
        recent_median / early_median
        if sufficient and early_median is not None and early_median > 0
        else None
    )
    normalized = tuple(
        value / early_median for _, value in recent
    ) if ratio is not None and early_median else ()

    recent_receipts = [receipt for receipt, _ in recent]
    recent_obs = [receipt.observation for receipt in recent_receipts]
    recent_candidate_seqs = [
        harness.state.artifacts[receipt.observation.candidate_id].provenance.event_seq
        for receipt in recent_receipts
    ]
    recent_start = min(recent_candidate_seqs) if recent_candidate_seqs else harness._next_seq
    prior_classes = {
        receipt.observation.mechanism_class
        for receipt in family_receipts
        if receipt.event_seq < recent_start and receipt.observation.mechanism_class
    }
    new_classes = {
        observation.mechanism_class
        for observation in recent_obs
        if observation.mechanism_class
        and observation.mechanism_class not in prior_classes
    }
    n_recent = len(recent_obs)
    improvements = [
        observation
        for observation in recent_obs
        if observation.verifier_metric is not None
        and observation.verifier_metric.delta > 0
    ]
    coverage_delta = sum(
        observation.verifier_metric.delta
        for observation in recent_obs
        if observation.verifier_metric is not None
        and observation.verifier_metric.kind == VerifierMetricKind.COVERAGE
    )
    objective_delta = max(
        (
            observation.verifier_metric.delta
            for observation in recent_obs
            if observation.verifier_metric is not None
            and observation.verifier_metric.kind
            in {VerifierMetricKind.OBJECTIVE, VerifierMetricKind.TEST_SCORE}
        ),
        default=0.0,
    )
    since_improvement = 0
    for receipt in reversed(family_receipts):
        metric = receipt.observation.verifier_metric
        if metric is not None and metric.delta > 0:
            break
        since_improvement += 1

    recent_end = recent_receipts[-1].event_seq if recent_receipts else -1
    gate_events = [
        event
        for event in harness.log.read()
        if recent_start <= event.seq <= recent_end
        and event.rule == Rule.MEASURE
        and event.inputs
        and str(event.inputs[0]).startswith("gate:")
        and len(event.inputs) > 2
        and event.inputs[2] in harness.state.problems
        and problem_family_key(harness.state, event.inputs[2]) == problem_family
    ]
    trigger = bool(
        sufficient
        and ratio is not None
        and ratio <= policy.soft_late_early_ratio_max
        and not new_classes
        and not any(observation.new_commitment for observation in recent_obs)
        and not improvements
        and len(gate_events) <= policy.soft_gate_blocks_max
    )
    source_seqs = sorted(
        {receipt.event_seq for receipt, _ in early}
        | {receipt.event_seq for receipt in recent_receipts}
        | set(recent_candidate_seqs)
        | {event.seq for event in gate_events}
    )
    denominator = n_recent or 1
    return SoftExhaustionSnapshot(
        sufficient_data=sufficient and early_median is not None and early_median > 0,
        problem_family=problem_family,
        early_novelty_median=early_median,
        recent_novelty_median=recent_median,
        within_run_normalised_semantic_novelty=normalized,
        late_early_novelty_ratio=ratio,
        mechanism_class_discovery_rate=len(new_classes) / denominator,
        new_executable_commitment_rate=(
            sum(observation.new_commitment for observation in recent_obs) / denominator
        ),
        verifier_coverage_delta=coverage_delta,
        best_objective_or_test_score_delta=objective_delta,
        new_counterexample_rate=(
            sum(observation.new_counterexample_class for observation in recent_obs)
            / denominator
        ),
        semantic_cluster_growth_without_functional_growth=(
            sum(not observation.functional_novelty for observation in recent_obs)
            / denominator
        ),
        admissions_since_last_verifier_improvement=since_improvement,
        problem_age=len(family_receipts),
        recent_gate_block_count=len(gate_events),
        verifier_improvement_count=len(improvements),
        trigger=trigger,
        source_event_seqs=tuple(source_seqs),
    )


def diagnose(hard: HardOrbitSnapshot, soft: SoftExhaustionSnapshot) -> DiagnosisResult:
    if hard.trigger and soft.trigger:
        label = Diagnosis.AMBIGUOUS
    elif hard.trigger:
        label = Diagnosis.HARD_ORBIT
    elif soft.trigger:
        label = Diagnosis.SOFT_EXHAUSTION
    elif not hard.sufficient_data or not soft.sufficient_data:
        label = Diagnosis.INSUFFICIENT_DATA
    else:
        label = Diagnosis.HEALTHY
    return DiagnosisResult(
        diagnosis=label,
        hard_trigger=hard.trigger,
        soft_trigger=soft.trigger,
        hard_sufficient=hard.sufficient_data,
        soft_sufficient=soft.sufficient_data,
        source_event_seqs=tuple(
            sorted(set(hard.source_event_seqs) | set(soft.source_event_seqs))
        ),
    )


def record_trigger_decision(harness, result: DiagnosisResult):
    """Log a prospective decision as process evidence, never as a warrant."""
    payload = json.dumps(
        result.model_dump(mode="json"), sort_keys=True, separators=(",", ":")
    )
    return harness.record_measure(inputs=[TRIGGER_SIGNAL, payload])
