"""The DEFAULT successor-question destination: the scratchpad, linked and seen.

Operator law, 2026-08-29 (CLAUDE.md, "Successor questions: optional to propose,
routed by pluggable destination, minting gated off-by-default"): "If it is
filled in, it goes to scratchpad by default, linked to the problem it was
proposed under and visible by conjecturers."

Three claims, and the third is the one that is usually asserted instead of
measured:

- an UNFILLED field records NOTHING AT ALL, so silence in the record means
  "nothing was proposed" rather than "something was dropped"
  (`DR-CON-criticism-source`'s uninvited-dispatch rule);
- a FILLED field becomes exactly one advisory block whose provenance names the
  originating problem -- that is the LINK;
- that block is then SELECTED for an ordinary conjecturer context and appears
  in the rendered pack a conjecturer seat is handed -- that is the VISIBILITY,
  measured through `plan_conjecture_context`, the same path the scheduler uses,
  rather than claimed.

A run whose scratch policy is OFF gets a typed disclosure instead of a silent
discard, because the all-configurations law forbids failing and the record is
the only admissible evidence about what happened.
"""

from __future__ import annotations

import pytest

from deepreason.bridge.retry import WorkflowRetryPolicyV1
from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.ontology import Problem, ProblemProvenance, Rule
from deepreason.run_manifest import (
    ConjectureContextPolicyV1,
    ContractVersionPolicyV1,
    ControlPlanePolicyV1,
    SchoolExecutionPolicyV1,
    compile_run_manifest,
)
from deepreason.scratch.conjecture import plan_conjecture_context
from deepreason.scratch.service import ScratchService
from deepreason.successor import route

STAMP = "2026-08-30T00:00:00Z"
PROBLEM_ID = "pi-successor-route"
QUESTION = "what evidence would settle whether the solar term is measurable here?"


class _Defaults:
    """A configuration naming no destination: the shipped default case."""


# --- the run manifest, compiled for real ----------------------------------- #


def _config(*, scratch_enabled: bool = True) -> Config:
    return Config(
        N_SCHOOLS=0,
        VS_K=1,
        FLOOR=0,
        SPEC_INJECTION=False,
        CONTROLLER=False,
        NEAR_DUP_EPS=None,
        RETRY_MAX=0,
        model_profile="standard",
        scratchpad={
            "enabled": scratch_enabled,
            "max_blocks_per_pack": 4,
            "max_guides_per_pack": 0,
            "semantic_retrieval": False,
            "keyword_retrieval": True,
            "coverage_enabled": False,
            "exploratory_fraction": 0.0,
            "underexposed_fraction": 0.0,
        },
        roles={
            "conjecturer": {
                "endpoint_id": "conjecturer-0",
                "endpoint": "mock://conjecturer-0",
                "model": "offline-conjecturer",
                "provider": "mock",
                "family": "offline-family",
                "max_tokens": 512,
            }
        },
    )


def _control_policy() -> ControlPlanePolicyV1:
    return ControlPlanePolicyV1(
        controller_version="workflow.controller.v1",
        mode="active_conjecture",
        workflow_profile="conjecture.active.v1",
        school_execution=SchoolExecutionPolicyV1(
            mode="conditioning_only",
            bindings=(),
            allow_shared=True,
            require_distinct_models=False,
            require_distinct_families=False,
        ),
        conjecture_context=ConjectureContextPolicyV1(
            mode="harness_only",
            initial_max_blocks=4,
            initial_max_guides=0,
            max_context_expansion_requests=0,
            max_extra_blocks=0,
            permitted_retrieval_channels=("focus", "keyword", "recent"),
            coverage_slot_mandatory=False,
            exploration_slot_mandatory=False,
        ),
        workflow_retry=WorkflowRetryPolicyV1(),
        contract_versions=ContractVersionPolicyV1(
            bridge_ledger_wire_contract="bridge.ledger.v2",
            conjecturer_turn_contract="conjecturer.turn.v4",
            control_event_schema="control.event.v1",
        ),
        capability_profile="conjecture-control.v1",
    )


def _manifest(*, scratch_enabled: bool = True):
    return compile_run_manifest(
        _config(scratch_enabled=scratch_enabled),
        schema_version=4,
        workload_profile="text",
        rubric_policy="forbid",
        compiled_at=STAMP,
        control_plane_policy=_control_policy(),
    )


@pytest.fixture
def bound(tmp_path, monkeypatch):
    """A harness whose bound manifest enables the workshop."""

    manifest = _manifest(scratch_enabled=True)
    monkeypatch.setattr(
        Harness, "_load_workflow_manifest", lambda self: manifest
    )
    harness = Harness(tmp_path / "run")
    return harness, manifest


def _seed(harness) -> Problem:
    return harness.register_problem(
        Problem(
            id=PROBLEM_ID,
            description="explain the tide table for this harbour",
            provenance=ProblemProvenance.model_validate(
                {"trigger": "seed", "from": []}
            ),
        )
    )


def _receipts(harness) -> list[list[str]]:
    return [
        list(event.inputs)
        for event in harness.log.read()
        if event.rule == Rule.MEASURE
        and event.inputs
        and event.inputs[0].startswith("successor-question:")
    ]


# --- an unfilled field records nothing at all ------------------------------ #


