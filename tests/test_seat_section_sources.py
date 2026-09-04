"""The SOURCE layer: what a brief section's content is computed from.

`seat_sections.py` holds the protocol that FORMATS a section; a plugin there
may not call the harness. Nine of the conjecturer's twenty sections need the
record to exist at all, so before this layer they were computed inside
`rules/conj.py` and handed to the renderer as strings. A source computes one
value from read access to the state and the record, is registered and
versioned like a plugin, and appends nothing.

Three claims are asserted here and each one can fail:

  1. every caller-computed slot is fed by the registered bundle, so none of
     them is still decided by editing the admission code;
  2. a source appends nothing to the record -- measured across every
     registered source, with a planted write to show the measurement bites;
  3. the one source that writes content-addressed blobs DECLARES it, and no
     other source writes anything at all.
"""

import ast
import pathlib

import pytest
from pydantic import BaseModel, ConfigDict

from deepreason.config import Config
from deepreason.llm.seat_source_plugins import (
    CONJECTURER_SEAT,
    CONJECTURER_SOURCE_BUNDLE,
    ensure_sources_seeded,
)
from deepreason.llm.seat_sources import (
    SECTION_SOURCE_REGISTRY,
    SEAT_SOURCE_BUNDLE_ENV,
    STAGE_POST_ALLOCATION,
    STAGE_POST_ALLOCATION_AFTER_ALIASES,
    STAGE_POST_ALLOCATION_CONTEXT,
    STAGE_PRE_CONTRACT,
    STAGE_RENDER,
    STAGES,
    SeatSourceBundleEntryV1,
    SeatSourceBundleV1,
    SeatSourceError,
    SectionSourceRequestV1,
    SectionSourceResultV1,
    register_seat_source_bundle,
    register_section_source,
    resolve_seat_source_bundle,
    resolve_section_source,
)
from tests.conj_pack_golden_cases import _seed


@pytest.fixture(autouse=True)
def seeded():
    ensure_sources_seeded()


# --- 1: the bundle feeds every caller-computed slot ------------------------ #


THE_NINE = {
    "frozen_evidence_context",
    "citable_evidence_context",
    "open_criticism_context",
    "capability_result_context",
    "frame_slice_context",
    "frame_crisis_context",
    "scratch_context",
    "generation_context",
    "reference_menus",
}

THE_FOUR_POST_ALLOCATION = {
    "scratch_render",
    "sealed_simulation_inputs",
    "scratch_workshop_prompt",
    "post_allocation_menus",
}


def _sources_for(stage):
    bundle = resolve_seat_source_bundle(CONJECTURER_SEAT)
    return [
        resolve_section_source(entry.source_id, entry.source_version)
        for entry in bundle.entries_for_stage(stage)
    ]


def test_the_bundle_supplies_every_caller_computed_slot():
    """The claim the tranche turns on: none of the thirteen is still computed
    by editing `rules/`. A slot dropped from the bundle fails here."""
    supplied = set()
    for stage in (STAGE_PRE_CONTRACT, STAGE_RENDER):
        supplied.update(source.supplies for source in _sources_for(stage))
    assert supplied == THE_NINE, sorted(supplied ^ THE_NINE)

    post = set()
    for stage in (
        STAGE_POST_ALLOCATION_CONTEXT,
        STAGE_POST_ALLOCATION,
        STAGE_POST_ALLOCATION_AFTER_ALIASES,
    ):
        post.update(source.supplies for source in _sources_for(stage))
    assert post == THE_FOUR_POST_ALLOCATION, sorted(post ^ THE_FOUR_POST_ALLOCATION)


def test_the_open_criticism_slot_resolves_before_the_contract_stage():
    """Not a stylistic ordering. The caller needs `discharge_enabled` before
    it builds the turn contract, because the atomic-decomposition recovery
    path builds its contract long before the pack renders."""
    assert [source.supplies for source in _sources_for(STAGE_PRE_CONTRACT)] == [
        "open_criticism_context"
    ]


def test_the_post_allocation_menus_run_after_the_alias_binding_stage():
    """The alias table is derived from the rendered pack and is bound by the
    CALLER, never by a source: it decides what a citation resolves to. The
    menus that describe those handles must therefore run in the stage after
    it."""
    assert [
        source.supplies
        for source in _sources_for(STAGE_POST_ALLOCATION_AFTER_ALIASES)
    ] == ["post_allocation_menus"]


