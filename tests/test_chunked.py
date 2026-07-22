"""Chunked website builds (manifest.py + easy._make_chunked): the design's
component manifest is an ordinary criticizable artifact; component contracts
are machine commitments through the normal verdict/warrant path; assembly is
deterministic repository code with full dependence traceability; integration
failures spawn TARGETED repair problems; refuted foundations SUSPEND their
dependents through standard support semantics — never deletion."""

import json

import pytest

from deepreason import easy
from deepreason.harness import Harness
from deepreason.manifest import (
    Manifest,
    assemble_html,
    integration_commitment,
    integration_wf,
    parse_manifest,
)
from deepreason.ontology import (
    Interface,
    Provenance,
    Ref,
    Rule,
    Status,
    Warrant,
    WarrantType,
)
from deepreason.rules.crit import crit_program

MANIFEST_JSON = {
    "title": "Todo",
    "libs": ["classless"],
    "components": [
        {"name": "header", "purpose": "brand bar", "element_id": "app-header",
         "css_prefix": "hd-", "js_exports": [], "js_uses": [],
         "events_emitted": [], "events_listened": [], "libs": [], "order": 0},
        {"name": "list", "purpose": "todo items", "element_id": "app-list",
         "css_prefix": "li-", "js_exports": ["addTodo"], "js_uses": [],
         "events_emitted": ["todo:add"], "events_listened": [],
         "libs": ["layout"], "order": 1},
    ],
}


def _design_doc(manifest=MANIFEST_JSON) -> str:
    return ("DESIGN: layout, palette, components, states. " * 20
            + "\n```manifest\n" + json.dumps(manifest) + "\n```\n")


HEADER_FRAGMENT = (
    '<header id="app-header"><h1>Todo</h1>'
    "<style>#app-header h1 { color: teal; }</style></header>"
)
LIST_FRAGMENT = """<section id="app-list"><ul id="app-list-items"></ul>
<style>.li-item { padding: 4px; }</style>
<script>
window.addTodo = function (text) {
  var li = document.createElement('li');
  li.className = 'li-item';
  li.textContent = text;
  document.getElementById('app-list-items').appendChild(li);
  document.dispatchEvent(new CustomEvent('todo:add'));
};
</script></section>"""


# ---- manifest: parseable, validated, ordinary artifact ------------------ #

def test_manifest_parses_and_validates():
    manifest, error = parse_manifest(_design_doc(), known_libs={"classless", "layout"})
    assert manifest is not None and error == ""
    assert [c.name for c in manifest.ordered()] == ["header", "list"]

    assert parse_manifest("no block here")[0] is None
    bad = dict(MANIFEST_JSON)
    bad["components"] = [dict(c) for c in MANIFEST_JSON["components"]]
    bad["components"][1]["element_id"] = "app-header"  # duplicate mount
    assert "duplicate" in parse_manifest(_design_doc(bad))[1]
    unknown = dict(MANIFEST_JSON, libs=["bootstrap"])
    assert "unknown libs" in parse_manifest(
        _design_doc(unknown), known_libs={"classless", "layout"})[1]
    orphan_use = dict(MANIFEST_JSON)
    orphan_use["components"] = [dict(c) for c in MANIFEST_JSON["components"]]
    orphan_use["components"][0]["js_uses"] = ["missingFn"]
    assert "no other component exports" in parse_manifest(_design_doc(orphan_use))[1]


def test_design_manifest_is_an_ordinary_criticizable_artifact(tmp_path):
    """The manifest lives inside a registered design artifact — visible in
    state, machine-gated by manifest_wf through the ordinary verdict path."""
    harness = Harness(tmp_path / "run")
    easy.seed_plan(harness, "a todo site")
    plan = harness.create_artifact("plan " * 200,
                                   provenance=Provenance(role="conjecturer"),
                                   problem_id="pi-plan")
    problem = easy.seed_design_chunked(harness, "a todo site", plan.id)
    evals = {harness.commitments[c].eval for c in problem.criteria}
    assert "program:manifest_wf" in evals and "program:lineage_ref" in evals

    good = harness.create_artifact(
        _design_doc(),
        interface=Interface(commitments=list(problem.criteria),
                            refs=[Ref(target=plan.id, role="dependence")]),
        provenance=Provenance(role="conjecturer"), problem_id="pi-design")
    crit_program(harness, good.id)
    assert harness.state.status.get(good.id) == Status.ACCEPTED

    manifestless = harness.create_artifact(
        "DESIGN without a manifest " * 40,
        interface=Interface(commitments=list(problem.criteria),
                            refs=[Ref(target=plan.id, role="dependence")]),
        provenance=Provenance(role="conjecturer"), problem_id="pi-design")
    crit_program(harness, manifestless.id)
    assert harness.state.status.get(manifestless.id) == Status.REFUTED


