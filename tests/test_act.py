"""Browser evidence rule (rules/act.py): exogenous browser outcomes enter as
import-role evidence (research pattern) — run once, record bytes, refute by
demonstrative warrant. Uses a FakeBrowser: the suite never needs Chromium."""

import json

from deepreason.browser import BrowserResult, browser_commitment
from deepreason.config import Config
from deepreason.ontology import Interface, Provenance, Status, WarrantType
from deepreason.programs import content_text
from deepreason.rules.act import browser_evidence, browser_rid, run_browser_evidence

from tests.conftest import attack

PNG = b"\x89PNG\r\n\x1a\nfakebytes"
SCRIPT = [{"op": "assert_text", "selector": "#t", "expected": "25:00"}]


class FakeBrowser:
    name = "fake-browser"

    def __init__(self, verdict="pass", screenshots=(PNG,)):
        self.verdict = verdict
        self.screenshots = list(screenshots)
        self.runs = 0

    def run(self, html, spec):
        self.runs += 1
        trace = {"steps": [{"i": 0, **SCRIPT[0], "error": "text mismatch"}],
                 "failed_step": 0} if self.verdict == "fail" else {"steps": []}
        return BrowserResult(self.verdict, trace, list(self.screenshots))


def _app(harness, c, html="<div id=t>25:00</div>"):
    return harness.create_artifact(
        html, codec="code:html",
        interface=Interface(commitments=[c.id]),
        provenance=Provenance(role="conjecturer"),
    )


def test_pass_records_evidence_and_no_warrant(harness):
    c = browser_commitment(SCRIPT)
    harness.register_commitment(c)
    app = _app(harness, c)
    browser = FakeBrowser("pass")

    critic = run_browser_evidence(harness, app.id, browser, Config())

    assert critic is None
    assert harness.state.status[app.id] == Status.ACCEPTED
    ev = browser_evidence(harness, app.id)
    assert len(ev) == 1 and ev[0]["verdict"] == "pass"
    # Screenshots landed as binary import artifacts under the research rid.
    shot = harness.state.artifacts[ev[0]["screenshots"][0]]
    assert shot.codec == "image/png"
    assert harness.blobs.get(shot.content_ref) == PNG
    rid = browser_rid(c.id, app.id)
    assert any(pid == rid for _, pid in harness.state.addr)
    last = list(harness.log.read())[-1]
    assert last.inputs == ["browser-pass", c.id, app.id]


def test_fail_registers_demonstrative_warrant(harness):
    c = browser_commitment(SCRIPT)
    harness.register_commitment(c)
    app = _app(harness, c, "<div id=t>00:00</div>")
    critic = run_browser_evidence(harness, app.id, FakeBrowser("fail"), Config())

    assert critic is not None
    assert harness.state.status[app.id] == Status.REFUTED
    w = next(w for w in harness.warrants.values() if w.target == app.id)
    assert w.type == WarrantType.DEMONSTRATIVE and w.commitment == c.id
    # The nu MENTIONs the recorded evidence artifact.
    nu = harness.state.artifacts[w.validity_node]
    ev = browser_evidence(harness, app.id)
    assert any(r.target == ev[0]["evidence_id"] for r in nu.interface.refs)


def test_run_once_idempotence(harness):
    c = browser_commitment(SCRIPT)
    harness.register_commitment(c)
    app = _app(harness, c)
    browser = FakeBrowser("pass")
    run_browser_evidence(harness, app.id, browser, Config())
    run_browser_evidence(harness, app.id, browser, Config())
    assert browser.runs == 1  # pending() guard: the browser ran exactly once


def test_refuting_reliability_orphans_the_evidence(harness):
    c = browser_commitment(SCRIPT)
    harness.register_commitment(c)
    app = _app(harness, c)
    run_browser_evidence(harness, app.id, FakeBrowser("pass"), Config())
    ev_id = browser_evidence(harness, app.id)[0]["evidence_id"]
    reliability = next(
        r.target for r in harness.state.artifacts[ev_id].interface.refs
        if r.role.value == "dependence"
    )

    attack(harness, reliability, "the-render-was-not-faithful")

    assert harness.state.status[reliability] == Status.REFUTED
    assert harness.state.status[ev_id] == Status.SUSPENDED_UNSUPPORTED


def test_overrun_is_a_spec_defect_not_a_refutation(harness):
    c = browser_commitment(SCRIPT)
    harness.register_commitment(c)
    app = _app(harness, c)
    run_browser_evidence(harness, app.id, FakeBrowser("overrun"), Config())
    assert harness.state.status[app.id] == Status.ACCEPTED
    last = list(harness.log.read())[-1]
    assert last.inputs[0] == "browser-spec-overrun"


def test_vision_can_read_the_recorded_trace(harness):
    # browser_evidence returns parsed payloads with screenshot ids — the
    # exact interface crit_vision and export consume.
    c = browser_commitment(SCRIPT)
    harness.register_commitment(c)
    app = _app(harness, c)
    run_browser_evidence(harness, app.id, FakeBrowser("pass", (PNG, PNG)), Config())
    ev = browser_evidence(harness, app.id)[0]
    assert len(ev["screenshots"]) == 2
    raw = json.loads(content_text(harness.state.artifacts[ev["evidence_id"]], harness.blobs))
    assert raw["browser"] == "fake-browser"
