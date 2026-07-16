"""Stage B4 bounded model recourse without workflow authority."""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from deepreason.bridge.retry import WorkflowRetryPolicyV1
from deepreason.canonical import canonical_json
from deepreason.config import Config
from deepreason.conjecture_events import (
    ConjectureTurnAction,
    ConjectureTurnEventPayloadV1,
)
from deepreason.conjecture_turn import (
    ConjectureAbstentionV1,
    ConjecturerTurnV4,
    ContextRequestV1,
    ReasoningConjecturerTurnV4,
)
from deepreason.harness import Harness
from deepreason.invariants import verify_root
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.budget import TokenMeter
from deepreason.llm.contracts import ConjectureCandidate
from deepreason.llm.endpoints import MockEndpoint
from deepreason.llm.firewall import ModelControlFieldError, leases_from_manifest
from deepreason.llm.wire import (
    AliasTable,
    ConjecturerTurnWireContractV4,
    minimal_example,
)
from deepreason.ontology import Problem, ProblemProvenance, Rule
from deepreason.rules.conj import conj
from deepreason.scheduler.scheduler import Scheduler
from deepreason.run_manifest import (
    ConjectureContextPolicyV1,
    ContractVersionPolicyV1,
    ControlPlanePolicyV1,
    RunManifest,
    SchoolExecutionPolicyV1,
    bind_run_manifest,
    compile_run_manifest,
)
from deepreason.scratch.conjecture import (
    plan_conjecture_context,
    plan_conjecture_context_expansion,
)
from deepreason.scratch.models import RetrievalChannel, ScratchProvenanceV1
from deepreason.scratch.render import ScratchRenderReceiptV1
from deepreason.scratch.service import ScratchService
from deepreason.workloads.text import ReasoningCandidateProposal


STAMP = "2026-07-16T00:00:00Z"
PROBLEM_ID = "pi-conjecturer-turn-v4"
OTHER_PROBLEM_ID = "pi-conjecturer-turn-v4-other"


def _wire_receipt() -> ScratchRenderReceiptV1:
    return ScratchRenderReceiptV1.create(
        state_seq=2,
        attention_receipt="sha256:" + "a" * 64,
        block_handles={"B1": "sha256:" + "b" * 64},
        cluster_handles={},
        link_handles={},
        guide_handles={},
    )


def _wire_contract() -> ConjecturerTurnWireContractV4:
    """One call-local contract: no formal aliases and one visible scratch block."""

    return ConjecturerTurnWireContractV4(
        reasoning=False,
        aliases=AliasTable(),
        scratch_aliases=_wire_receipt().block_handles,
        permitted_retrieval_channels=("keyword",),
    )


def _request_wire(
    *,
    query: str = "look for the delayed feedback note",
    aliases: list[str] | None = None,
    channels: list[str] | None = None,
) -> dict:
    return {
        "query": query,
        "requested_visible_aliases": aliases or [],
        "desired_retrieval_channels": channels or ["keyword"],
        "purpose": None,
    }


def _candidate_wire(content: str = "A provisional nonstandard mechanism.") -> dict:
    return {
        "content": content,
        "typicality": 0.37,
        "neighbours": [],
    }


def test_request_only_is_a_meaningful_turn_outcome():
    turn = _wire_contract().parse_compile(
        json.dumps({"context_request": _request_wire(aliases=["B1"])})
    )
    assert isinstance(turn, ConjecturerTurnV4)
    assert turn.candidates == ()
    assert turn.context_request is not None
    assert turn.context_request.query == "look for the delayed feedback note"
    assert turn.context_request.requested_refs == (
        "sha256:" + "b" * 64,
    )
    assert turn.abstention is None


def test_candidates_and_context_request_may_coexist():
    turn = _wire_contract().parse_compile(
        json.dumps(
            {
                "candidates": [_candidate_wire("A candidate worth testing now.")],
                "context_request": _request_wire(),
            }
        )
    )
    assert len(turn.candidates) == 1
    assert turn.candidates[0].content == "A candidate worth testing now."
    assert turn.context_request is not None


