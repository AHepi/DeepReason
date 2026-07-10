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


def test_make_runs_and_exports_survivors(tmp_path, monkeypatch):
    """End-to-end through the real seeding and export paths; only the
    scheduler run itself is stubbed (it needs live endpoints)."""
    from deepreason import ops
    from deepreason.ontology import Interface, Provenance

    monkeypatch.setenv("FAKE_MAKE_KEY", "k")
    cfg = tmp_path / "engine.yaml"
    cfg.write_text(yaml.safe_dump({"roles": {"conjecturer": {
        "endpoint": "https://x.invalid", "model": "m",
        "api_key_env": "FAKE_MAKE_KEY"}}}))

    def fake_run(harness, config, cycles, token_budget=None, on_cycle=None):
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
                      echo=lines.append)
    pages = [p for p in paths if p.suffix == ".html"]
    assert len(pages) == 1 and pages[0].exists()
    joined = "\n".join(lines)
    assert "Your website is ready" in joined
    assert "1,234 tokens" in joined


def test_make_reports_wipeout_honestly(tmp_path, monkeypatch):
    from deepreason import ops

    monkeypatch.setenv("FAKE_MAKE_KEY", "k")
    cfg = tmp_path / "engine.yaml"
    cfg.write_text(yaml.safe_dump({"roles": {"conjecturer": {
        "endpoint": "https://x.invalid", "model": "m",
        "api_key_env": "FAKE_MAKE_KEY"}}}))
    monkeypatch.setattr(
        ops, "run_scheduler",
        lambda *a, **k: ({"survivors": 0}, None, {"logged_tokens_this_run": 7}))
    lines = []
    paths = easy.make("doomed site", out=str(tmp_path / "site"),
                      config=str(cfg), root=str(tmp_path / "r"),
                      echo=lines.append)
    assert not [p for p in paths if p.suffix == ".html"]  # README only
    joined = "\n".join(lines)
    assert "Nothing survived criticism" in joined and "--cycles" in joined


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