# ---- component contracts: ordinary warrants, not opaque gates ----------- #

def _component_harness(tmp_path):
    harness = Harness(tmp_path / "run")
    easy.seed_plan(harness, "a todo site")
    plan = harness.create_artifact("plan " * 200,
                                   provenance=Provenance(role="conjecturer"),
                                   problem_id="pi-plan")
    easy.seed_design_chunked(harness, "a todo site", plan.id)
    design = harness.create_artifact(
        _design_doc(), provenance=Provenance(role="conjecturer"),
        problem_id="pi-design")
    manifest, _ = parse_manifest(_design_doc())
    problems = {
        spec.name: easy.seed_component(
            harness, "a todo site", design.id, manifest, spec, 4000)
        for spec in manifest.components
    }
    return harness, design, manifest, problems


def _candidate(harness, problem, design, content):
    return harness.create_artifact(
        content,
        interface=Interface(commitments=list(problem.criteria),
                            refs=[Ref(target=design.id, role="dependence")]),
        provenance=Provenance(role="conjecturer"), problem_id=problem.id)


def test_plan_pack_requires_actual_copy_instead_of_content_placeholders(tmp_path):
    harness = Harness(tmp_path / "plan-run")
    problem = easy.seed_plan(harness, "an educational site")
    assert "actual headings, labels, explanatory copy, facts" in problem.description
    assert '"educational text"' in problem.description
    assert "system-level `prefers-reduced-motion`" in problem.description
    assert "before any animation starts" in problem.description


def test_chunked_design_pack_allows_only_its_required_manifest_metadata(tmp_path):
    harness = Harness(tmp_path / "design-run")
    easy.seed_plan(harness, "an educational site")
    plan = harness.create_artifact(
        "complete product plan " * 40,
        provenance=Provenance(role="conjecturer"),
        problem_id="pi-plan",
    )
    problem = easy.seed_design_chunked(harness, "an educational site", plan.id)
    assert "not implementation HTML, JavaScript, or" in problem.description
    assert "COMPONENT MANIFEST is allowed as structured design metadata" in (
        problem.description
    )


def test_animated_component_pack_requires_the_os_reduced_motion_query(tmp_path):
    _, _, _, problems = _component_harness(tmp_path)
    description = problems["header"].description
    assert "window.matchMedia('(prefers-reduced-motion: reduce)')" in description
    assert "manual motion toggle alone" in description


@pytest.mark.parametrize("mutate, expected_violation", [
    (lambda f: f + "x" * 5000, "oversized"),
    (lambda f: "<!doctype html><html><body>" + f + "</body></html>",
     "full HTML document"),
    (lambda f: f.replace('id="app-list"', 'id="wrong-mount"'),
     "missing declared mount id"),
    (lambda f: f.replace('id="app-list-items"', 'id="rogue-global-id"'),
     "outside the component's namespace"),
    (lambda f: f.replace("window.addTodo =", "window.sneakyGlobal ="),
     "undeclared global assignment"),
    (lambda f: f.replace("document.getElementById",
                         "window.someOtherComponentFn(); document.getElementById"),
     "undeclared dependency call"),
    (lambda f: f.replace(".li-item {", ".unscoped-anywhere {"),
     "not scoped"),
])
def test_component_contract_violations_are_refuted_with_warrants(
        tmp_path, mutate, expected_violation):
    harness, design, manifest, problems = _component_harness(tmp_path)
    bad = _candidate(harness, problems["list"], design, mutate(LIST_FRAGMENT))
    critics = crit_program(harness, bad.id)
    assert harness.state.status.get(bad.id) == Status.REFUTED
    # The failure is an ordinary demonstrative warrant with a readable
    # trace, not an opaque gate: the violation is named on the record.
    assert critics, "no critic artifact registered for the failed contract"
    traces = []
    for critic in critics:
        for wid in critic.warrants:
            warrant = harness.warrants[wid]
            if warrant.trace_ref:
                traces.append(harness.blobs.get(warrant.trace_ref).decode())
    assert any(expected_violation in t for t in traces)


