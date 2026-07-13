"""Append-only attempt tracing for bounded structured-output repair."""

import json

import pytest

from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.llm.adapter import LLMAdapter, SchemaRepairError, build_adapter
from deepreason.llm.contracts import ConjecturerOutput, ProseOutput
from deepreason.llm.endpoints import MockEndpoint
from deepreason.llm.firewall import RouteFirewallError
from deepreason.llm.wire import AliasTable, ConjecturerWireContract, DirectWireContract
from deepreason.ontology.event import LLMCall
from deepreason.report import eval_report
from deepreason.rules.crit import crit_argumentative


INVALID_INITIAL = '{"candidates":[{"content":"keep","typicality":2}]}'
INVALID_WHOLE_REPAIR = '{"candidates":[{"content":"keep","typicality":3}]}'
VALID_SUBTREE_REPAIR = "0.4"
VALIDATION_PATH = "/candidates/0/typicality"


def test_successful_repair_event_keeps_every_attempt_blob_reachable(tmp_path):
    harness = Harness(tmp_path / "run")
    endpoint = MockEndpoint(
        [INVALID_INITIAL, INVALID_WHOLE_REPAIR, VALID_SUBTREE_REPAIR],
        name="mock://gemma",
        model="gemma4:31b",
    )
    adapter = LLMAdapter(
        {"conjecturer": endpoint},
        harness.blobs,
        retry_max=2,
    )

    output, call = adapter.call("conjecturer", "PACK", ConjecturerOutput)
    assert output.candidates[0].typicality == 0.4
    harness.record_llm_calls([call], "test-repaired-call")

    # Read the fsynced JSONL back through the canonical event model; do not
    # rely on the adapter's in-memory LLMCall.
    event = next(e for e in Harness(harness.root).log.read() if e.llm is not None)
    logged = event.llm
    assert logged is not None
    assert logged.attempts == 3
    assert logged.tokens == sum(item.tokens for item in logged.attempt_trace)
    assert [item.attempt for item in logged.attempt_trace] == [0, 1, 2]
    assert [item.valid for item in logged.attempt_trace] == [False, False, True]
    assert [item.validation_path for item in logged.attempt_trace] == [
        VALIDATION_PATH,
        VALIDATION_PATH,
        VALIDATION_PATH,
    ]

    raw_texts = [
        harness.blobs.get(item.raw_ref).decode()
        for item in logged.attempt_trace
    ]
    assert raw_texts == [
        INVALID_INITIAL,
        INVALID_WHOLE_REPAIR,
        VALID_SUBTREE_REPAIR,
    ]
    prompt_texts = [
        harness.blobs.get(item.prompt_ref).decode()
        for item in logged.attempt_trace
    ]
    assert "PACK" in prompt_texts[0]
    assert "complete corrected JSON value" in prompt_texts[1]
    assert "replacement JSON value" in prompt_texts[2]
    assert all(VALIDATION_PATH in prompt for prompt in prompt_texts[1:])

    diagnostics = [
        json.loads(harness.blobs.get(item.diagnostic_ref))
        for item in logged.attempt_trace[:2]
    ]
    assert [item["path"] for item in diagnostics] == [
        VALIDATION_PATH,
        VALIDATION_PATH,
    ]
    assert logged.prompt_ref == logged.attempt_trace[-1].prompt_ref
    assert logged.raw_ref == logged.attempt_trace[-1].raw_ref
    assert all(item.contract_id == "conjecturer.direct.v1" for item in logged.attempt_trace)
    assert all(item.endpoint_id == "mock://gemma" for item in logged.attempt_trace)
    assert len({item.route_sha256 for item in logged.attempt_trace}) == 1


def test_attempt_trace_records_effective_controller_transport_limits(tmp_path):
    endpoint = MockEndpoint(
        ['{"candidates":[{"content":"x","typicality":0.5}]}'],
        name="mock://gemma",
        model="gemma4:31b",
    )
    endpoint.max_tokens = 800
    endpoint.timeout_s = 300
    adapter = LLMAdapter(
        {"conjecturer": endpoint}, Harness(tmp_path / "limits-run").blobs
    )

    # These two knobs are the bounded controller exception to the otherwise
    # immutable route lease. The trace must record the effective request.
    endpoint.max_tokens = 1280
    endpoint.timeout_s = 450
    _, call = adapter.call("conjecturer", "PACK", ConjecturerOutput)

    assert call.attempt_trace[0].max_tokens == 1280
    assert call.attempt_trace[0].timeout_s == 450