def test_existing_reasoning_need_context_signal_compiles_to_one_request():
    contract = ConjecturerTurnWireContractV4(
        reasoning=True,
        aliases=AliasTable(),
        scratch_aliases=_wire_receipt().block_handles,
        permitted_retrieval_channels=("keyword",),
    )
    turn = contract.parse_compile(
        json.dumps(
            {
                "candidates": [
                    {
                        "claim": "A provisional explanation can coexist with recourse.",
                        "mechanism": "A still-open coupling shifts the response.",
                        "counterconditions": ["The coupling vanishes."],
                        "typicality": 0.31,
                        "optional_refs": [],
                        "sidecar": {
                            "search_signal": "need_context",
                            "requested_context_aliases": ["B1"],
                        },
                    }
                ]
            }
        )
    )
    assert isinstance(turn, ReasoningConjecturerTurnV4)
    assert len(turn.candidates) == 1
    assert turn.context_request is not None
    assert turn.context_request.requested_refs == ("sha256:" + "b" * 64,)


def test_reasoning_merged_context_refs_cannot_bypass_canonical_limit():
    scratch_aliases = {
        f"B{index}": "sha256:" + f"{index:064x}"
        for index in range(1, 66)
    }
    contract = ConjecturerTurnWireContractV4(
        reasoning=True,
        aliases=AliasTable(),
        scratch_aliases=scratch_aliases,
        permitted_retrieval_channels=("keyword",),
    )
    candidate = {
        "claim": "A bounded proposal can still request visible context.",
        "mechanism": "The sidecar contributes call-local aliases.",
        "counterconditions": ["The aliases do not identify visible context."],
        "typicality": 0.29,
        "optional_refs": [],
        "sidecar": {
            "search_signal": "need_context",
            # Individually this sidecar is valid. Merging it with the explicit
            # request below crosses ContextRequestV1's canonical limit of 64.
            "requested_context_aliases": [
                f"B{index}" for index in range(2, 66)
            ],
        },
    }

    with pytest.raises((ValidationError, ValueError), match="64|length|requested"):
        contract.parse_compile(
            json.dumps(
                {
                    "candidates": [candidate],
                    "context_request": _request_wire(aliases=["B1"]),
                }
            )
        )


def test_bounded_abstention_needs_no_fabricated_reason():
    turn = ConjecturerTurnV4(
        abstention=ConjectureAbstentionV1(
            search_signal="capability_mismatch",
            note=None,
        )
    )
    assert turn.candidates == ()
    assert turn.context_request is None
    assert turn.abstention.note is None

    with pytest.raises(ValidationError, match="search_signal"):
        ConjectureAbstentionV1(search_signal="productive", note=None)
    with pytest.raises(ValidationError, match="meaningful|search_signal"):
        ConjecturerTurnV4()


@pytest.mark.parametrize("payload", ({}, {"purpose": "Purpose alone is not a query."}))
def test_context_request_requires_bounded_search_material(payload: dict):
    with pytest.raises(ValidationError, match="meaningful|query|alias|channel"):
        ContextRequestV1.model_validate(payload)


def test_candidates_and_abstention_are_mutually_exclusive():
    with pytest.raises(ValidationError, match="candidate|abstention|exclusive"):
        ConjecturerTurnV4(
            candidates=(
                ConjectureCandidate(
                    content="A real candidate cannot simultaneously be no-proposal.",
                    typicality=0.41,
                ),
            ),
            abstention=ConjectureAbstentionV1(search_signal="stuck"),
        )


def test_prompt_minimal_example_is_a_valid_v4_turn():
    contract = _wire_contract()
    wire = contract.validate_value(json.loads(minimal_example(contract)))
    turn = contract.compile(wire)
    assert isinstance(turn, ConjecturerTurnV4)
    assert turn.candidates or turn.context_request or turn.abstention


@pytest.mark.parametrize(
    "unseen",
    (
        "B2",
        "sha256:" + "c" * 64,
        "c" * 64,
    ),
)
def test_context_request_rejects_unseen_or_canonical_ids(unseen: str):
    contract = _wire_contract()
    with pytest.raises(ValueError, match="alias|canonical|unknown|visible"):
        contract.parse_compile(
            json.dumps(
                {
                    "context_request": _request_wire(aliases=[unseen]),
                }
            )
        )


