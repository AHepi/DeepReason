"""G02: public CLI construction and run-root admission are V6-only."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

import deepreason.cli.bridge as bridge_cli
import deepreason.cli.main as cli_module
import deepreason.cli.scratch as scratch_cli
from deepreason.application import RunStartedV1, TEXT_RUN_SERVICE, TextRunTerminalResultV1
from deepreason.canonical import canonical_json
from deepreason.cli.main import main
from deepreason.config import Config
from deepreason.evidence import (
    AttachedSourceProvenanceV1,
    EvidenceDossierV1,
    RunInputManifestV2,
    RunInputProblemV2,
    bind_run_input,
)
from deepreason.evidence.state import EVIDENCE_DOSSIER_HASH_NAME, EVIDENCE_DOSSIER_NAME
from deepreason.harness import Harness
from deepreason.run_manifest import bind_run_manifest, compile_run_manifest
from deepreason.workloads.text import spec_from_text


def _prepared_v6_root(
    root: Path,
    *,
    text: str = "Why must public run roots carry exact V6 authority?",
    manifest_digest: str | None = None,
    grounded_bridge: bool = False,
):
    from tests.test_run_input_v6_commitments import _config, _control

    spec = spec_from_text(text)
    dossier = EvidenceDossierV1.create(
        problem_ref=spec.problem.id,
        sources=(),
        total_byte_count=0,
        creation_provenance=AttachedSourceProvenanceV1(
            supplied_by="G02 CLI fixture",
            acquisition_method="test preparation",
        ),
    )
    run_input = RunInputManifestV2.create(
        problem=RunInputProblemV2.from_commitments(
            id=spec.problem.id,
            description=spec.problem.description,
            criteria=spec.criteria,
        ),
        evidence_dossier_digest=dossier.dossier_digest,
    )
    bind_run_input(run_input, dossier, root)
    base = _config()
    roles = dict(base.roles)
    updates = {
        "scratchpad": base.scratchpad.model_copy(update={"enabled": True}),
    }
    if grounded_bridge:
        route = roles["conjecturer"]
        roles.update({"summarizer": route, "thesis": route})
        updates.update(
            {
                "roles": roles,
                "bridge": base.bridge.model_copy(
                    update={"mode": "grounded_two_stage", "grounding_review": False}
                ),
            }
        )
    configured = base.model_copy(update=updates)
    manifest = compile_run_manifest(
        configured,
        schema_version=6,
        workload_profile="text",
        rubric_policy="forbid",
        compiled_at="2026-07-22T00:00:00Z",
        control_plane_policy=_control(6),
        run_input_digest=run_input.run_input_digest,
    )
    manifest_path, _ = bind_run_manifest(manifest, root)
    if manifest_digest is not None:
        manifest = manifest.model_copy(update={"run_input_digest": manifest_digest})
        payload = manifest.canonical_bytes()
        manifest_path.write_bytes(payload)
        (root / "run-manifest.sha256").write_text(
            hashlib.sha256(payload).hexdigest() + "\n",
            encoding="utf-8",
        )
    return SimpleNamespace(
        root=root,
        spec=spec,
        dossier=dossier,
        run_input=run_input,
        manifest=manifest,
        manifest_path=manifest_path,
    )


ROOT_COMMANDS = {
    "attack": ("attack", "id"),
    "blob": ("blob", "sha256:deadbeef"),
    "calibrate": ("calibrate",),
    "cancel": ("cancel",),
    "capture": ("capture",),
    "continue": ("continue", "--budget", "1"),
    "docket": ("docket",),
    "evidence": ("evidence", "id"),
    "expand": ("expand",),
    "export": ("export", "--out", "unused"),
    "focus": ("focus", "id"),
    "frontier": ("frontier",),
    "merge": ("merge", "other-root"),
    "narrate": ("narrate",),
    "prose": ("prose", "id"),
    "report": ("report",),
    "report-research-failure": (
        "report-research-failure",
        "problem",
        "--source",
        "source",
        "--reason",
        "unavailable",
    ),
    "research": ("research",),
    "reseed": ("reseed", "school"),
    "rule": ("rule", "case", "--holding", "hold", "--standard", "standard"),
    "schools": ("schools",),
    "signals": ("signals",),
    "skills": ("skills", "--capsule", "missing", "--query", "q", "--school", "s"),
    "step": ("step",),
    "submit-evidence": (
        "submit-evidence",
        "problem",
        "--source",
        "source",
        "--file",
        "missing",
    ),
    "theory": ("theory", "id"),
    "trace": ("trace", "id"),
    "watch": ("watch", "--once"),
    "why": ("why", "id"),
}


@pytest.mark.parametrize("command", sorted(ROOT_COMMANDS))
def test_every_shared_root_command_rejects_missing_manifest_before_interpretation(
    command, tmp_path, monkeypatch, capsys
):
    root = tmp_path / "missing"
    monkeypatch.setattr(
        cli_module,
        "Harness",
        lambda *_args, **_kwargs: pytest.fail("missing root reached Harness"),
    )

    assert main(["--root", str(root), *ROOT_COMMANDS[command]]) == 1
    assert "MANIFEST_FILE_UNAVAILABLE" in capsys.readouterr().err
    assert not root.exists()


@pytest.mark.parametrize("schema_version", range(1, 6))
@pytest.mark.parametrize(
    "arguments",
    (
        ("frontier",),
        ("scratch", "search", "anything", "--json"),
        ("bridge", "status"),
    ),
    ids=("shared", "scratch", "bridge"),
)
def test_historical_roots_with_sidecars_fail_before_command_services(
    schema_version, arguments, tmp_path, monkeypatch, capsys
):
    root = tmp_path / f"v{schema_version}"
    root.mkdir()
    (root / "run-manifest.json").write_text(
        json.dumps(
            {
                "schema_version": schema_version,
                "nested_historical_payload": {"must_not_be_interpreted": True},
            }
        )
    )
    (root / "run-manifest.sha256").write_text("0" * 64 + "\n")
    (root / "run-input.json").write_text('{"schema":"run-input-manifest.v2"}')
    before = {path.name: path.read_bytes() for path in root.iterdir()}
    monkeypatch.setattr(
        cli_module,
        "Harness",
        lambda *_args, **_kwargs: pytest.fail("historical root reached Harness"),
    )
    monkeypatch.setattr(
        scratch_cli,
        "ScratchService",
        lambda *_args, **_kwargs: pytest.fail("historical root reached scratch"),
    )
    monkeypatch.setattr(
        bridge_cli.GROUNDED_BRIDGE_SERVICE,
        "status",
        lambda *_args, **_kwargs: pytest.fail("historical root reached bridge"),
    )

    assert main(["--root", str(root), *arguments]) == 1
    captured = capsys.readouterr()
    assert "UNSUPPORTED_RUN_MANIFEST_VERSION" in captured.err
    assert {path.name: path.read_bytes() for path in root.iterdir()} == before


@pytest.mark.parametrize("command", sorted(ROOT_COMMANDS))
def test_every_shared_root_command_rejects_a_historical_manifest(
    command, tmp_path, capsys
):
    root = tmp_path / command
    root.mkdir()
    (root / "run-manifest.json").write_text('{"schema_version":3}')
    (root / "run-manifest.sha256").write_text("0" * 64 + "\n")
    before = {path.name: path.read_bytes() for path in root.iterdir()}

    assert main(["--root", str(root), *ROOT_COMMANDS[command]]) == 1
    assert "UNSUPPORTED_RUN_MANIFEST_VERSION" in capsys.readouterr().err
    assert {path.name: path.read_bytes() for path in root.iterdir()} == before


@pytest.mark.parametrize("schema_version", range(1, 6))
def test_config_schema_selection_is_not_public(schema_version, tmp_path, capsys):
    target = tmp_path / "manifest.json"
    with pytest.raises(SystemExit) as raised:
        main(
            [
                "config",
                "compile",
                "--schema-version",
                str(schema_version),
                "--out",
                str(target),
            ]
        )
    assert raised.value.code == 2
    assert "unrecognized arguments: --schema-version" in capsys.readouterr().err
    assert not target.exists()


def test_incomplete_config_compile_fails_actionably_without_output(tmp_path, capsys):
    target = tmp_path / "manifest.json"
    assert main(["config", "compile", "--out", str(target)]) == 1
    assert "V6_COMPILE_INPUTS_REQUIRED" in capsys.readouterr().err
    assert not target.exists()


def test_v5_input_and_experimental_flags_are_not_public(tmp_path, capsys):
    problem = tmp_path / "problem.json"
    problem.write_text(spec_from_text("freeze me").model_dump_json(by_alias=True))
    attempts = (
        ("input", "freeze", "--problem", str(problem), "--schema-version", "5"),
        ("reason", "--text", "q", "--experimental-v5"),
        ("continue", "--budget", "1", "--experimental-v5"),
        ("run", "--budget", "1", "--experimental-v5"),
    )
    for arguments in attempts:
        with pytest.raises(SystemExit) as raised:
            main(["--root", str(tmp_path / "unused"), *arguments])
        assert raised.value.code == 2
        capsys.readouterr()
    import deepreason.application.text_runs as text_runs

    assert not hasattr(text_runs, "_check_experimental_v5")


def test_question_only_reason_requires_preparation_without_creating_root(tmp_path, capsys):
    root = tmp_path / "missing"
    assert main(["--root", str(root), "reason", "--text", "What now?"]) == 1
    assert "V6_PREPARATION_REQUIRED" in capsys.readouterr().err
    assert not root.exists()


def test_explicit_manifest_cannot_bind_an_unprepared_root(tmp_path, capsys):
    prepared = _prepared_v6_root(tmp_path / "source")
    destination = tmp_path / "unbound"

    assert (
        main(
            [
                "--root",
                str(destination),
                "reason",
                "--text",
                prepared.spec.problem.description,
                "--run-manifest",
                str(prepared.manifest_path),
            ]
        )
        == 1
    )
    assert "MANIFEST_FILE_UNAVAILABLE" in capsys.readouterr().err
    assert not destination.exists()


def test_v6_input_digest_and_dossier_mismatch_fail_before_harness(
    tmp_path, monkeypatch, capsys
):
    digest_root = tmp_path / "digest"
    _prepared_v6_root(digest_root, manifest_digest="f" * 64)
    monkeypatch.setattr(
        cli_module,
        "Harness",
        lambda *_args, **_kwargs: pytest.fail("mismatch reached Harness"),
    )
    assert main(["--root", str(digest_root), "frontier"]) == 1
    assert "RUN_INPUT_MISMATCH" in capsys.readouterr().err

    dossier_root = tmp_path / "dossier"
    prepared = _prepared_v6_root(dossier_root)
    replacement = EvidenceDossierV1.create(
        problem_ref=prepared.spec.problem.id,
        sources=(),
        total_byte_count=0,
        creation_provenance=AttachedSourceProvenanceV1(
            supplied_by="different fixture",
            acquisition_method="tamper test",
        ),
    )
    (dossier_root / EVIDENCE_DOSSIER_NAME).write_bytes(
        canonical_json(replacement.model_dump(mode="json", by_alias=True))
    )
    (dossier_root / EVIDENCE_DOSSIER_HASH_NAME).write_text(
        replacement.dossier_digest + "\n"
    )
    assert main(["--root", str(dossier_root), "frontier"]) == 1
    assert "RUN_INPUT_DOSSIER_MISMATCH" in capsys.readouterr().err


def test_v6_manifest_rejects_v1_run_input_without_translation(tmp_path, capsys):
    from tests.test_run_input_v6_commitments import _bind_v1, _commitment, _manifest

    root = tmp_path / "v1-input"
    run_input = _bind_v1(root, _commitment())
    manifest = _manifest(6, run_input.run_input_digest)
    payload = manifest.canonical_bytes()
    (root / "run-manifest.json").write_bytes(payload)
    (root / "run-manifest.sha256").write_text(manifest.sha256 + "\n")

    assert main(["--root", str(root), "frontier"]) == 1
    assert "RUN_INPUT_SCHEMA_MISMATCH" in capsys.readouterr().err
    assert (root / "run-input.json").read_text().count("run-input-manifest.v1") == 1


def test_reason_question_mismatch_fails_before_application_service(
    tmp_path, monkeypatch, capsys
):
    prepared = _prepared_v6_root(tmp_path / "run", text="the frozen question")
    monkeypatch.setattr(
        TEXT_RUN_SERVICE,
        "start",
        lambda *_args, **_kwargs: pytest.fail("mismatch reached application start"),
    )

    assert (
        main(
            [
                "--root",
                str(prepared.root),
                "reason",
                "--text",
                "a different question",
                "--run-manifest",
                str(prepared.manifest_path),
            ]
        )
        == 1
    )
    assert "RUN_INPUT_MISMATCH" in capsys.readouterr().err


def test_run_requires_qualification_before_operator_lock(tmp_path, monkeypatch, capsys):
    import deepreason.locking as locking

    prepared = _prepared_v6_root(tmp_path / "run")
    monkeypatch.setattr(
        locking,
        "operator_locks",
        lambda *_args, **_kwargs: pytest.fail("unqualified run acquired a lock"),
    )

    assert main(["--root", str(prepared.root), "run", "--budget", "1"]) == 1
    assert "DOCTOR_REPORT_MISSING" in capsys.readouterr().err


def test_prepared_v6_root_and_reason_reach_shared_application_seam(
    tmp_path, monkeypatch, capsys
):
    text = "Does the explicit V6 CLI reach shared application admission?"
    prepared = _prepared_v6_root(tmp_path / "run", text=text)
    captured = []

    def start(intent, **kwargs):
        captured.append((intent, kwargs))
        return RunStartedV1(
            root=str(prepared.root.resolve()),
            manifest_digest=prepared.manifest.sha256,
        )

    monkeypatch.setattr(TEXT_RUN_SERVICE, "start", start)
    monkeypatch.setattr(TEXT_RUN_SERVICE, "wait", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        TEXT_RUN_SERVICE,
        "result",
        lambda _intent: TextRunTerminalResultV1(
            lifecycle="completed",
            payload={
                "schema": "deepreason-run-result-v2",
                "state": "completed",
                "workload": "text",
            },
        ),
    )

    assert (
        main(
            [
                "--root",
                str(prepared.root),
                "reason",
                "--text",
                text,
                "--run-manifest",
                str(prepared.manifest_path),
                "--cycles",
                "1",
            ]
        )
        == 0
    )
    assert captured[0][1]["manifest_override"] == prepared.manifest
    assert "experimental_v5" not in captured[0][0].model_dump()
    assert json.loads(capsys.readouterr().out)["state"] == "completed"


def test_v6_watch_bridge_scratch_and_temporal_query_pass_admission(
    tmp_path, monkeypatch, capsys
):
    prepared = _prepared_v6_root(
        tmp_path / "run",
        grounded_bridge=True,
    )
    snapshot = SimpleNamespace(
        presentation_payload=lambda: {
            "state": "completed",
            "workload": "text",
            "phase": "terminal",
            "activity": "done",
        }
    )
    monkeypatch.setattr(TEXT_RUN_SERVICE, "watch", lambda _intent: [snapshot])
    assert main(["--root", str(prepared.root), "watch", "--once"]) == 0
    assert "completed" in capsys.readouterr().out

    bridge_result = SimpleNamespace(
        presentation_payload=lambda: {"state": "completed", "resolution": None},
        exit_code=0,
    )
    monkeypatch.setattr(
        bridge_cli.GROUNDED_BRIDGE_SERVICE,
        "status",
        lambda _intent: bridge_result,
    )
    assert main(["--root", str(prepared.root), "bridge", "status"]) == 0
    assert "Bridge: completed" in capsys.readouterr().out

    assert (
        main(
            [
                "--root",
                str(prepared.root),
                "scratch",
                "add",
                "--content",
                "first temporal thought",
                "--json",
            ]
        )
        == 0
    )
    first = json.loads(capsys.readouterr().out)["result"]
    at_seq = Harness(prepared.root)._next_seq - 1
    assert (
        main(
            [
                "--root",
                str(prepared.root),
                "scratch",
                "add",
                "--content",
                "later temporal thought",
                "--json",
            ]
        )
        == 0
    )
    capsys.readouterr()
    assert (
        main(
            [
                "--root",
                str(prepared.root),
                "scratch",
                "show",
                first["id"][7:19],
                "--at-seq",
                str(at_seq),
                "--json",
            ]
        )
        == 0
    )
    historical = json.loads(capsys.readouterr().out)
    assert historical["at_seq"] == at_seq
    assert historical["result"]["block"]["body"]["content"] == (
        "first temporal thought"
    )


def test_derived_bridge_requires_an_existing_v6_destination_before_service(
    tmp_path, monkeypatch, capsys
):
    source = _prepared_v6_root(
        tmp_path / "source",
        grounded_bridge=True,
    )
    destination = tmp_path / "missing-derived-root"
    monkeypatch.setattr(
        bridge_cli.GROUNDED_BRIDGE_SERVICE,
        "build",
        lambda *_args, **_kwargs: pytest.fail("unadmitted derived bridge reached service"),
    )

    assert (
        main(
            [
                "--root",
                str(source.root),
                "bridge",
                "build",
                source.spec.problem.id,
                "--run-manifest",
                str(source.manifest_path),
                "--derived-output",
                str(destination),
                "--at-seq",
                "0",
            ]
        )
        == 1
    )
    assert "MANIFEST_FILE_UNAVAILABLE" in capsys.readouterr().err
    assert not destination.exists()


def test_derived_bridge_requires_explicit_v6_manifest_after_both_roots_admit(
    tmp_path, monkeypatch, capsys
):
    source = _prepared_v6_root(tmp_path / "source", grounded_bridge=True)
    destination = _prepared_v6_root(
        tmp_path / "destination",
        grounded_bridge=True,
    )
    monkeypatch.setattr(
        bridge_cli.GROUNDED_BRIDGE_SERVICE,
        "build",
        lambda *_args, **_kwargs: pytest.fail("manifest-less bridge reached service"),
    )

    assert (
        main(
            [
                "--root",
                str(source.root),
                "bridge",
                "build",
                source.spec.problem.id,
                "--derived-output",
                str(destination.root),
                "--at-seq",
                "0",
            ]
        )
        == 1
    )
    assert "V6_BRIDGE_DERIVED_MANIFEST_REQUIRED" in capsys.readouterr().err


def test_prospective_endpoint_doctor_needs_no_run_root(tmp_path, capsys):
    root = tmp_path / "doctor-root"
    assert (
        main(
            [
                "--root",
                str(root),
                "doctor",
                "--endpoint",
                "https://example.invalid/v1",
                "--model",
                "offline-model",
                "--provider",
                "ollama",
                "--dry-run",
            ]
        )
        == 0
    )
    assert json.loads(capsys.readouterr().out)["contacted"] is False
    assert not root.exists()


def test_public_parser_omits_make_and_unqualified_advanced_commands():
    commands = cli_module.build_parser()._subparsers._group_actions[0].choices
    assert {"make", "prove", "check-proof", "code", "simulate"}.isdisjoint(commands)
    assert cli_module._ROOT_ADMISSION_COMMANDS == frozenset(ROOT_COMMANDS)
