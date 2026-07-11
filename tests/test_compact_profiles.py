"""Model profiles alter presentation/transport only."""

import json

import pytest

from deepreason.config import Config
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.capabilities import ModelCapabilities
from deepreason.llm.contracts import ArgumentativeCriticOutput, ConjecturerOutput
from deepreason.llm.endpoints import MockEndpoint
from deepreason.llm.profiles import (
    ModelProfile,
    apply_profile_to_config,
    clip_pack,
    get_profile,
    select_profile,
)
from deepreason.llm.roles import render_role_prompt
from deepreason.llm.wire import AliasTable, AliasTableRequiredError, wire_contract_for
from deepreason.storage.blobs import BlobStore


def _caps(**changes):
    values = dict(
        provider="mock",
        endpoint="mock://one",
        model="m",
        native_json_schema=True,
        grammar=True,
        enum_adherence=1.0,
        nested_object_reliability=1.0,
        array_reliability=1.0,
        long_context_retention=1.0,
        max_reliable_output_tokens=4000,
        stop_sequence_reliable=True,
        repair_reliability=1.0,
    )
    values.update(changes)
    return ModelCapabilities(**values)


def test_compact_profile_has_plan_limits():
    compact = get_profile("compact")
    assert compact.pack_tokens_min == 700
    assert compact.pack_tokens_max == 1200
    assert compact.max_meaningful_nesting == 2
    assert compact.vs_k == 4
    assert compact.default_concurrency == 1
    assert compact.website_design_mode == "skeleton_first"
    assert not compact.direct_contracts


def test_standard_and_frontier_preserve_direct_paths():
    standard = get_profile(ModelProfile.STANDARD)
    frontier = get_profile(ModelProfile.FRONTIER)
    assert standard.pack_tokens_max == 2500 and standard.direct_contracts
    assert frontier.pack_tokens_max == 3000 and frontier.direct_contracts
    assert standard.vs_k is None and frontier.vs_k is None
    assert frontier.batching and frontier.parallel_calls


def test_measured_contract_failure_selects_compact():
    assert select_profile(_caps(nested_object_reliability=0.0)).name == ModelProfile.COMPACT
    assert select_profile(_caps(array_reliability=0.0)).name == ModelProfile.COMPACT
    assert select_profile(_caps(enum_adherence=0.0)).name == ModelProfile.COMPACT


def test_capable_route_selects_frontier_and_unknown_length_selects_standard():
    assert select_profile(_caps()).name == ModelProfile.FRONTIER
    assert select_profile(_caps(max_reliable_output_tokens=0)).name == ModelProfile.STANDARD


def test_compact_prompt_has_one_example_and_no_operator_context():
    prompt = render_role_prompt(
        "conjecturer",
        schema='{"type":"object"}',
        pack="PROBLEM: explain tides",
        profile="compact",
        example='{"candidates":[]}',
        aliases="A1\nA2",
    )
    assert prompt.count("ONE SYNTAX EXAMPLE") == 1
    assert "explain tides" in prompt and "A1" in prompt
    lowered = prompt.lower()
    for forbidden in ("endpoint", "provider", "configuration", "harness"):
        assert forbidden not in lowered


def test_profile_clipping_is_presentation_only():
    pack = "x" * 20_000
    compact = clip_pack(pack, "compact")
    frontier = clip_pack(pack, "frontier")
    assert len(compact) == 1200 * 4
    assert len(frontier) == 3000 * 4
    assert compact == pack[: len(compact)]


def test_compact_config_applies_only_model_facing_process_defaults():
    original = Config(VS_K=9, PACK_TOKEN_BUDGET=9000, CRIT_BATCH_K=8)
    compact = apply_profile_to_config(original, "compact")
    assert compact.VS_K == 4
    assert compact.PACK_TOKEN_BUDGET == 1200
    assert compact.CRIT_BATCH_K is None
    assert original.VS_K == 9 and original.CRIT_BATCH_K == 8


def test_standard_and_frontier_preserve_configured_sampling():
    original = Config(VS_K=9, PACK_TOKEN_BUDGET=9000, CRIT_BATCH_K=8)
    standard = apply_profile_to_config(original, "standard")
    frontier = apply_profile_to_config(original, "frontier")
    assert standard.VS_K == frontier.VS_K == 9
    assert standard.CRIT_BATCH_K == frontier.CRIT_BATCH_K == 8
    assert standard.PACK_TOKEN_BUDGET == 2500
    assert frontier.PACK_TOKEN_BUDGET == 3000


def test_alias_dependent_hot_roles_fail_closed_without_a_table():
    for role, output in (
        ("conjecturer", ConjecturerOutput),
        ("argumentative_critic", ArgumentativeCriticOutput),
    ):
        with pytest.raises(AliasTableRequiredError):
            wire_contract_for(role, output, "compact", None)


def test_conjecturer_can_explicitly_have_no_neighbour_aliases():
    contract = wire_contract_for(
        "conjecturer", ConjecturerOutput, "compact", AliasTable()
    )
    assert contract.contract_id == "conjecturer.compact.v1"


def test_selected_alias_transport_hides_canonical_hashes(tmp_path):
    artifact_id = "a" * 64
    aliases = AliasTable({"A1": artifact_id})
    raw = json.dumps(
        {
            "candidates": [
                {"content": "new relation", "typicality": 0.4, "neighbours": ["A1"]}
            ]
        }
    )
    endpoint = MockEndpoint([raw])
    blobs = BlobStore(tmp_path / "blobs")
    adapter = LLMAdapter(
        {"conjecturer": endpoint}, blobs, model_profile="compact"
    )
    output, call = adapter.call(
        "conjecturer",
        f"NEIGHBOUR {artifact_id}: prior idea",
        ConjecturerOutput,
        aliases=aliases,
    )
    prompt = blobs.get(call.prompt_ref).decode()
    assert artifact_id not in prompt and "A1" in prompt
    assert output.candidates[0].refs[0].target == artifact_id