def test_context_request_never_grants_direct_open_retrieval():
    contract = ConjecturerTurnWireContractV4(
        reasoning=False,
        aliases=AliasTable(),
        scratch_aliases=_wire_receipt().block_handles,
        # Even accidental policy exposure cannot turn direct-open access into
        # model authority.
        permitted_retrieval_channels=("direct_open",),
    )
    with pytest.raises(ValueError, match="direct_open|retrieval channel|policy"):
        contract.parse_compile(
            json.dumps(
                {
                    "context_request": _request_wire(
                        channels=["direct_open"],
                    )
                }
            )
        )


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("route", "alternate"),
        ("phase", "finalize"),
        ("budget", {"tokens": 1000000}),
        ("status", "accepted"),
    ),
)
def test_context_request_cannot_author_control_fields(field: str, value):
    payload = {"context_request": {**_request_wire(), field: value}}
    with pytest.raises(ValueError) as raised:
        _wire_contract().validate_value(payload)
    if isinstance(raised.value, ModelControlFieldError):
        assert raised.value.code == "MODEL_CONTROL_FIELD_FORBIDDEN"
        assert raised.value.field == field
    else:
        assert f"/{field}" in str(raised.value)


def test_semantic_candidate_fields_remain_open_vocabulary():
    request = ContextRequestV1(
        query="Seek a different conceptual frame.",
        desired_retrieval_channels=(RetrievalChannel.KEYWORD,),
    )
    assert request.query.startswith("Seek a different")

    ordinary = ConjecturerTurnV4(
        candidates=(
            ConjectureCandidate(
                content=(
                    "A palimpsestic phase braid could preserve local disagreement; "
                    "this is deliberately outside any fixed mechanism taxonomy."
                ),
                typicality=0.11,
            ),
        )
    )
    assert "palimpsestic phase braid" in ordinary.candidates[0].content

    reasoning = ReasoningConjecturerTurnV4(
        candidates=(
            ReasoningCandidateProposal(
                claim="The transition may depend on an unclassified coupling.",
                mechanism="A bespoke Möbius-lattice coupling with no enum label.",
                counterconditions=("The coupling disappears under inversion.",),
                typicality=0.23,
            ),
        )
    )
    assert reasoning.candidates[0].mechanism.startswith("A bespoke Möbius-lattice")


