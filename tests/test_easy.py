"""The two-command path (easy.py): setup wizard, private key storage, and
`deepreason make` — sugar over the same machinery as the expert surface.
The one Chromium test is guarded like test_browser.py."""

import os
import stat

import pytest
import yaml

from deepreason import easy
from deepreason.config import Config


@pytest.fixture(autouse=True)
def _home(tmp_path, monkeypatch):
    """Redirect ~/.deepreason into the test sandbox."""
    monkeypatch.setenv("DEEPREASON_HOME", str(tmp_path / "dot"))
    return tmp_path


# ---- credentials: stored privately, loaded everywhere, env always wins ----

def test_save_and_load_credentials_roundtrip(monkeypatch):
    monkeypatch.delenv("FAKE_KEY_A", raising=False)
    path = easy.save_credential("FAKE_KEY_A", "secret-123")
    assert stat.S_IMODE(path.stat().st_mode) == 0o600  # owner-only
    assert easy.load_credentials() == 1
    assert os.environ["FAKE_KEY_A"] == "secret-123"


def test_existing_environment_wins_over_stored_key(monkeypatch):
    easy.save_credential("FAKE_KEY_B", "stored")
    monkeypatch.setenv("FAKE_KEY_B", "from-shell")
    easy.load_credentials()
    assert os.environ["FAKE_KEY_B"] == "from-shell"


def test_save_credential_replaces_not_duplicates():
    easy.save_credential("FAKE_KEY_C", "one")
    easy.save_credential("FAKE_KEY_C", "two")
    lines = easy.credentials_path().read_text().splitlines()
    assert lines.count("FAKE_KEY_C=two") == 1
    assert not any("=one" in ln for ln in lines)


def test_load_credentials_without_file_is_quiet():
    assert easy.load_credentials() == 0


# ---- setup wizard: two questions, key never lands in the config file ----

