"""C10 approachable CLI surface for the grounded two-stage bridge."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import replace
from types import SimpleNamespace

import pytest

from deepreason.cli import bridge as bridge_cli
from deepreason.bridge.models import (
    BridgeOutputV1,
    ClaimLedgerEntryV1,
    ClaimLedgerV1,
    ClaimUseV1,
)
from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.ontology import Problem, ProblemProvenance
from deepreason.run_manifest import (
    bind_run_manifest,
    compile_run_manifest,
    write_run_manifest,
)
from deepreason.scratch.models import ScratchProvenanceV1
from deepreason.scratch.service import ScratchService


STAMP = "2026-07-16T00:00:00Z"


def _route(model: str = "fixture-31b") -> dict:
    return {
        "endpoint_id": "fixture-route",
        "endpoint": "https://models.invalid/v1",
        "model": model,
        "provider": "fixture",
        "family": "fixture",
    }


def _manifest(
    *,
    output_section_limit: int = 32,
    max_schema_repair_attempts: int = 0,
    grounding_review: bool = False,
    max_grounding_repair_attempts: int = 0,
):
    roles = {"summarizer": _route(), "thesis": _route()}
    if grounding_review:
        roles["judge"] = _route()
    return compile_run_manifest(
        Config(
            scratchpad={"enabled": True},
            bridge={
                "mode": "grounded_two_stage",
                "grounding_review": grounding_review,
                "max_schema_repair_attempts": max_schema_repair_attempts,
                "max_grounding_repair_attempts": max_grounding_repair_attempts,
                "output_section_limit": output_section_limit,
            },
            roles=roles,
        ),
        schema_version=3,
        workload_profile="text",
        rubric_policy="forbid",
        compiled_at=STAMP,
    )


def _problem(problem_id: str) -> Problem:
    return Problem(
        id=problem_id,
        description="What conclusion is justified by this run?",
        provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    subparsers = parser.add_subparsers(dest="command", required=True)
    bridge_cli.register_parser(subparsers)
    return parser


def _run(root, *argv: str) -> int:
    args = _parser().parse_args(["--root", str(root), "bridge", *argv])
    return bridge_cli.run_command(args)


def _scripted_adapter(harness: Harness) -> LLMAdapter:
    endpoints = {
        "summarizer": MockEndpoint(
            [
                json.dumps(
                    {
                        "entries": [
                            {
                                "entry_key": "K1",
                                "claim_class": "unknown",
                                "claim": "The requested conclusion is not established.",
                                "scratch_handles": ["B1"],
                            }
                        ],
                        "uncovered_requirements": [
                            {
                                "requirement": "Evidence establishing the conclusion.",
                                "reason": "Scratch provenance cannot ground an answer.",
                                "scratch_handles": ["B1"],
                            }
                        ],
                    }
                )
            ],
            name="scripted-summarizer",
        ),
        "thesis": MockEndpoint(
            [
                json.dumps(
                    {
                        "sections": [
                            {
                                "span_id": "S1",
                                "text": "The requested conclusion remains unknown.",
                                "rendering_mode": "unknown",
                                "ledger_entry_handles": ["E1"],
                            }
                        ],
                        "resolution": "insufficient_evidence",
                        "resolution_reason": "The bounded record supplies no grounding.",
                    }
                )
            ],
            name="scripted-thesis",
        ),
    }
    return LLMAdapter(endpoints, harness.blobs, retry_max=0)


def _reviewed_adapter(harness: Harness) -> LLMAdapter:
    base = _scripted_adapter(harness)
    return LLMAdapter(
        {
            **base.endpoints,
            "judge": MockEndpoint(
                [json.dumps({"finding": "supported"})], name="scripted-judge"
            ),
        },
        harness.blobs,
        retry_max=0,
    )


def _safe_removal_adapter(harness: Harness) -> LLMAdapter:
    base = _scripted_adapter(harness)
    return LLMAdapter(
        {
            **base.endpoints,
            "judge": MockEndpoint(
                [
                    json.dumps(
                        {
                            "finding": "unsupported",
                            "message": "The span must remain unresolved.",
                        }
                    ),
                    json.dumps({"action": "remove_span"}),
                ],
                name="scripted-safe-removal",
            ),
        },
        harness.blobs,
        retry_max=0,
    )


@pytest.fixture()
def bridge_run(tmp_path):
    root = tmp_path / "run"
    harness = Harness(root)
    harness.register_problem(_problem("problem-grounded-answer"))
    manifest = _manifest()
    bind_run_manifest(manifest, root)
    scratch = ScratchService(harness)
    provenance = ScratchProvenanceV1(actor="user", origin="cli-test")
    block = scratch.create_block(
        {"content": "A useful but ungrounded line of thought."}, provenance
    )
    cluster = scratch.create_cluster("Possible answer", provenance)
    scratch.add_cluster_member(cluster.id, block.id, None, provenance)
    return SimpleNamespace(
        root=root,
        manifest=manifest,
        problem_id="problem-grounded-answer",
        block=block,
        cluster=cluster,
    )


@pytest.fixture()
def built_bridge(bridge_run, monkeypatch, capsys):
    monkeypatch.setattr(
        bridge_cli,
        "_build_bridge_adapter",
        lambda _manifest, harness: _scripted_adapter(harness),
    )
    assert (
        _run(
            bridge_run.root,
            "build",
            "problem-grounded",
            "--focus-block",
            bridge_run.block.id[7:19],
            "--focus-cluster",
            bridge_run.cluster.id[7:19],
        )
        == 0
    )
    human = capsys.readouterr().out
    assert "Resolution: Insufficient evidence" in human
    assert "[Unknown" in human
    assert "Grounding sources: 0" in human
    return bridge_run


def _tree_digest(root) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def test_build_resolves_focus_prefixes_and_records_bounded_advisory_context(
    built_bridge,
):
    harness = Harness(built_bridge.root)
    terminal = bridge_cli._load_terminal(built_bridge.root)
    ledger = harness.bridge_state.ledgers[terminal.claim_ledger_id]

    assert terminal.process_status == "success"
    assert terminal.resolution.value == "insufficient_evidence"
    assert ledger.advisory_context_ref in harness.scratch_state.advisory_contexts
    context = harness.scratch_state.advisory_contexts[ledger.advisory_context_ref]
    assert [block.id for block in context.blocks] == [built_bridge.block.id]
    assert context.retrieval_receipt in harness.scratch_state.attention_receipts
    assert ledger.entries[0].scratch_refs == [built_bridge.block.id]
    assert not ledger.entries[0].source_refs


def test_json_result_and_claims_expose_full_typed_stable_ids(
    built_bridge, capsys
):
    assert _run(built_bridge.root, "result", "--json") == 0
    result = json.loads(capsys.readouterr().out)
    assert result["schema"] == "deepreason-cli-bridge-result-v1"
    assert result["terminal"]["claim_ledger_id"].startswith("sha256:")
    assert result["output"]["id"].startswith("sha256:")
    assert result["output"]["resolution"] == "insufficient_evidence"

    assert _run(built_bridge.root, "claims", "--json") == 0
    claims = json.loads(capsys.readouterr().out)
    assert claims["claim_ledger_id"].startswith("sha256:")
    assert claims["entries"][0]["id"].startswith("sha256:")
    assert claims["entries"][0]["claim_class"] == "unknown"
    assert claims["entries"][0]["scratch_refs"] == [built_bridge.block.id]


def test_unresolved_status_result_and_validation_are_process_success(
    built_bridge, capsys
):
    for command in ("status", "result", "inspect", "claims", "validate"):
        assert _run(built_bridge.root, command) == 0
        capsys.readouterr()

    assert _run(built_bridge.root, "status", "--json") == 0
    status = json.loads(capsys.readouterr().out)
    assert status["process_status"] == "success"
    assert status["resolution"] == "insufficient_evidence"
    assert status["stable_ids"]["bridge_output_id"].startswith("sha256:")


def test_bridge_read_commands_are_physically_read_only(built_bridge, capsys):
    before = _tree_digest(built_bridge.root)
    for command in ("status", "result", "inspect", "claims", "validate"):
        assert _run(built_bridge.root, command, "--json") == 0
        capsys.readouterr()
        assert _tree_digest(built_bridge.root) == before


def test_manifest_schema_repair_cap_controls_adapter_without_policy_mutation(
    bridge_run, monkeypatch
):
    sentinel = SimpleNamespace(retry_max=0, has_role=lambda _role: True)

    def fake_build(config, *_args, **_kwargs):
        assert config.RETRY_MAX == 0
        return sentinel

    monkeypatch.setattr("deepreason.llm.adapter.build_adapter", fake_build)
    before = bridge_run.manifest.canonical_bytes()

    adapter = bridge_cli._build_bridge_adapter(
        bridge_run.manifest, Harness(bridge_run.root)
    )

    assert adapter is sentinel
    assert adapter.retry_max == 0
    assert bridge_run.manifest.bridge_policy.max_schema_repair_attempts == 0
    assert bridge_run.manifest.canonical_bytes() == before


def test_bound_manifest_conflict_fails_before_any_adapter_call(
    bridge_run, tmp_path, monkeypatch, capsys
):
    conflicting = _manifest(output_section_limit=31)
    manifest_path, _ = write_run_manifest(conflicting, tmp_path / "different.json")
    monkeypatch.setattr(
        bridge_cli,
        "_build_bridge_adapter",
        lambda *_args: pytest.fail("manifest conflict reached adapter construction"),
    )

    assert (
        _run(
            bridge_run.root,
            "build",
            bridge_run.problem_id,
            "--run-manifest",
            str(manifest_path),
        )
        == 1
    )
    assert "RUN_MANIFEST_CONFLICT" in capsys.readouterr().err


def test_v3_bound_manifest_is_required_before_build(tmp_path, monkeypatch, capsys):
    root = tmp_path / "legacy-run"
    harness = Harness(root)
    harness.register_problem(_problem("problem-legacy"))
    legacy = compile_run_manifest(
        Config(roles={"summarizer": _route()}),
        schema_version=2,
        workload_profile="text",
        rubric_policy="forbid",
        compiled_at=STAMP,
    )
    bind_run_manifest(legacy, root)
    monkeypatch.setattr(
        bridge_cli,
        "_build_bridge_adapter",
        lambda *_args: pytest.fail("v2 bridge reached adapter construction"),
    )

    assert _run(root, "build", "problem-legacy") == 1
    assert "BRIDGE_MANIFEST_V3_REQUIRED" in capsys.readouterr().err


def test_problem_prefix_must_be_exact_or_unique(bridge_run, monkeypatch, capsys):
    harness = Harness(bridge_run.root)
    harness.register_problem(_problem("problem-grounded-alternative"))
    monkeypatch.setattr(
        bridge_cli,
        "_build_bridge_adapter",
        lambda *_args: pytest.fail("ambiguous problem reached adapter construction"),
    )

    assert _run(bridge_run.root, "build", "problem-grounded") == 1
    assert "BRIDGE_PROBLEM_PREFIX_AMBIGUOUS" in capsys.readouterr().err


@pytest.mark.parametrize(
    "command,filename",
    [
        ("result", "bridge-result.json"),
        ("status", "bridge-status.json"),
    ],
)
def test_corrupt_control_records_return_nonzero(
    built_bridge, command, filename, capsys
):
    (built_bridge.root / filename).write_text("{not-json", encoding="utf-8")
    assert _run(built_bridge.root, command) == 1
    assert "BRIDGE_RECORD_CORRUPT" in capsys.readouterr().err


def test_terminal_status_requires_its_exact_result_record(built_bridge, capsys):
    (built_bridge.root / "bridge-result.json").unlink()

    assert _run(built_bridge.root, "status") == 1
    assert "terminal result is absent" in capsys.readouterr().err


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("process_status", "failure"),
        ("formal_seq", 0),
        ("resolution", "outside_scope"),
    ],
)
def test_status_cannot_disagree_with_terminal_result(
    built_bridge, field, value, capsys
):
    status_path = built_bridge.root / "bridge-status.json"
    payload = json.loads(status_path.read_text(encoding="utf-8"))
    payload[field] = value
    if field == "process_status":
        payload["state"] = "failed"
        payload["error_code"] = "TAMPERED"
        payload["resolution"] = None
    status_path.write_text(json.dumps(payload), encoding="utf-8")

    assert _run(built_bridge.root, "status") == 1
    assert "BRIDGE_STATUS_INVALID" in capsys.readouterr().err


def test_fixed_control_records_must_not_be_symlinks(built_bridge, tmp_path, capsys):
    result_path = built_bridge.root / "bridge-result.json"
    outside = tmp_path / "outside-result.json"
    outside.write_bytes(result_path.read_bytes())
    result_path.unlink()
    try:
        result_path.symlink_to(outside)
    except OSError:
        pytest.skip("platform does not permit unprivileged symlink creation")

    assert _run(built_bridge.root, "result") == 1
    assert "BRIDGE_RECORD_UNAVAILABLE" in capsys.readouterr().err


def test_human_epistemic_labels_cover_every_non_laundered_mode():
    assert set(bridge_cli._CLAIM_LABELS.values()) == {
        "Grounded fact",
        "Recorded observation",
        "Supported inference",
        "Surviving conjecture",
        "Explicit assumption",
        "Unknown",
        "Conflicting evidence",
    }


def test_human_object_prefixes_expand_until_unique():
    first = "sha256:" + "a" * 12 + "1" * 52
    second = "sha256:" + "a" * 12 + "2" * 52

    prefixes = bridge_cli._unique_short_ids([first, second])

    assert prefixes[first] != prefixes[second]
    assert len(prefixes[first]) == 13


def test_focus_inputs_are_bounded_and_reject_non_ids(bridge_run, capsys):
    assert (
        _run(
            bridge_run.root,
            "build",
            bridge_run.problem_id,
            "--focus-block",
            "../../objects",
        )
        == 1
    )
    assert "BRIDGE_INPUT_INVALID" in capsys.readouterr().err

    values = [value for index in range(65) for value in ("--focus-block", f"{index:02x}")]
    assert _run(bridge_run.root, "build", bridge_run.problem_id, *values) == 1
    assert "BRIDGE_INPUT_TOO_LARGE" in capsys.readouterr().err


def test_unbound_invalid_problem_is_rejected_without_binding_or_mutation(
    tmp_path, capsys
):
    root = tmp_path / "unbound"
    Harness(root).register_problem(_problem("known-problem"))
    manifest_path, _ = write_run_manifest(_manifest(), tmp_path / "bridge-v3.json")
    before = _tree_digest(root)

    assert (
        _run(
            root,
            "build",
            "missing-problem",
            "--run-manifest",
            str(manifest_path),
        )
        == 1
    )

    assert "BRIDGE_PROBLEM_NOT_FOUND" in capsys.readouterr().err
    assert not (root / "run-manifest.json").exists()
    assert not (root / "run-manifest.sha256").exists()
    assert _tree_digest(root) == before


def test_adapter_preflight_failure_does_not_commit_attention_receipt(
    bridge_run, monkeypatch, capsys
):
    before_seq = Harness(bridge_run.root)._next_seq
    monkeypatch.setattr(
        bridge_cli,
        "_build_bridge_adapter",
        lambda *_args: (_ for _ in ()).throw(ValueError("BRIDGE_ROUTE_UNAVAILABLE")),
    )

    assert (
        _run(
            bridge_run.root,
            "build",
            bridge_run.problem_id,
            "--focus-block",
            bridge_run.block.id[7:19],
        )
        == 1
    )

    reopened = Harness(bridge_run.root)
    assert reopened._next_seq == before_seq
    assert not reopened.scratch_state.attention_receipts
    assert "BRIDGE_ROUTE_UNAVAILABLE" in capsys.readouterr().err


def test_failed_stage_a_terminal_remains_readable_without_bridge_objects(
    bridge_run, monkeypatch, capsys
):
    def exhausted(harness):
        return LLMAdapter(
            {
                "summarizer": MockEndpoint([], name="exhausted-summarizer"),
                "thesis": MockEndpoint([], name="unused-thesis"),
            },
            harness.blobs,
            retry_max=0,
        )

    monkeypatch.setattr(bridge_cli, "_build_bridge_adapter", lambda _m, h: exhausted(h))

    assert _run(bridge_run.root, "build", bridge_run.problem_id) == 1
    assert "Bridge failed" in capsys.readouterr().out
    terminal = bridge_cli._load_terminal(bridge_run.root)
    assert terminal.process_status == "failure"
    assert terminal.claim_ledger_id is None
    assert terminal.bridge_output_id is None
    state = Harness(bridge_run.root).bridge_state
    assert terminal.evidence_pack_id in state.evidence_packs
    assert terminal.failure_id in state.failures
    failure = state.failures[terminal.failure_id]
    assert failure.catalog_id in state.catalogs
    assert failure.evidence_pack_id == terminal.evidence_pack_id
    assert failure.error_code == terminal.error_code

    assert _run(bridge_run.root, "result", "--json") == 1
    result = json.loads(capsys.readouterr().out)
    assert result["terminal"]["failure_id"] == terminal.failure_id
    assert result["failure"]["id"] == terminal.failure_id


def test_terminal_sidecar_must_match_exact_completed_event_inputs(
    built_bridge, capsys
):
    terminal_path = built_bridge.root / "bridge-result.json"
    payload = json.loads(terminal_path.read_text(encoding="utf-8"))
    state = Harness(built_bridge.root).bridge_state
    different = next(
        report.id
        for report in state.validation_reports.values()
        if report.id != payload["validation_report_id"]
    )
    payload["validation_report_id"] = different
    terminal_path.write_text(json.dumps(payload), encoding="utf-8")

    assert _run(built_bridge.root, "result") == 1
    assert "terminal completion inputs differ" in capsys.readouterr().err


def test_human_rendering_neutralizes_untrusted_controls_and_newlines(
    built_bridge,
):
    snapshot = bridge_cli._load_snapshot(built_bridge.root)
    entry = snapshot.ledger.entries[0]
    section = ClaimUseV1.create(
        span_id="S1",
        text="unknown\x1b[31m\nFORGED STATUS",
        rendering_mode="unknown",
        ledger_entry_ids=[entry.id],
    )
    malicious_output = BridgeOutputV1.create(
        claim_ledger_id=snapshot.ledger.id,
        sections=[section],
        resolution="insufficient_evidence",
        resolution_reason="missing\r\nFORGED RESULT",
    )
    rendered = bridge_cli._render_result(replace(snapshot, output=malicious_output))

    assert "\x1b" not in rendered
    assert "\\u001b" in rendered
    assert "\nFORGED STATUS" not in rendered
    assert "\nFORGED RESULT" not in rendered


def test_malformed_fixed_sidecar_does_not_echo_model_authored_input(
    built_bridge, capsys
):
    secret = "MODEL_CONTROL_TEXT_SHOULD_NOT_ECHO"
    status_path = built_bridge.root / "bridge-status.json"
    payload = json.loads(status_path.read_text(encoding="utf-8"))
    payload["model_authored_extra"] = secret
    status_path.write_text(json.dumps(payload), encoding="utf-8")

    assert _run(built_bridge.root, "status") == 1
    error = capsys.readouterr().err
    assert "BRIDGE_STATUS_INVALID" in error
    assert secret not in error


def test_main_dispatch_returns_zero_for_unresolved_and_nonzero_for_corruption(
    built_bridge, capsys
):
    from deepreason.cli.main import main

    assert (
        main(["--root", str(built_bridge.root), "bridge", "result", "--json"])
        == 0
    )
    assert json.loads(capsys.readouterr().out)["output"]["resolution"] == (
        "insufficient_evidence"
    )

    (built_bridge.root / "bridge-result.json").write_text(
        "{corrupt", encoding="utf-8"
    )
    assert main(["--root", str(built_bridge.root), "bridge", "result"]) == 1
    assert "BRIDGE_RECORD_CORRUPT" in capsys.readouterr().err


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("run_manifest_digest", "f" * 64, "manifest digest differs"),
        ("resolution", "outside_scope", "resolution differs from output"),
    ],
)
def test_terminal_manifest_and_resolution_are_reconciled_to_canonical_state(
    built_bridge, field, value, message, capsys
):
    result_path = built_bridge.root / "bridge-result.json"
    payload = json.loads(result_path.read_text(encoding="utf-8"))
    payload[field] = value
    result_path.write_text(json.dumps(payload), encoding="utf-8")

    assert _run(built_bridge.root, "result") == 1
    assert message in capsys.readouterr().err


def test_status_uses_full_snapshot_validation_not_only_sidecar_fields(
    built_bridge, monkeypatch, capsys
):
    terminal = bridge_cli._load_terminal(built_bridge.root)
    historical = Harness.at(built_bridge.root, terminal.terminal_event_seq)
    report = historical.bridge_state.validation_reports[terminal.validation_report_id]
    historical.bridge_state.validation_reports[report.id] = report.model_copy(
        update={"valid": False}
    )
    monkeypatch.setattr(
        Harness,
        "at",
        classmethod(lambda _cls, _root, _seq: historical),
    )

    assert _run(built_bridge.root, "status") == 1
    assert "successful result requires valid report" in capsys.readouterr().err


@pytest.mark.parametrize("tamper", ["passed", "relation"])
def test_successful_review_must_match_output_and_pass(
    tmp_path, monkeypatch, capsys, tamper
):
    root = tmp_path / "reviewed"
    harness = Harness(root)
    harness.register_problem(_problem("problem-reviewed"))
    bind_run_manifest(_manifest(grounding_review=True), root)
    monkeypatch.setattr(
        bridge_cli,
        "_build_bridge_adapter",
        lambda _manifest, current: _reviewed_adapter(current),
    )
    assert _run(root, "build", "problem-reviewed") == 0
    capsys.readouterr()

    terminal = bridge_cli._load_terminal(root)
    historical = Harness.at(root, terminal.terminal_event_seq)
    review = historical.bridge_state.grounding_reviews[terminal.review_id]
    if tamper == "passed":
        changed = review.model_copy(update={"passed": False})
        expected = "grounded review did not pass"
    else:
        changed = review.model_copy(update={"bridge_output_id": "sha256:" + "f" * 64})
        expected = "grounded review names different objects"
    historical.bridge_state.grounding_reviews[review.id] = changed
    monkeypatch.setattr(
        Harness,
        "at",
        classmethod(lambda _cls, _root, _seq: historical),
    )

    assert _run(root, "result") == 1
    assert expected in capsys.readouterr().err


def test_failed_review_on_prior_output_accepts_only_replayed_safe_removal(
    tmp_path, monkeypatch, capsys
):
    root = tmp_path / "safe-removal"
    harness = Harness(root)
    harness.register_problem(_problem("problem-safe-removal"))
    bind_run_manifest(
        _manifest(
            grounding_review=True,
            max_grounding_repair_attempts=2,
        ),
        root,
    )
    monkeypatch.setattr(
        bridge_cli,
        "_build_bridge_adapter",
        lambda _manifest, current: _safe_removal_adapter(current),
    )

    assert _run(root, "build", "problem-safe-removal") == 0
    capsys.readouterr()
    snapshot = bridge_cli._load_snapshot(root)

    assert snapshot.review is not None and not snapshot.review.passed
    assert snapshot.review.bridge_output_id != snapshot.output.id
    assert snapshot.output.sections == []
    assert snapshot.output.resolution.value == "insufficient_evidence"
    assert _run(root, "result", "--json") == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["grounded_review"]["passed"] is False
    assert payload["output"]["sections"] == []


def test_failure_sidecar_fields_reconcile_to_replay_record(
    bridge_run, monkeypatch, capsys
):
    monkeypatch.setattr(
        bridge_cli,
        "_build_bridge_adapter",
        lambda _manifest, harness: LLMAdapter(
            {
                "summarizer": MockEndpoint([], name="exhausted"),
                "thesis": MockEndpoint([], name="unused"),
            },
            harness.blobs,
            retry_max=0,
        ),
    )
    assert _run(bridge_run.root, "build", bridge_run.problem_id) == 1
    capsys.readouterr()
    result_path = bridge_run.root / "bridge-result.json"
    payload = json.loads(result_path.read_text(encoding="utf-8"))
    payload["error_message"] = "tampered failure detail"
    result_path.write_text(json.dumps(payload), encoding="utf-8")

    assert _run(bridge_run.root, "result") == 1
    assert "failure fields differ from replay" in capsys.readouterr().err


def test_result_claims_and_inspect_have_deterministic_pagination_and_truncation(
    built_bridge,
):
    snapshot = bridge_cli._load_snapshot(built_bridge.root)
    entries = [
        ClaimLedgerEntryV1.create(
            claim_class="unknown",
            claim=("x" * 20_000 if index == 1 else f"claim {index}"),
            scratch_refs=(
                [f"sha256:{value:064x}" for value in range(101)]
                if index == 1
                else None
            ),
        )
        for index in range(4)
    ]
    ledger = ClaimLedgerV1.create(
        problem_ref=snapshot.ledger.problem_ref,
        formal_seq=snapshot.ledger.formal_seq,
        output_target=snapshot.ledger.output_target,
        entries=entries,
    )
    sections = [
        ClaimUseV1.create(
            span_id=f"S{index + 1}",
            text=f"section {index}",
            rendering_mode="unknown",
            ledger_entry_ids=[entry.id],
        )
        for index, entry in enumerate(entries)
    ]
    output = BridgeOutputV1.create(
        claim_ledger_id=ledger.id,
        sections=sections,
        resolution="insufficient_evidence",
    )
    paged = replace(snapshot, ledger=ledger, output=output)

    claims = bridge_cli._claims_payload(paged, limit=2, offset=1)
    result = bridge_cli._result_payload(paged, limit=2, offset=1)
    inspect = bridge_cli._inspect_payload(snapshot, limit=1, offset=0)
    validate, _ = bridge_cli._validate_payload(snapshot, limit=1, offset=0)

    assert [item["id"] for item in claims["entries"]] == [
        entries[1].id,
        entries[2].id,
    ]
    assert claims["pagination"]["collections"][0]["total"] == 4
    assert claims["truncation"]["truncated"] is True
    assert len(claims["entries"][0]["claim"]) == 16_384
    assert len(claims["entries"][0]["scratch_refs"]) == 100
    assert claims["truncation"]["array_limit_items"] == 100
    assert [item["id"] for item in result["output"]["sections"]] == [
        sections[1].id,
        sections[2].id,
    ]
    assert result["terminal"]["claim_ledger_id"].startswith("sha256:")
    assert inspect["pagination"]["limit"] == 1
    assert all(
        collection["returned"] <= 1
        for collection in inspect["pagination"]["collections"]
    )
    assert all(
        collection["returned"] <= 1
        for collection in validate["pagination"]["collections"]
    )
    human = bridge_cli._render_claims(paged, limit=2, offset=1)
    assert "showing 2 of 4" in human
    assert "More records are available" in human


def test_invalid_page_bounds_fail_before_bridge_construction(
    bridge_run, monkeypatch, capsys
):
    monkeypatch.setattr(
        bridge_cli,
        "_build_bridge_adapter",
        lambda *_args: pytest.fail("invalid page reached bridge construction"),
    )

    assert (
        _run(
            bridge_run.root,
            "build",
            bridge_run.problem_id,
            "--limit",
            "0",
        )
        == 1
    )
    assert "BRIDGE_PAGE_LIMIT_INVALID" in capsys.readouterr().err
