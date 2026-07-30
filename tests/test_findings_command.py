"""The findings command: reader-facing summary of rivalries, refutations,
suspended positions, side branches, and capability ledgers, replay-derived
and exposed both on the CLI (deepreason findings) and the MCP surface
(run_findings)."""

import json

from deepreason.config import Config
from deepreason.findings import findings_summary, render_findings
from deepreason.harness import Harness
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.ontology import Commitment, Problem, ProblemProvenance
from deepreason.scheduler.scheduler import Scheduler


def _vs(prompt: str) -> str:
    return json.dumps(
        {
            "candidates": [
                {"content": f"the moon pulls the sea ({hash(prompt) % 97})", "typicality": 0.8},
                {"content": f"the tides are magic ({hash(prompt) % 89})", "typicality": 0.2},
            ]
        }
    )


def _edits(prompt: str) -> str:
    return json.dumps({"edits": [{"content": f"edit {i}: another mechanism"} for i in range(3)]})


def test_findings_summary_reports_rivals_refutations_and_branches(tmp_path):
    harness = Harness(tmp_path / "run")
    harness.register_commitment(Commitment(id="k-moon", eval="predicate:'moon' in content"))
    harness.register_problem(
        Problem(
            id="pi-tides",
            description="explain the tides",
            criteria=["k-moon"],
            provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
        )
    )
    adapter = LLMAdapter(
        {"conjecturer": MockEndpoint(_vs), "variator": MockEndpoint(_edits)},
        harness.blobs,
        retry_max=2,
    )
    config = Config(VS_K=2, N_SCHOOLS=2, HV_K=3, HV_MIN=0.5, CAPTURE_W=10)
    Scheduler(harness, adapter, config).run(4)

    summary = findings_summary(harness.root)
    assert summary["schema"] == "deepreason-findings.v1"
    # The magic-tides candidate fails k-moon every cycle: refutations with
    # structure, plus spawned side branches, must surface.
    assert summary["positions"]["refuted"], "refuted positions missing"
    assert all("attacked_by" in row for row in summary["positions"]["refuted"])
    assert summary["positions"]["accepted"]
    triggers = {row["trigger"] for row in summary["branches"]}
    assert "seed" in triggers and len(triggers) > 1, triggers
    assert isinstance(summary["starved_branches"], list)
    assert summary["criticism"]["attacks_recorded"] >= 0

    text = render_findings(summary)
    for heading in (
        "# Findings summary",
        "## Refutations",
        "## Criticism ledger",
        "## Side branches",
        "## Capability trail",
    ):
        assert heading in text, f"missing section: {heading}"
    # JSON round-trip: the summary is fully serializable.
    json.dumps(summary)


def test_findings_rejects_non_run_root(tmp_path):
    import pytest

    with pytest.raises(ValueError, match="not a run root"):
        findings_summary(tmp_path / "nowhere")


def test_run_findings_is_on_the_mcp_surface():
    from deepreason.mcp_server import _RUN_TOOL_NAMES, _tools

    assert "run_findings" in _RUN_TOOL_NAMES
    (tool,) = [t for t in _tools() if t["name"] == "run_findings"]
    assert set(tool["inputSchema"]["required"]) == {"run_id"}
    assert "json" in tool["inputSchema"]["properties"]