class _MutatingEndpoint(MockEndpoint):
    def __init__(self):
        super().__init__(
            [INVALID_INITIAL, VALID_SUBTREE_REPAIR],
            name="mock://gemma",
            model="gemma4:31b",
        )
        self.requests = 0

    def complete(self, prompt, images=None, **kwargs):
        self.requests += 1
        raw = super().complete(prompt, images=images, **kwargs)
        if self.requests == 1:
            self.model = "deepseek-v4"
        return raw


def test_lease_is_reverified_before_repair_and_prior_spend_is_loggable(tmp_path):
    harness = Harness(tmp_path / "route-run")
    endpoint = _MutatingEndpoint()
    adapter = LLMAdapter(
        {"conjecturer": endpoint}, harness.blobs, retry_max=2
    )

    with pytest.raises(RouteFirewallError) as raised:
        adapter.call("conjecturer", "PACK", ConjecturerOutput)

    assert endpoint.requests == 1
    spend = raised.value.spend
    assert spend is not None
    assert spend.model == "gemma4:31b"
    assert spend.endpoint == "mock://gemma"
    assert spend.attempts == 1
    assert len(spend.attempt_trace) == 1
    assert harness.blobs.get(spend.attempt_trace[0].raw_ref).decode() == INVALID_INITIAL
    assert harness.blobs.get(spend.attempt_trace[0].diagnostic_ref)

    # The terminal firewall handler can append prior spend before re-raising;
    # prove that the carried record and all its refs survive a clean reopen.
    harness.record_llm_calls([spend], "terminal-route-firewall")
    reopened = Harness(harness.root)
    logged = next(e.llm for e in reopened.log.read() if e.llm is not None)
    assert logged is not None
    assert logged.attempt_trace[0].attempt == 0
    assert reopened.blobs.get(logged.attempt_trace[0].prompt_ref)
    assert reopened.blobs.get(logged.attempt_trace[0].raw_ref)
    assert reopened.blobs.get(logged.attempt_trace[0].diagnostic_ref)


def test_historical_attempt_trace_defaults_remain_replay_compatible():
    call = LLMCall.model_validate(
        {
            "role": "conjecturer",
            "model": "legacy",
            "endpoint": "mock://legacy",
            "prompt_ref": "p",
            "raw_ref": "r",
            "attempt_trace": [
                {
                    "prompt_ref": "p",
                    "raw_ref": "r",
                    "repair_scope": "/x",
                    "valid": False,
                }
            ],
        }
    )
    assert call.attempt_trace[0].attempt == 0
    assert call.attempt_trace[0].validation_path == ""
    assert call.attempt_trace[0].transport_profile == ""
    assert call.attempt_trace[0].max_tokens is None
    assert call.attempt_trace[0].timeout_s is None


def test_attempt_profile_remains_the_frozen_base_during_wire_recovery(tmp_path):
    endpoint = MockEndpoint(
        ['{"candidates":[{"content":"x","typicality":0.5}]}'],
        name="mock://gemma",
        model="gemma4:31b",
    )
    adapter = LLMAdapter(
        {"conjecturer": endpoint},
        Harness(tmp_path / "profile-run").blobs,
        model_profile="standard",
    )
    _, call = adapter.call(
        "conjecturer",
        "PACK",
        ConjecturerOutput,
        # Simulate a scheduler-selected transport recovery. The frozen run
        # identity remains standard; transport_profile identifies rendering.
        model_profile="compact",
        wire_contract=DirectWireContract(ConjecturerOutput),
    )
    assert call.attempt_trace[0].model_profile == "standard"
    assert call.attempt_trace[0].transport_profile == "compact"
    assert call.attempt_trace[0].contract_id == "conjecturer.direct.v1"


