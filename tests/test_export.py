"""Export view (views/export.py): a finished run's survivors become files a
human can open — app HTML, raw PNG screenshots, and a README with the
why-chain. Binary-safe throughout."""

from deepreason.browser import browser_commitment
from deepreason.config import Config
from deepreason.ontology import Interface, Problem, ProblemProvenance, Provenance
from deepreason.rules.act import run_browser_evidence
from deepreason.views.export import export_run

from tests.test_act import PNG, SCRIPT, FakeBrowser

APP_HTML = "<!doctype html><div id=t>25:00</div><button id=start>Start</button>"


def _run_shape(harness):
    c = browser_commitment(SCRIPT)
    harness.register_commitment(c)
    harness.register_problem(Problem(
        id="pi-app", description="build a pomodoro timer", criteria=[c.id],
        provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
    ))
    app = harness.create_artifact(
        APP_HTML, codec="code:html",
        interface=Interface(commitments=[c.id]),
        provenance=Provenance(role="conjecturer"), problem_id="pi-app",
    )
    run_browser_evidence(harness, app.id, FakeBrowser("pass"), Config())
    return app


def test_export_writes_app_screenshots_and_readme(harness, tmp_path):
    app = _run_shape(harness)
    paths = export_run(harness, tmp_path / "out")

    names = {p.name for p in paths}
    app_file = next(p for p in paths if p.suffix == ".html")
    assert app_file.read_text() == APP_HTML          # the deliverable, verbatim
    shot = next(p for p in paths if p.suffix == ".png")
    assert shot.read_bytes() == PNG                  # binary-safe raw copy
    assert "README.md" in names
    readme = (tmp_path / "out" / "README.md").read_text()
    assert "build a pomodoro timer" in readme        # the problem statement
    assert "Browser verdict:** pass" in readme
    assert app.id[:8] in readme                      # the why-chain names the app


def test_export_specific_artifact(harness, tmp_path):
    app = _run_shape(harness)
    other = harness.create_artifact("unrelated prose")
    paths = export_run(harness, tmp_path / "out", app.id)
    assert all(other.id[:12] not in p.name for p in paths)
    assert any(app.id[:12] in p.name for p in paths)


def test_export_skips_refuted_candidates(harness, tmp_path):
    from tests.conftest import attack

    app = _run_shape(harness)
    attack(harness, app.id, "kill-it")
    paths = export_run(harness, tmp_path / "out")
    assert not any(p.suffix == ".html" for p in paths)  # nothing survived
