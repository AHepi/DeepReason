"""The model-profile registry: where a model's settings come from, and the
architecture checks that keep them from coming from anywhere else.

Operator design law, 2026-08-26 (CLAUDE.md), verbatim: "There needs to be a
priority that enforces modularity. Customisation needs to be easy." — and
"enforced" means a check that can fail. Operator, 2026-09-01, on this tranche:
"Take this particular task out of the hands of the machine because we don't
really know what future LLMs settings will be?" and "Home directory only,
nothing ships."

Every test below is written to go RED on the BYPASS it names, not on a rename.

Tranche: experiments/2026-09-01-change-model-profile-registry/ (S1, S2, S3,
S4, S7).
"""

import pathlib

import pytest

from deepreason import model_profiles as mp

BLOCK = """schema: deepreason-model-profile.v1
model_id: {model_id}
measured_on: 2026-09-01
reasoning:
  documented_values: [low, high, max]
  extraction_value: {extraction}
  thinking_disablable: {disablable}
  disabling_values: []
  trace_destination: {{low: side_channel}}
"""


def _write(root: pathlib.Path, directory: str, model_id: str, *,
           extraction: str = "low", disablable: str = "false") -> pathlib.Path:
    home = root / "model-profiles" / directory
    home.mkdir(parents=True, exist_ok=True)
    path = home / "agent.md"
    path.write_text(
        "# a model\n\nprose a human wrote.\n\n"
        f"```{mp.FENCE_INFO}\n"
        + BLOCK.format(model_id=model_id, extraction=extraction, disablable=disablable)
        + "```\n"
    )
    return path


def _env(root: pathlib.Path) -> dict:
    return {"DEEPREASON_HOME": str(root)}


# --- 1: where the harness looks, and that nothing ships -------------------- #


def test_profiles_root_is_the_home_directory_and_nothing_else(tmp_path):
    """Operator, 2026-09-01: "Home directory only, nothing ships"."""

    assert mp.profiles_root(environ=_env(tmp_path)) == tmp_path / "model-profiles"


def test_the_installed_package_ships_no_profile_of_its_own(tmp_path):
    """A fresh container knows nothing about any model. That is the design.

    The bypass this forbids: a shipped default row that quietly re-introduces
    the machine's own opinion about a model the operator never described.
    """

    package = pathlib.Path(mp.__file__).parent
    documents = [
        p for p in package.rglob("*")
        if p.suffix in {".md", ".yaml", ".yml", ".json"}
    ]
    assert documents == [], documents
    # Positive anchor: the package really is where we think it is, so a moved
    # tree fails here instead of passing vacuously.
    assert (package / "registry.py").is_file()
    assert mp.installed(environ=_env(tmp_path)) == {}


# --- 2: the declared id is the key ---------------------------------------- #


def test_a_profile_resolves_by_its_declared_id_not_its_directory_name(tmp_path):
    _write(tmp_path, "whatever-the-human-called-it", "gpt-oss:120b")
    env = _env(tmp_path)
    assert mp.resolve("gpt-oss:120b", environ=env).model_id == "gpt-oss:120b"
    assert mp.resolve("whatever-the-human-called-it", environ=env) is None


def test_an_unknown_model_resolves_to_none_and_never_raises(tmp_path):
    """The all-configurations law (2026-08-12) applied to a lookup: disclose,
    never refuse. Nothing on the dispatch path may raise for a model nobody
    has described."""

    assert mp.resolve("a-model-from-2029", environ=_env(tmp_path)) is None
    assert mp.resolve("", environ=_env(tmp_path)) is None
    assert mp.resolve(None, environ=_env(tmp_path)) is None
    # Not even when the home directory does not exist at all.
    assert mp.resolve("x", environ={"DEEPREASON_HOME": str(tmp_path / "absent")}) is None


# --- 3: problems are disclosed, never silent and never fatal --------------- #