def test_compact_aliasing_precedes_clipping_and_lists_only_visible_aliases(tmp_path):
    visible_id = "a" * 64
    hidden_id = "b" * 64
    aliases = AliasTable(
        {"XVISIBLE": visible_id, "XHIDDEN": hidden_id}
    )
    seen = []

    def respond(prompt):
        seen.append(prompt)
        return '{"candidates":[{"content":"x","typicality":0.5,"neighbours":[]}]}'

    endpoint = MockEndpoint(respond, name="mock://gemma", model="gemma4:31b")
    adapter = LLMAdapter(
        {"conjecturer": endpoint},
        Harness(tmp_path / "alias-run").blobs,
        model_profile="compact",
    )
    pack = "x" * 4770 + visible_id + "TAIL" + "y" * 1500 + hidden_id
    adapter.call(
        "conjecturer",
        pack,
        ConjecturerOutput,
        wire_contract=ConjecturerWireContract(aliases),
    )

    prompt = seen[0]
    assert "XVISIBLETAIL" in prompt
    assert visible_id not in prompt
    assert "XHIDDEN" not in prompt


def test_direct_exhaustion_arms_only_the_next_ordinary_call_for_compact(tmp_path):
    harness = Harness(tmp_path / "recovery-run")
    endpoint = MockEndpoint(
        [
            "bad-initial",
            "bad-whole-repair",
            "bad-subtree-repair",
            '{"candidates":[{"content":"recovered","typicality":0.4,"neighbours":[]}]}',
        ],
        name="mock://gemma",
        model="gemma4:31b",
    )
    adapter = LLMAdapter(
        {"conjecturer": endpoint},
        harness.blobs,
        retry_max=99,
        model_profile="standard",
    )

    with pytest.raises(SchemaRepairError) as raised:
        adapter.call(
            "conjecturer",
            "PACK",
            ConjecturerOutput,
            aliases=AliasTable(),
        )
    failed = raised.value.spend
    assert failed is not None
    assert failed.attempts == 3
    assert len(endpoint._responses) == 1
    assert {item.contract_id for item in failed.attempt_trace} == {
        "conjecturer.direct.v1"
    }
    assert {item.model_profile for item in failed.attempt_trace} == {"standard"}
    assert {item.transport_profile for item in failed.attempt_trace} == {"standard"}
    harness.record_llm_calls([failed], "dropped-call", "schema-exhausted")
    assert len(list(harness.log.read())) == 1

    assert adapter.profile_for("conjecturer") == "compact"
    output, recovered = adapter.call(
        "conjecturer",
        "PACK",
        ConjecturerOutput,
        aliases=AliasTable(),
    )
    assert output.candidates[0].content == "recovered"
    assert recovered.attempts == 1
    assert recovered.attempt_trace[0].contract_id == "conjecturer.compact.v1"
    assert recovered.attempt_trace[0].model_profile == "standard"
    assert recovered.attempt_trace[0].transport_profile == "compact"
    assert (
        recovered.attempt_trace[0].route_sha256
        == failed.attempt_trace[0].route_sha256
    )
    assert endpoint._responses == []
    harness.record_llm_calls([recovered], "recovered-call")

    events = list(Harness(harness.root).log.read())
    assert [event.seq for event in events] == [0, 1]
    assert events[0].llm == failed
    report = eval_report(harness, Config())
    transport = report["process"]["transport_totals"]
    assert transport["profiles"] == {"compact": 1, "standard": 1}
    assert transport["compact_recovery_calls"] == 1
    assert report["llm"]["conjecturer"]["compact_recovery_calls"] == 1


def test_frontier_uses_direct_without_recovery_overhead_before_failure(tmp_path):
    endpoint = MockEndpoint(
        ['{"candidates":[{"content":"direct","typicality":0.5}]}'],
        name="mock://frontier",
        model="frontier-1",
    )
    adapter = LLMAdapter(
        {"conjecturer": endpoint},
        Harness(tmp_path / "frontier-run").blobs,
        model_profile="frontier",
    )
    _, call = adapter.call(
        "conjecturer", "PACK", ConjecturerOutput, aliases=AliasTable()
    )
    assert call.attempts == 1
    assert call.attempt_trace[0].contract_id == "conjecturer.direct.v1"
    assert call.attempt_trace[0].transport_profile == "frontier"
    assert adapter.profile_for("conjecturer") == "frontier"


