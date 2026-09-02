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


# --- 5: the emission leg reads the document, never a constant -------------- #
#
# S2/S3. The defect these replace: `llm/providers.py` carried
# `REASONING_OFF = "none"` and `llm/split.py:163` sent it on every emission leg
# of every model. On glm-5.3 that value does not stop the thinking, it stops
# the SEPARATION -- 0/8 clean content at `none` against 8/8 at `low` -- so the
# trace landed in `message.content`, the 512-token leg was cut before any JSON,
# and the cap ratchet shrank the budget until the seat exhausted. Three runs.


def _facts(**overrides):
    body = BLOCK.format(
        model_id=overrides.pop("model_id", "glm-5.3"),
        extraction=overrides.pop("extraction", "low"),
        disablable=overrides.pop("disablable", "false"),
    )
    return mp.parse_document(f"```{mp.FENCE_INFO}\n{body}```\n")


def test_the_extraction_leg_sends_what_the_document_declares(tmp_path):
    from deepreason.llm.split import plan_split

    plan = plan_split(
        mode="on",
        ceiling=4096,
        extraction_tokens=512,
        provider="ollama",
        reasoning="high",
        profile=_facts(extraction="low"),
    )
    assert plan.armed and plan.extract_reasoning == "low"

    other = plan_split(
        mode="on",
        ceiling=4096,
        extraction_tokens=512,
        provider="ollama",
        reasoning="high",
        profile=_facts(extraction="none"),
    )
    # Same code, same call, different document -> different value on the wire.
    # That is the whole modularity claim, made falsifiable.
    assert other.extract_reasoning == "none"


def test_a_document_may_declare_that_the_knob_is_omitted(tmp_path):
    """`extraction_value: null` is a DECLARATION ("send nothing"), distinct
    from a document that says nothing about reasoning at all."""

    from deepreason.llm.split import plan_split

    body = BLOCK.format(model_id="q", extraction="null", disablable="true")
    profile = mp.parse_document(f"```{mp.FENCE_INFO}\n{body}```\n")
    plan = plan_split(
        mode="on", ceiling=4096, extraction_tokens=512,
        provider="ollama", reasoning="high", profile=profile,
    )
    assert plan.armed and plan.extract_reasoning is None


def test_plan_split_requires_a_profile_rather_than_defaulting(tmp_path):
    """No default, deliberately: a caller that forgets the profile must get a
    TypeError, never the old guessing behaviour silently restored."""

    from deepreason.llm.split import plan_split

    with pytest.raises(TypeError) as caught:
        plan_split(
            mode="on", ceiling=4096, extraction_tokens=512,
            provider="ollama", reasoning="high",
        )
    assert "profile" in str(caught.value)


def test_an_unknown_model_stands_the_split_down_and_says_why(tmp_path):
    """R2, the operator's own question: "Would this work for all unknown models
    as well?" Under "nothing ships" this is the DEFAULT path, not an edge."""

    from deepreason.llm.split import NOTICE_MODEL_PROFILE_MISSING, plan_split

    plan = plan_split(
        mode="on", ceiling=4096, extraction_tokens=512,
        provider="ollama", reasoning="high", profile=None,
    )
    assert not plan.armed
    assert plan.extract_reasoning is None
    assert plan.notice == NOTICE_MODEL_PROFILE_MISSING
    assert plan.disclosed is True


def test_an_unknown_model_is_silent_under_auto_and_disclosed_under_on(tmp_path):
    """`disclosed` exists so a constant string is not stamped on every attempt
    of every run (llm/split.py's own rule for a seat that does not think).
    Nothing ships, so under `auto` that would be EVERY attempt of EVERY run."""

    from deepreason.llm.split import NOTICE_MODEL_PROFILE_MISSING, plan_split

    auto = plan_split(
        mode="auto", ceiling=4096, extraction_tokens=512,
        provider="ollama", reasoning=None, profile=None,
    )
    assert not auto.armed
    assert auto.notice == NOTICE_MODEL_PROFILE_MISSING
    assert auto.disclosed is False


def test_a_profile_silent_about_reasoning_also_stands_down(tmp_path):
    from deepreason.llm.split import (
        NOTICE_PROFILE_DECLARES_NO_REASONING,
        plan_split,
    )

    silent = mp.parse_document(
        f"```{mp.FENCE_INFO}\nschema: deepreason-model-profile.v1\n"
        "model_id: quiet\nmeasured_on: 2026-09-01\n```\n"
    )
    plan = plan_split(
        mode="on", ceiling=4096, extraction_tokens=512,
        provider="ollama", reasoning="high", profile=silent,
    )
    assert not plan.armed and plan.notice == NOTICE_PROFILE_DECLARES_NO_REASONING