def test_setup_wizard_writes_config_without_the_key(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    answers = iter(["1"])  # provider: deepseek
    path = easy.setup_wizard(
        input_fn=lambda _: next(answers),
        getpass_fn=lambda _: "sk-super-secret",
    )
    text = path.read_text()
    assert "sk-super-secret" not in text          # the invariant: no keys in configs
    assert "api_key_env: DEEPSEEK_API_KEY" in text
    config = Config.model_validate(yaml.safe_load(text))
    assert "conjecturer" in config.roles and "argumentative_critic" in config.roles
    assert config.FUZZ_N == 0 and config.BROWSER_PER_CYCLE == 2
    assert "DEEPSEEK_API_KEY=sk-super-secret" in easy.credentials_path().read_text()


def test_setup_wizard_custom_provider_asks_url_and_model():
    answers = iter(["3", "https://api.example.com/v1", "my-model"])
    path = easy.setup_wizard(
        input_fn=lambda _: next(answers),
        getpass_fn=lambda _: "k",
    )
    config = Config.model_validate(yaml.safe_load(path.read_text()))
    seat = config.roles["conjecturer"]
    assert seat["endpoint"] == "https://api.example.com/v1"
    assert seat["model"] == "my-model"
    assert seat["api_key_env"] == "LLM_API_KEY"


def test_setup_wizard_rejects_nonsense_then_recovers():
    answers = iter(["banana", "0", "1"])
    path = easy.setup_wizard(
        input_fn=lambda _: next(answers),
        getpass_fn=lambda _: "k",
    )
    assert path.exists()


def test_gemma4_31b_preset_pins_every_model_bearing_role_to_ollama_cloud():
    preset = easy.PROVIDERS["gemma4_31b"]
    profile = Config.model_validate({
        **easy.MAKE_OVERRIDES,
        "roles": preset["roles"](preset["base"], preset["model"], preset["env"]),
    })
    expected = {
        "conjecturer", "variator", "argumentative_critic", "defender", "judge",
        "synthesizer", "summarizer", "vision_critic", "property_designer", "thesis",
    }
    assert expected <= set(profile.roles)
    for configured in profile.roles.values():
        seats = configured if isinstance(configured, list) else [configured]
        for seat in seats:
            assert seat["endpoint"] == "https://ollama.com/v1"
            assert seat["model"] == "gemma4:31b"
            assert seat["api_key_env"] == "OLLAMA_API_KEY"
            assert seat["provider"] == "ollama"


# ---- seeding: the same record-grade objects the expert surface makes ----

def test_seed_website_registers_browser_commitment(tmp_path):
    from deepreason.browser import BROWSER_PROGRAM, load_spec
    from deepreason.harness import Harness

    harness = Harness(tmp_path / "run")
    problem = easy.seed_website(harness, "a tiny recipe site")
    assert problem.id == "pi-website"
    cid = problem.criteria[0]
    kappa = harness.commitments[cid]
    assert kappa.eval == f"program:{BROWSER_PROGRAM}"
    assert kappa.observation_valued
    assert load_spec(kappa.budget)["script"] == easy.WEBSITE_SCRIPT
    assert "a tiny recipe site" in problem.description
    assert "self-contained HTML5" in problem.description


def test_website_script_uses_only_known_ops():
    from deepreason.browser import _STEP_OPS

    assert {step["op"] for step in easy.WEBSITE_SCRIPT} <= _STEP_OPS


# ---- make: friendly wrapper, honest failure modes ----

def test_make_without_config_fails_with_guidance(monkeypatch):
    monkeypatch.setattr("sys.stdin", type("T", (), {"isatty": lambda self: False})())
    with pytest.raises(SystemExit, match="deepreason setup"):
        easy.make("a site", root="unused")


def test_make_without_key_fails_with_guidance(tmp_path, monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    cfg = tmp_path / "engine.yaml"
    cfg.write_text(yaml.safe_dump({"roles": {"conjecturer": {
        "endpoint": "https://api.deepseek.com", "model": "m",
        "api_key_env": "DEEPSEEK_API_KEY"}}}))
    with pytest.raises(SystemExit, match="DEEPSEEK_API_KEY"):
        easy.make("a site", config=str(cfg), root=str(tmp_path / "r"))


def _fake_cfg(tmp_path, monkeypatch):
    monkeypatch.setenv("FAKE_MAKE_KEY", "k")
    cfg = tmp_path / "engine.yaml"
    cfg.write_text(yaml.safe_dump({"roles": {"conjecturer": {
        "endpoint": "https://x.invalid", "model": "m",
        "api_key_env": "FAKE_MAKE_KEY"}}}))
    return cfg


def _stage_faker(calls):
    """A run_scheduler stub that plays a compliant engine: per invocation it
    registers one ACCEPTED artifact addressed to the newest seeded problem,
    carrying that problem's criteria and (for lineage-bound stages) the
    required dependence ref."""
    from deepreason.ontology import Interface, Provenance, Ref

    def fake_run(harness, config, cycles, token_budget=None, on_cycle=None,
                 run_manifest=None):
        pid = list(harness.state.problems)[-1]
        problem = harness.state.problems[pid]
        refs = []
        for cid in problem.criteria:
            kappa = harness.commitments.get(cid)
            if kappa is not None and kappa.eval == "program:lineage_ref":
                refs = [Ref(target=e, role="dependence")
                        for e in kappa.budget.extra["endpoints"].split(",")]
        content = {
            "pi-plan": "PLAN: pages, features, interactions, acceptance. " * 15,
            "pi-design": "DESIGN: layout, palette, components, states. " * 20,
            "pi-website": "<!doctype html><html><head><title>Hi</title></head>"
                          "<body><h1>Hi</h1></body></html>",
        }[pid]
        harness.create_artifact(
            content,
            interface=Interface(commitments=list(problem.criteria), refs=refs),
            provenance=Provenance(role="conjecturer"), problem_id=pid)
        if on_cycle is not None:  # one "cycle", as the real scheduler would
            from types import SimpleNamespace

            on_cycle(SimpleNamespace(harness=harness))
        calls.append({"pid": pid, "focus_family": config.FOCUS_FAMILY,
                      "token_budget": token_budget})
        return ({"survivors": 1}, None, {"logged_tokens_this_run": 1000,
                                         "metered_tokens": 1000})

    return fake_run


def test_staged_make_runs_three_stages_and_exports(tmp_path, monkeypatch):
    """plan -> design -> build through the real seeding, picking, and export
    paths; only the scheduler runs are stubbed (they need live endpoints)."""
    from deepreason import ops

    cfg = _fake_cfg(tmp_path, monkeypatch)
    calls = []
    monkeypatch.setattr(ops, "run_scheduler", _stage_faker(calls))
    lines = []
    paths = easy.make("my test site", out=str(tmp_path / "site"),
                      config=str(cfg), root=str(tmp_path / "r"),
                      echo=lines.append, chunked=False)  # legacy compat mode
    assert [c["pid"] for c in calls] == ["pi-plan", "pi-design", "pi-website"]
    assert [c["focus_family"] for c in calls] == ["pi-plan", "pi-design", "pi-website"]
    # One global ceiling, threaded as the remainder.
    assert calls[0]["token_budget"] == 150_000
    assert calls[1]["token_budget"] == 149_000
    assert calls[2]["token_budget"] == 148_000
    pages = [p for p in paths if p.suffix == ".html"]
    assert len(pages) == 1 and pages[0].exists()
    docs = sorted(p.name for p in paths if p.suffix == ".md" and p.name != "README.md")
    assert any(n.startswith("plan-") for n in docs)
    assert any(n.startswith("design-") for n in docs)
    joined = "\n".join(lines)
    assert "planning round" in joined and "designing round" in joined \
        and "building round" in joined
    assert "plan chosen:" in joined and "design chosen:" in joined
    assert "Your website is ready" in joined
    # The picks are on the record.
    from deepreason.harness import Harness
    from deepreason.ontology import Rule
    harness = Harness(tmp_path / "r")
    picks = [e.inputs[1] for e in harness.log.read()
             if e.rule == Rule.MEASURE and e.inputs and e.inputs[0] == "stage-pick"]
    assert picks == ["plan", "design"]


def test_staged_make_stops_when_no_plan_survives(tmp_path, monkeypatch):
    from deepreason import ops

    cfg = _fake_cfg(tmp_path, monkeypatch)
    calls = []

    def barren(harness, config, cycles, token_budget=None, on_cycle=None,
               run_manifest=None):
        calls.append(config.FOCUS_FAMILY)
        return ({"survivors": 0}, None, {"logged_tokens_this_run": 7})

    monkeypatch.setattr(ops, "run_scheduler", barren)
    lines = []
    paths = easy.make("doomed site", out=str(tmp_path / "site"),
                      config=str(cfg), root=str(tmp_path / "r"),
                      echo=lines.append, chunked=False)
    assert paths == []
    assert calls == ["pi-plan"]  # later stages never ran
    joined = "\n".join(lines)
    assert "No plan survived" in joined and "--cycles" in joined


def test_make_single_stage_legacy_path(tmp_path, monkeypatch):
    """staged=False reproduces the old single-problem behavior."""
    from deepreason import ops
    from deepreason.ontology import Interface, Provenance

    cfg = _fake_cfg(tmp_path, monkeypatch)

    def fake_run(harness, config, cycles, token_budget=None, on_cycle=None,
                 run_manifest=None):
        assert config.FOCUS_FAMILY is None
        cid = next(iter(harness.commitments))
        harness.create_artifact(
            "<!doctype html><html><head><title>Hi</title></head>"
            "<body><h1>Hi</h1></body></html>",
            interface=Interface(commitments=[cid]),
            provenance=Provenance(role="conjecturer"), problem_id="pi-website")
        return ({"survivors": 1}, None, {"logged_tokens_this_run": 1234})

    monkeypatch.setattr(ops, "run_scheduler", fake_run)
    lines = []
    paths = easy.make("my test site", out=str(tmp_path / "site"),
                      config=str(cfg), root=str(tmp_path / "r"),
                      echo=lines.append, staged=False)
    pages = [p for p in paths if p.suffix == ".html"]
    assert len(pages) == 1 and pages[0].exists()
    assert "1,234 tokens" in "\n".join(lines)


def test_direct_easy_make_binds_manifest_before_scheduler(tmp_path, monkeypatch):
    from deepreason import ops
    from deepreason.run_manifest import load_run_manifest

    cfg = _fake_cfg(tmp_path, monkeypatch)
    run_root = tmp_path / "bound-run"

    def fake_run(harness, config, cycles, token_budget=None, on_cycle=None,
                 run_manifest=None):
        manifest_path = run_root / "run-manifest.json"
        assert manifest_path.exists()
        manifest = load_run_manifest(manifest_path)
        assert run_manifest == manifest
        assert config.roles["conjecturer"]["model"] == "m"
        assert manifest.roles["conjecturer"][0].model_id == "m"
        return ({"survivors": 0}, None, {"logged_tokens_this_run": 0})

    monkeypatch.setattr(ops, "run_scheduler", fake_run)
    easy.make(
        "bound site", config=str(cfg), root=str(run_root),
        out=str(tmp_path / "out"), staged=False, echo=lambda *_: None,
    )
    assert (run_root / "run-manifest.sha256").exists()
    assert (run_root / ".run-manifest-config.json").exists()


def test_direct_easy_make_resume_uses_bound_manifest_not_new_source(
    tmp_path, monkeypatch
):
    from deepreason import ops
    from deepreason.run_manifest import (
        bind_run_manifest,
        compile_run_manifest,
        load_run_manifest,
    )

    cfg_path = _fake_cfg(tmp_path, monkeypatch)
    source = Config.model_validate(yaml.safe_load(cfg_path.read_text()))
    manifest = compile_run_manifest(
        source, rubric_policy="forbid", compiled_at="2026-07-11T00:00:00Z"
    )
    run_root = tmp_path / "resume-run"
    bind_run_manifest(manifest, run_root)
    monkeypatch.setattr(
        "deepreason.run_manifest.compile_run_manifest",
        lambda *_a, **_k: pytest.fail("resume attempted to compile a new manifest"),
    )

    def fake_run(harness, config, cycles, token_budget=None, on_cycle=None,
                 run_manifest=None):
        assert load_run_manifest(run_root / "run-manifest.json") == manifest
        assert run_manifest == manifest
        assert config.roles["conjecturer"]["model"] == "m"
        return ({"survivors": 0}, None, {"logged_tokens_this_run": 0})

    monkeypatch.setattr(ops, "run_scheduler", fake_run)
    easy.make(
        "resume site", config=str(tmp_path / "does-not-exist.yaml"),
        root=str(run_root), out=str(tmp_path / "resume-out"),
        staged=False, echo=lambda *_: None,
    )


# ---- staged seeding, enforcement, and the FOUNDATION pack section ----

def test_seed_plan_design_build_wire_the_lineage(tmp_path):
    from deepreason.browser import BROWSER_PROGRAM
    from deepreason.harness import Harness
    from deepreason.ontology import Provenance

    harness = Harness(tmp_path / "run")
    easy.seed_plan(harness, "a site")
    plan = harness.create_artifact("plan " * 200,
                                   provenance=Provenance(role="conjecturer"),
                                   problem_id="pi-plan")
    design_problem = easy.seed_design(harness, "a site", plan.id)
    lineage = [harness.commitments[c] for c in design_problem.criteria
               if harness.commitments[c].eval == "program:lineage_ref"]
    assert len(lineage) == 1
    assert lineage[0].budget.extra["endpoints"] == plan.id
    design = harness.create_artifact("design " * 200,
                                     provenance=Provenance(role="conjecturer"),
                                     problem_id="pi-design")
    build_problem = easy.seed_build(harness, "a site", design.id)
    evals = {harness.commitments[c].eval for c in build_problem.criteria}
    assert f"program:{BROWSER_PROGRAM}" in evals
    assert "program:lineage_ref" in evals


def test_lineage_enforced_mechanically(tmp_path):
    """A design without the dependence ref is refuted with zero LLM calls;
    with the ref it stands."""
    from deepreason.harness import Harness
    from deepreason.ontology import Interface, Provenance, Ref, Status
    from deepreason.rules.crit import crit_program

    harness = Harness(tmp_path / "run")
    easy.seed_plan(harness, "a site")
    plan = harness.create_artifact("plan " * 200,
                                   provenance=Provenance(role="conjecturer"),
                                   problem_id="pi-plan")
    problem = easy.seed_design(harness, "a site", plan.id)
    bare = harness.create_artifact(
        "design " * 200, interface=Interface(commitments=list(problem.criteria)),
        provenance=Provenance(role="conjecturer"), problem_id="pi-design")
    crit_program(harness, bare.id)
    assert harness.state.status[bare.id] == Status.REFUTED
    bound = harness.create_artifact(
        "design2 " * 200,
        interface=Interface(commitments=list(problem.criteria),
                            refs=[Ref(target=plan.id, role="dependence")]),
        provenance=Provenance(role="conjecturer"), problem_id="pi-design")
    crit_program(harness, bound.id)
    assert harness.state.status[bound.id] == Status.ACCEPTED


def test_foundation_section_renders_and_preserves_directive(tmp_path):
    from deepreason.harness import Harness
    from deepreason.llm.packs import render_conj_pack
    from deepreason.ontology import Provenance

    harness = Harness(tmp_path / "run")
    plan_problem = easy.seed_plan(harness, "a site")
    plan = harness.create_artifact("PLAN CONTENT " * 800,  # ~10KB > cap
                                   provenance=Provenance(role="conjecturer"),
                                   problem_id="pi-plan")
    design_problem = easy.seed_design(harness, "a site", plan.id)
    pack = render_conj_pack(design_problem, harness.state, harness.commitments,
                            harness.blobs, vs_k=2, token_budget=6000)
    assert "FOUNDATION" in pack
    assert plan.id in pack                       # the FULL id, verbatim
    assert '"role": "dependence"' in pack        # the exact JSON to emit
    assert "DIRECTIVE" in pack                   # cap kept the tail alive
    assert pack.find("FOUNDATION") < pack.find("DIRECTIVE")
    # A problem without lineage criteria renders no FOUNDATION at all.
    plain = render_conj_pack(plan_problem, harness.state, harness.commitments,
                             harness.blobs, vs_k=2, token_budget=6000)
    assert "FOUNDATION" not in plain


def test_conj_resolves_ref_prefixes():
    from deepreason.rules.conj import _resolve_ref

    artifacts = {"abcdef0123456789": 1, "abzz": 1}
    assert _resolve_ref("abcdef0123456789", artifacts) == "abcdef0123456789"
    assert _resolve_ref("abcdef", artifacts) == "abcdef0123456789"  # unique prefix
    assert _resolve_ref("ab", artifacts) is None                    # ambiguous
    assert _resolve_ref("zz", artifacts) is None                    # unknown
    assert _resolve_ref("", artifacts) is None


def test_refuting_the_design_orphans_the_build(tmp_path):
    """Dep semantics: a build depending on a later-refuted design is
    SUSPENDED (orphaned), never falsely refuted — and export omits it."""
    from deepreason.harness import Harness
    from deepreason.ontology import Interface, Provenance, Ref, Status
    from deepreason.views.export import export_run

    harness = Harness(tmp_path / "run")
    easy.seed_plan(harness, "a site")
    plan = harness.create_artifact("plan " * 200,
                                   provenance=Provenance(role="conjecturer"),
                                   problem_id="pi-plan")
    easy.seed_design(harness, "a site", plan.id)
    design = harness.create_artifact(
        "design " * 200,
        interface=Interface(refs=[Ref(target=plan.id, role="dependence")]),
        provenance=Provenance(role="conjecturer"), problem_id="pi-design")
    build_problem = easy.seed_build(harness, "a site", design.id)
    build = harness.create_artifact(
        "<!doctype html><html><head><title>x</title></head><body>x</body></html>",
        interface=Interface(commitments=list(build_problem.criteria),
                            refs=[Ref(target=design.id, role="dependence")]),
        provenance=Provenance(role="conjecturer"), problem_id="pi-website")
    assert harness.state.status[build.id] == Status.ACCEPTED
    from deepreason.rules.warrants import register_fail_warrant
    register_fail_warrant(
        harness, commitment_id=list(build_problem.criteria)[0],
        target_id=design.id, nu_content="nu: the design fails",
        critic_content="critic: the design is wrong", trace_ref="")
    assert harness.state.status[design.id] == Status.REFUTED
    assert harness.state.status[build.id] == Status.SUSPENDED_UNSUPPORTED
    paths = export_run(harness, tmp_path / "site")
    assert not [p for p in paths if p.suffix == ".html"]


# ---- the generic script against real Chromium (guarded) ----

def test_website_script_passes_a_real_page_and_fails_a_blank_one():
    pytest.importorskip("playwright")
    from deepreason.browser import PlaywrightBrowser

    browser = PlaywrightBrowser()
    spec = {"script": easy.WEBSITE_SCRIPT, "viewport": {"width": 800, "height": 600}}
    good = browser.run(
        "<!doctype html><html><head><title>Recipes</title></head>"
        "<body><h1>Recipes</h1><p>Soup.</p></body></html>", spec)
    assert good.verdict == "pass"
    assert len(good.screenshots) == 2
    blank = browser.run("<!doctype html><html><head></head><body></body></html>", spec)
    assert blank.verdict == "fail"