def test_unsupported_auxiliary_contract_uses_safe_direct_wire_recovery(tmp_path):
    endpoint = MockEndpoint(
        ["bad", "bad", "bad", '{"prose":"safe direct fallback"}'],
        name="mock://aux",
        model="frontier-1",
    )
    adapter = LLMAdapter(
        {"summarizer": endpoint},
        Harness(tmp_path / "aux-run").blobs,
        model_profile="standard",
    )
    with pytest.raises(SchemaRepairError) as raised:
        adapter.call("summarizer", "PACK", ProseOutput)
    assert raised.value.spend.attempts == 3
    assert adapter.profile_for("summarizer") == "compact"

    output, call = adapter.call("summarizer", "PACK", ProseOutput)
    assert output.prose == "safe direct fallback"
    assert call.attempt_trace[0].contract_id == "prose.direct.v1"
    assert call.attempt_trace[0].model_profile == "standard"
    assert call.attempt_trace[0].transport_profile == "compact"


def test_compact_profile_never_changes_after_exhaustion(tmp_path):
    endpoint = MockEndpoint(
        ["bad", "bad", "bad"],
        name="mock://compact",
        model="gemma4:31b",
    )
    adapter = LLMAdapter(
        {"conjecturer": endpoint},
        Harness(tmp_path / "compact-run").blobs,
        model_profile="compact",
    )
    with pytest.raises(SchemaRepairError) as raised:
        adapter.call(
            "conjecturer", "PACK", ConjecturerOutput, aliases=AliasTable()
        )
    assert adapter.profile_for("conjecturer") == "compact"
    assert {item.transport_profile for item in raised.value.spend.attempt_trace} == {
        "compact"
    }


def test_missing_required_field_remains_a_local_subtree_repair(tmp_path):
    endpoint = MockEndpoint(
        [
            '{"candidates":[{"typicality":0.5}]}',
            '{"candidates":[{"typicality":0.5}]}',
            '"restored"',
        ]
    )
    harness = Harness(tmp_path / "missing-field-run")
    output, call = LLMAdapter(
        {"conjecturer": endpoint}, harness.blobs, retry_max=2
    ).call("conjecturer", "PACK", ConjecturerOutput)

    assert output.candidates[0].content == "restored"
    final = call.attempt_trace[-1]
    assert final.repair_scope == "/candidates/0/content"
    assert final.validation_path == "/candidates/0/content"
    prompt = harness.blobs.get(final.prompt_ref).decode()
    assert "CURRENT JSON:\nnull" in prompt


def test_critic_callsite_rebuilds_bound_compact_contract_after_failure(tmp_path):
    harness = Harness(tmp_path / "critic-recovery-run")
    target = harness.create_artifact("a criticizable claim")
    endpoint = MockEndpoint(
        [
            "bad",
            "bad",
            "bad",
            json.dumps(
                {
                    "attack": False,
                    "target_alias": "A1",
                    "claim": "",
                    "grounds": "",
                    "cited_input_aliases": [],
                    "counterexample": None,
                }
            ),
        ],
        name="mock://critic",
        model="gemma4:31b",
    )
    adapter = LLMAdapter(
        {"argumentative_critic": endpoint},
        harness.blobs,
        model_profile="standard",
    )

    with pytest.raises(SchemaRepairError) as raised:
        crit_argumentative(harness, target.id, adapter, Config())
    harness.record_llm_calls([raised.value.spend], "dropped-call")
    assert adapter.profile_for("argumentative_critic") == "compact"

    assert crit_argumentative(harness, target.id, adapter, Config()) is None
    logged = [event.llm for event in harness.log.read() if event.llm is not None]
    assert logged[-1].attempt_trace[0].contract_id == (
        "argumentative_critic.compact.v1"
    )
    assert logged[-1].attempt_trace[0].transport_profile == "compact"


