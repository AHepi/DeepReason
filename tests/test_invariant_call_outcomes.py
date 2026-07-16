"""Typed success/failure outcomes for LLM attempt-trace invariants."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from deepreason.bridge.events import BridgeAction
from deepreason.harness import Harness
from deepreason.invariants import verify_root
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.ontology import Problem, ProblemProvenance


JOLT_RUN = (
    Path(__file__).parents[1]
    / "experiments"
    / "jolt_architecture_2026-07-16"
    / "run"
)


def _failed_stage_a_root(root: Path) -> Path:
    harness = Harness(root)
    harness.register_problem(
        Problem(
            id="problem-call-outcome",
            description="What is supported?",
            provenance=ProblemProvenance(trigger="seed", **{"from": []}),
        )
    )
    invalid = "not a claim ledger"
    adapter = LLMAdapter(
        {
            "summarizer": MockEndpoint([invalid, invalid, invalid]),
            "thesis": MockEndpoint([]),
        },
        harness.blobs,
        retry_max=2,
    )
    terminal = harness.build_bridge(
        "problem-call-outcome",
        "answer",
        {"grounding_review": False, "max_grounding_repair_attempts": 0},
        run_manifest_digest="a" * 64,
        stage_a_adapter=adapter,
    )
    assert terminal.error_code == "BRIDGE_LEDGER_REPAIR_EXHAUSTED"
    assert list(harness.log.read())[-1].bridge.action == BridgeAction.FAILED
    return root


def _rewrite_event(root: Path, event_index: int, mutate) -> None:
    path = root / "log.jsonl"
    events = [json.loads(line) for line in path.read_text().splitlines()]
    mutate(events[event_index])
    path.write_text(
        "".join(json.dumps(event, separators=(",", ":")) + "\n" for event in events)
    )


def _checks(root: Path) -> set[str]:
    return {item["check"] for item in verify_root(root)["violations"]}


def test_typed_failed_call_requires_all_attempts_invalid(tmp_path):
    root = _failed_stage_a_root(tmp_path / "run")
    assert verify_root(root)["violations"] == []

    _rewrite_event(
        root,
        -1,
        lambda event: event["llm"]["attempt_trace"][-1].__setitem__(
            "valid", True
        ),
    )
    assert "attempt-validity" in _checks(root)


def test_typed_failed_call_requires_trace_and_invalid_diagnostics(tmp_path):
    no_trace = _failed_stage_a_root(tmp_path / "no-trace")
    _rewrite_event(
        no_trace,
        -1,
        lambda event: event["llm"].__setitem__("attempt_trace", []),
    )
    assert "attempt-trace" in _checks(no_trace)

    no_diagnostic = _failed_stage_a_root(tmp_path / "no-diagnostic")
    _rewrite_event(
        no_diagnostic,
        -1,
        lambda event: event["llm"]["attempt_trace"][0].__setitem__(
            "diagnostic_ref", ""
        ),
    )
    assert "attempt-blobs" in _checks(no_diagnostic)


def test_nonfailed_event_with_all_invalid_trace_remains_a_violation(tmp_path):
    root = _failed_stage_a_root(tmp_path / "run")
    harness = Harness(root)
    failed_call = list(harness.log.read())[-1].llm
    harness.record_measure(inputs=["ordinary-call"], llm=failed_call)

    details = [
        item
        for item in verify_root(root)["violations"]
        if item["check"] == "attempt-validity"
    ]
    assert len(details) == 1
    assert "successful call" in details[0]["detail"]


def test_exact_immutable_jolt_legacy_failure_chain_verifies_clean(tmp_path):
    copied = tmp_path / "jolt-run"
    shutil.copytree(JOLT_RUN, copied)

    report = verify_root(copied)

    assert report["violations"] == []
    totals = report["stats"]["process"]["profile_totals"]["standard"]
    assert totals["schema_exhausted"] == 2
    assert totals["eventual_valid"] == 20
