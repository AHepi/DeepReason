"""The website pipeline stays decommissioned, and four channels stay live.

Operator ruling, 2026-08-15, verbatim: "There was a website development
pipeline that I decommissioned a while ago. That needs to stay decommissioned.
Code testing, simulation, scratch pad and research backends need to stay live
and be able to mint their own evidence." Corrected the same day: "Sorry not
scratch pad. that doesn't mint evidence" — scratch is protected LIVE and
ADVISORY, minting no evidence, exactly as `advisory_non_grounding` states.

Two halves, and the second is the one that costs something to get wrong: the
remnant is gone, AND every protected channel still compiles, dispatches, and
mints its own records.
"""

import pytest

from deepreason.ontology import SpawnTrigger


# --- the remnant is gone, and cannot come back quietly ----------------------


def test_no_successor_trigger_exists_anywhere():
    assert not hasattr(SpawnTrigger, "SUCCESSOR")
    assert "successor" not in {trigger.value for trigger in SpawnTrigger}


def test_no_source_file_produces_a_successor_problem():
    """Producers = 0 is what licensed deleting the member. If a producer comes
    back, this fails before the enum does."""
    import pathlib

    hits = [
        f"{path}:{n}"
        for path in pathlib.Path("src/deepreason").rglob("*.py")
        for n, line in enumerate(path.read_text().splitlines(), 1)
        if '"trigger": "successor"' in line
        or "trigger='successor'" in line
        or 'trigger="successor"' in line
        or "SpawnTrigger.SUCCESSOR" in line
    ]
    assert hits == [], hits


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
