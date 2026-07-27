"""Stage B0: freeze semantic freedom before adding workflow control.

These tests characterize the legacy conjecture boundary.  The measurements
are process diagnostics only: none is allowed to participate in admission,
status, routing, or adjudication.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from deepreason import programs
from deepreason.bridge.models import (
    BridgeOutputV1,
    ClaimClass,
    ClaimLedgerEntryV1,
    ClaimLedgerV1,
    UncoveredRequirementV1,
    UnresolvedItemV1,
)
from deepreason.bridge.validate import validate_bridge_output, validate_claim_ledger
from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.llm.firewall import (
    ModelControlFieldError,
    reject_model_control_fields,
)
from deepreason.ontology import (
    Commitment,
    Problem,
    ProblemProvenance,
    Provenance,
    Rule,
    Status,
)
from deepreason.rules.conj import conj
from deepreason.rules.crit import crit_argumentative
from deepreason.scratch.models import ScratchBlockV1
from deepreason.workflows.manifest_compiler import CompactDesignOutline
from deepreason.workloads.code import CodePatchCandidate
from deepreason.workloads.formal import FormalClaim
from deepreason.workloads.simulation import SimulationClaim
from deepreason.workloads.text import (
    ReasoningCandidateProposal,
    ReasoningEnvelopeV1,
    ReasoningWorkloadSpec,
    WorkloadProblem,
    seed_reasoning_workload,
)


FIXTURE_ROOT = Path(__file__).parent / "fixtures"
BASELINE_PATH = FIXTURE_ROOT / "semantic_freedom_baseline_v1.json"


def _hash(character: str) -> str:
    return f"sha256:{character * 64}"


def _text_semantic_fixture():
    phrase = "Aperiodic memory wakes only when a counterfactual echo decays."
    return (
        ReasoningCandidateProposal(
            claim=phrase,
            mechanism=(
                "A braided feedback loop retains phase information without "
                "treating the words route, retry, stop, or status as commands."
            ),
            counterconditions=("The echo remains phase-locked indefinitely.",),
            typicality=0.17,
        ),
        phrase,
    )


def _code_semantic_fixture():
    phrase = "Preserve the sentinel's identity while folding adjacent spans."
    return (
        CodePatchCandidate(
            patches=(
                {
                    "file": "F1",
                    "anchor": "S1",
                    "replacement": "return fold(spans, keep_identity=sentinel)",
                },
            ),
            rationale=phrase,
            typicality=0.29,
        ),
        phrase,
    )


def _simulation_semantic_fixture():
    phrase = "Metastable islands exchange mass through a delayed stochastic gate."
    return SimulationClaim(statement=phrase), phrase


def _formal_semantic_fixture():
    phrase = "Every finite braid admits a parity-preserving normal form."
    return FormalClaim(statement=phrase), phrase


def _website_semantic_fixture():
    phrase = "A quiet orbital archive reveals its strata through oblique motion."
    return (
        CompactDesignOutline(
            components=[{"alias": "C1", "purpose": phrase}]
        ),
        phrase,
    )


@pytest.mark.parametrize(
    ("workload", "factory"),
    [
        ("text", _text_semantic_fixture),
        ("code", _code_semantic_fixture),
        ("simulation", _simulation_semantic_fixture),
        ("proof", _formal_semantic_fixture),
        ("website", _website_semantic_fixture),
    ],
)
def test_open_semantic_vocabulary_survives_workload_contracts(workload, factory):
    value, novel_phrase = factory()

    encoded = json.dumps(
        value.model_dump(mode="json", by_alias=True),
        sort_keys=True,
        ensure_ascii=False,
    )

    assert novel_phrase in encoded, f"{workload} contract closed the semantic payload"


def test_control_shell_does_not_close_semantic_payload():
    """Authority-shaped keys fail while the same words remain valid prose."""

    proposal, phrase = _text_semantic_fixture()
    semantic_value = proposal.model_dump(mode="json")
    reject_model_control_fields({"candidates": [semantic_value]})
    assert proposal.claim == phrase

    schema = ReasoningCandidateProposal.model_json_schema()["properties"]
    assert "enum" not in schema["claim"]
    assert "enum" not in schema["mechanism"]

    for field, value in (
        ("route", "alternate-seat"),
        ("status", "accepted"),
        ("concurrency", 99),
    ):
        with pytest.raises(ModelControlFieldError) as raised:
            reject_model_control_fields(
                {"candidates": [{**semantic_value, field: value}]}
            )
        assert raised.value.pointer == f"/candidates/0/{field}"
        with pytest.raises(ValidationError):
            ReasoningCandidateProposal.model_validate(
                {**semantic_value, field: value}
            )


def test_reasoning_shape_keeps_optional_semantic_fields_optional():
    envelope = ReasoningEnvelopeV1(
        claim="An unfamiliar causal story remains open to criticism.",
        mechanism="Two delayed loops exchange a conserved discrepancy.",
    )

    assert envelope.model_fields_set == {"claim", "mechanism"}
    assert envelope.analogy is None
    assert envelope.definitions == ()
    assert envelope.premises == ()
    assert envelope.derivation == ()
    assert envelope.scope.covers == ()
    assert envelope.scope.excludes == ()
    assert envelope.uncertainties == ()


def test_scratch_block_optional_fields_remain_optional():
    block = ScratchBlockV1.create(
        body={"content": "A loose conjectural fragment with no forced metadata."},
        instance={"run_id": _hash("a"), "seq": 1},
        provenance={"actor": "llm"},
    )

    assert block.body.model_fields_set == {"content"}
    assert block.body.why_keep_this is None
    assert block.body.unfinished is None
    assert block.body.possible_next_move is None
    assert block.provenance.origin is None
    assert block.provenance.source_refs == []
    assert block.provenance.formal_artifact_refs == []


def test_unknown_and_insufficient_evidence_remain_valid_bridge_outcomes():
    unknown = ClaimLedgerEntryV1.create(
        claim_class=ClaimClass.UNKNOWN,
        claim="The bounded record does not establish the requested value.",
    )
    uncovered = UncoveredRequirementV1.create(
        requirement="Obtain a measurement for the unobserved interval.",
        reason="Neither formal observations nor source evidence cover it.",
        related_ledger_entry_ids=[unknown.id],
    )
    ledger = ClaimLedgerV1.create(
        problem_ref="problem:semantic-freedom",
        formal_seq=0,
        output_target="answer",
        entries=[unknown],
        uncovered_requirements=[uncovered],
    )
    output = BridgeOutputV1.create(
        claim_ledger_id=ledger.id,
        sections=[],
        unresolved_items=[
            UnresolvedItemV1.create(
                description="The requested value remains unresolved.",
                reason="The admitted ledger contains only an explicit unknown.",
                ledger_entry_ids=[unknown.id],
            )
        ],
        resolution="insufficient_evidence",
        resolution_reason="The validated record is insufficient.",
    )

    assert validate_claim_ledger(ledger).valid
    assert validate_bridge_output(ledger, output).valid


def test_observe_only_criticism_remains_warrant_free(harness):
    target = harness.create_artifact(
        "A novel mechanism offered for open scrutiny.",
        provenance=Provenance(role="conjecturer"),
    )
    adapter = LLMAdapter(
        {
            "argumentative_critic": MockEndpoint(
                [
                    json.dumps(
                        {
                            "attack": True,
                            "case": "The mechanism omits a delayed feedback path.",
                        }
                    )
                ]
            )
        },
        harness.blobs,
        retry_max=0,
    )

    critic = crit_argumentative(
        harness,
        target.id,
        adapter,
        Config(ARGUMENTATIVE_AUTHORITY="observe_only"),
    )

    assert critic is not None
    assert harness.state.status[target.id] == Status.ACCEPTED
    assert not harness.warrants
    assert not harness.carried_warrant_ids(critic.id)


def test_context_and_abstention_signals_do_not_directly_transition(harness):
    problem = seed_reasoning_workload(
        harness,
        ReasoningWorkloadSpec(
            problem=WorkloadProblem(
                id="reason:signals",
                description="Characterize a poorly understood transition.",
            )
        ),
    )
    signals = ("need_context", "stuck", "capability_mismatch")
    response = json.dumps(
        {
            "candidates": [
                {
                    "claim": f"Open proposal for {signal}.",
                    "mechanism": f"A distinct provisional mechanism for {signal}.",
                    "counterconditions": [f"The {signal} premise fails."],
                    "typicality": 0.2 + index / 10,
                    "sidecar": {
                        "search_signal": signal,
                        "requested_context_aliases": [],
                    },
                }
                for index, signal in enumerate(signals)
            ]
        }
    )
    adapter = LLMAdapter(
        {"conjecturer": MockEndpoint([response])},
        harness.blobs,
        model_profile="compact",
    )
    diagnostics: list[dict] = []

    admitted = conj(
        harness,
        problem.id,
        adapter,
        Config(VS_K=3, model_profile="compact"),
        diagnostics,
    )

    assert len(admitted) == len(signals)
    assert {row["search_signal"] for row in diagnostics} == set(signals)
    assert all(harness.state.status[item.id] == Status.ACCEPTED for item in admitted)
    assert set(harness.state.problems) == {problem.id}
    llm_events = [event for event in harness.log.read() if event.llm is not None]
    assert len(llm_events) == 1
    assert llm_events[0].rule == Rule.CONJ


@pytest.fixture
def offline_semantic_baseline(tmp_path):
    harness = Harness(tmp_path / "baseline-run")
    commitment = Commitment(id="k-open", eval="predicate:True")
    harness.register_commitment(commitment)
    problem = harness.register_problem(
        Problem(
            id="pi-semantic-baseline",
            description="Propose two independent explanations.",
            criteria=[commitment.id],
            provenance=ProblemProvenance.model_validate(
                {"trigger": "seed", "from": []}
            ),
        )
    )
    responses = [
        "not-json",
        json.dumps(
            {
                "candidates": [
                    {
                        "content": "A delayed-loop explanation from family alpha.",
                        "typicality": 0.21,
                    }
                ]
            }
        ),
        json.dumps(
            {
                "candidates": [
                    {
                        "content": "A boundary-exchange explanation from family beta.",
                        "typicality": 0.37,
                    }
                ]
            }
        ),
    ]
    adapter = LLMAdapter(
        {
            "conjecturer": MockEndpoint(
                responses,
                name="mock://shared-conjecturer-seat",
                model="shared-semantic-model",
            )
        },
        harness.blobs,
        retry_max=1,
    )
    config = Config(VS_K=1, N_SCHOOLS=0)
    artifacts = []
    for school_id, stance in (
        ("school-alpha", "seek delayed causal structure"),
        ("school-beta", "seek boundary counterexamples"),
    ):
        artifacts.extend(
            conj(
                harness,
                problem.id,
                adapter,
                config,
                school={
                    "id": school_id,
                    "stance_text": stance,
                    "weight": 1.0,
                },
            )
        )
    calls = [event.llm for event in harness.log.read() if event.llm is not None]
    return harness, commitment, artifacts, calls


def test_schools_may_share_one_frozen_model_route(offline_semantic_baseline):
    _harness, _commitment, artifacts, calls = offline_semantic_baseline

    assert {artifact.provenance.school for artifact in artifacts} == {
        "school-alpha",
        "school-beta",
    }
    assert {(call.endpoint, call.model) for call in calls} == {
        ("mock://shared-conjecturer-seat", "shared-semantic-model")
    }


def test_offline_semantic_freedom_baseline_is_measurable(
    offline_semantic_baseline,
):
    harness, commitment, artifacts, calls = offline_semantic_baseline
    statuses_before = dict(harness.state.status)
    verdicts = [
        programs.evaluate(commitment, artifact, harness.blobs)[0]
        for artifact in artifacts
    ]
    useful = sum(verdict == programs.PASS for verdict in verdicts)
    measured = {
        "valid_first_attempt_rate": sum(
            bool(call.attempt_trace and call.attempt_trace[0].valid) for call in calls
        )
        / len(calls),
        "repair_rate": sum(call.attempts > 1 for call in calls) / len(calls),
        "candidate_family_count": len(
            {artifact.provenance.school for artifact in artifacts}
        ),
        "unique_candidate_bodies": len(
            {artifact.content_ref for artifact in artifacts}
        ),
        "executable_test_yield": len(verdicts) / len(artifacts),
        "verifier_backed_success_rate": useful / len(verdicts),
        "tokens_per_admitted_useful_candidate": sum(
            call.tokens for call in calls
        )
        / useful,
    }
    baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))

    assert baseline["evidence_class"] == "offline_mock"
    assert baseline["status_input"] is False
    assert measured == baseline["metrics"]
    assert harness.state.status == statuses_before