def test_a_model_that_cannot_stop_thinking_still_splits_and_discloses(tmp_path):
    """glm-5.3's case. `low` gives clean content, so the split is worth having;
    the leg still thinks, so the record says so. Disclose, never refuse."""

    from deepreason.llm.split import NOTICE_THINKING_NOT_DISABLABLE, plan_split

    plan = plan_split(
        mode="on", ceiling=4096, extraction_tokens=512,
        provider="ollama", reasoning="max",
        profile=_facts(extraction="low", disablable="false"),
    )
    assert plan.armed and plan.extract_reasoning == "low"
    assert plan.notice == NOTICE_THINKING_NOT_DISABLABLE and plan.disclosed


def test_auto_mode_asks_the_document_whether_the_seat_already_thinks(tmp_path):
    """The deeper form of the same defect. `reasoning_disabled("none")` was a
    per-MODEL claim decided by a per-VOCABULARY constant, and on glm-5.3 it is
    FALSE: `none` does not disable thinking there. Only the document knows."""

    from deepreason.llm.split import NOTICE_NOT_A_REASONING_SEAT, plan_split

    body = BLOCK.format(model_id="honest", extraction="low", disablable="true")
    body = body.replace("disabling_values: []", "disabling_values: [none]")
    disables = mp.parse_document(f"```{mp.FENCE_INFO}\n{body}```\n")

    out_of_scope = plan_split(
        mode="auto", ceiling=4096, extraction_tokens=512,
        provider="ollama", reasoning="none", profile=disables,
    )
    assert not out_of_scope.armed
    assert out_of_scope.notice == NOTICE_NOT_A_REASONING_SEAT

    # Same configured value, a model whose document says it does NOT disable:
    # the seat is still a thinking seat and the split still applies.
    still_thinks = plan_split(
        mode="auto", ceiling=4096, extraction_tokens=512,
        provider="ollama", reasoning="none",
        profile=_facts(extraction="low", disablable="false"),
    )
    assert still_thinks.armed


# --- 6: the constant is gone, and cannot come back ------------------------ #


def test_the_hard_coded_off_token_is_absent_from_the_whole_tree():
    """The bypass this forbids: any reintroduction of a repo-wide "off" token
    that an emission leg could reach for instead of asking the document.

    Bound by AST and not by grep, deliberately. A string search would be
    satisfied by deleting the prose that EXPLAINS the retirement -- and
    `docs/map/SCHEMA.md` requires a Traps entry naming a fixed defect to be
    rewritten in place, never deleted, so the name must survive in prose while
    being absent from the code. Binding the symbol is also check-rule 2 from
    that document: never bind a guard by its message string alone.
    """

    import ast

    root = pathlib.Path(__file__).resolve().parent.parent
    scanned = 0
    offenders = []
    for path in sorted((root / "src").rglob("*.py")):
        scanned += 1
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            named = None
            if isinstance(node, ast.Name):
                named = node.id
            elif isinstance(node, ast.alias):
                named = node.asname or node.name
            elif isinstance(node, ast.FunctionDef):
                named = node.name
            elif isinstance(node, ast.Attribute):
                named = node.attr
            if named in {"REASONING_OFF", "reasoning_disabled"}:
                offenders.append(f"{path.relative_to(root)}:{getattr(node, 'lineno', '?')}")
    assert offenders == [], offenders
    # Positive anchors: a moved or renamed tree fails here rather than passing
    # vacuously on an empty scan (docs/map/SCHEMA.md check-rule 1), and the
    # scanner itself is proven able to see a name of this shape.
    assert scanned > 150, scanned
    providers = root / "src" / "deepreason" / "llm" / "providers.py"
    assert providers.is_file()
    live = {
        node.name
        for node in ast.walk(ast.parse(providers.read_text(encoding="utf-8")))
        if isinstance(node, ast.FunctionDef)
    }
    assert "reasoning_body" in live and "reasoning_knob_available" in live, live


# --- 7: the run's record says which documents built it -------------------- #
#
# S4. `ModuleFingerprintV1`'s own docstring declares this extension point:
# "`registry` names the registry that resolved it, so further registries can be
# stamped later WITHOUT A SCHEMA CHANGE". So this costs no frozen surface: no
# manifest field, no compile notice, no new event type. Measured, not assumed —
# `experiments/2026-09-01-change-model-profile-registry/PRICE_NOTICE_ROAD.txt`
# shows one added compile notice moving both the manifest sha and the
# qualification subject digest, which is the road this replaces.


