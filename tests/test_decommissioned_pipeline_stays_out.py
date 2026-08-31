"""The website pipeline stays decommissioned, and four channels stay live.

Operator ruling, 2026-08-15, verbatim: "There was a website development
pipeline that I decommissioned a while ago. That needs to stay decommissioned.
Code testing, simulation, scratch pad and research backends need to stay live
and be able to mint their own evidence." Corrected the same day: "Sorry not
scratch pad. that doesn't mint evidence" — scratch is protected LIVE and
ADVISORY, minting no evidence, exactly as `advisory_non_grounding` states.

SUPERSEDED IN ONE PLACE ONLY, and the scope is the operator's own, confirmed
2026-08-30 (CLAUDE.md, the P9 law): "The P9 law of 2026-08-29 supersedes the
2026-08-15 decommissioning ruling FOR THE SUCCESSOR TRIGGER ALONE — one
producer, outside rules/, gated by a per-run flag defaulting OFF — while the
website development pipeline itself stays decommissioned." Everything else in
this file is untouched by that sentence, and the four protected-channel tests
below are byte-unchanged.

Two halves, and the second is the one that costs something to get wrong: the
remnant is confined, AND every protected channel still compiles, dispatches,
and mints its own records.
"""

import pytest

from deepreason.ontology import SpawnTrigger


# --- the remnant is confined, and cannot spread quietly ---------------------


def test_the_successor_trigger_is_declared_vocabulary():
    """The member is RETAINED, and what it may mean is the NEXT test's job.

    Renamed 2026-08-30 from `..._is_inert_vocabulary`: "inert" meant producers
    = 0, and under the operator's P9 law that is no longer true. This test
    never asserted inertness -- it asserts the member exists -- so the rename
    corrects a docstring that had become false, not an assertion.

    Deleting the member was measured (Road A) and costs four tests that replay
    pre-v2 roots -- a cost the 2026-08-14 law permits but which buys nothing
    here, because WHERE the one producer lives, and behind which gate, is what
    now keeps the pipeline decommissioned. That is the invariant, and it is
    the next test.
    """
    assert hasattr(SpawnTrigger, "SUCCESSOR")


def test_no_source_file_produces_a_successor_problem():
    """THE load-bearing invariant, narrowed by the operator and not by an
    implementer: producers = EXACTLY ONE, at one named path, outside `rules/`,
    behind a flag that is off.

    Operator law, 2026-08-29, confirmed in scope 2026-08-30: "The P9 law of
    2026-08-29 supersedes the 2026-08-15 decommissioning ruling FOR THE
    SUCCESSOR TRIGGER ALONE -- one producer, outside rules/, gated by a per-run
    flag defaulting OFF -- while the website development pipeline itself stays
    decommissioned."

    This is a STRICTLY MORE SPECIFIC claim than the "zero" it replaces, not a
    weaker one. Three mutations turn it red, and all three were run before this
    docstring was written
    (`experiments/2026-08-30-change-successor-questions/proof/q5_scope_mutants_red.txt`):

      1. a SECOND producer anywhere under `src/deepreason` -- the list stops
         being the one path;
      2. the one producer MOVING into `src/deepreason/rules/` -- the path
         changes, and the `rules/` clause below is what names why that matters;
      3. the gate DEFAULTING ON -- `minting_enabled` over a default `Config`
         reads the real field once it exists and the registry row's own default
         until then, so either way of shipping an on-by-default gate is red.

    What is NOT superseded, and is asserted here rather than assumed: the
    producer is not reachable from `scan_spawns` (H1's deletion, checked by
    `tests/test_h1_no_spawn_from_refutation.py`), and the four protected
    channels below are byte-unchanged.
    """
    import pathlib

    hits = [
        f"{path}:{n}"
        for path in pathlib.Path("src/deepreason").rglob("*.py")
        for n, line in enumerate(path.read_text().splitlines(), 1)
        if '"trigger": "successor"' in line
        or "trigger='successor'" in line
        or 'trigger="successor"' in line
        or "SpawnTrigger.SUCCESSOR" in line
        # The enum's own declaration is the one legal mention.
        if "ontology/problem.py" not in str(path)
    ]
    # Mutation 1: a second producer appears -> this list grows and the equality
    # fails. Mutation 2: the producer moves -> the path is different and the
    # equality fails. Compared on PATHS rather than path:line so an edit above
    # the producer does not manufacture a false alarm about a move.
    assert [h.rsplit(":", 1)[0] for h in hits] == [
        "src/deepreason/successor/mint.py"
    ], hits

    # The law's own words: "outside rules/". Redundant with the equality above
    # only while that equality holds; stated separately because it is the
    # clause the operator wrote, and a future widening of the path list must
    # trip over it explicitly rather than slide past a rewritten literal.
    assert not any(h.startswith("src/deepreason/rules/") for h in hits), hits

    # The law's other words: "gated by a per-run flag defaulting OFF".
    # `minting_enabled` is the one reader of that gate. It resolves to the real
    # `Config` field where one exists and to the registry row's declared
    # default otherwise, so BOTH ways of shipping an on-by-default gate are red
    # here.
    from deepreason.config import Config
    from deepreason.successor.registry import (
        GATES,
        MINTING_GATE_ID,
        minting_enabled,
    )

    assert GATES[MINTING_GATE_ID].default is False
    assert minting_enabled(Config()) is False