def test_compliant_fragments_survive_their_contracts(tmp_path):
    harness, design, manifest, problems = _component_harness(tmp_path)
    for name, fragment in (("header", HEADER_FRAGMENT), ("list", LIST_FRAGMENT)):
        good = _candidate(harness, problems[name], design, fragment)
        crit_program(harness, good.id)
        assert harness.state.status.get(good.id) == Status.ACCEPTED, name


# ---- deterministic assembly + traceability ------------------------------ #

def test_assembly_is_deterministic_ordered_and_fully_traced(tmp_path):
    harness, design, manifest, problems = _component_harness(tmp_path)
    chosen = {
        "header": _candidate(harness, problems["header"], design, HEADER_FRAGMENT).id,
        "list": _candidate(harness, problems["list"], design, LIST_FRAGMENT).id,
    }
    assembled = easy.register_assembly(harness, design.id, manifest, chosen)
    html = harness.blobs.get(assembled.content_ref).decode() \
        if not assembled.content_ref.startswith("inline:") \
        else assembled.content_ref[len("inline:"):]
    # Order and vendored injection.
    assert html.index('id="app-header"') < html.index('id="app-list"')
    assert "vendored: baseline" in html
    assert "vendored: classless" in html and "vendored: layout" in html
    assert html.count("<!doctype") == 1
    # Pure-function determinism: same inputs, same bytes.
    from deepreason import assets
    again = assemble_html(
        manifest,
        {"header": HEADER_FRAGMENT, "list": LIST_FRAGMENT},
        {"classless": assets.catalog()["classless"],
         "layout": assets.catalog()["layout"]},
        assets.baseline(),
    )
    assert again == html
    # Complete dependence traceability: design + both components + libs.
    dep_targets = {r.target for r in assembled.interface.refs
                   if r.role.value == "dependence"}
    assert design.id in dep_targets
    assert set(chosen.values()) <= dep_targets
    lib_artifacts = [a for a in harness.state.artifacts.values()
                     if a.codec == "code:css"]
    assert len(lib_artifacts) == 2
    assert {a.id for a in lib_artifacts} <= dep_targets
    # It carries the browser and integration commitments and is ACCEPTED.
    evals = {harness.commitments[c].eval for c in assembled.interface.commitments}
    assert "program:integration_wf" in evals
    assert harness.state.status.get(assembled.id) == Status.ACCEPTED


def test_options_are_not_injected_unless_selected():
    """assemble_html injects the baseline always (documented technical
    floor) and catalog options only when the manifest selects them."""
    from deepreason import assets

    manifest = Manifest.model_validate({
        "title": "t",
        "components": [{"name": "a", "element_id": "a-root",
                        "css_prefix": "a-", "order": 0}],
    })
    page = assemble_html(manifest, {"a": '<div id="a-root"></div>'},
                         lib_css={}, baseline_css=assets.baseline())
    assert "vendored: baseline" in page
    assert "vendored: classless" not in page and "vendored: layout" not in page


# ---- integration criticism + targeted repair ---------------------------- #

def test_integration_wf_names_the_implicated_component():
    manifest = Manifest.model_validate(MANIFEST_JSON)
    kappa = integration_commitment(manifest)
    # list's export is missing from the page and its mount is duplicated.
    broken = assemble_html(
        manifest,
        {"header": HEADER_FRAGMENT,
         "list": '<section id="app-list"></section><div id="app-list"></div>'},
        {}, "")
    verdict, trace = integration_wf(broken, kappa.budget)
    assert verdict == "fail"
    assert "list" in trace["implicated"]
    good = assemble_html(
        manifest, {"header": HEADER_FRAGMENT, "list": LIST_FRAGMENT}, {}, "")
    assert integration_wf(good, kappa.budget)[0] == "pass"


