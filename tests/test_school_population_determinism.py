"""Rung 3 tranche B: routing school population through the registry changed
nothing a run records."""

import json

from deepreason.capture import schools
from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.ontology import Problem, ProblemProvenance
from deepreason.scheduler.scheduler import Scheduler


# Wall-clock only. Two runs of identical work differ on these and nothing
# else, so excluding them compares every rule, id, and content address while
# staying independent of how long the machine took.
_WALL_CLOCK_EVENT_FIELDS = ("ts",)
_WALL_CLOCK_LLM_FIELDS = ("ms",)


class _BareFunctionBackend:
    """The pre-migration call shape: straight to the module-level functions."""

    def fingerprint(self) -> dict:
        return {"backend": "bare-functions-under-test"}

    def init_schools(self, harness, config):
        return schools.init_schools(harness, config)

    def roster(self, harness):
        return schools.roster(harness)

    def allocate(self, harness, problem, roster, config):
        return schools.allocate(harness, problem, roster, config)

    def reseed(self, harness, school_id, current, reason, crossover_from=None):
        return schools.reseed(harness, school_id, current, reason, crossover_from)


def _vs(*contents) -> str:
    return json.dumps(
        {"candidates": [{"content": c, "typicality": 0.5} for c in contents]}
    )


def _seed_problem(harness) -> None:
    harness.register_problem(
        Problem(
            id="pi-seed",
            description="a seed problem",
            criteria=[],
            provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
        )
    )


def _run(root, cycles=3):
    """One scheduled run against a mock provider; returns (harness, roster)."""

    harness = Harness(root)
    _seed_problem(harness)
    counter = {"n": 0}

    def generate(_prompt: str) -> str:
        counter["n"] += 1
        return _vs(f"account number {counter['n']}")

    adapter = LLMAdapter(
        {"conjecturer": MockEndpoint(generate)}, harness.blobs, retry_max=2
    )
    scheduler = Scheduler(
        harness, adapter, Config(N_SCHOOLS=2, VS_K=1, FLOOR=0, CAPTURE_W=10)
    )
    roster = dict(scheduler.schools)
    scheduler.run(cycles)
    return harness, roster


def _comparable_log(harness) -> list[dict]:
    events = []
    for event in harness.log.read():
        data = json.loads(event.model_dump_json())
        for field in _WALL_CLOCK_EVENT_FIELDS:
            data.pop(field, None)
        if isinstance(data.get("llm"), dict):
            for field in _WALL_CLOCK_LLM_FIELDS:
                data["llm"].pop(field, None)
        events.append(data)
    return events


def test_registry_path_records_exactly_what_the_bare_functions_recorded(
    tmp_path, monkeypatch
):
    """Implements R7 (rung 3): a run's outputs are byte-identical before and
    after the registry.

    Run A goes through the migrated path (`schools.active_backend()`); run B
    is built with `active_backend` patched to a backend that calls the bare
    module functions directly — the shape every caller used before this
    rung. Identical seeds and config, so any difference is the indirection's
    fault.

    NOTE the fixture: rung 3's acceptance text names
    `tests/test_attached_evidence_citation.py`'s offline no-provider
    pattern, which monkeypatches `deepreason.ops.run_scheduler` — the very
    function that constructs the `Scheduler`. That pattern therefore never
    reaches `init_schools` or `allocate`, and a byte-identity test built on
    it would pass without executing one migrated line. The mock-endpoint
    scheduler used here does construct a real `Scheduler`; the roster
    assertion below is what keeps that honest.
    """

    after_harness, after_roster = _run(tmp_path / "after")

    monkeypatch.setattr(schools, "active_backend", _BareFunctionBackend)
    before_harness, before_roster = _run(tmp_path / "before")

    # Proof the runs actually populated schools -- without this, everything
    # below is satisfied trivially by two runs that never touched the code
    # under test.
    assert before_roster and after_roster
    assert before_roster == after_roster

    assert before_harness.state.model_dump_json() == after_harness.state.model_dump_json()
    assert _comparable_log(before_harness) == _comparable_log(after_harness)


def test_the_determinism_comparison_can_actually_fail(tmp_path, monkeypatch):
    """A comparison that cannot fail proves nothing (docs_verify --audit's
    own principle). Swapping in a backend that allocates differently must
    break the equality the test above asserts."""

    class _ReversedAllocation(_BareFunctionBackend):
        def allocate(self, harness, problem, roster, config):
            return list(reversed(schools.allocate(harness, problem, roster, config)))

    after_harness, _ = _run(tmp_path / "after")

    monkeypatch.setattr(schools, "active_backend", _ReversedAllocation)
    mutated_harness, _ = _run(tmp_path / "mutated")

    assert _comparable_log(mutated_harness) != _comparable_log(after_harness)
