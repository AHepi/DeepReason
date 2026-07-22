"""CLI follow-the-evidence surface (cli/main.py): trace (compact + --json),
blob (text/binary/--out/prefix resolution), evidence, signals. First direct
main() coverage — thin smokes over a FakeBrowser-seeded root."""

import json

import pytest

from deepreason.browser import browser_commitment
from deepreason.cli.main import main
from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.ontology import Interface, Problem, ProblemProvenance, Provenance
from deepreason.rules.act import run_browser_evidence

from tests.test_act import PNG, SCRIPT, FakeBrowser


@pytest.fixture()
def root(tmp_path):
    from tests.test_v6_only_cli_admission import _prepared_v6_root

    prepared = _prepared_v6_root(tmp_path / "run")
    harness = Harness(prepared.root)
    c = browser_commitment(SCRIPT)
    harness.register_commitment(c)
    harness.register_problem(Problem(
        id="pi-app", description="build a pomodoro timer", criteria=[c.id],
        provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
    ))
    app = harness.create_artifact(
        "<div id=t>00:00</div>", codec="code:html",
        interface=Interface(commitments=[c.id]),
        provenance=Provenance(role="conjecturer"), problem_id="pi-app",
    )
    run_browser_evidence(harness, app.id, FakeBrowser("fail"), Config())
    return prepared.root, harness, app


def test_trace_compact_and_json(root, capsys):
    path, harness, app = root
    assert main(["--root", str(path), "trace", app.id[:10]]) == 0
    compact = capsys.readouterr().out
    assert "#" in compact and "Register" in compact  # human lines with seq+rule

    assert main(["--root", str(path), "trace", app.id[:10], "--json"]) == 0
    raw = capsys.readouterr().out.strip().splitlines()
    json.loads(raw[0])  # legacy machine format intact


def test_blob_text_binary_and_prefix(root, capsys, tmp_path):
    path, harness, app = root
    w = next(w for w in harness.warrants.values() if w.target == app.id)

    assert main(["--root", str(path), "blob", w.trace_ref[:12]]) == 0
    dumped = capsys.readouterr().out
    assert "verdict" in dumped  # the browser trace JSON, from a 12-char prefix

    shot_ref = next(a.content_ref for a in harness.state.artifacts.values()
                    if a.codec == "image/png")
    assert main(["--root", str(path), "blob", shot_ref]) == 1  # binary refusal
    err = capsys.readouterr().err
    assert "image/png" in err and "--out" in err

    out_file = tmp_path / "shot.png"
    assert main(["--root", str(path), "blob", shot_ref, "--out", str(out_file)]) == 0
    assert out_file.read_bytes() == PNG

    assert main(["--root", str(path), "blob", "ffffffffffff"]) == 1  # no match
    assert "no blob matches" in capsys.readouterr().err


def test_evidence_and_why_from_cli(root, capsys):
    path, harness, app = root
    assert main(["--root", str(path), "evidence", app.id[:10]]) == 0
    out = capsys.readouterr().out
    assert "WARRANTS AGAINST IT" in out and "BROWSER EVIDENCE" in out

    assert main(["--root", str(path), "why", app.id[:10]]) == 0
    out = capsys.readouterr().out
    assert "via demonstrative warrant" in out  # CLI passes harness.warrants


def test_signals_command_lists_meanings_and_counts(root, capsys):
    path, _, _ = root
    assert main(["--root", str(path), "signals"]) == 0
    out = capsys.readouterr().out
    assert "browser-pass:" in out            # registry meanings listed
    assert "trial-blocked:*" in out          # prefix families listed
    assert "(unregistered" not in out.replace("(unregistered signal)", "")
