"""Evidence dossier (views/evidence.py) + why() warrant lines: the joins that
replaced every ad-hoc forensic script this project's runs required."""

import json

from deepreason.browser import browser_commitment
from deepreason.config import Config
from deepreason.ontology import Interface, Problem, ProblemProvenance, Provenance
from deepreason.rules.act import run_browser_evidence
from deepreason.views.evidence import evidence
from deepreason.views.why import why

from tests.conftest import attack
from tests.test_act import SCRIPT, FakeBrowser


def _app(harness, verdict="fail"):
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
    run_browser_evidence(harness, app.id, FakeBrowser(verdict), Config())
    return c, app


def test_dossier_shows_the_full_refutation_chain(harness):
    c, app = _app(harness, "fail")
    out = evidence(harness, app.id)

    assert f"ARTIFACT {app.id}" in out
    assert "status refuted" in out
    assert f"{c.id}: program:browser_oracle · observation-valued" in out
    assert "interaction steps" in out                 # spec summary
    assert "WARRANTS AGAINST IT" in out
    assert "demonstrative · commitment browser@" in out
    assert "verdict fail" in out
    assert "nu " in out and "[accepted]" in out       # the attackable ν + status
    assert "trace " in out                            # the trace_ref pointer
    assert "BROWSER EVIDENCE" in out
    assert "verdict fail · failed step 0" in out
    assert "screenshot " in out and "blob " in out    # followable refs
    assert "deepreason blob <ref>" in out             # the footer teaches the next hop


def test_dossier_shows_reinstatement_visibility(harness):
    _, app = _app(harness, "fail")
    w = next(w for w in harness.warrants.values() if w.target == app.id)
    attack(harness, w.validity_node, "the-render-lied")  # criticize the critic

    out = evidence(harness, app.id)
    assert "status accepted" in out                   # reinstated
    assert f"nu {w.validity_node[:12]} [refuted]" in out  # and the reader sees WHY


def test_dossier_dependencies_and_critic_side(harness):
    _, app = _app(harness, "fail")
    critic = next(a for a in harness.state.artifacts.values()
                  if any(harness.warrants[w].target == app.id for w in a.warrants))
    out = evidence(harness, critic.id)
    assert "WARRANTS IT CARRIES" in out
    assert app.id[:12] in out


def test_why_shows_warrant_evidence_lines(harness):
    _, app = _app(harness, "fail")
    out = why(app.id, harness.state, harness.warrants)
    assert "via demonstrative warrant" in out
    assert "commitment browser@" in out
    assert "verdict fail" in out
    assert "nu " in out and "trace " in out
    # Legacy shape preserved without the warrants param.
    legacy = why(app.id, harness.state)
    assert "via demonstrative warrant" not in legacy
    assert "<- attacked by" in legacy


def test_dossier_shows_llm_provenance(harness):
    from deepreason.ontology.event import LLMCall

    c = browser_commitment(SCRIPT)
    harness.register_commitment(c)
    call = LLMCall(role="conjecturer", model="m", endpoint="e",
                   prompt_ref=harness.blobs.put(b"the pack"),
                   raw_ref=harness.blobs.put(b"{}"), tokens=42)
    app = harness.create_artifact(
        "<div id=t>25:00</div>", codec="code:html",
        interface=Interface(commitments=[c.id]),
        provenance=Provenance(role="conjecturer"), llm=call,
    )
    out = evidence(harness, app.id)
    assert "LLM CALLS THAT PRODUCED IT" in out
    assert "conjecturer · m · 42 tokens" in out
    assert call.prompt_ref[:12] in out and call.raw_ref[:12] in out


def test_property_sourced_verdicts_name_their_source(harness):
    from deepreason.oracle import property_oracle_commitment
    from deepreason.rules.experiment import propose_properties
    from deepreason.llm.adapter import LLMAdapter
    from deepreason.llm.endpoints import MockEndpoint

    base = property_oracle_commitment(
        "solve", [[[3, 1, 2]]],
        "def check(inp, out):\n    xs = inp[0]\n"
        "    return isinstance(out, list) and sorted(xs) == out\n",
    )
    harness.register_commitment(base)
    problem = harness.register_problem(Problem(
        id="pi-sort", description="return the input sorted ascending",
        criteria=[base.id],
        provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
    ))
    trap = harness.create_artifact(
        "def solve(xs):\n    return xs if len(xs) < 3 else sorted(xs)\n",
        codec="code:python", interface=Interface(commitments=[base.id]),
        provenance=Provenance(role="conjecturer"),
    )
    harness.create_artifact(
        "def solve(xs):\n    return sorted(xs)\n",
        codec="code:python", interface=Interface(commitments=[base.id]),
        provenance=Provenance(role="conjecturer"),
    )
    checker = (
        "def check(inp, out):\n    xs = inp[0]\n"
        "    if not isinstance(out, list) or sorted(out) != sorted(xs):\n"
        "        return False\n"
        "    for i in range(len(out) - 1):\n"
        "        if out[i] > out[i + 1]:\n"
        "            return False\n"
        "    return True\n"
    )
    adapter = LLMAdapter(
        {
            "property_designer": MockEndpoint([json.dumps(
                {"properties": [{"claim": "output must be ascending", "checker": checker}]}
            )]),
            "judge": [
                MockEndpoint(
                    [json.dumps({"verdict": "pass", "decisive_point": "ascending"})],
                    name="mock://judge-gemma",
                    model="gemma-test",
                ),
                MockEndpoint(
                    [json.dumps({"verdict": "pass", "decisive_point": "ascending"})],
                    name="mock://judge-qwen",
                    model="qwen-test",
                ),
            ],
        },
        harness.blobs, retry_max=2,
    )
    props = propose_properties(harness, base, problem, adapter, Config())
    assert props
    # Frozen inputs pass for the trap (len 3): fuzz needs a generator, so
    # violate via frozen-inputs of the property directly on a short list —
    # extend the frozen inputs by re-running crit_fuzz with the property's
    # own frozen check (the trap fails on [2, 1]-style inputs only via
    # generators; here the property's frozen check uses base inputs, which
    # the trap passes — so instead assert the dossier names the source on a
    # crafted warrant path). Simpler: register the violation directly.
    from deepreason.oracle import property_violation_commitment
    from deepreason.rules.warrants import register_fail_warrant

    cx = property_violation_commitment(
        base, props[0].id, checker, [[2, 1]]
    )
    harness.register_commitment(cx)
    register_fail_warrant(
        harness, commitment_id=cx.id, target_id=trap.id,
        nu_content="nu: sourced verdict", critic_content="critic: sourced",
        trace_ref=harness.blobs.put(b"{}"),
    )
    out = evidence(harness, trap.id)
    assert "sourced from proposed property" in out
    assert props[0].id[:12] in out
    assert "stands as long as its source does" in out