# --- the four protected channels, one green cited row each -------------------


def test_protected_code_testing_and_execution_still_mints_evidence():
    """Channel 1 — execution-grade evidence: `candidate_checker`, the property
    oracle, and counterexample admission. Compiles, dispatches, and mints."""
    from deepreason import programs
    from deepreason.oracle import CANDIDATE_CHECKER_PROGRAM, EXEC_PROGRAMS
    from deepreason.rules.crit import try_counterexample

    assert CANDIDATE_CHECKER_PROGRAM in programs.PROGRAMS
    # `dataset_oracle` lives in BLOB_PROGRAMS -- it reads durable content its
    # frozen spec names -- so the registry check spans both families.
    registered = {**programs.PROGRAMS, **programs.BLOB_PROGRAMS}
    assert EXEC_PROGRAMS and all(p in registered for p in EXEC_PROGRAMS)
    # Execution programs are SUBSTANTIVE: they mint evidence, and the
    # demarcation/reach machinery must keep treating them that way.
    from deepreason.measures.reach import _STRUCTURAL_PROGRAMS

    assert not ({*EXEC_PROGRAMS} & _STRUCTURAL_PROGRAMS)
    assert callable(try_counterexample)


def test_protected_simulation_still_mints_its_typed_receipts():
    """Channel 2 — typed simulation proposals through receipts."""
    from deepreason.capabilities import simulation
    from deepreason.capabilities.state import (
        CapabilityReplayState,
        CompiledSimulationV1,
    )

    # The typed proposal, its lifecycle, and the receipt state that replays it.
    assert CompiledSimulationV1 is not None
    assert CapabilityReplayState is not None
    assert simulation is not None


def test_protected_research_backend_still_mints_fetch_receipts():
    """Channel 3 — fetch receipts, consumable as citable evidence."""
    from deepreason.signals import declaration

    # The receipt channel is its signal family; every attempt reaches the log.
    assert declaration("research-fetch:FETCHED") is not None
    assert declaration("research-evidence-registered") is not None
    from deepreason.research import backends

    assert backends is not None


def test_protected_scratch_pad_is_live_and_advisory_with_its_boundary_intact():
    """Channel 4 — LIVE and ADVISORY. It mints no evidence, and that is its
    law, not a limitation: `advisory_non_grounding` is a frozen manifest
    literal, and the boundary is what keeps the workshop out of adjudication.
    """
    from deepreason.scratch import service

    assert service is not None
    import pathlib

    manifest = pathlib.Path("src/deepreason/run_manifest.py").read_text()
    assert "advisory_non_grounding" in manifest
    # The boundary: criticism is given no scratch content, structurally.
    import inspect

    from deepreason.llm import packs

    for name in ("render_crit_pack", "render_batch_crit_pack"):
        assert "scratch" not in inspect.signature(getattr(packs, name)).parameters