def _stamp(tmp_path, environ):
    """Drive `Scheduler._record_module_fingerprints` against a real Harness.

    Called unbound on a stub carrying only the two attributes it reads, so the
    test exercises the stamping logic itself rather than a whole scheduler
    boot — and so it fails if that logic starts reaching for anything else.
    """

    import os

    from deepreason.harness import Harness
    from deepreason.module_events import recorded_module_fingerprints
    from deepreason.scheduler.scheduler import Scheduler

    harness = Harness(tmp_path / "run")

    class _Stub:
        _module_fingerprints_recorded = False

    stub = _Stub()
    stub.harness = harness
    previous = os.environ.get("DEEPREASON_HOME")
    os.environ["DEEPREASON_HOME"] = environ["DEEPREASON_HOME"]
    try:
        Scheduler._record_module_fingerprints(stub)
    finally:
        if previous is None:
            os.environ.pop("DEEPREASON_HOME", None)
        else:
            os.environ["DEEPREASON_HOME"] = previous
    return recorded_module_fingerprints(Harness(tmp_path / "run", read_only=True))


def test_record_stamp_names_the_model_profile_registry(tmp_path):
    home = tmp_path / "home"
    _write(home, "glm-5.3", "glm-5.3", extraction="low")
    stamps = _stamp(tmp_path, _env(home))

    assert len(stamps) == 1
    registries = [module.registry for module in stamps[0].modules]
    # The school-population row is untouched; the new one sits beside it.
    assert "school-population" in registries
    assert "model-profiles" in registries

    row = next(m for m in stamps[0].modules if m.registry == "model-profiles")
    assert row.module_id == mp.MODEL_PROFILE_REGISTRY_VERSION
    assert row.fingerprint["count"] == 1
    assert row.fingerprint["profiles"][0]["model_id"] == "glm-5.3"
    assert len(row.fingerprint["profiles"][0]["digest"]) == 64
    assert len(row.fingerprint_sha256) == 64


def test_record_stamp_of_an_empty_registry_is_still_recorded(tmp_path):
    """Under "nothing ships" this is the common case, and it is the
    `model-profile-missing` disclosure for the whole run: the record says, in
    typed form, that this run knew nothing about any model."""

    stamps = _stamp(tmp_path, _env(tmp_path / "empty-home"))
    row = next(m for m in stamps[0].modules if m.registry == "model-profiles")
    assert row.fingerprint["count"] == 0
    assert row.fingerprint["profiles"] == []


def test_the_stamp_carries_identity_only_so_two_runs_agree(tmp_path):
    """`module_events.py`'s own rule: "no wall-clock and no counter, so two
    runs built by the same modules stamp byte-identical payloads"."""

    home = tmp_path / "home"
    _write(home, "glm-5.3", "glm-5.3", extraction="low")
    first = _stamp(tmp_path / "a", _env(home))
    second = _stamp(tmp_path / "b", _env(home))
    row_a = next(m for m in first[0].modules if m.registry == "model-profiles")
    row_b = next(m for m in second[0].modules if m.registry == "model-profiles")
    assert row_a.fingerprint_sha256 == row_b.fingerprint_sha256

    # And it moves when a document moves, or it would be recording nothing.
    _write(home, "glm-5.3", "glm-5.3", extraction="high")
    third = _stamp(tmp_path / "c", _env(home))
    row_c = next(m for m in third[0].modules if m.registry == "model-profiles")
    assert row_c.fingerprint_sha256 != row_a.fingerprint_sha256


def test_an_unreadable_document_reaches_the_record(tmp_path):
    """A run that could not read a document must say so on its own record.

    The record is the only admissible evidence; a document that failed to load
    and left no trace is indistinguishable from a model nobody described.
    """

    home = tmp_path / "home"
    broken = home / "model-profiles" / "typo"
    broken.mkdir(parents=True)
    (broken / "agent.md").write_text("# a human meant to declare something\n")

    stamps = _stamp(tmp_path, _env(home))
    row = next(m for m in stamps[0].modules if m.registry == "model-profiles")
    assert row.fingerprint["problem_count"] == 1
    assert row.fingerprint["problems"][0]["code"] == "MODEL_PROFILE_NO_BLOCK"


# --- 8: the architecture checks (S7) -------------------------------------- #
#
# Operator design law, 2026-08-26: "There needs to be a priority that enforces
# modularity. Customisation needs to be easy." Enforced means a check that can
# fail, so each of these is written against the BYPASS it forbids.