def _config(*, schools: int = 0) -> Config:
    return Config(
        N_SCHOOLS=schools,
        VS_K=1,
        FLOOR=0,
        SPEC_INJECTION=False,
        CONTROLLER=False,
        NEAR_DUP_EPS=None,
        RETRY_MAX=0,
        RESEARCH_BACKEND=None,
        model_profile="standard",
        scratchpad={
            "enabled": True,
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


def _manifest(
    config: Config,
    *,
    permitted_channels: tuple[str, ...] = ("focus", "keyword", "recent"),
    max_expansions: int = 1,
    initial_max_blocks: int = 1,
    max_extra_blocks: int = 1,
    context_mode: str = "harness_plus_model_request",
) -> RunManifest:
    expandable = context_mode == "harness_plus_model_request"
    context = ConjectureContextPolicyV1(
        mode=context_mode,
        initial_max_blocks=initial_max_blocks,
        initial_max_guides=0,
        max_context_expansion_requests=max_expansions if expandable else 0,
        max_extra_blocks=max_extra_blocks if expandable else 0,
        permitted_retrieval_channels=permitted_channels,
        coverage_slot_mandatory=False,
        exploration_slot_mandatory=False,
    )
    control = ControlPlanePolicyV1(
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
        conjecture_context=context,
        workflow_retry=WorkflowRetryPolicyV1(),
        contract_versions=ContractVersionPolicyV1(
            bridge_ledger_wire_contract="bridge.ledger.v2",
            conjecturer_turn_contract="conjecturer.turn.v4",
            control_event_schema="control.event.v1",
        ),
        capability_profile="conjecture-control.v1",
    )
    return compile_run_manifest(
        config,
        schema_version=4,
        workload_profile="text",
        rubric_policy="forbid",
        compiled_at=STAMP,
        control_plane_policy=control,
    )


def _seed_run(
    tmp_path,
    *,
    permitted_channels=("focus", "keyword", "recent"),
    max_expansions=1,
    initial_max_blocks=1,
    max_extra_blocks=1,
    context_mode="harness_plus_model_request",
    school_id: str | None = None,
    include_other_problem: bool = False,
):
    # Include a second canonical school for the later invariant-tamper case;
    # the live call itself remains bound to school-0.
    config = _config(schools=2 if school_id is not None else 0)
    manifest = _manifest(
        config,
        permitted_channels=permitted_channels,
        max_expansions=max_expansions,
        initial_max_blocks=initial_max_blocks,
        max_extra_blocks=max_extra_blocks,
        context_mode=context_mode,
    )
    root = tmp_path / "run"
    bind_run_manifest(manifest, root)
    harness = Harness(root)
    problem = harness.register_problem(
        Problem(
            id=PROBLEM_ID,
            description="Explain why delayed feedback may stabilize this record.",
            provenance=ProblemProvenance.model_validate(
                {"trigger": "seed", "from": []}
            ),
        )
    )
    if include_other_problem:
        harness.register_problem(
            Problem(
                id=OTHER_PROBLEM_ID,
                description="A second canonical problem used only for identity tampering.",
                provenance=ProblemProvenance.model_validate(
                    {"trigger": "seed", "from": []}
                ),
            )
        )
    service = ScratchService(harness)
    provenance = ScratchProvenanceV1(actor="user", origin="b4-test")
    focus = service.create_block(
        {"content": "Delayed feedback is the explicit focus block."},
        provenance.model_copy(update={"formal_artifact_refs": [problem.id]}),
    )
    expansion = service.create_block(
        {
            "content": (
                "quasar-only topology supplies a distant alternative."
            )
        },
        provenance,
    )
    tertiary = service.create_block(
        {
            "content": (
                "tertiary-only material would require another expansion."
            )
        },
        provenance,
    )
    fence = harness._next_seq - 1
    plan = plan_conjecture_context(
        service,
        problem=problem,
        school_id=school_id,
        manifest_digest=manifest.sha256,
        scratch_policy=manifest.scratch_policy,
        context_policy=manifest.control_plane_policy.conjecture_context,
        formal_fence_seq=fence,
        scratch_fence_seq=fence,
    )
    assert plan is not None
    assert plan.attention_pack.selection_receipt.final_order == [focus.id]
    return harness, service, problem, config, manifest, plan, focus, expansion, tertiary


def test_expansion_cap_counts_blocks_actually_added_to_the_prior_view(tmp_path):
    (
        harness,
        service,
        problem,
        _config_,
        manifest,
        prior,
        focus,
        expansion,
        tertiary,
    ) = _seed_run(
        tmp_path,
        permitted_channels=("focus", "keyword"),
        # Deliberately leave the initial allocation under-filled. The expansion
        # budget is one added block, not all unused initial capacity plus one.
        initial_max_blocks=3,
        max_extra_blocks=1,
    )
    fence = harness._next_seq - 1
    expanded = plan_conjecture_context_expansion(
        service,
        problem=problem,
        school_id=None,
        manifest_digest=manifest.sha256,
        scratch_policy=manifest.scratch_policy,
        context_policy=manifest.control_plane_policy.conjecture_context,
        request=ContextRequestV1(
            query="quasar-only tertiary-only",
            desired_retrieval_channels=(RetrievalChannel.KEYWORD,),
        ),
        prior_plan=prior,
        expansion_decision_ref="sha256:" + "d" * 64,
        expansion_index=1,
        formal_fence_seq=fence,
        scratch_fence_seq=fence,
    )
    assert expanded is not None
    original_ids = prior.attention_pack.selection_receipt.final_order
    expanded_ids = expanded.attention_pack.selection_receipt.final_order
    assert expanded_ids[: len(original_ids)] == original_ids == [focus.id]
    assert len(expanded_ids) == len(original_ids) + 1
    assert set(expanded_ids) - set(original_ids) <= {expansion.id, tertiary.id}


def _run_turn(
    tmp_path,
    responses,
    *,
    permitted_channels=("focus", "keyword", "recent"),
    max_expansions=1,
    initial_max_blocks=1,
    max_extra_blocks=1,
    context_mode="harness_plus_model_request",
    school_id: str | None = None,
    include_other_problem: bool = False,
):
    fixture = _seed_run(
        tmp_path,
        permitted_channels=permitted_channels,
        max_expansions=max_expansions,
        initial_max_blocks=initial_max_blocks,
        max_extra_blocks=max_extra_blocks,
        context_mode=context_mode,
        school_id=school_id,
        include_other_problem=include_other_problem,
    )
    harness, _service, problem, config, manifest, plan, *_blocks = fixture
    pending = [json.dumps(response) for response in responses]
    prompts: list[str] = []

    def complete(prompt: str) -> str:
        prompts.append(prompt)
        if not pending:
            raise AssertionError("unexpected extra conjecturer call")
        return pending.pop(0)

    endpoint = MockEndpoint(
        complete,
        name=manifest.roles["conjecturer"][0].base_url,
        model=manifest.roles["conjecturer"][0].model_id,
        max_tokens=512,
    )
    adapter = LLMAdapter(
        {"conjecturer": endpoint},
        harness.blobs,
        retry_max=0,
        model_profile=manifest.model_profile,
        leases=leases_from_manifest(manifest),
    )
    admitted = conj(
        harness,
        problem.id,
        adapter,
        config,
        workload_profile="text",
        school=(
            {
                "id": school_id,
                "stance_text": "A bounded school identity for receipt tests.",
                "weight": 1.0,
                "crossover": [],
            }
            if school_id is not None
            else None
        ),
        endpoint_lease=(
            adapter.leases["conjecturer"][0]
            if school_id is not None
            else None
        ),
        execution_school_id=school_id,
        conjecture_context_plan=plan,
        run_manifest=manifest,
    )
    return fixture, admitted, prompts


def _turn_events(harness: Harness):
    events = [
        event
        for event in harness.log.read()
        if getattr(event, "conjecture_turn", None) is not None
    ]
    assert all(event.rule == Rule.CONJECTURE_TURN for event in events)
    return events


def _replace_turn_payload(
    payload: ConjectureTurnEventPayloadV1,
    **updates,
) -> ConjectureTurnEventPayloadV1:
    values = payload.model_dump(mode="json", by_alias=True, exclude_none=True)
    values.pop("schema")
    values.pop("decision_id")
    return ConjectureTurnEventPayloadV1.create(**{**values, **updates})


def _rewrite_logged_event(harness: Harness, predicate, mutate) -> None:
    records = [json.loads(line) for line in harness.log.path.read_text().splitlines()]
    target = next(record for record in records if predicate(record))
    mutate(target)
    harness.log.path.write_text(
        "".join(
            json.dumps(record, separators=(",", ":")) + "\n"
            for record in records
        )
    )


def _payload_text(event) -> str:
    return json.dumps(
        event.conjecture_turn.model_dump(mode="json", by_alias=True),
        sort_keys=True,
    )


def _request_only(query: str, channel: str = "keyword") -> dict:
    return {
        "context_request": _request_wire(
            query=query,
            channels=[channel],
        )
    }


def test_one_configured_expansion_records_original_and_expanded_receipts(tmp_path):
    fixture, admitted, prompts = _run_turn(
        tmp_path,
        [
            _request_only("quasar-only", "keyword"),
            {"candidates": [_candidate_wire("The quasar topology is testable.")]},
        ],
    )
    harness, service, _problem, _config_, _manifest_, _plan_, focus, expansion, _ = fixture
    assert len(admitted) == 1
    assert len(prompts) == 2
    initial_prompt = prompts[0].casefold()
    assert "return exactly" not in initial_prompt
    assert "context_request" in initial_prompt
    assert "abstention" in initial_prompt

    turns = _turn_events(harness)
    assert len(turns) == 1
    assert "context_granted" in _payload_text(turns[0])
    calls = [
        event.llm
        for event in harness.log.read()
        if event.llm is not None and event.llm.role == "conjecturer"
    ]
    assert len(calls) == 2
    assert calls[0].conjecture_context is not None
    assert calls[1].conjecture_context is not None
    original = calls[0].conjecture_context
    expanded = calls[1].conjecture_context
    assert original.selection_receipt_ref != expanded.selection_receipt_ref
    expanded_context = service.state.advisory_contexts[expanded.advisory_context_ref]
    assert [block.id for block in expanded_context.blocks] == [focus.id, expansion.id]

    # The follow-up receipt links to the original selection, while each call
    # retains its own complete selection/advisory/render provenance.
    assert expanded.prior_selection_receipt_ref == original.selection_receipt_ref
    assert list(expanded.root_block_refs) == [focus.id]
    assert expanded.expansion_decision_ref is not None
    for receipt in (original, expanded):
        assert receipt.selection_receipt_ref in service.state.attention_receipts
        assert receipt.advisory_context_ref in service.state.advisory_contexts
        assert harness.blobs.get(receipt.render_receipt_ref)
        assert harness.blobs.get(receipt.rendered_context_ref)

    # Active-v4 call accounting stays process-owned; the formal registration
    # does not duplicate the follow-up LLM call.
    register = next(event for event in harness.log.read() if admitted[0].id in event.outputs)
    assert register.llm is None
    assert verify_root(harness.root)["violations"] == []


def test_expanded_receipts_bind_root_and_invariants_enforce_cumulative_cap(tmp_path):
    fixture, admitted, prompts = _run_turn(
        tmp_path,
        [
            _request_only("quasar-only", "keyword"),
            _request_only("tertiary-only", "keyword"),
            {"candidates": [_candidate_wire("Both added blocks are now visible.")]},
        ],
        max_expansions=2,
        max_extra_blocks=2,
    )
    harness, service, _problem, _config_, _manifest_, _plan_, focus, expansion, tertiary = (
        fixture
    )
    assert len(admitted) == 1
    assert len(prompts) == 3

    call_events = [
        event
        for event in harness.log.read()
        if event.llm is not None and event.llm.role == "conjecturer"
    ]
    expanded_events = [
        event
        for event in call_events
        if event.llm.conjecture_context is not None
        and event.llm.conjecture_context.expansion_index is not None
    ]
    assert [
        event.llm.conjecture_context.expansion_index for event in expanded_events
    ] == [1, 2]
    for event in expanded_events:
        receipt = event.llm.conjecture_context
        assert list(receipt.root_block_refs) == [focus.id]
        selection = service.state.attention_receipts[receipt.selection_receipt_ref]
        cumulative = [
            block_id
            for block_id in selection.final_order
            if block_id not in set(receipt.root_block_refs)
        ]
        assert len(cumulative) <= 2

    second = expanded_events[-1].llm.conjecture_context
    second_context = service.state.advisory_contexts[second.advisory_context_ref]
    assert [block.id for block in second_context.blocks] == [
        focus.id,
        expansion.id,
        tertiary.id,
    ]
    assert verify_root(harness.root)["violations"] == []

    # Empty roots are valid when the initial view was empty, so receipt shape
    # alone cannot catch this tamper. Replay invariants must apply max_extra to
    # the full selection relative to the persisted root.
    second_seq = expanded_events[-1].seq
    _rewrite_logged_event(
        harness,
        lambda record: record["seq"] == second_seq,
        lambda record: record["llm"]["conjecture_context"].__setitem__(
            "root_block_refs", []
        ),
    )
    violations = verify_root(harness.root)["violations"]
    assert any(
        item["check"] in {"conjecture-context", "conjecture-turn"}
        and any(
            token in item["detail"].casefold()
            for token in ("root", "cumulative", "extra", "expanded")
        )
        for item in violations
    )


def test_grant_source_and_child_bind_problem_manifest_context_and_school(tmp_path):
    fixture, admitted, _prompts = _run_turn(
        tmp_path,
        [
            _request_only("quasar-only", "keyword"),
            {
                "abstention": {
                    "search_signal": "stuck",
                    "note": "The school-bound follow-up remains inconclusive.",
                }
            },
        ],
        school_id="school-0",
        include_other_problem=True,
    )
    harness, _service, problem, _config_, manifest, _plan_, *_blocks = fixture
    assert admitted == []
    grant_event = next(
        event
        for event in _turn_events(harness)
        if event.conjecture_turn.action == ConjectureTurnAction.CONTEXT_GRANTED
    )
    grant = grant_event.conjecture_turn
    assert grant.action == ConjectureTurnAction.CONTEXT_GRANTED

    source_event = next(
        event for event in harness.log.read() if event.seq == grant.source_call_seq
    )
    assert source_event.inputs[0] == "conjecture-turn-call"
    assert any(problem.id in value for value in source_event.inputs)
    assert any(manifest.sha256 in value for value in source_event.inputs)
    source_context = source_event.llm.conjecture_context
    assert source_context.problem_id == grant.problem_id == problem.id
    assert source_context.manifest_digest == grant.manifest_digest == manifest.sha256
    assert source_context.school_id == grant.school_id == "school-0"
    assert source_context.selection_receipt_ref == grant.prior_selection_receipt_ref

    child_event = next(
        event
        for event in harness.log.read()
        if event.llm is not None
        and event.llm.conjecture_context is not None
        and event.llm.conjecture_context.expansion_decision_ref == grant.decision_id
    )
    child = child_event.llm.conjecture_context
    assert child.problem_id == grant.problem_id
    assert child.manifest_digest == grant.manifest_digest
    assert child.school_id == grant.school_id
    assert verify_root(harness.root)["violations"] == []

    # Keep the forged child internally self-consistent with its route so only
    # the exact grant/source identity comparison can reject it. The alternate
    # problem was canonical before the context fence.
    def forge_child(record: dict) -> None:
        record["llm"]["conjecture_context"]["problem_id"] = OTHER_PROBLEM_ID
        record["llm"]["conjecture_context"]["school_id"] = "school-1"
        record["llm"]["school_route"]["school_id"] = "school-1"

    _rewrite_logged_event(
        harness,
        lambda record: record["seq"] == child_event.seq,
        forge_child,
    )
    violations = verify_root(harness.root)["violations"]
    assert any(
        item["check"] in {"conjecture-turn", "open"}
        and any(
            token in item["detail"].casefold()
            for token in ("school", "problem", "authority")
        )
        for item in violations
    )


def test_active_v4_rejects_raw_generation_context_before_provider_spend(tmp_path):
    harness, _service, problem, config, manifest, _plan_, *_blocks = _seed_run(
        tmp_path
    )
    provider_calls = 0

    def complete(_prompt: str) -> str:
        nonlocal provider_calls
        provider_calls += 1
        return json.dumps({"candidates": [_candidate_wire()]})

    meter = TokenMeter(budget=100_000)
    endpoint = MockEndpoint(
        complete,
        name=manifest.roles["conjecturer"][0].base_url,
        model=manifest.roles["conjecturer"][0].model_id,
        max_tokens=512,
    )
    adapter = LLMAdapter(
        {"conjecturer": endpoint},
        harness.blobs,
        meter=meter,
        retry_max=0,
        model_profile=manifest.model_profile,
        leases=leases_from_manifest(manifest),
    )
    next_seq = harness._next_seq

    with pytest.raises(ValueError, match="generation_context|raw.*context|typed"):
        conj(
            harness,
            problem.id,
            adapter,
            config,
            workload_profile="text",
            generation_context="MODEL-UNBOUNDED RAW CONTEXT",
            # Deliberately omit the typed plan: active-v4 forbids this legacy
            # escape hatch even when no scratch context was prepared.
            conjecture_context_plan=None,
            run_manifest=manifest,
        )

    assert provider_calls == 0
    assert harness._next_seq == next_seq
    assert meter.snapshot() == {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total": 0,
        "budget": 100_000,
        "calls": 0,
        "reserved": 0,
    }


@pytest.mark.parametrize("evidence_kind", ("request", "abstention"))
def test_record_turn_event_rejects_noncanonical_evidence_before_append(
    tmp_path,
    evidence_kind: str,
):
    if evidence_kind == "request":
        fixture, _admitted, _prompts = _run_turn(
            tmp_path,
            [_request_only("quasar-only", "keyword")],
            context_mode="harness_only",
        )
        harness = fixture[0]
        original = _turn_events(harness)[0].conjecture_turn
        alternate = ContextRequestV1(
            query="A different canonical request blob.",
            desired_retrieval_channels=(RetrievalChannel.KEYWORD,),
        )
        alternate_ref = harness.blobs.put(
            canonical_json(alternate.model_dump(mode="json", exclude_none=True))
        )
        forged = _replace_turn_payload(original, request_ref=alternate_ref)
        evidence_args = {"request": alternate}
    else:
        fixture, _admitted, _prompts = _run_turn(
            tmp_path,
            [
                {
                    "abstention": {
                        "search_signal": "stuck",
                        "note": "The current view does not support a proposal.",
                    }
                }
            ],
        )
        harness = fixture[0]
        original = _turn_events(harness)[0].conjecture_turn
        alternate = ConjectureAbstentionV1(
            search_signal="capability_mismatch",
            note="A different canonical abstention blob.",
        )
        alternate_ref = harness.blobs.put(
            canonical_json(alternate.model_dump(mode="json", exclude_none=True))
        )
        forged = _replace_turn_payload(original, abstention_ref=alternate_ref)
        evidence_args = {"abstention": alternate}

    next_seq = harness._next_seq
    with pytest.raises(ValueError, match="request|abstention|evidence|hash|canonical"):
        harness.record_conjecture_turn_event(forged, **evidence_args)
    assert harness._next_seq == next_seq
    assert len(_turn_events(harness)) == 1


def test_record_turn_event_validates_source_call_before_append(tmp_path):
    fixture, _admitted, _prompts = _run_turn(
        tmp_path,
        [_request_only("quasar-only", "keyword")],
        context_mode="harness_only",
    )
    harness = fixture[0]
    original = _turn_events(harness)[0].conjecture_turn
    forged = _replace_turn_payload(original, source_call_seq=0)
    next_seq = harness._next_seq

    with pytest.raises(ValueError, match="source|call|conjecturer|preced"):
        harness.record_conjecture_turn_event(forged)
    assert harness._next_seq == next_seq
    assert len(_turn_events(harness)) == 1


def test_scheduler_enacts_the_bounded_v4_follow_up(tmp_path):
    fixture = _seed_run(tmp_path)
    harness, _service, _problem, config, manifest, _plan, *_ = fixture
    pending = [
        json.dumps(_request_only("quasar-only", "keyword")),
        json.dumps(
            {"candidates": [_candidate_wire("Scheduler follow-up candidate.")]}
        ),
    ]
    endpoint = MockEndpoint(
        lambda _prompt: pending.pop(0),
        name=manifest.roles["conjecturer"][0].base_url,
        model=manifest.roles["conjecturer"][0].model_id,
        max_tokens=512,
    )
    adapter = LLMAdapter(
        {"conjecturer": endpoint},
        harness.blobs,
        retry_max=0,
        model_profile=manifest.model_profile,
        leases=leases_from_manifest(manifest),
    )

    Scheduler(harness, adapter, config, run_manifest=manifest).run(1)

    calls = [
        event.llm
        for event in harness.log.read()
        if event.llm is not None and event.llm.role == "conjecturer"
    ]
    assert len(calls) == 2
    assert any(
        event.conjecture_turn is not None
        and event.conjecture_turn.action.value == "context_granted"
        for event in harness.log.read()
    )
    assert verify_root(harness.root)["violations"] == []


@pytest.mark.parametrize(
    ("responses", "channels", "context_mode", "expected", "expected_calls"),
    (
        (
            [_request_only("quasar-only", "keyword")],
            ("focus", "keyword", "recent"),
            "harness_only",
            "context_denied",
            1,
        ),
        (
            [
                _request_only("quasar-only", "keyword"),
                _request_only("tertiary-only", "keyword"),
            ],
            ("focus", "keyword", "recent"),
            "harness_plus_model_request",
            "context_exhausted",
            2,
        ),
        (
            [
                {
                    "abstention": {
                        "search_signal": "stuck",
                        "note": "The bounded record does not support a proposal.",
                    }
                }
            ],
            ("focus", "keyword", "recent"),
            "harness_plus_model_request",
            "abstained",
            1,
        ),
    ),
)
def test_deny_exhaustion_and_abstention_are_typed_process_evidence(
    tmp_path,
    responses,
    channels,
    context_mode: str,
    expected: str,
    expected_calls: int,
):
    (fixture, admitted, prompts) = _run_turn(
        tmp_path,
        responses,
        permitted_channels=channels,
        context_mode=context_mode,
    )
    harness = fixture[0]
    assert admitted == []
    assert len(prompts) == expected_calls
    turns = _turn_events(harness)
    assert len(turns) == expected_calls
    assert expected in _payload_text(turns[-1])
    if expected == "context_exhausted":
        assert "context_granted" in _payload_text(turns[0])