@pytest.mark.parametrize("empty", [None, "", "   "])
def test_an_unfilled_field_records_nothing_at_all(tmp_path, empty):
    """The uninvited-dispatch rule. A receipt here would destroy the very
    difference the receipt records: before this channel, "proposed nothing" and
    "was never able to propose" would both be zero."""
    harness = Harness(tmp_path / "run")
    before = harness._next_seq
    assert route(harness, _Defaults(), problem_id=PROBLEM_ID, question=empty) is None
    assert harness._next_seq == before
    assert harness.scratch_state.blocks == {}
    assert _receipts(harness) == []


# --- a filled field becomes one linked block ------------------------------- #


def test_a_filled_field_becomes_exactly_one_linked_block(tmp_path):
    """The LINK is `ScratchProvenanceV1.origin`, which is a free string outside
    the block's `body_hash` -- so carrying the problem id costs no stored block
    id. The actor must be `llm`: BLOCK_CREATED is an interpretive action and
    the event validator refuses a harness-authored one."""
    harness = Harness(tmp_path / "run")
    _seed(harness)
    block = route(harness, _Defaults(), problem_id=PROBLEM_ID, question=QUESTION)

    assert block is not None
    assert list(harness.scratch_state.blocks) == [block.id]
    assert block.body.content == QUESTION
    assert block.body.unfinished == "Successor question"
    assert block.provenance.origin == PROBLEM_ID
    assert block.provenance.actor.value == "llm"
    assert _receipts(harness) == [
        ["successor-question:ROUTED", "scratchpad.v1", PROBLEM_ID]
    ]


def test_a_proposal_with_no_problem_to_link_to_discloses_and_routes_nothing(tmp_path):
    """"Linked to the problem it was proposed under" is a CONDITION, not a
    decoration: with no problem there is nothing to link to, so nothing is
    written and the absence is recorded rather than inferred."""
    harness = Harness(tmp_path / "run")
    assert route(harness, _Defaults(), problem_id=None, question=QUESTION) is None
    assert harness.scratch_state.blocks == {}
    assert _receipts(harness) == [["successor-question:UNLINKED", "scratchpad.v1"]]


def test_routing_writes_no_artifact_and_no_attack_edge(tmp_path):
    """The workshop is advisory. A routed question adds a block and a Measure,
    and nothing that adjudication can see."""
    harness = Harness(tmp_path / "run")
    _seed(harness)
    route(harness, _Defaults(), problem_id=PROBLEM_ID, question=QUESTION)
    assert harness.state.artifacts == {}
    assert harness.state.att == []
    assert harness.state.status == {}


# --- the visibility half, MEASURED ----------------------------------------- #


def test_the_routed_block_reaches_a_conjecturer_context(bound):
    """R2's second half, measured on the path the scheduler actually uses.

    `plan_conjecture_context` is what `Scheduler._plan_conjecture_context`
    calls; the assertion is that the routed block is SELECTED by it and appears
    in the render receipt's ordered block refs -- the handles a conjecturer
    seat is handed. Asserting "the scratchpad is visible to conjecturers" in
    prose would prove nothing: this is the same claim with a command behind it.
    """
    harness, manifest = bound
    problem = _seed(harness)
    block = route(harness, _Defaults(), problem_id=problem.id, question=QUESTION)
    assert block is not None

    service = ScratchService(harness)
    fence = harness._next_seq - 1
    plan = plan_conjecture_context(
        service,
        problem=problem,
        school_id=None,
        manifest_digest=manifest.sha256,
        scratch_policy=manifest.scratch_policy,
        context_policy=manifest.control_plane_policy.conjecture_context,
        formal_fence_seq=fence,
        scratch_fence_seq=fence,
    )
    assert plan is not None
    assert block.id in [item.id for item in plan.attention_pack.blocks]
    assert block.id in plan.rendered_context.receipt.ordered_refs("block")
    assert QUESTION in plan.rendered_context.text


# --- a disabled workshop discloses rather than discarding ------------------ #


def test_a_scratch_disabled_run_discloses_instead_of_discarding(tmp_path):
    """Never a silent discard. A run whose workshop is off still records that a
    question was proposed and could not be placed, so an operator reading the
    record can tell the difference between "nobody proposed one" and "one was
    proposed into a void".

    The policy is read from the CONFIGURATION, which is where a
    manifest-launched run has it reconstructed from the compiled policy -- one
    answer rather than two that can disagree.
    """
    harness = Harness(tmp_path / "run")
    _seed(harness)
    off = _config(scratch_enabled=False)
    assert off.scratchpad.enabled is False

    assert route(harness, off, problem_id=PROBLEM_ID, question=QUESTION) is None
    assert harness.scratch_state.blocks == {}
    assert _receipts(harness) == [
        ["successor-question:UNAVAILABLE", "scratchpad.v1", PROBLEM_ID]
    ]


def test_an_enabled_workspace_routes_through_the_same_configuration(tmp_path):
    """The other side of the same switch, so the disclosure above is not merely
    a function that always refuses."""
    harness = Harness(tmp_path / "run")
    _seed(harness)
    on = _config(scratch_enabled=True)
    assert on.scratchpad.enabled is True

    block = route(harness, on, problem_id=PROBLEM_ID, question=QUESTION)
    assert block is not None
    assert list(harness.scratch_state.blocks) == [block.id]
    assert _receipts(harness) == [
        ["successor-question:ROUTED", "scratchpad.v1", PROBLEM_ID]
    ]