def test_an_unreadable_document_is_recorded_as_a_problem_not_swallowed(tmp_path):
    """A document with a typo must not look like a model nobody described.

    The bypass this forbids: `except Exception: continue` in the loader, which
    would make a broken document and an absent one indistinguishable — and the
    broken one is the case a human needs told about.
    """

    broken = tmp_path / "model-profiles" / "broken"
    broken.mkdir(parents=True)
    (broken / "agent.md").write_text("# no block here at all\n")
    env = _env(tmp_path)

    assert mp.resolve("anything", environ=env) is None
    fingerprint = mp.registry_fingerprint(environ=env)
    assert fingerprint["problem_count"] == 1
    problem = fingerprint["problems"][0]
    assert problem["code"] == "MODEL_PROFILE_NO_BLOCK"
    assert problem["path"].endswith("broken/agent.md")


def test_two_documents_declaring_one_id_resolve_to_neither(tmp_path):
    """Picking one silently would make the record's stamp a lie about which
    document answered. Both are recorded as a problem and the model stays
    unknown, which is the safe disposition."""

    _write(tmp_path, "first", "glm-5.3")
    _write(tmp_path, "second", "glm-5.3", extraction="high")
    env = _env(tmp_path)

    assert mp.resolve("glm-5.3", environ=env) is None
    fingerprint = mp.registry_fingerprint(environ=env)
    codes = [p["code"] for p in fingerprint["problems"]]
    assert codes == ["MODEL_PROFILE_DUPLICATE_ID"]
    assert "first" in fingerprint["problems"][0]["detail"]
    assert "second" in fingerprint["problems"][0]["detail"]


# --- 4: in-process registration, for tests and plugins -------------------- #


def test_register_is_in_process_and_writes_no_file(tmp_path):
    env = _env(tmp_path)
    profile = mp.parse_document(
        f"```{mp.FENCE_INFO}\n"
        + BLOCK.format(model_id="plugin-model", extraction="low", disablable="false")
        + "```\n"
    )
    try:
        mp.register(profile)
        assert mp.resolve("plugin-model", environ=env) is profile
        assert not (tmp_path / "model-profiles").exists()
    finally:
        mp.unregister("plugin-model")
    assert mp.resolve("plugin-model", environ=env) is None


def test_the_fingerprint_says_where_each_profile_came_from(tmp_path):
    """A run's record must be able to distinguish a document a human wrote
    from a profile some code registered."""

    _write(tmp_path, "glm-5.3", "glm-5.3")
    env = _env(tmp_path)
    registered = mp.parse_document(
        f"```{mp.FENCE_INFO}\n"
        + BLOCK.format(model_id="plugin-model", extraction="low", disablable="false")
        + "```\n"
    )
    try:
        mp.register(registered)
        fingerprint = mp.registry_fingerprint(environ=env)
    finally:
        mp.unregister("plugin-model")

    sources = {p["model_id"]: p["source"] for p in fingerprint["profiles"]}
    assert sources == {"glm-5.3": "document", "plugin-model": "registered"}
    assert fingerprint["registry"] == mp.MODEL_PROFILE_REGISTRY_VERSION
    assert fingerprint["count"] == 2
    # Identity only: no wall-clock, no counter, so two runs over the same
    # documents stamp byte-identical fingerprints (the rule
    # `module_events.py` states for every registry it carries).
    assert "at" not in fingerprint and "timestamp" not in fingerprint
    for entry in fingerprint["profiles"]:
        assert len(entry["digest"]) == 64 and entry["measured_on"]


def test_the_fingerprint_of_an_empty_registry_is_still_a_stamp(tmp_path):
    """Zero profiles is the common case under "nothing ships", and it is a
    meaningful thing to record: it says the run knew nothing about any model."""

    fingerprint = mp.registry_fingerprint(environ=_env(tmp_path))
    assert fingerprint["count"] == 0
    assert fingerprint["profiles"] == []
    assert fingerprint["registry"] == mp.MODEL_PROFILE_REGISTRY_VERSION
