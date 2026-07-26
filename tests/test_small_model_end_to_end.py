"""End-to-end reproductions of the Gemma operator-confusion failures.

These tests keep provider I/O offline, but deliberately retain the real CLI,
RunManifest, endpoint construction, route leases, compact wire contracts,
bounded repair, website workflow, event log, and replay paths.  The only
substitution is a scripted completion transport.

Under the V6-only contract, the public CLI compiles only schema-version-6
manifests and the retired ``make`` facade fails closed, so the original
complete page build is reproduced at the component level while the public
half asserts the current compile and dispatch boundaries.
"""

from __future__ import annotations

import json
import re
import threading
import time
from collections import Counter

import pytest
import yaml

from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.llm.endpoints import OpenAICompatEndpoint
from deepreason.llm.repair import SchemaRepairError
from deepreason.ontology import Rule
from deepreason.run_manifest import (
    compile_run_manifest,
    config_from_run_manifest,
    load_run_manifest,
    persist_run_manifest,
)
from deepreason.workflows.manifest_compiler import (
    CompactArtDirection,
    CompactDesignOutline,
)
from deepreason.workflows.website import WebsiteWorkflow


GEMMA_MODEL = "gemma4:31b"
GEMMA_ENDPOINT = "https://gemma.invalid/v1"
DEEPSEEK_MODEL = "deepseek-v4"
DEEPSEEK_ENDPOINT = "https://deepseek.invalid/v1"
STAMP = "2026-07-11T00:00:00Z"


@pytest.fixture
def _below_public_admission(monkeypatch):
    """Keep pre-v6 component coverage below the public V6-only admission.

    Mirrors the committed test_cli_bridge idiom: the raw V6-only loading
    boundary has its own coverage in test_v6_only_manifest_loading; these
    reproductions exercise the pre-transactional compact seat contracts,
    which v6 dispatch closes (asserted by the r1 regression above).
    """

    from pathlib import Path

    import deepreason.invariants as invariants_module
    from deepreason.run_manifest import RunManifest

    def _load(path, **_kwargs):
        return RunManifest.model_validate_json(Path(path).read_bytes())

    monkeypatch.setattr("deepreason.run_manifest.load_run_manifest", _load)
    monkeypatch.setattr(invariants_module, "load_run_manifest", _load)
    monkeypatch.setattr(
        "deepreason.runtime.launch_policy.require_v6_launch_allowed",
        lambda _subject, *, operation: None,
    )


def _route(model: str, endpoint: str, *, endpoint_id: str, family: str) -> dict:
    return {
        "endpoint_id": endpoint_id,
        "endpoint": endpoint,
        "model": model,
        "provider": "ollama" if family == "gemma" else "deepseek",
        "family": family,
        "reasoning": "none",
        "temperature": 0.0,
        # A compiled completion cap: the reserve-settle TokenMeter fails
        # closed when a finite budget meets a route with no max_tokens.
        "max_tokens": 2048,
        "output_mechanism": "json_text",
    }


