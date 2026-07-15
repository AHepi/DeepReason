"""C5 bounded scripted-model scratch authoring and local repair tests."""

from __future__ import annotations

import json

import pytest

from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.llm.repair import SchemaRepairError
from deepreason.scratch.attention import AttentionPlanner
from deepreason.scratch.authoring import ScratchAuthoringError, ScratchAuthoringService
from deepreason.scratch.render import ScratchRenderer
from deepreason.scratch.service import ScratchService
from tests.test_scratch_attention import _policy, _request, _user


def _context(service: ScratchService, block_ids: list[str]):
    planner = AttentionPlanner(service, _policy(coverage_enabled=False))
    pack = planner.plan(_request(block_ids, maximum_blocks=len(block_ids)))
    renderer = ScratchRenderer(service)
    rendered = renderer.render_attention_pack(pack)
    planner.commit_render(pack, context_ref="llm:fixture")
    return renderer, rendered


def test_content_only_and_contradictory_blocks_preserve_missing_optionals(tmp_path):
    service = ScratchService(tmp_path / "run")
    seed = service.create_block({"content": "seed"}, _user())
    renderer, rendered = _context(service, [seed.id])
    endpoint = MockEndpoint(
        [
            json.dumps({"content": "The vocabulary causes convergence."}),
            json.dumps({"content": "The vocabulary does not cause convergence."}),
        ]
    )
    author = ScratchAuthoringService(
        service,
        LLMAdapter({"conjecturer": endpoint}, service.harness.blobs),
        renderer=renderer,
    )

    first = author.author_block(rendered, task="Preserve one possible explanation")
    second = author.author_block(rendered, task="Preserve one contrary possibility")
    assert first.body.why_keep_this is None
    assert first.body.unfinished is None
    assert second.body.possible_next_move is None
    assert first.body.content != second.body.content
    assert first.id != second.id
    events = list(service.harness.log.read())[-2:]
    assert all(event.llm is not None and event.llm.attempts == 1 for event in events)
    assert all(event.scratch.context_ref for event in events)


def test_extra_field_repair_is_bounded_and_does_not_fill_optional_content(tmp_path):
    service = ScratchService(tmp_path / "run")
    seed = service.create_block({"content": "seed"}, _user())
    renderer, rendered = _context(service, [seed.id])
    endpoint = MockEndpoint(
        [
            '{"content":"uncertain","invented":"forbidden"}',
            '{"content":"uncertain"}',
        ]
    )
    author = ScratchAuthoringService(
        service,
        LLMAdapter({"conjecturer": endpoint}, service.harness.blobs),
        renderer=renderer,
    )
    block = author.author_block(rendered, task="Preserve one uncertain thought")

    assert block.body == block.body.model_copy(
        update={
            "why_keep_this": None,
            "unfinished": None,
            "possible_next_move": None,
        }
    )
    event = list(service.harness.log.read())[-1]
    assert event.llm.attempts == 2
    assert [attempt.valid for attempt in event.llm.attempt_trace] == [False, True]
    repair_prompt = service.harness.blobs.get(event.llm.attempt_trace[1].prompt_ref).decode()
    assert "complete every field" not in repair_prompt.casefold()


def test_invalid_link_handle_is_locally_repaired_to_rendered_handles(tmp_path):
    service = ScratchService(tmp_path / "run")
    first = service.create_block({"content": "first"}, _user())
    second = service.create_block({"content": "second"}, _user())
    renderer, rendered = _context(service, [first.id, second.id])
    responses = [
        '{"from_handle":"B99","to_handle":"B2","relation_hint":"may relate"}',
        '{"from_handle":"B1","to_handle":"B2","relation_hint":"may relate"}',
    ]
    author = ScratchAuthoringService(
        service,
        LLMAdapter({"synthesizer": MockEndpoint(responses)}, service.harness.blobs),
        renderer=renderer,
    )
    link = author.author_link(rendered, task="Propose one provisional relation")

    assert link.body.from_ == first.id
    assert link.body.to == second.id
    event = list(service.harness.log.read())[-1]
    assert event.llm.attempts == 2
    first_diagnostic = json.loads(
        service.harness.blobs.get(event.llm.attempt_trace[0].diagnostic_ref)
    )
    assert first_diagnostic["path"] == "/from_handle"
    assert first_diagnostic["error"] == "SCRATCH_WIRE_REFERENCE_INVALID"