# --- 2: selection is configuration, and never a Config field --------------- #


def test_selection_is_by_argument_or_environment_never_config():
    """Measured, not preferred. `run_manifest.py` dumps every `Config` field
    into `engine_config_json` and `qualification.py` folds that into every
    qualification subject digest, so a bundle knob on `Config` would move the
    digest of every qualification bundle in the tree."""
    fields = {name.upper() for name in Config.model_fields}
    assert SEAT_SOURCE_BUNDLE_ENV not in fields
    assert not [
        name for name in fields if "SOURCE_BUNDLE" in name or "SECTION_SOURCE" in name
    ], sorted(fields)


def test_the_environment_selects_a_bundle_without_a_restart(monkeypatch):
    other = register_seat_source_bundle(
        SeatSourceBundleV1(
            bundle_id="conj-sources.test-empty",
            entries=(),
        )
    )
    monkeypatch.setenv(SEAT_SOURCE_BUNDLE_ENV, f"{CONJECTURER_SEAT}=other-bundle")
    with pytest.raises(SeatSourceError) as unknown:
        resolve_seat_source_bundle(CONJECTURER_SEAT)
    assert unknown.value.code == "SEAT_SOURCE_BUNDLE_UNKNOWN"
    monkeypatch.setenv(SEAT_SOURCE_BUNDLE_ENV, f"{CONJECTURER_SEAT}={other.bundle_id}")
    assert resolve_seat_source_bundle(CONJECTURER_SEAT).bundle_id == other.bundle_id
    monkeypatch.delenv(SEAT_SOURCE_BUNDLE_ENV)
    assert (
        resolve_seat_source_bundle(CONJECTURER_SEAT).bundle_id
        == CONJECTURER_SOURCE_BUNDLE
    )


def test_a_malformed_assignment_is_refused_and_never_silently_ignored(monkeypatch):
    monkeypatch.setenv(SEAT_SOURCE_BUNDLE_ENV, "conjecturer")
    with pytest.raises(SeatSourceError) as error:
        resolve_seat_source_bundle(CONJECTURER_SEAT)
    assert error.value.code == "SEAT_SOURCE_BUNDLE_ASSIGNMENT_MALFORMED"


def test_an_unregistered_source_id_is_a_typed_refusal_never_a_path_lookup():
    """A source runs inside the harness WITH the harness in its hand, so the
    only thing that may introduce one is the operator."""
    with pytest.raises(SeatSourceError) as error:
        resolve_section_source("dr.src.not.registered")
    assert error.value.code == "SEAT_SOURCE_UNKNOWN"


def test_a_stage_outside_the_vocabulary_is_refused_at_construction():
    with pytest.raises(SeatSourceError) as error:
        SeatSourceBundleEntryV1(source_id="dr.src.frame_slice", stage="whenever")
    assert error.value.code == "SEAT_SOURCE_STAGE_UNKNOWN"
    assert set(STAGES) == {
        STAGE_PRE_CONTRACT,
        STAGE_RENDER,
        STAGE_POST_ALLOCATION_CONTEXT,
        STAGE_POST_ALLOCATION,
        STAGE_POST_ALLOCATION_AFTER_ALIASES,
    }


# --- 3: a source appends nothing -------------------------------------------- #