def _note_completion(endpoint: OpenAICompatEndpoint, prompt: str, raw: str) -> str:
    """Populate the same process fields as a successful provider exchange."""
    endpoint.last_usage = {
        "prompt_tokens": max(1, len(prompt) // 4),
        "completion_tokens": max(1, len(raw) // 4),
    }
    endpoint.last_finish_reason = "stop"
    endpoint.last_mean_surprisal = None
    endpoint.last_transport_attempts = 1
    endpoint.last_transport_diagnostics = []
    return raw


def _install_dna_transport(monkeypatch, calls: list[tuple[str, str, str]]) -> None:
    """Script valid, flat Gemma website values on real endpoint instances."""

    def complete(self, prompt, images=None, **_kwargs):
        calls.append((self.model, self.name, prompt))
        if self.model != GEMMA_MODEL:
            raise AssertionError(f"decoy model was invoked: {self.model}")
        if "WEBSITE DESIGN OUTLINE" in prompt:
            value = {
                "components": [
                    {"alias": "C1", "purpose": "animated DNA hero"},
                    {"alias": "C2", "purpose": "replication explanation"},
                ]
            }
        elif "WEBSITE ART DIRECTION" in prompt:
            value = {
                "palette": "deep navy with cyan highlights",
                "typography": "geometric headings and readable body text",
                "spacing_strategy": "fluid grid spacing",
                "responsive_strategy": "single column on narrow screens",
                "interaction_state_model": "local controls plus global motion state",
                "motion_language": "slow orbital strand motion",
                "scroll_narrative": "hero gives way to replication",
                "depth_structure": "helix above quiet cellular layers",
                "transition_grammar": "opacity and transform",
                "texture_language": "luminous grain",
                "reduced_motion_version": "all content remains visible and still",
                "static_fallback": "complete readable still composition",
            }
        elif "Target: C1" in prompt:
            value = {
                "alias": "C1",
                "slots": ["root"],
                "exports": ["mount"],
                "owned_dom_ids": ["dna-hero"],
                "depends_on": [],
                "content_requirements": ["title", "helix illustration"],
                "motion_requirement": "static",
            }
        elif "Target: C2" in prompt:
            value = {
                "alias": "C2",
                "slots": ["root"],
                "exports": ["destroy"],
                "owned_dom_ids": ["dna-copy"],
                "depends_on": ["C1"],
                "content_requirements": ["replication steps"],
                "motion_requirement": "static",
            }
        else:
            raise AssertionError(f"unexpected provider prompt: {prompt[:200]}")
        return _note_completion(self, prompt, json.dumps(value))

    monkeypatch.setattr(OpenAICompatEndpoint, "complete", complete)


def test_r1_persisted_single_model_manifest_makes_decoy_configs_irrelevant(
    tmp_path,
    monkeypatch,
):
    """The original DNA run cannot discover or invoke the DeepSeek decoy.

    V6-only migration: the public CLI now compiles only schema-version-6
    manifests, the ``make`` facade is retired, and v6 provider dispatch is
    transactional.  The decoy-irrelevance theorem is asserted at the current
    boundaries: compile-time route freezing, runtime input isolation, and
    fail-closed dispatch before any transport.
    """
    from deepreason.cli.main import main
    from deepreason.llm.adapter import WorkflowAuthorizationError
    from deepreason.llm.firewall import leases_from_manifest
    from deepreason.ontology import Commitment
    from deepreason.run_manifest import bind_run_manifest
    from tests.test_run_input_v6_commitments import _bind_v2, _control

    gemma_config = tmp_path / "gemma.yaml"
    deepseek_config = tmp_path / "deepseek.yaml"
    manifest_path = tmp_path / "compiled-run-manifest.json"
    run_root = tmp_path / "dna-run"
    output = tmp_path / "dna-site"

    # The selected source contains a decoy route, and an unrelated DeepSeek
    # config sits beside it exactly as in the reported repository failure.
    gemma_config.write_text(
        yaml.safe_dump(
            {
                "model_profile": "compact",
                "BROWSER_PER_CYCLE": 0,
                "roles": {
                    "conjecturer": _route(
                        GEMMA_MODEL,
                        GEMMA_ENDPOINT,
                        endpoint_id="gemma-cloud",
                        family="gemma",
                    ),
                    "summarizer": _route(
                        DEEPSEEK_MODEL,
                        DEEPSEEK_ENDPOINT,
                        endpoint_id="deepseek-decoy",
                        family="deepseek",
                    ),
                },
            }
        ),
        encoding="utf-8",
    )
    deepseek_config.write_text(
        yaml.safe_dump(
            {
                "model_profile": "compact",
                "roles": {
                    "conjecturer": _route(
                        DEEPSEEK_MODEL,
                        DEEPSEEK_ENDPOINT,
                        endpoint_id="deepseek-decoy",
                        family="deepseek",
                    )
                },
            }
        ),
        encoding="utf-8",
    )

    discovery_calls = []

    def forbidden_discovery(*args, **kwargs):
        discovery_calls.append((args, kwargs))
        raise AssertionError("runtime model discovery was attempted")

    monkeypatch.setattr("deepreason.llm.endpoints.list_models", forbidden_discovery)

    # V6 compile inputs: one frozen run input and one complete control-plane
    # policy.  The decoy config file remains beside the selected source.
    run_input = _bind_v2(
        run_root, Commitment(id="k-r1-dna-run", eval="predicate:True")
    )
    policy_path = tmp_path / "control-plane-policy.json"
    policy_path.write_text(
        _control(6).model_dump_json(by_alias=True), encoding="utf-8"
    )
    assert main(
        [
            "--root",
            str(tmp_path / "compile-state"),
            "--config",
            str(gemma_config),
            "config",
            "compile",
            "--single-model",
            GEMMA_MODEL,
            "--profile",
            "compact",
            "--rubric-policy",
            "forbid",
            "--workload-profile",
            "website",
            "--control-plane-policy",
            str(policy_path),
            "--run-input-digest",
            run_input.run_input_digest,
            "--out",
            str(manifest_path),
        ]
    ) == 0
    compiled = load_run_manifest(manifest_path)
    assert compiled.schema_version == 6
    assert {
        route.model_id
        for routes in compiled.roles.values()
        for route in routes
    } == {GEMMA_MODEL}
    assert {
        route.endpoint_id
        for routes in compiled.roles.values()
        for route in routes
    } == {"gemma-cloud"}

    # Once compiled, neither the explicitly supplied decoy source file nor
    # provider discovery is a runtime input.  The bound manifest is the only
    # route authority seen by the runtime reconstruction paths.
    def forbidden_source_reload(*_args, **_kwargs):
        raise AssertionError("source/decoy configuration was read after compilation")

    monkeypatch.setattr("deepreason.config.load", forbidden_source_reload)
    endpoint_calls: list[tuple[str, str, str]] = []
    _install_dna_transport(monkeypatch, endpoint_calls)

    bind_run_manifest(compiled, run_root)
    persisted = load_run_manifest(run_root / "run-manifest.json")
    assert persisted.canonical_bytes() == compiled.canonical_bytes()

    # Route authority reconstructed from the persisted manifest alone: every
    # role seat leases the frozen Gemma route; the decoy has no seat.
    leases = leases_from_manifest(persisted)
    assert set(leases) == {
        role for role, routes in persisted.roles.items() if routes
    }
    assert {
        lease.route.endpoint_id
        for seats in leases.values()
        for lease in seats
    } == {"gemma-cloud"}
    assert {
        lease.route.model_id for seats in leases.values() for lease in seats
    } == {GEMMA_MODEL}

    harness = Harness(run_root)
    runtime_config = config_from_run_manifest(persisted)
    workflow = WebsiteWorkflow(
        harness,
        runtime_config,
        "the wonders of DNA",
        output,
        10,
        100_000,
        lambda _message: None,
        run_manifest=persisted,
    )

    # V6 dispatch fails closed before any transport: without a bound
    # transaction not even the legitimate frozen route can be invoked, so a
    # decoy invocation is unreachable a fortiori.
    with pytest.raises(
        WorkflowAuthorizationError, match="requires a bound transaction"
    ):
        workflow._compact_outline_call("an ordinary adjudicated plan")

    assert endpoint_calls == []
    assert discovery_calls == []
    assert [
        event for event in Harness(run_root).log.read() if event.llm is not None
    ] == []


def test_r2_malicious_control_json_exhausts_locally_and_only_logs_process_drop(
    tmp_path,
    monkeypatch,
    _below_public_admission,
):
    """Authored routing/guard commands cannot mutate or select another seat."""
    gemma = _route(
        GEMMA_MODEL,
        GEMMA_ENDPOINT,
        endpoint_id="gemma-cloud",
        family="gemma",
    )
    deepseek = _route(
        DEEPSEEK_MODEL,
        DEEPSEEK_ENDPOINT,
        endpoint_id="deepseek-seat",
        family="deepseek",
    )
    manifest = compile_run_manifest(
        Config(
            model_profile="compact",
            RETRY_MAX=20,
            roles={"conjecturer": [gemma, deepseek]},
        ),
        model_profile="compact",
        rubric_policy="forbid",
        compiled_at=STAMP,
    )
    run_root = tmp_path / "malicious-run"
    persist_run_manifest(manifest, run_root)
    harness = Harness(run_root)
    config = config_from_run_manifest(manifest)
    workflow = WebsiteWorkflow(
        harness,
        config,
        "the wonders of DNA",
        tmp_path / "site",
        10,
        100_000,
        lambda _message: None,
        run_manifest=manifest,
    )

    forbidden_fields = {
        "model": DEEPSEEK_MODEL,
        "endpoint": "https://forbidden-route.invalid/v1",
        "delegate": "FORBIDDEN-DELEGATE-CANARY",
        "bypass_guards": "FORBIDDEN-GUARD-CANARY",
        "permission": "FORBIDDEN-PERMISSION-CANARY",
        "command": "FORBIDDEN-COMMAND-CANARY",
    }
    malicious = json.dumps({
        "components": [{"alias": "C1", "purpose": "DNA hero"}],
        **forbidden_fields,
    })
    provider_calls: Counter[str] = Counter()
    gemma_prompts: list[str] = []

    def complete(self, prompt, images=None, **_kwargs):
        provider_calls[self.model] += 1
        if self.model == GEMMA_MODEL:
            gemma_prompts.append(prompt)
        raw = (
            json.dumps({"components": [{"alias": "C9", "purpose": "alternate"}]})
            if self.model == DEEPSEEK_MODEL
            else malicious
        )
        return _note_completion(self, prompt, raw)

    monkeypatch.setattr(OpenAICompatEndpoint, "complete", complete)
    state_before = harness.state.model_dump(mode="json")
    commitments_before = dict(harness.commitments)
    warrants_before = dict(harness.warrants)
    manifest_before = manifest.canonical_bytes()
    config_before = config.model_dump(mode="json")

    with pytest.raises(SchemaRepairError) as raised:
        workflow._compact_outline_call("an ordinary adjudicated plan")

    # RETRY_MAX=20 cannot open a fourth transport turn. Every repair stays on
    # the original leased seat; the model-authored DeepSeek name is inert.
    assert provider_calls == Counter({GEMMA_MODEL: 3})
    assert len(gemma_prompts) == 3
    for repair_prompt in gemma_prompts[1:]:
        lowered = repair_prompt.casefold()
        for field, forbidden_value in forbidden_fields.items():
            assert f'"{field}"' not in lowered
            assert forbidden_value not in repair_prompt
    assert raised.value.spend is not None
    assert raised.value.spend.model == GEMMA_MODEL
    assert raised.value.spend.endpoint == GEMMA_ENDPOINT
    assert raised.value.spend.attempts == 3
    assert [attempt.valid for attempt in raised.value.spend.attempt_trace] == [
        False,
        False,
        False,
    ]

    assert harness.state.model_dump(mode="json") == state_before
    assert harness.commitments == commitments_before
    assert harness.warrants == warrants_before
    assert manifest.canonical_bytes() == manifest_before
    assert config.model_dump(mode="json") == config_before

    events = list(Harness(run_root).log.read())
    assert len(events) == 1
    event = events[0]
    assert event.rule == Rule.MEASURE
    assert list(event.inputs[:2]) == ["website-compact-dropped", "design-outline"]
    assert list(event.outputs) == []
    assert event.llm is not None and event.llm.model == GEMMA_MODEL
    assert event.state_diff.model_dump(mode="json", by_alias=True) == {
        "att+": [],
        "dep+": [],
        "A+": [],
        "Π+": [],
        "status_changed": [],
        "hv_set": {},
        "reach_set": {},
        "addr+": [],
        "carry+": [],
    }
    raw_attempts = [
        harness.blobs.get(attempt.raw_ref).decode("utf-8")
        for attempt in event.llm.attempt_trace
    ]
    assert raw_attempts == [malicious, malicious, malicious]
    assert all(
        json.loads(raw)["bypass_guards"] == "FORBIDDEN-GUARD-CANARY"
        for raw in raw_attempts
    )


def test_r3_concurrent_peer_command_is_inert_and_events_commit_in_alias_order(
    tmp_path,
    monkeypatch,
    _below_public_admission,
):
    """Concurrent endpoint replies cannot create calls or reorder the writer."""
    route = _route(
        GEMMA_MODEL,
        GEMMA_ENDPOINT,
        endpoint_id="gemma-cloud",
        family="gemma",
    )
    manifest = compile_run_manifest(
        Config(model_profile="compact", roles={"conjecturer": route}),
        single_model=GEMMA_MODEL,
        model_profile="compact",
        rubric_policy="forbid",
        concurrency=3,
        compiled_at=STAMP,
    )
    run_root = tmp_path / "concurrent-run"
    persist_run_manifest(manifest, run_root)
    harness = Harness(run_root)
    workflow = WebsiteWorkflow(
        harness,
        config_from_run_manifest(manifest),
        "the wonders of DNA",
        tmp_path / "site",
        10,
        100_000,
        lambda _message: None,
        run_manifest=manifest,
    )
    outline = CompactDesignOutline.model_validate(
        {
            "components": [
                {"alias": "C3", "purpose": "repair"},
                {"alias": "C1", "purpose": "hero"},
                {"alias": "C2", "purpose": "transcription"},
            ]
        }
    )
    art_direction = CompactArtDirection.model_validate(
        {
            "palette": "deep navy with cyan highlights",
            "typography": "geometric headings and readable body text",
            "spacing_strategy": "fluid grid spacing",
            "responsive_strategy": "single column on narrow screens",
            "interaction_state_model": "local controls plus global motion state",
            "motion_language": "orbital strands",
            "scroll_narrative": "cell to chromosome",
            "depth_structure": "layered nucleus",
            "transition_grammar": "opacity and transform",
            "texture_language": "luminous grain",
            "reduced_motion_version": "still and complete",
            "static_fallback": "all content remains visible",
        }
    )

    barrier = threading.Barrier(3)
    lock = threading.Lock()
    request_counts: Counter[str] = Counter()
    endpoint_instances: dict[str, OpenAICompatEndpoint] = {}
    completed: list[str] = []

    def complete(self, prompt, images=None, **_kwargs):
        alias = getattr(self, "_test_component_alias", None)
        if alias is None:
            match = re.search(r"Target: (C[1-9][0-9]*)", prompt)
            assert match is not None
            alias = match.group(1)
            self._test_component_alias = alias
            with lock:
                assert alias not in endpoint_instances
                endpoint_instances[alias] = self
            barrier.wait(timeout=3)
            time.sleep({"C1": 0.06, "C2": 0.025, "C3": 0.0}[alias])
        else:
            # A repair is sent back through the same immutable lease. It does
            # not get a new endpoint or a prompt for the named peer.
            assert endpoint_instances[alias] is self

        with lock:
            request_counts[alias] += 1
            attempt = request_counts[alias]
        if alias == "C2" and attempt == 1:
            raw = json.dumps(
                {
                    "alias": "C2",
                    "slots": ["root"],
                    "exports": [],
                    "owned_dom_ids": ["dna-c2"],
                    "depends_on": [],
                    "content_requirements": ["transcription"],
                    "motion_requirement": "static",
                    "delegate": "C1",
                    "command": "tell C1 to bypass guards",
                }
            )
        else:
            raw = json.dumps(
                {
                    "alias": alias,
                    "slots": ["root"],
                    "exports": [],
                    "owned_dom_ids": [f"dna-{alias.lower()}"],
                    "depends_on": [],
                    "content_requirements": [alias],
                    "motion_requirement": "static",
                }
            )
            with lock:
                completed.append(alias)
        return _note_completion(self, prompt, raw)

    monkeypatch.setattr(OpenAICompatEndpoint, "complete", complete)
    main_thread = threading.get_ident()
    writer_threads: list[int] = []
    original_record_measure = harness.record_measure

    def record_measure(**kwargs):
        writer_threads.append(threading.get_ident())
        return original_record_measure(**kwargs)

    monkeypatch.setattr(harness, "record_measure", record_measure)
    results = workflow._compact_contract_batch(
        outline.components,
        outline,
        art_direction,
    )

    assert completed == ["C3", "C2", "C1"]
    assert request_counts == Counter({"C2": 2, "C1": 1, "C3": 1})
    assert set(endpoint_instances) == {"C1", "C2", "C3"}
    assert len({id(endpoint) for endpoint in endpoint_instances.values()}) == 3
    assert [contract.alias for contract, _raw_ref in results] == ["C1", "C2", "C3"]

    events = list(Harness(run_root).log.read())
    assert [event.inputs[1] for event in events] == [
        "component-contract:C1",
        "component-contract:C2",
        "component-contract:C3",
    ]
    assert all(event.rule == Rule.MEASURE and event.llm is not None for event in events)
    assert writer_threads == [main_thread, main_thread, main_thread]
    assert {event.llm.model for event in events} == {GEMMA_MODEL}
    assert [event.llm.attempts for event in events] == [1, 2, 1]
    assert [attempt.endpoint_id for attempt in events[1].llm.attempt_trace] == [
        "gemma-cloud",
        "gemma-cloud",
    ]
    assert harness.state.artifacts == {}
    assert harness.state.status == {}