def test_integration_failure_refutes_page_and_spawns_targeted_repair(tmp_path):
    harness, design, manifest, problems = _component_harness(tmp_path)
    chosen = {
        "header": _candidate(harness, problems["header"], design, HEADER_FRAGMENT).id,
        # list fragment that never defines its declared export: locally the
        # mount/CSS are fine but the page-level dependency contract breaks.
        "list": _candidate(harness, problems["list"], design,
                           '<section id="app-list"></section>').id,
    }
    assembled = easy.register_assembly(harness, design.id, manifest, chosen)
    cfg = easy.Config(**easy.MAKE_OVERRIDES)
    implicated = easy.integration_criticism(
        harness, assembled.id, manifest, cfg, browser_backend=None)
    assert "list" in implicated
    # Ordinary verdict path: the assembled page is refuted by a warrant.
    assert harness.state.status.get(assembled.id) == Status.REFUTED
    # The repair signal is logged for the post-hoc reader.
    repairs = [e for e in harness.log.read()
               if e.rule == Rule.MEASURE and e.inputs
               and e.inputs[0] == "integration-repair"]
    assert repairs and repairs[0].inputs[1] == assembled.id


# ---- support semantics: refuted foundations suspend, never delete ------- #

def test_refuted_design_suspends_components_and_assembly(tmp_path):
    harness, design, manifest, problems = _component_harness(tmp_path)
    chosen = {
        "header": _candidate(harness, problems["header"], design, HEADER_FRAGMENT).id,
        "list": _candidate(harness, problems["list"], design, LIST_FRAGMENT).id,
    }
    assembled = easy.register_assembly(harness, design.id, manifest, chosen)
    assert harness.state.status.get(assembled.id) == Status.ACCEPTED

    nu = harness.create_artifact("nu: the attack on the design is sound",
                                 provenance=Provenance(role="critic"))
    harness.create_artifact(
        "critic: the design's information architecture contradicts the plan",
        provenance=Provenance(role="critic"),
        warrants=[Warrant(id="w:attack:design", target=design.id,
                          type=WarrantType.ARGUMENTATIVE,
                          validity_node=nu.id)],
        rule=Rule.CRIT,
    )
    assert harness.state.status.get(design.id) == Status.REFUTED
    for aid in (*chosen.values(), assembled.id):
        assert harness.state.status.get(aid) == Status.SUSPENDED_UNSUPPORTED
    # Nothing was deleted or mutated: every artifact is still on the record.
    assert design.id in harness.state.artifacts
    assert all(aid in harness.state.artifacts for aid in chosen.values())


def test_successor_manifest_supports_revision_without_mutating_history(tmp_path):
    harness, design, manifest, problems = _component_harness(tmp_path)
    old_ids = set(harness.state.artifacts)
    revised_json = dict(MANIFEST_JSON, title="Todo v2")
    revised = harness.create_artifact(
        _design_doc(revised_json),
        interface=Interface(refs=[Ref(target=design.id, role="dependence")]),
        provenance=Provenance(role="conjecturer"), problem_id="pi-design")
    new_manifest, _ = parse_manifest(_design_doc(revised_json))
    spec = new_manifest.components[0]
    easy.seed_component(harness, "a todo site", revised.id, new_manifest, spec,
                        4000, suffix="-v2")
    fragment = harness.create_artifact(
        HEADER_FRAGMENT,
        interface=Interface(refs=[Ref(target=revised.id, role="dependence")]),
        provenance=Provenance(role="conjecturer"),
        problem_id=f"pi-comp-{spec.name}-v2")
    assembled = easy.register_assembly(
        harness, revised.id, new_manifest,
        {"header": fragment.id,
         "list": _candidate(harness, problems["list"], revised, LIST_FRAGMENT).id})
    assert harness.state.status.get(assembled.id) == Status.ACCEPTED
    # Prior history intact: every pre-revision artifact still present.
    assert old_ids <= set(harness.state.artifacts)


