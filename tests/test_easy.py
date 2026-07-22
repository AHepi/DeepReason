"""The two-command path (easy.py): setup wizard, private key storage, and
`deepreason make` — sugar over the same machinery as the expert surface.
The one Chromium test is guarded like test_browser.py."""

import os
import stat

import pytest

from deepreason import easy
from deepreason.config import Config
from deepreason.provider_profile import load_provider_profile


@pytest.fixture(autouse=True)
def _home(tmp_path, monkeypatch):
    """Redirect ~/.deepreason into the test sandbox."""
    monkeypatch.setenv("DEEPREASON_HOME", str(tmp_path / "dot"))
    return tmp_path


# ---- credentials: stored privately, loaded everywhere, env always wins ----

def test_save_and_load_credentials_roundtrip(monkeypatch):
    monkeypatch.delenv("FAKE_KEY_A", raising=False)
    path = easy.save_credential("FAKE_KEY_A", "secret-123")
    if os.name != "nt":
        # Windows does not represent its ACL through POSIX mode bits.
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


# ---- setup wizard: typed provider profile, key never lands in the profile ----

def test_setup_wizard_writes_config_without_the_key(monkeypatch, capsys):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    answers = iter(["1", "262144", "4096"])  # provider and finite capacities
    path = easy.setup_wizard(
        input_fn=lambda _: next(answers),
        getpass_fn=lambda _: "sk-super-secret",
    )
    text = path.read_text()
    assert "sk-super-secret" not in text          # the invariant: no keys in configs
    assert "credential_env: DEEPSEEK_API_KEY" in text
    profile = load_provider_profile(path)
    assert profile.provider == "deepseek"
    assert profile.context_window_tokens == 262144
    assert profile.maximum_completion_tokens == 4096
    assert "DEEPSEEK_API_KEY=sk-super-secret" in easy.credentials_path().read_text()
    output = capsys.readouterr().out
    assert "sk-super-secret" not in output
    assert "deepreason make" not in output
    assert "public question entry is wired in the next bounded task" in output


def test_setup_wizard_custom_provider_asks_url_and_model():
    answers = iter(
        ["3", "https://api.example.com/v1", "my-model", "131072", "2048"]
    )
    path = easy.setup_wizard(
        input_fn=lambda _: next(answers),
        getpass_fn=lambda _: "k",
    )
    profile = load_provider_profile(path)
    assert profile.endpoint == "https://api.example.com/v1"
    assert profile.model_id == "my-model"
    assert profile.credential_env == "LLM_API_KEY"


def test_setup_wizard_rejects_nonsense_then_recovers():
    answers = iter(["banana", "0", "1", "65536", "1024"])
    path = easy.setup_wizard(
        input_fn=lambda _: next(answers),
        getpass_fn=lambda _: "k",
    )
    assert path.exists()


def test_setup_wizard_reuses_existing_credential_without_prompt(monkeypatch):
    monkeypatch.setenv("EXISTING_KEY", "already-set")

    def forbidden(_prompt):
        pytest.fail("setup asked for a credential that is already available")

    path = easy.setup_wizard(
        input_fn=lambda _prompt: pytest.fail("explicit setup should not prompt"),
        getpass_fn=forbidden,
        provider="custom",
        endpoint="https://api.example.com/v1",
        model="model-1",
        context_window_tokens=32768,
        maximum_completion_tokens=1024,
        credential_env="EXISTING_KEY",
    )

    assert load_provider_profile(path).credential_env == "EXISTING_KEY"
    assert not easy.credentials_path().exists()


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


# ---- retired Easy execution: fail closed before any side effect ----

@pytest.mark.parametrize(
    "kwargs",
    [
        {},
        {"staged": False},
        {"chunked": False},
        {"config": "missing-engine.yaml"},
    ],
)
def test_easy_make_requires_future_v6_preparation_before_any_side_effect(
    tmp_path, monkeypatch, kwargs
):
    from deepreason import ops, run_manifest

    run_root = tmp_path / "must-not-exist"

    def forbidden(*_args, **_kwargs):
        pytest.fail("retired Easy execution reached a stateful or provider-facing seam")

    monkeypatch.setattr(run_manifest, "compile_run_manifest", forbidden)
    monkeypatch.setattr(run_manifest, "bind_run_manifest", forbidden)
    monkeypatch.setattr(ops, "run_scheduler", forbidden)

    with pytest.raises(easy.EasyV6PreparationRequired) as error:
        easy.make("a site", root=str(run_root), **kwargs)

    assert error.value.code == "V6_PREPARATION_REQUIRED"
    assert not run_root.exists()


@pytest.mark.parametrize("entry", [easy._run_stage, easy._make_chunked, easy._make_single])
def test_internal_easy_execution_facades_are_fail_closed_tombstones(entry):
    with pytest.raises(easy.EasyV6PreparationRequired) as error:
        if entry is easy._run_stage:
            entry(
                None,
                None,
                label="retired",
                root_pid="pi",
                cycles=1,
                token_budget=1,
                echo=lambda *_: None,
                stop_on_survivor=False,
            )
        else:
            entry(None, None, "retired", None, 1, 1, lambda *_: None)
    assert error.value.code == "V6_PREPARATION_REQUIRED"


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
