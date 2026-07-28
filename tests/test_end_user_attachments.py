"""End-user attachment path: one shared admission door for CLI, MCP, and web."""

from __future__ import annotations

import json

import pytest

from deepreason.admission.attach import (
    MAX_ATTACHMENT_FILES,
    admit_attachment_paths,
    collect_attachment_inputs,
)
from deepreason.admission.parse import AdmissionError


QUESTION = "What do the widget studies show?"

MARKDOWN = (
    "# Widget Study\n"
    "\n"
    "Widgets are made of interchangeable parts.\n"
).encode("utf-8")

CSV = b"name,score\nalpha,10\nbeta,20\n"


def _tree(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "study.md").write_bytes(MARKDOWN)
    (docs / "scores.csv").write_bytes(CSV)
    return docs


def test_paths_expand_deterministically_and_fail_closed(tmp_path):
    docs = _tree(tmp_path)
    inputs = collect_attachment_inputs([docs])
    assert [item.locator for item in inputs] == sorted(
        item.locator for item in inputs
    )
    assert len(inputs) == 2

    with pytest.raises(AdmissionError) as missing:
        collect_attachment_inputs([tmp_path / "nowhere.txt"])
    assert missing.value.code == "ADMISSION_PATH_UNAVAILABLE"

    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(AdmissionError) as vacant:
        collect_attachment_inputs([empty])
    assert vacant.value.code == "ADMISSION_PATH_UNAVAILABLE"

    crowd = tmp_path / "crowd"
    crowd.mkdir()
    for index in range(MAX_ATTACHMENT_FILES + 1):
        (crowd / f"f{index:03}.txt").write_bytes(b"body\n")
    with pytest.raises(AdmissionError) as too_many:
        collect_attachment_inputs([crowd])
    assert too_many.value.code == "ADMISSION_TOO_MANY_SOURCES"


def test_admitted_attachments_bind_the_exact_question(tmp_path, monkeypatch):
    monkeypatch.setenv("DEEPREASON_HOME", str(tmp_path / "home"))
    from deepreason.admission import admission_store
    from deepreason.preparation import _question_digest

    docs = _tree(tmp_path)
    admitted = admit_attachment_paths(
        QUESTION, [docs], supplied_by="tests.attach"
    )
    assert admitted.dossier.problem_ref == (
        f"question-{_question_digest(QUESTION)[:32]}"
    )
    summary = admitted.summary()
    assert summary["evidence_dossier_digest"] == admitted.dossier_digest
    assert summary["sources_admitted"] == 2
    assert summary["refusals"] == []

    # The dossier and its source bytes are durably stored and reloadable.
    stored = admission_store().load(admitted.dossier_digest)
    assert stored.dossier_digest == admitted.dossier_digest

    # Same bytes, same question, same digest: the door is deterministic.
    again = admit_attachment_paths(QUESTION, [docs], supplied_by="tests.attach")
    assert again.dossier_digest == admitted.dossier_digest

    with pytest.raises(AdmissionError) as blank:
        admit_attachment_paths("   ", [docs], supplied_by="tests.attach")
    assert blank.value.code == "ADMISSION_PROBLEM_REQUIRED"


def test_mcp_start_run_admits_attachments_into_the_run_identity(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.setenv("DEEPREASON_HOME", str(tmp_path / "home"))
    from types import SimpleNamespace

    from deepreason import mcp_server

    docs = _tree(tmp_path)
    seen = {}

    from deepreason.workloads.text import spec_from_text

    class PreparedService:
        def prepare(self, request):
            seen["dossier_digest"] = request.dossier_digest
            seen["question"] = request.question
            return SimpleNamespace(
                root=str(tmp_path / "run"),
                managed_run_id="run-fixture",
                run_manifest_ref=str(tmp_path / "run" / "run-manifest.json"),
                workload=spec_from_text(request.question),
                budget=request.budget,
            )

    class AcceptedService:
        def start(self, intent, progress_callback=None, credential_checker=None):
            return SimpleNamespace(lifecycle="accepted", root=intent.root)

    monkeypatch.setattr(mcp_server, "_require_readiness", lambda: None)
    monkeypatch.setattr(mcp_server, "_preparation_service", PreparedService)
    monkeypatch.setattr(mcp_server, "TEXT_RUN_SERVICE", AcceptedService())

    response = json.loads(
        mcp_server.call_tool(
            "start_run",
            {"question": QUESTION, "attachments": [str(docs)]},
        )
    )
    assert response["run_id"] == "run-fixture"
    assert response["evidence"]["sources_admitted"] == 2
    assert seen["dossier_digest"] == response["evidence"]["evidence_dossier_digest"]

    # A missing path is a typed failure before any run state is created.
    with pytest.raises(Exception) as refused:
        mcp_server.call_tool(
            "start_run",
            {
                "question": QUESTION,
                "attachments": [str(tmp_path / "nowhere.pdf")],
            },
        )
    assert "ADMISSION_PATH_UNAVAILABLE" in str(refused.value)


def test_mcp_readiness_carries_plain_language_guidance(tmp_path, monkeypatch):
    from deepreason import mcp_server

    monkeypatch.setenv("DEEPREASON_HOME", str(tmp_path / "home"))
    monkeypatch.delenv("DEEPREASON_PROVIDER_PROFILE", raising=False)
    payload = json.loads(mcp_server.call_tool("get_readiness", {}))
    assert payload["ready"] is False
    assert "deepreason setup" in payload["guidance"]
    # The guidance explains the jargon it uses instead of assuming it.
    assert "API key" in payload["guidance"]


def test_reason_attach_flag_admits_before_preparing(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("DEEPREASON_HOME", str(tmp_path / "home"))
    from deepreason.cli.main import main as cli_main

    docs = _tree(tmp_path)
    seen = {}

    class PreparedService:
        def prepare(self, request):
            seen["dossier_digest"] = request.dossier_digest
            raise ValueError("PREPARATION_STOPPED_BY_TEST: far enough")

    monkeypatch.setattr(
        "deepreason.preparation.RunPreparationService", PreparedService
    )
    exit_code = cli_main(
        ["reason", QUESTION, "--attach", str(docs / "study.md")]
    )
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "PREPARATION_STOPPED_BY_TEST" in captured.err
    # Spec §9: the one-step convenience prints the minted dossier digest.
    assert seen["dossier_digest"] in captured.err
    assert "evidence_dossier_digest" in captured.err

    conflict = cli_main(
        [
            "reason",
            QUESTION,
            "--attach",
            str(docs / "study.md"),
            "--dossier",
            "a" * 64,
        ]
    )
    captured = capsys.readouterr()
    assert conflict == 1
    assert "ATTACH_DOSSIER_CONFLICT" in captured.err