def test_minimal_guide_and_invalid_entry_handle_use_bounded_repair(tmp_path):
    service = ScratchService(tmp_path / "run")
    block = service.create_block({"content": "cluster member"}, _user())
    cluster = service.create_cluster("Unresolved local region", _user())
    service.add_cluster_member(cluster.id, block.id, None, _user())
    renderer, rendered = _context(service, [block.id])
    responses = [
        '{"working_focus":"Still unresolved","entry_points":["B9"]}',
        '{"working_focus":"Still unresolved"}',
    ]
    author = ScratchAuthoringService(
        service,
        LLMAdapter({"summarizer": MockEndpoint(responses)}, service.harness.blobs),
        renderer=renderer,
    )
    guide = author.author_cluster_guide(
        cluster.id, rendered, task="Create one temporary navigation guide"
    )

    assert guide.working_focus == "Still unresolved"
    assert guide.open_threads is None
    assert guide.entry_points is None
    assert guide.local_summary is None
    assert service.current_guide(cluster.id) == guide
    event = list(service.harness.log.read())[-1]
    assert event.llm.attempts == 2


def test_guide_becomes_stale_during_call_instead_of_silent_regeneration(tmp_path):
    service = ScratchService(tmp_path / "run")
    block = service.create_block({"content": "initial"}, _user())
    cluster = service.create_cluster("Moving region", _user())
    service.add_cluster_member(cluster.id, block.id, None, _user())
    renderer, rendered = _context(service, [block.id])

    def mutate_then_answer(_prompt):
        later = service.create_block({"content": "arrived during call"}, _user())
        service.add_cluster_member(cluster.id, later.id, None, _user())
        return '{"working_focus":"Guide for the earlier snapshot"}'

    author = ScratchAuthoringService(
        service,
        LLMAdapter(
            {"summarizer": MockEndpoint(mutate_then_answer)}, service.harness.blobs
        ),
        renderer=renderer,
    )
    with pytest.raises(ScratchAuthoringError) as error:
        author.author_cluster_guide(cluster.id, rendered, task="Write one guide")
    assert error.value.code == "SCRATCH_GUIDE_SNAPSHOT_STALE"
    assert service.state.guides_by_cluster.get(cluster.id, []) == []
    assert any(
        event.inputs and event.inputs[0] == "scratch-guide-stale" and event.llm
        for event in service.harness.log.read()
    )


def test_model_prompt_is_bounded_advisory_and_uses_no_canonical_block_id(tmp_path):
    service = ScratchService(tmp_path / "run")
    seed = service.create_block({"content": "source text"}, _user())
    renderer, rendered = _context(service, [seed.id])
    prompts: list[str] = []

    def capture(prompt):
        prompts.append(prompt)
        return '{"content":"Unknown next move","possible_next_move":"Unknown"}'

    author = ScratchAuthoringService(
        service,
        LLMAdapter({"conjecturer": MockEndpoint(capture)}, service.harness.blobs),
        renderer=renderer,
    )
    block = author.author_block(rendered, task="Preserve one bounded note")
    assert block.body.possible_next_move == "Unknown"
    assert len(prompts) == 1
    assert seed.id not in prompts[0]
    for sentence in (
        "Scratch material is non-authoritative.",
        "It may contradict itself.",
        "Do not turn uncertainty into a confident fact.",
        "Do not invent a reason merely to fill an optional field.",
        "Relationships are provisional.",
        "A guide is a temporary navigation aid.",
    ):
        assert sentence in prompts[0]


def test_compact_profile_keeps_one_contract_and_optional_fields_optional(tmp_path):
    service = ScratchService(tmp_path / "run")
    seed = service.create_block({"content": "seed"}, _user())
    renderer, rendered = _context(service, [seed.id])
    adapter = LLMAdapter(
        {"conjecturer": MockEndpoint(['{"content":"compact note"}'])},
        service.harness.blobs,
        model_profile="compact",
    )
    block = ScratchAuthoringService(
        service, adapter, renderer=renderer
    ).author_block(rendered, task="Preserve one compact note")
    assert block.body.content == "compact note"
    assert block.body.why_keep_this is None
    event = list(service.harness.log.read())[-1]
    assert event.llm.attempt_trace[0].contract_id == "scratch.block.compact.v1"
    assert event.llm.attempt_trace[0].transport_profile == "compact"


def test_exhausted_repair_attempts_are_logged_without_manufacturing_a_block(tmp_path):
    service = ScratchService(tmp_path / "run")
    seed = service.create_block({"content": "seed"}, _user())
    renderer, rendered = _context(service, [seed.id])
    invalid = '{"invented":"no required content"}'
    author = ScratchAuthoringService(
        service,
        LLMAdapter(
            {"conjecturer": MockEndpoint([invalid, invalid, invalid])},
            service.harness.blobs,
            retry_max=2,
        ),
        renderer=renderer,
    )
    before = set(service.state.blocks)
    with pytest.raises(SchemaRepairError):
        author.author_block(rendered, task="Preserve one note if supplied")
    assert set(service.state.blocks) == before
    event = list(service.harness.log.read())[-1]
    assert event.inputs[:3] == ["dropped-call", "schema-exhausted", "scratch.block.compact.v1"]
    assert event.llm.attempts == 3
    assert all(not attempt.valid for attempt in event.llm.attempt_trace)