class _NoParams(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class _PlantedWriteSource:
    """A source that appends an event. Registered only inside the mutation
    test below, to show that the measurement is a measurement."""

    source_id = "dr.src.test.planted_write"
    source_version = "1.0.0"
    supplies = "planted"
    parameters_model = _NoParams
    requires: tuple[str, ...] = ()
    writes_blobs = False

    def resolve(self, request, params):
        from deepreason.ontology import Provenance

        request.harness.create_artifact(
            "a source that wrote to the record",
            provenance=Provenance(role="seed"),
        )
        return SectionSourceResultV1(supplies=self.supplies, value="written")


def _record_fingerprint(harness):
    """Three independent measurements, because one of them alone could be
    fooled: an event count misses a rewrite, a byte count misses an in-place
    edit of equal length, and a status map misses an event that moved
    nothing."""
    log_path = pathlib.Path(harness.root) / "log.jsonl"
    return (
        harness._next_seq,
        log_path.read_bytes() if log_path.exists() else b"",
        dict(harness.state.status),
    )


def _blob_fingerprint(harness):
    root = pathlib.Path(harness.root) / "blobs"
    if not root.is_dir():
        return frozenset()
    return frozenset(str(path.relative_to(root)) for path in root.rglob("*") if path.is_file())


def _drive_every_source(harness, problem, sources):
    """Call every source with the broadest legal request.

    Exceptions are swallowed on purpose: this test is not about whether a
    source can resolve on a bare harness, it is about what it leaves behind
    when it tries. A source that raised halfway through after appending would
    be exactly the failure worth catching.
    """
    request = SectionSourceRequestV1(
        harness=harness,
        config=Config(),
        problem=problem,
        inputs={"problem_id": problem.id, "active_v5": False, "active_v6": False},
    )
    for source in sources:
        try:
            source.resolve(request, source.parameters_model())
        except Exception:  # noqa: BLE001 - the point is what it left behind
            pass


def _assert_appends_nothing(harness, problem, sources):
    before = _record_fingerprint(harness)
    _drive_every_source(harness, problem, sources)
    assert _record_fingerprint(harness) == before, (
        "a section source appended to the record; a source may READ the log "
        "and may never write to it"
    )


def test_no_registered_source_appends_to_the_record(tmp_path):
    """R5's clause, measured over every source the tree ships."""
    problem, harness, _ = _seed(tmp_path)
    _assert_appends_nothing(
        harness, problem, list(SECTION_SOURCE_REGISTRY.values())
    )


def test_the_never_appends_measurement_goes_red_on_a_planted_write(tmp_path):
    """The mutation proof. Without this, the test above would pass equally
    well if `_record_fingerprint` measured nothing at all."""
    problem, harness, _ = _seed(tmp_path)
    planted = _PlantedWriteSource()
    with pytest.raises(AssertionError) as failure:
        _assert_appends_nothing(harness, problem, [planted])
    assert "may never write to it" in str(failure.value)


def test_only_a_declaring_source_writes_blobs(tmp_path):
    """One source writes, and it says so. `pack_dossier` must materialise the
    excerpts it selected before its receipt can name them; a blob put is keyed
    by the hash of its own bytes, appends no event and moves no digest. Every
    other source writes nothing at all, and an undeclared write fails here."""
    problem, harness, _ = _seed(tmp_path)
    declaring = [
        source
        for source in SECTION_SOURCE_REGISTRY.values()
        if getattr(source, "writes_blobs", False)
    ]
    assert [source.source_id for source in declaring] == [
        "dr.src.frozen_evidence"
    ], [source.source_id for source in declaring]

    silent = [
        source
        for source in SECTION_SOURCE_REGISTRY.values()
        if not getattr(source, "writes_blobs", False)
    ]
    before = _blob_fingerprint(harness)
    _drive_every_source(harness, problem, silent)
    assert _blob_fingerprint(harness) == before, (
        "a source that does not declare writes_blobs put a file in the blob "
        "store"
    )


# --- 4: the admission code computes no section ----------------------------- #


PACK_SECTION_TYPES = {
    "PackSection",
    "PackIR",
    "AllocatedPack",
    "SectionRenderV1",
    "SectionRequestV1",
    "allocate_pack",
    "_pack_section",
    "_allocate_sections",
    "approximate_tokens",
}

# The nine computations that used to live in `conj`. Each one is a function
# whose RESULT is a section's content; a call to any of them from the
# admission code means a section is being computed there again.
SECTION_CONTENT_CALLS = {
    "render_dossier_pack",
    "pack_dossier",
    "citable_legend",
    "render_frame_slice_context",
    "render_frame_crisis_context",
    "render_open_criticism_context",
    "menu_renders_for",
    "render_v6_conjecture_context",
}


def _conj_source():
    return pathlib.Path("src/deepreason/rules/conj.py").read_text()


def _imported_names(tree):
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names.update(alias.asname or alias.name for alias in node.names)
    return names


def _called_names(tree):
    names = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        function = node.func
        if isinstance(function, ast.Name):
            names.add(function.id)
        elif isinstance(function, ast.Attribute):
            names.add(function.attr)
    return names


def _assert_no_pack_section_type(source):
    tree = ast.parse(source)
    imported = _imported_names(tree) & PACK_SECTION_TYPES
    assert not imported, sorted(imported)
    constructed = _called_names(tree) & PACK_SECTION_TYPES
    assert not constructed, sorted(constructed)


def _assert_no_section_content_call(source):
    tree = ast.parse(source)
    called = _called_names(tree) & SECTION_CONTENT_CALLS
    assert not called, sorted(called)
    imported = _imported_names(tree) & SECTION_CONTENT_CALLS
    assert not imported, sorted(imported)


def test_the_admission_code_neither_imports_nor_builds_a_pack_section():
    """R8. `rules/conj.py` used to import `AllocatedPack` and re-wrap the pack
    four times; the re-wraps moved to the runner with the insertions that
    needed them."""
    _assert_no_pack_section_type(_conj_source())


def test_the_admission_code_computes_no_section_content():
    """The half that bites. A pack-section TYPE was never imported here; what
    `conj` did was compute the nine contents and hand them over as strings, so
    a check on the types alone would have passed before this tranche too."""
    _assert_no_section_content_call(_conj_source())


@pytest.mark.parametrize(
    "planted, assertion",
    [
        ("AllocatedPack(pack)", _assert_no_pack_section_type),
        ("render_frame_slice_context(harness, problem_id)",
         _assert_no_section_content_call),
        ("citable_legend(blocks, harness.blobs)",
         _assert_no_section_content_call),
        ("reference_menu.menu_renders_for(contract, binding)",
         _assert_no_section_content_call),
    ],
)
def test_the_no_section_checks_go_red_on_a_planted_call(planted, assertion):
    """The mutation proof for R9. Each check is fed the real file with one
    call put back; a check that could not fail is not a check."""
    planted_source = (
        _conj_source()
        + f"\n\ndef _planted(pack, harness, problem_id, blocks, contract, binding):\n"
        f"    return {planted}\n"
    )
    with pytest.raises(AssertionError):
        assertion(planted_source)


# --- 5: the static half of the never-appends clause ------------------------ #

# Every name in the tree by which a source could reach the record. The
# dynamic measurement above cannot drive the frozen-evidence path without a
# full v6 run fixture, so the paths it cannot reach are covered statically.
RECORD_WRITING_CALLS = {
    "create_artifact",
    "register_problem",
    "append",
    "commit_dossier_pack_receipt",
    "record_dossier_pack_receipt",
    "record_discharges",
    "activate_contract_decomposition",
    "apply_event",
}


def _source_modules():
    return [
        pathlib.Path("src/deepreason/llm/seat_source_plugins.py"),
        pathlib.Path("src/deepreason/llm/seat_sources.py"),
    ]


def _assert_no_record_write(source):
    """Flag a record-writing verb only when its RECEIVER is the record.

    `lines.append(...)` builds a string and `blocks.append(...)` builds a
    tuple; neither is a write to anything. What would be a write is the same
    verb aimed at the harness or its log, so the receiver is part of the
    pattern rather than the verb alone.
    """

    offenders = []
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Call):
            continue
        function = node.func
        if isinstance(function, ast.Name) and function.id in RECORD_WRITING_CALLS:
            offenders.append(function.id)
        elif isinstance(function, ast.Attribute) and function.attr in RECORD_WRITING_CALLS:
            receiver = ast.unparse(function.value)
            if "harness" in receiver or receiver.endswith("log"):
                offenders.append(ast.unparse(function))
    assert not offenders, sorted(set(offenders))


def test_no_source_module_reaches_a_record_writing_api():
    """The clause stated where the dynamic test cannot go: the frozen-evidence
    source needs a full v6 run to resolve at all, and its `pack_dossier` call
    sits beside `commit_dossier_pack_receipt` in the code it moved out of. The
    commit stayed with the caller, and this is what says so."""
    for path in _source_modules():
        _assert_no_record_write(path.read_text())


@pytest.mark.parametrize("planted", sorted(RECORD_WRITING_CALLS))
def test_the_static_never_appends_check_goes_red_on_a_planted_write(planted):
    planted_source = (
        pathlib.Path("src/deepreason/llm/seat_source_plugins.py").read_text()
        + f"\n\ndef _planted(harness, value):\n    return harness.{planted}(value)\n"
    )
    with pytest.raises(AssertionError):
        _assert_no_record_write(planted_source)
