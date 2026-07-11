"""Harness-owned website concurrency and recovery selection."""

from __future__ import annotations

import json
import threading
import time
from types import SimpleNamespace

from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.ontology import Interface, LLMAttempt, LLMCall, Provenance
from deepreason.rules.crit import crit_program
from deepreason.workflows.manifest_compiler import (
    CompactArtDirection,
    CompactDesignOutline,
)
from deepreason.workflows.website import WebsiteWorkflow


def _workflow(tmp_path, *, concurrency: int, profile: str = "compact"):
    harness = Harness(tmp_path / f"run-{profile}-{concurrency}")
    manifest = SimpleNamespace(model_profile=profile, concurrency=concurrency)
    workflow = WebsiteWorkflow(
        harness,
        Config(model_profile=profile),
        "the wonders of DNA",
        tmp_path / "site",
        10,
        100_000,
        lambda _message: None,
        run_manifest=manifest,
    )
    return harness, workflow


def _outline():
    # Deliberately shuffled: commit order is canonical alias order, never
    # caller order or worker completion order.
    return CompactDesignOutline.model_validate({"components": [
        {"alias": "C3", "purpose": "repair"},
        {"alias": "C1", "purpose": "hero"},
        {"alias": "C2", "purpose": "transcription"},
    ]})


def _art_direction():
    return CompactArtDirection.model_validate({
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
    })


def test_manifest_concurrency_is_bounded_and_profile_defaults_stay_sequential(tmp_path):
    _harness, compact = _workflow(tmp_path, concurrency=1)
    assert compact._component_concurrency(8) == 1

    _harness, parallel = _workflow(tmp_path, concurrency=3)
    assert parallel._component_concurrency(8) == 3
    assert parallel._component_concurrency(2) == 2

    _harness, bounded = _workflow(tmp_path, concurrency=10_000)
    assert bounded._component_concurrency(10_000) == 12

    # A library call without a persisted manifest consumes the profile's
    # declared default: compact stays one; frontier retains its fast-path cap.
    harness = Harness(tmp_path / "profile-defaults")
    compact_default = WebsiteWorkflow(
        harness, Config(model_profile="compact"), "dna", tmp_path / "a", 2,
        None, lambda _message: None,
    )
    frontier_default = WebsiteWorkflow(
        harness, Config(model_profile="frontier"), "dna", tmp_path / "b", 2,
        None, lambda _message: None,
    )
    assert compact_default._component_concurrency(8) == 1
    assert frontier_default._component_concurrency(8) == 4


def test_compact_default_keeps_the_sequential_adapter_path(tmp_path, monkeypatch):
    _harness, workflow = _workflow(tmp_path, concurrency=1)
    outline = _outline()
    calls: list[tuple[str, int]] = []
    main_thread = threading.get_ident()

    def compact_call(**job):
        alias = job["label"].rsplit(":", 1)[-1]
        calls.append((alias, threading.get_ident()))
        return SimpleNamespace(alias=alias), f"raw-{alias}"

    monkeypatch.setattr(workflow, "_compact_call", compact_call)
    monkeypatch.setattr(
        workflow,
        "_collect_compact_call",
        lambda **_kwargs: (_ for _ in ()).throw(
            AssertionError("default compact path must not create a worker adapter")
        ),
    )

    results = workflow._compact_contract_batch(
        outline.components, outline, _art_direction()
    )

    assert calls == [("C1", main_thread), ("C2", main_thread), ("C3", main_thread)]
    assert [value.alias for value, _raw in results] == ["C1", "C2", "C3"]


def test_component_transports_overlap_but_commit_in_component_id_order(
    tmp_path, monkeypatch,
):
    harness, workflow = _workflow(tmp_path, concurrency=3)
    outline = _outline()
    art = _art_direction()
    state = {"active": 0, "peak": 0}
    lock = threading.Lock()
    all_started = threading.Event()

    def response(prompt: str) -> str:
        alias = next(alias for alias in ("C1", "C2", "C3") if f"Target: {alias}" in prompt)
        with lock:
            state["active"] += 1
            state["peak"] = max(state["peak"], state["active"])
            if state["active"] == 3:
                all_started.set()
        assert all_started.wait(timeout=2), "component transports did not overlap"
        # Complete in reverse order to prove completion timing cannot select
        # append order.
        time.sleep({"C1": 0.03, "C2": 0.015, "C3": 0.0}[alias])
        with lock:
            state["active"] -= 1
        return json.dumps({
            "alias": alias,
            "slots": ["root"],
            "exports": [],
            "owned_dom_ids": [f"dna-{alias.lower()}"],
            "depends_on": [],
            "content_requirements": [alias],
            "motion_requirement": "static",
        })

    def fake_build_adapter(config, blob_store, meter=None, only_roles=None,
                           run_manifest=None):
        endpoint = MockEndpoint(response, name="gemma-cloud", model="gemma4:31b")
        return LLMAdapter(
            {"conjecturer": endpoint},
            blob_store,
            retry_max=config.RETRY_MAX,
            meter=meter,
            model_profile="compact",
        )

    monkeypatch.setattr("deepreason.llm.adapter.build_adapter", fake_build_adapter)
    main_thread = threading.get_ident()
    writer_threads: list[int] = []
    original_record = harness.record_measure

    def record_measure(**kwargs):
        writer_threads.append(threading.get_ident())
        return original_record(**kwargs)

    monkeypatch.setattr(harness, "record_measure", record_measure)
    results = workflow._compact_contract_batch(outline.components, outline, art)

    assert state["peak"] == 3
    assert [contract.alias for contract, _raw in results] == ["C1", "C2", "C3"]
    labels = [
        event.inputs[1]
        for event in harness.log.read()
        if event.inputs and event.inputs[0] == "website-compact-call"
    ]
    assert labels == [
        "component-contract:C1",
        "component-contract:C2",
        "component-contract:C3",
    ]
    assert writer_threads == [main_thread, main_thread, main_thread]
    assert {event.llm.model for event in harness.log.read() if event.llm} == {
        "gemma4:31b"
    }


def test_direct_recovery_requires_measured_schema_or_manifest_failure(tmp_path):
    harness, workflow = _workflow(tmp_path, concurrency=1, profile="frontier")
    assert workflow._direct_recovery_reason(0) is None

    prompt_ref = harness.blobs.put(b"prompt")
    raw_ref = harness.blobs.put(b"not-json")
    diagnostic_ref = harness.blobs.put(b"schema diagnostic")
    harness.record_measure(
        inputs=["dropped-call", "role conjecturer: no schema-valid output"],
        llm=LLMCall(
            role="conjecturer",
            model="gemma4:31b",
            endpoint="gemma-cloud",
            prompt_ref=prompt_ref,
            raw_ref=raw_ref,
            attempts=1,
            attempt_trace=[LLMAttempt(
                prompt_ref=prompt_ref,
                raw_ref=raw_ref,
                diagnostic_ref=diagnostic_ref,
                valid=False,
            )],
        ),
    )
    assert workflow._direct_recovery_reason(0) == "schema-repair-exhausted"


def test_manifest_wf_refutation_is_a_measured_recovery_trigger(tmp_path):
    from deepreason.manifest import manifest_commitment

    harness, workflow = _workflow(tmp_path, concurrency=1, profile="standard")
    commitment = manifest_commitment(set())
    harness.register_commitment(commitment)
    artifact = harness.create_artifact(
        "a design with no component manifest",
        interface=Interface(commitments=[commitment.id]),
        provenance=Provenance(role="conjecturer"),
    )
    crit_program(harness, artifact.id)

    assert workflow._direct_recovery_reason(0) == "manifest-wf-failed"