def test_component_stage_runs_through_the_real_scheduler(tmp_path):
    """No side pipeline: a component problem is worked by the ordinary
    scheduler — schools exist, candidates flow Conj -> Crit -> Adj, an
    oversized fragment is refuted mechanically (warrant on the record) while
    the compliant rival survives, and the root replays byte-for-byte."""
    from deepreason.config import Config
    from deepreason.llm.adapter import LLMAdapter
    from deepreason.llm.endpoints import MockEndpoint
    from deepreason.scheduler.scheduler import Scheduler

    harness, design, manifest, problems = _component_harness(tmp_path)

    def scripted(prompt):
        # Two rival fragments for the list component: one oversized (blows
        # the CHUNK bound), one compliant — both born-connected to the
        # design, exactly as the pack instructs.
        ref = [{"target": design.id[:12], "role": "dependence"}]
        return json.dumps({"candidates": [
            {"content": LIST_FRAGMENT.replace(
                "</section>", "<!-- " + "pad " * 1200 + " --></section>"),
             "typicality": 0.6, "refs": ref},
            {"content": LIST_FRAGMENT, "typicality": 0.5, "refs": ref},
        ]})

    adapter = LLMAdapter({"conjecturer": MockEndpoint(scripted)}, harness.blobs)
    config = Config(**{**easy.MAKE_OVERRIDES, "BROWSER_PER_CYCLE": 0,
                       "FOCUS_FAMILY": "pi-comp-list"})
    scheduler = Scheduler(harness, adapter, config)
    assert len(scheduler.schools) == config.N_SCHOOLS  # capture population up
    scheduler.step()

    family_candidates = [
        aid for aid, pid in harness.state.addr
        if pid == "pi-comp-list"
        and (a := harness.state.artifacts.get(aid)) is not None
        and a.provenance and a.provenance.role.value == "conjecturer"
    ]
    statuses = {harness.state.status.get(a) for a in family_candidates}
    assert Status.REFUTED in statuses, "the oversized fragment must be refuted"
    assert Status.ACCEPTED in statuses, "the compliant fragment must survive"
    survivor = easy.pick_survivor(harness, "pi-comp-list")
    assert survivor is not None
    # The refutation went through the ordinary warrant path.
    assert any(
        w.commitment and w.commitment.startswith("component-wf@")
        for w in harness.warrants.values()
    )
    # Replay: a fresh harness over the same log reconstructs the state.
    replayed = Harness(tmp_path / "run")
    assert set(replayed.state.artifacts) == set(harness.state.artifacts)
    assert replayed.state.status == harness.state.status


# ---- the chunked make flow drives the NORMAL engine --------------------- #



def test_make_chunked_public_facade_is_fail_closed_without_side_effects(
    tmp_path, monkeypatch
):
    """The retired Easy facade cannot recreate the historical workflow."""
    calls = []
    monkeypatch.setattr(
        "deepreason.ops.run_scheduler",
        lambda *_args, **_kwargs: calls.append("scheduler"),
    )
    root = tmp_path / "run"
    output = tmp_path / "site"

    with pytest.raises(easy.EasyV6PreparationRequired) as caught:
        easy.make("a todo site", out=str(output), root=str(root))

    assert caught.value.code == "V6_PREPARATION_REQUIRED"
    assert calls == []
    assert not root.exists()
    assert not output.exists()


def test_assembled_page_passes_browser_smoke_in_real_chromium(tmp_path):
    """Executable half of integration criticism: the deterministically
    assembled page loads, renders, and survives the smoke script in a real
    headless Chromium (networking disabled — vendored CSS must carry it)."""
    pytest.importorskip("playwright")
    from deepreason.browser import PlaywrightBrowser
    from deepreason.rules.act import browser_evidence

    harness, design, manifest, problems = _component_harness(tmp_path)
    chosen = {
        "header": _candidate(harness, problems["header"], design, HEADER_FRAGMENT).id,
        "list": _candidate(harness, problems["list"], design, LIST_FRAGMENT).id,
    }
    assembled = easy.register_assembly(harness, design.id, manifest, chosen)
    cfg = easy.Config(**easy.MAKE_OVERRIDES)
    implicated = easy.integration_criticism(
        harness, assembled.id, manifest, cfg, browser_backend=PlaywrightBrowser())
    assert implicated == []
    assert harness.state.status.get(assembled.id) == Status.ACCEPTED
    evidence = browser_evidence(harness, assembled.id)
    assert evidence and evidence[0]["verdict"] == "pass"
    assert evidence[0]["screenshots"]


def test_make_chunked_repair_facade_cannot_read_config_or_create_a_root(
    tmp_path, monkeypatch
):
    """Even former repair-mode arguments reach only the Easy tombstone."""
    calls = []
    monkeypatch.setattr(
        "deepreason.ops.run_scheduler",
        lambda *_args, **_kwargs: calls.append("scheduler"),
    )
    missing_config = tmp_path / "must-not-be-read.yaml"
    root = tmp_path / "repair-run"
    output = tmp_path / "site"

    with pytest.raises(easy.EasyV6PreparationRequired) as caught:
        easy.make(
            "a todo site",
            out=str(output),
            config=str(missing_config),
            root=str(root),
        )

    assert caught.value.code == "V6_PREPARATION_REQUIRED"
    assert calls == []
    assert not missing_config.exists()
    assert not root.exists()
    assert not output.exists()