def test_compact_recovery_rehydrates_from_durable_direct_drop(
    tmp_path, monkeypatch
):
    harness = Harness(tmp_path / "rehydrated-recovery-run")
    endpoint = MockEndpoint(
        [
            "bad-initial",
            "bad-whole-repair",
            "bad-subtree-repair",
            '{"candidates":[{"content":"after resume","typicality":0.6,"neighbours":[]}]}',
        ],
        name="mock://gemma",
        model="gemma4:31b",
    )
    first = LLMAdapter(
        {"conjecturer": endpoint},
        harness.blobs,
        retry_max=2,
        model_profile="standard",
    )
    with pytest.raises(SchemaRepairError) as raised:
        first.call(
            "conjecturer", "PACK", ConjecturerOutput, aliases=AliasTable()
        )
    failed = raised.value.spend
    assert failed is not None
    harness.record_llm_calls([failed], "dropped-call", "schema-exhausted")

    config = Config(
        model_profile="standard",
        roles={
            "conjecturer": {
                "endpoint": endpoint.name,
                "model": endpoint.model,
                "provider": "mock",
            }
        },
    )
    monkeypatch.setattr(
        "deepreason.llm.adapter._endpoint_from_spec", lambda _spec: endpoint
    )
    rebuilt = build_adapter(
        config,
        harness.blobs,
        process_events=Harness(harness.root).log.read(),
    )
    assert rebuilt is not first
    assert rebuilt.profile_for("conjecturer") == "compact"

    output, recovered = rebuilt.call(
        "conjecturer", "PACK", ConjecturerOutput, aliases=AliasTable()
    )
    assert output.candidates[0].content == "after resume"
    assert recovered.attempts == 1
    assert recovered.attempt_trace[0].contract_id == "conjecturer.compact.v1"
    assert recovered.attempt_trace[0].model_profile == "standard"
    assert recovered.attempt_trace[0].transport_profile == "compact"
    assert recovered.model == failed.model == "gemma4:31b"
    assert recovered.endpoint == failed.endpoint == "mock://gemma"
    assert (
        recovered.attempt_trace[0].route_sha256
        == failed.attempt_trace[0].route_sha256
    )


def test_model_output_cannot_rehydrate_compact_recovery(
    tmp_path, monkeypatch
):
    harness = Harness(tmp_path / "untrusted-recovery-run")
    original = MockEndpoint(
        ["bad", "bad", "bad"], name="mock://original", model="gemma4:31b"
    )
    first = LLMAdapter(
        {"conjecturer": original},
        harness.blobs,
        model_profile="standard",
    )
    with pytest.raises(SchemaRepairError) as raised:
        first.call("conjecturer", "PACK", ConjecturerOutput)
    # Even a model-authored phrase that names recovery is not the
    # harness-owned dropped-call process signal.
    harness.record_llm_calls(
        [raised.value.spend], "model-output", "compact-recovery"
    )

    config = Config(
        model_profile="standard",
        roles={
            "conjecturer": {
                "endpoint": original.name,
                "model": original.model,
                "provider": "mock",
            }
        },
    )
    monkeypatch.setattr(
        "deepreason.llm.adapter._endpoint_from_spec", lambda _spec: original
    )
    rebuilt = build_adapter(
        config,
        harness.blobs,
        process_events=Harness(harness.root).log.read(),
    )
    assert rebuilt.profile_for("conjecturer") == "standard"


def test_foreign_route_drop_cannot_rehydrate_compact_recovery(
    tmp_path, monkeypatch
):
    harness = Harness(tmp_path / "foreign-route-recovery-run")
    original = MockEndpoint(
        ["bad", "bad", "bad"], name="mock://original", model="gemma4:31b"
    )
    first = LLMAdapter(
        {"conjecturer": original}, harness.blobs, model_profile="standard"
    )
    with pytest.raises(SchemaRepairError) as raised:
        first.call("conjecturer", "PACK", ConjecturerOutput)
    harness.record_llm_calls(
        [raised.value.spend], "dropped-call", "schema-exhausted"
    )

    replacement = MockEndpoint(
        ['{"candidates":[]}'], name="mock://replacement", model="gemma4:31b"
    )
    config = Config(
        model_profile="standard",
        roles={
            "conjecturer": {
                "endpoint": replacement.name,
                "model": replacement.model,
                "provider": "mock",
            }
        },
    )
    monkeypatch.setattr(
        "deepreason.llm.adapter._endpoint_from_spec", lambda _spec: replacement
    )
    rebuilt = build_adapter(
        config,
        harness.blobs,
        process_events=Harness(harness.root).log.read(),
    )
    assert rebuilt.profile_for("conjecturer") == "standard"