def test_adding_a_model_needs_no_source_edit(tmp_path):
    """The modularity claim itself, made falsifiable.

    The bypass this forbids: a registry where describing a new model means
    editing a table, a Literal, an enum, or any other file under src/.
    """

    root = pathlib.Path(mp.__file__).resolve().parent.parent.parent
    before = {
        path: path.read_bytes()
        for path in sorted(root.rglob("*.py"))
        if "__pycache__" not in str(path)
    }
    assert len(before) > 150, len(before)

    # A model id that appears nowhere in the tree, described from scratch.
    novel = "a-model-nobody-has-heard-of:2029"
    _write(tmp_path, "novel", novel, extraction="whatever-it-takes")
    env = _env(tmp_path)

    resolved = mp.resolve(novel, environ=env)
    assert resolved is not None
    assert resolved.reasoning.extraction_value == "whatever-it-takes"

    # And it reaches the wire through the ordinary interface, unedited.
    from deepreason.llm.split import plan_split

    plan = plan_split(
        mode="on", ceiling=4096, extraction_tokens=512,
        provider="ollama", reasoning="high", profile=resolved,
    )
    assert plan.armed and plan.extract_reasoning == "whatever-it-takes"

    after = {
        path: path.read_bytes()
        for path in sorted(root.rglob("*.py"))
        if "__pycache__" not in str(path)
    }
    assert before == after, "describing a model touched the source tree"


def test_no_consumer_reaches_past_the_declared_interface():
    """`deepreason.model_profiles` is the only legal import surface.

    Resolved through the AST with import LEVELS handled, because a substring
    grep walks straight past `from ..model_profiles.registry import ...` —
    docs/map/SCHEMA.md check-rule 3, which was found by falsification on a
    seam's own core dependency claim.
    """

    import ast

    root = pathlib.Path(mp.__file__).resolve().parent
    tree_root = root.parent
    offenders = []
    scanned = 0
    for path in sorted(tree_root.rglob("*.py")):
        if "__pycache__" in str(path) or path.is_relative_to(root):
            continue
        scanned += 1
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if node.level:
                    # Resolve the relative import to an absolute dotted path.
                    package = path.parent
                    for _ in range(node.level - 1):
                        package = package.parent
                    prefix = ".".join(
                        ["deepreason", *package.relative_to(tree_root).parts]
                    )
                    module = f"{prefix}.{module}" if module else prefix
                if module.startswith("deepreason.model_profiles."):
                    offenders.append(f"{path.relative_to(tree_root)}:{node.lineno}")
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith("deepreason.model_profiles."):
                        offenders.append(f"{path.relative_to(tree_root)}:{node.lineno}")
    assert offenders == [], offenders
    # Positive anchors: the scan really ran, and it really can see an import
    # of this shape (the package's own __init__ uses exactly that form).
    assert scanned > 150, scanned
    init = (root / "__init__.py").read_text(encoding="utf-8")
    assert "from deepreason.model_profiles.registry import" in init


def test_no_module_specific_reasoning_literal_survives_in_the_llm_boundary():
    """`llm/` may know what a provider's WIRE takes; never what a model does.

    The bypass this forbids: a model id, a model table, or a reasoning value
    chosen by anything but the document, reappearing in the two files that
    used to carry one.
    """

    import ast

    root = pathlib.Path(mp.__file__).resolve().parent.parent
    known_models = {
        "glm-5.2", "glm-5.3", "deepseek-v4-pro:0813", "qwen3.5:397b",
        "gpt-oss:120b",
    }
    offenders = []
    for name in ("llm/split.py", "llm/providers.py"):
        path = root / name
        tree = ast.parse(path.read_text(encoding="utf-8"))
        docstrings = {
            id(node.body[0].value)
            for node in ast.walk(tree)
            if isinstance(node, (ast.Module, ast.FunctionDef, ast.ClassDef))
            and node.body
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Constant)
        }
        for node in ast.walk(tree):
            if not isinstance(node, ast.Constant) or id(node) in docstrings:
                continue
            if isinstance(node.value, str) and node.value in known_models:
                offenders.append(f"{name}:{node.lineno}: {node.value!r}")
    assert offenders == [], offenders

    # Positive anchor: the scanner can see a string constant in these files,
    # so an empty offender list means "none present", not "none looked at".
    split_source = (root / "llm" / "split.py").read_text(encoding="utf-8")
    assert "split-budget:" in split_source
