"""Bounded conjecture recourse: the v4 wire contract and the V6-only runtime.

The v4 turn wire contract remains a repository-owned artifact and keeps its
unit coverage.  Runtime coverage is V6-only: pre-V6 active-conjecture
manifests fail closed at root admission with UNSUPPORTED_RUN_MANIFEST_VERSION,
and the behaviors that survive (bounded context planning, the pre-spend raw
context guard, expansion receipts) are exercised through schema-version-6
manifests.
"""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from deepreason.bridge.retry import WorkflowRetryPolicyV1
from deepreason.canonical import canonical_json
from deepreason.capabilities.policy import InquiryCapabilityPolicyV1
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
from deepreason.evidence import (
    AttachedSourceProvenanceV1,
    EvidenceDossierV1,
    RunInputManifestV2,
    RunInputProblemV2,
    bind_run_input,
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
from deepreason.ontology import Commitment, Problem, ProblemProvenance, Rule
from deepreason.rules.conj import conj
from deepreason.run_manifest import (
    ConjectureContextPolicyV1,
    ContractVersionPolicyV1,
    ContractVersionPolicyV3,
    ControlPlanePolicyV1,
    ControlPlanePolicyV3,
    RunManifest,
    RunManifestError,
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
from tests.test_v6_context_continuation import (
    _abstention as _v6_abstention,
    _adapter as _v6_adapter,
    _request as _v6_request,
)


STAMP = "2026-07-16T00:00:00Z"
PROBLEM_ID = "pi-conjecturer-turn-v4"
PROBLEM_TEXT = "Explain why delayed feedback may stabilize this record."


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


def _request_only(query: str, channel: str = "keyword") -> dict:
    return {
        "context_request": _request_wire(
            query=query,
            channels=[channel],
        )
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


def _commitment() -> Commitment:
    return Commitment(
        id="k-conjecturer-turn-v6", eval="predicate:len(content) > 0"
    )


def _v6_run_input(root) -> str:
    """Bind one canonical v2 run input and return its digest."""

    dossier = EvidenceDossierV1.create(
        problem_ref=PROBLEM_ID,
        sources=(),
        total_byte_count=0,
        creation_provenance=AttachedSourceProvenanceV1(
            supplied_by="offline fixture",
            acquisition_method="pre-freeze construction",
        ),
    )
    run_input = RunInputManifestV2.create(
        problem=RunInputProblemV2.from_commitments(
            id=PROBLEM_ID,
            description=PROBLEM_TEXT,
            criteria=(_commitment(),),
        ),
        evidence_dossier_digest=dossier.dossier_digest,
    )
    bind_run_input(run_input, dossier, root)
    return run_input.run_input_digest


def _v6_config() -> Config:
    return Config(
        N_SCHOOLS=0,
        RETRY_MAX=0,
        roles={
            "conjecturer": [
                {
                    "endpoint_id": "conjecturer-0",
                    "endpoint": "mock://conjecturer-0",
                    "model": "offline-conjecturer",
                    "provider": "mock",
                    "family": "offline-family",
                    "max_tokens": 512,
                    "context_window_tokens": 262_144,
                }
            ]
        },
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
    )


def _v6_manifest(
    config: Config,
    *,
    permitted_channels: tuple[str, ...] = ("focus", "keyword"),
    max_expansions: int = 1,
    initial_max_blocks: int = 1,
    max_extra_blocks: int = 1,
    run_input_digest: str = "c" * 64,
) -> RunManifest:
    context = ConjectureContextPolicyV1(
        mode="harness_plus_model_request",
        initial_max_blocks=initial_max_blocks,
        initial_max_guides=0,
        max_context_expansion_requests=max_expansions,
        max_extra_blocks=max_extra_blocks,
        permitted_retrieval_channels=permitted_channels,
        coverage_slot_mandatory=False,
        exploration_slot_mandatory=False,
    )
    control = ControlPlanePolicyV3(
        school_execution=SchoolExecutionPolicyV1(
            mode="conditioning_only",
            bindings=(),
            allow_shared=True,
            require_distinct_models=False,
            require_distinct_families=False,
        ),
        conjecture_context=context,
        workflow_retry=WorkflowRetryPolicyV1(),
        contract_versions=ContractVersionPolicyV3(),
    )
    return compile_run_manifest(
        config,
        schema_version=6,
        workload_profile="text",
        rubric_policy="forbid",
        compiled_at=STAMP,
        control_plane_policy=control,
        inquiry_capability_policy=InquiryCapabilityPolicyV1(
            capability_profile="inquiry-capabilities.v2"
        ),
        run_input_digest=run_input_digest,
    )


def _seed_v6_root(
    tmp_path,
    *,
    permitted_channels=("focus", "keyword"),
    max_expansions=1,
    initial_max_blocks=1,
    max_extra_blocks=1,
):
    """One durably bound v6 root with a registered problem and scratch blocks."""

    root = tmp_path / "run"
    digest = _v6_run_input(root)
    config = _v6_config()
    manifest = _v6_manifest(
        config,
        permitted_channels=permitted_channels,
        max_expansions=max_expansions,
        initial_max_blocks=initial_max_blocks,
        max_extra_blocks=max_extra_blocks,
        run_input_digest=digest,
    )
    bind_run_manifest(manifest, root)
    harness = Harness(root)
    commitment = _commitment()
    harness.register_commitment(commitment)
    problem = harness.register_problem(
        Problem(
            id=PROBLEM_ID,
            description=PROBLEM_TEXT,
            criteria=[commitment.id],
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
    return harness, service, problem, config, manifest, focus, expansion, tertiary


def _assert_pre_v6_admission_fails_closed(root, manifest) -> None:
    """The V6-only contract: a pre-V6 binding can never admit a run root."""

    assert manifest.schema_version == 4
    bind_run_manifest(manifest, root)

    with pytest.raises(RunManifestError) as raised:
        Harness(root)

    assert raised.value.code == "UNSUPPORTED_RUN_MANIFEST_VERSION"
    assert raised.value.pointer == "/schema_version"
    assert raised.value.rejected_version == 4
    # Fail-closed: admission stopped before any canonical run state existed.
    assert not (root / "log.jsonl").exists()


def test_expansion_cap_counts_blocks_actually_added_to_the_prior_view(tmp_path):
    (
        harness,
        service,
        problem,
        _config_,
        manifest,
        focus,
        expansion,
        tertiary,
    ) = _seed_v6_root(
        tmp_path,
        permitted_channels=("focus", "keyword"),
        # Deliberately leave the initial allocation under-filled. The expansion
        # budget is one added block, not all unused initial capacity plus one.
        initial_max_blocks=3,
        max_extra_blocks=1,
    )
    fence = harness._next_seq - 1
    prior = plan_conjecture_context(
        service,
        problem=problem,
        school_id=None,
        manifest_digest=manifest.sha256,
        scratch_policy=manifest.scratch_policy,
        context_policy=manifest.control_plane_policy.conjecture_context,
        formal_fence_seq=fence,
        scratch_fence_seq=fence,
    )
    assert prior is not None
    assert prior.attention_pack.selection_receipt.final_order == [focus.id]
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
    """Legacy v4 fixture retained for cross-module imports.

    Under the V6-only contract this now fails closed at ``Harness`` admission
    with UNSUPPORTED_RUN_MANIFEST_VERSION, because the root is bound to a
    schema-version-4 manifest.
    """

    # Include a second canonical school for school-conditioned callers; the
    # live call itself remains bound to school-0.
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
            description=PROBLEM_TEXT,
            provenance=ProblemProvenance.model_validate(
                {"trigger": "seed", "from": []}
            ),
        )
    )
    if include_other_problem:
        harness.register_problem(
            _problem_with_id(f"{PROBLEM_ID}-other")
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


def _problem_with_id(problem_id: str) -> Problem:
    return Problem(
        id=problem_id,
        description="A second canonical problem used only for identity tampering.",
        provenance=ProblemProvenance.model_validate(
            {"trigger": "seed", "from": []}
        ),
    )


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
    """Legacy v4 turn runner retained for cross-module imports."""

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


def _v6_candidates(content: str) -> dict:
    return {"candidates": [{"content": content, "typicality": 0.37}]}


def _run_v6_turn(harness, config, manifest, adapter):
    return conj(
        harness,
        PROBLEM_ID,
        adapter,
        config,
        workload_profile="text",
        run_manifest=manifest,
    )


def test_one_configured_expansion_records_original_and_expanded_receipts(tmp_path):
    harness, service, _problem, config, manifest, focus, expansion, _ = _seed_v6_root(
        tmp_path
    )
    adapter, prompts = _v6_adapter(
        harness,
        manifest,
        [
            _v6_request("quasar-only"),
            _v6_candidates("The quasar topology is testable."),
        ],
    )

    admitted = _run_v6_turn(harness, config, manifest, adapter)

    assert len(admitted) == 1
    assert len(prompts) == 2
    initial_prompt = prompts[0].casefold()
    assert "return exactly" not in initial_prompt
    assert "context_request" in initial_prompt
    assert "abstention" in initial_prompt

    # The grant is durable typed authority: the follow-up work item carries
    # one eligible context continuation bound to its parent work.
    parent, child = tuple(harness.workflow_state.transaction_work.values())
    binding = child.preparation.task_payload_value["context_continuation"]
    assert binding["parent_work_id"] == parent.preparation.id
    assert binding["eligibility"] == "eligible"
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
    assert expanded.expansion_decision_ref == binding["decision_ref"]
    for receipt in (original, expanded):
        assert receipt.selection_receipt_ref in service.state.attention_receipts
        assert receipt.advisory_context_ref in service.state.advisory_contexts
        assert harness.blobs.get(receipt.render_receipt_ref)
        assert harness.blobs.get(receipt.rendered_context_ref)

    # Call accounting stays process-owned; the formal registration does not
    # duplicate the follow-up LLM call.
    register = next(event for event in harness.log.read() if admitted[0].id in event.outputs)
    assert register.llm is None
    # KNOWN SRC BUG (V6-only migration): verify_root falsely flags legitimate
    # v6 context expansions because invariants.py:validate_conjecture_context
    # requires a conjecture_turn decision event for every
    # expansion_decision_ref, but the v6 transactional continuation path
    # records continuation decisions, not turn events. See
    # src/deepreason/invariants.py (~line 1912). Do not weaken this assertion.
    assert verify_root(harness.root)["violations"] == []


def test_pre_v6_expansion_authority_fails_closed_at_admission(tmp_path):
    """The v4 multi-expansion recourse loop is unreachable under V6-only.

    A schema-version-4 manifest that froze a two-expansion allowance can be
    compiled and written, but the root it binds can never be admitted, so its
    turn-event invariants can never be exercised by a new run.
    """

    manifest = _manifest(_config(), max_expansions=2, max_extra_blocks=2)

    _assert_pre_v6_admission_fails_closed(tmp_path / "run", manifest)


def test_pre_v6_school_bound_turn_authority_fails_closed_at_admission(tmp_path):
    """A school-conditioned v4 turn authority also fails closed at admission."""

    manifest = _manifest(_config(schools=2))

    _assert_pre_v6_admission_fails_closed(tmp_path / "run", manifest)


def test_active_manifest_rejects_raw_generation_context_before_provider_spend(
    tmp_path,
):
    harness, _service, _problem, config, manifest, *_blocks = _seed_v6_root(
        tmp_path
    )
    meter = TokenMeter(budget=100_000)
    adapter, prompts = _v6_adapter(harness, manifest, [], meter=meter)
    next_seq = harness._next_seq

    with pytest.raises(ValueError, match="generation_context|raw.*context|typed"):
        conj(
            harness,
            PROBLEM_ID,
            adapter,
            config,
            workload_profile="text",
            generation_context="MODEL-UNBOUNDED RAW CONTEXT",
            # Deliberately omit the typed plan: active manifests forbid this
            # legacy escape hatch even when no scratch context was prepared.
            conjecture_context_plan=None,
            run_manifest=manifest,
        )

    assert prompts == []
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
    """No v6 provider call can source a pre-V6 turn event, even with canonical evidence.

    Turn events belonged to the removed v4/v5 recourse loop. On a V6-only
    root the append is rejected before any durable state changes, because a
    conjecturer.turn.v6 call is never a valid turn source.
    """

    harness, _service, _problem, config, manifest, *_blocks = _seed_v6_root(
        tmp_path
    )
    adapter, _prompts = _v6_adapter(harness, manifest, [_v6_abstention()])
    assert _run_v6_turn(harness, config, manifest, adapter) == []
    (source,) = [
        event
        for event in harness.log.read()
        if event.llm is not None and event.llm.role == "conjecturer"
    ]
    assert {
        attempt.contract_id for attempt in source.llm.attempt_trace
    } == {"conjecturer.turn.v6"}

    if evidence_kind == "request":
        evidence = ContextRequestV1(
            query="A canonical request blob.",
            desired_retrieval_channels=(RetrievalChannel.KEYWORD,),
        )
        evidence_ref = harness.blobs.put(
            canonical_json(evidence.model_dump(mode="json", exclude_none=True))
        )
        payload = ConjectureTurnEventPayloadV1.create(
            action=ConjectureTurnAction.CONTEXT_EXHAUSTED,
            manifest_digest=manifest.sha256,
            problem_id=PROBLEM_ID,
            source_call_seq=source.seq,
            expansion_index=1,
            maximum_expansions=1,
            request_hash=evidence.request_hash,
            request_ref=evidence_ref,
            reason_code="request_limit_reached",
        )
        evidence_args = {"request": evidence}
    else:
        evidence = ConjectureAbstentionV1(
            search_signal="capability_mismatch",
            note="A canonical abstention blob.",
        )
        evidence_ref = harness.blobs.put(
            canonical_json(evidence.model_dump(mode="json", exclude_none=True))
        )
        payload = ConjectureTurnEventPayloadV1.create(
            action=ConjectureTurnAction.ABSTAINED,
            manifest_digest=manifest.sha256,
            problem_id=PROBLEM_ID,
            source_call_seq=source.seq,
            expansion_index=0,
            maximum_expansions=1,
            abstention_hash=evidence.abstention_hash,
            abstention_ref=evidence_ref,
            reason_code="abstained",
        )
        evidence_args = {"abstention": evidence}

    next_seq = harness._next_seq
    with pytest.raises(ValueError, match="source|call|conjecturer|preced"):
        harness.record_conjecture_turn_event(payload, **evidence_args)
    assert harness._next_seq == next_seq
    assert _turn_events(harness) == []


def test_record_turn_event_validates_source_call_before_append(tmp_path):
    harness, _service, _problem, _config_, manifest, *_blocks = _seed_v6_root(
        tmp_path
    )
    evidence = ConjectureAbstentionV1(
        search_signal="stuck",
        note="No source call exists for this claimed turn.",
    )
    evidence_ref = harness.blobs.put(
        canonical_json(evidence.model_dump(mode="json", exclude_none=True))
    )
    forged = ConjectureTurnEventPayloadV1.create(
        action=ConjectureTurnAction.ABSTAINED,
        manifest_digest=manifest.sha256,
        problem_id=PROBLEM_ID,
        source_call_seq=0,
        expansion_index=0,
        maximum_expansions=1,
        abstention_hash=evidence.abstention_hash,
        abstention_ref=evidence_ref,
        reason_code="abstained",
    )
    next_seq = harness._next_seq

    with pytest.raises(ValueError, match="source|call|conjecturer|preced"):
        harness.record_conjecture_turn_event(forged, abstention=evidence)
    assert harness._next_seq == next_seq
    assert _turn_events(harness) == []


def test_scheduler_cannot_enact_the_pre_v6_follow_up(tmp_path):
    """The bounded v4 scheduler follow-up can never start under V6-only.

    Admission of the v4-bound root fails closed before a scheduler, adapter,
    or provider endpoint could observe it, so neither of the two calls the
    old follow-up loop performed can happen.
    """

    manifest = _manifest(_config())
    root = tmp_path / "run"
    pending = [
        json.dumps({"context_request": _request_wire(query="quasar-only")}),
        json.dumps({"candidates": [_candidate_wire("Scheduler follow-up candidate.")]}),
    ]

    _assert_pre_v6_admission_fails_closed(root, manifest)

    assert len(pending) == 2


@pytest.mark.parametrize(
    "context_mode",
    ("harness_only", "harness_plus_model_request"),
)
def test_deny_exhaustion_and_abstention_are_typed_process_evidence(
    tmp_path,
    context_mode: str,
):
    """Pre-V6 typed turn evidence is unreachable: admission fails closed first.

    The deny/exhaustion/abstention turn events were v4 process evidence. Under
    the V6-only contract every context-mode variant of the v4 manifest is
    rejected at admission, before a provider call or a turn event could exist.
    """

    manifest = _manifest(
        _config(),
        permitted_channels=("focus", "keyword", "recent"),
        context_mode=context_mode,
    )

    _assert_pre_v6_admission_fails_closed(tmp_path / "run", manifest)
