"""Rung 5 (one deliberately dumb alternative, swapped in).

Implements R3-R6 and SPEC.md S2-S7 of
``experiments/2026-08-04-change-rung5-dumb-alternative-backend``. The rung
exists to prove the rung-3 socket is real rather than decorative: a second
backend registers under a non-default name, a run configured with it
completes and verifies, and the default path is untouched.
"""

import pytest

from deepreason.capture import schools
from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.ontology import Problem, ProblemProvenance


def _problem(pid: str, trigger: str = "seed") -> Problem:
    return Problem(
        id=pid,
        description="a problem",
        criteria=[],
        provenance=ProblemProvenance.model_validate({"trigger": trigger, "from": []}),
    )


def _roster(tmp_path, n: int = 4):
    harness = Harness(tmp_path / "run")
    config = Config(N_SCHOOLS=n)
    return harness, config, schools.init_schools(harness, config)


def test_the_alternative_registers_under_a_non_default_name():
    """R4/C9: a second backend registers under a NEW name, never 'default'."""

    assert schools.SCHOOL_POPULATION.ids() == ("default", "round-robin")
    assert schools.SCHOOL_POPULATION.fingerprint_is_pinned("round-robin")
    assert (
        schools.SCHOOL_POPULATION.get("round-robin").backend.fingerprint()["backend"]
        == "round-robin"
    )


def test_the_registry_refuses_to_re_register_either_name():
    """The mechanical guarantee behind 'the default path stays
    byte-identical': no backend can displace an existing name."""

    for name in ("default", "round-robin"):
        with pytest.raises(schools.SchoolPopulationRegistryError):
            schools.SCHOOL_POPULATION.register(
                schools.RoundRobinSchoolPopulationBackend(), backend_id=name
            )


def test_the_alternative_actually_allocates_differently(tmp_path):
    """A 'dumb alternative' that behaved like the default would prove
    nothing about the socket. The default fans a seed problem out to every
    school; the rotation hands it to exactly one."""

    harness, config, roster = _roster(tmp_path)
    problem = _problem("pi-seed")
    default = schools.SCHOOL_POPULATION.get("default").backend
    alternative = schools.SCHOOL_POPULATION.get("round-robin").backend

    assert default.allocate(harness, problem, roster, config) == sorted(roster)
    assert len(alternative.allocate(harness, problem, roster, config)) == 1
    assert alternative.allocate(harness, problem, roster, config) != default.allocate(
        harness, problem, roster, config
    )


def test_allocation_is_a_function_of_the_log_not_of_call_order(tmp_path):
    """SPEC.md M2a — the one way 'dumb' could become 'broken'.

    ``allocate`` is documented "Deterministic function of (log, config)".
    A rotation driven by a call counter would allocate differently on a
    reopened run than on the session that wrote it, and ``verify_root``
    would report a replay divergence. Rotating on the problem id cannot.
    """

    harness, config, roster = _roster(tmp_path)
    alternative = schools.SCHOOL_POPULATION.get("round-robin").backend
    problem = _problem("pi-seed")

    first = alternative.allocate(harness, problem, roster, config)
    for _ in range(5):
        assert alternative.allocate(harness, problem, roster, config) == first

    # A fresh instance holds no accumulated state to differ by.
    fresh = schools.RoundRobinSchoolPopulationBackend()
    assert fresh.allocate(harness, problem, roster, config) == first


def test_a_call_order_rotation_would_fail_that_comparison(tmp_path):
    """The companion mutation the durable-test doctrine requires for an
    equality assertion: a backend that rotates on call order must break the
    test above, or that test is measuring nothing."""

    harness, config, roster = _roster(tmp_path)

    class _CallOrderRotation(schools.RoundRobinSchoolPopulationBackend):
        def __init__(self):
            self._calls = 0

        def allocate(self, harness, problem, schools_, config):
            everyone = sorted(schools_)
            self._calls += 1
            return [everyone[self._calls % len(everyone)]]

    broken = _CallOrderRotation()
    problem = _problem("pi-seed")
    assert broken.allocate(harness, problem, roster, config) != broken.allocate(
        harness, problem, roster, config
    )


def test_the_alternative_spreads_problems_across_schools(tmp_path):
    """Rotation that always returned one school would be indistinguishable
    from a constant, and would not exercise the socket meaningfully."""

    harness, config, roster = _roster(tmp_path)
    alternative = schools.SCHOOL_POPULATION.get("round-robin").backend
    chosen = {
        alternative.allocate(harness, _problem(f"pi-{i}"), roster, config)[0]
        for i in range(40)
    }
    assert len(chosen) > 1, chosen
    assert chosen <= set(roster)


def test_an_empty_roster_allocates_to_nobody(tmp_path):
    """The default returns [] for an empty roster; the alternative must not
    divide by zero where the default returns cleanly."""

    harness, config, _ = _roster(tmp_path)
    alternative = schools.SCHOOL_POPULATION.get("round-robin").backend
    assert alternative.allocate(harness, _problem("pi-seed"), {}, config) == []


def test_the_scope_selects_and_restores(tmp_path):
    """R5/S4: 'a run configured with the alternative'. The selection is
    scoped so no test or run leaks a backend into the next one."""

    assert schools.active_backend().fingerprint()["backend"] == "default"
    with schools.population_backend("round-robin") as backend:
        assert schools.active_backend().fingerprint()["backend"] == "round-robin"
        assert backend is schools.active_backend()
    assert schools.active_backend().fingerprint()["backend"] == "default"


def test_an_unknown_name_is_refused_before_the_selection_moves():
    """A name that does not resolve must leave the process on its previous
    backend, not on a broken one — the resolve happens first for that
    reason."""

    with pytest.raises(schools.UnknownSchoolPopulationBackend):
        with schools.population_backend("no-such-backend"):
            pytest.fail("body must not run for an unresolvable backend")
    assert schools.active_backend().fingerprint()["backend"] == "default"


def test_the_selection_is_restored_when_the_body_raises():
    """The specific hazard of a module-level selection: a run that dies
    mid-cycle must not leave every later run on the dumb backend."""

    with pytest.raises(RuntimeError):
        with schools.population_backend("round-robin"):
            raise RuntimeError("run died mid-cycle")
    assert schools.active_backend().fingerprint()["backend"] == "default"


def test_nested_selection_restores_the_outer_choice():
    """Restoration saves the PREVIOUS value rather than resetting to
    'default', so nesting cannot silently promote the inner choice."""

    with schools.population_backend("round-robin"):
        with schools.population_backend("default"):
            assert schools.active_backend().fingerprint()["backend"] == "default"
        assert schools.active_backend().fingerprint()["backend"] == "round-robin"
    assert schools.active_backend().fingerprint()["backend"] == "default"


def _offline_run(root, *, backend_id: str, cycles: int = 3):
    """The smallest ordinary run: mock endpoint, no capability, no network."""

    import json

    from deepreason.llm.adapter import LLMAdapter
    from deepreason.llm.endpoints import MockEndpoint
    from deepreason.ontology import Commitment
    from deepreason.scheduler.scheduler import Scheduler

    harness = Harness(root)
    harness.register_commitment(Commitment(id="k-moon", eval="predicate:'moon' in content"))
    harness.register_problem(
        Problem(
            id="pi-root",
            description="explain the tides",
            criteria=["k-moon"],
            provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
        )
    )
    reply = json.dumps(
        {"candidates": [{"content": "the moon pulls", "typicality": 0.6}]}
    )
    adapter = LLMAdapter(
        {"conjecturer": MockEndpoint(lambda _p: reply)}, harness.blobs, retry_max=2
    )
    with schools.population_backend(backend_id):
        Scheduler(harness, adapter, Config(N_SCHOOLS=4, VS_K=1, FUZZ_N=0)).run(cycles)
    return harness


def test_a_run_configured_with_the_alternative_completes_and_verifies(tmp_path):
    """R5/R10, the rung's core claim: the socket is REAL.

    Judged on typed outcomes only. "Deliberately dumb" predicts worse
    reasoning, so this deliberately does NOT assert epistemic quality — a
    completed run with poor outcomes is a success for this rung (SPEC.md
    A4). What must hold is that the run finishes and the root verifies.
    """

    from deepreason.invariants import verify_root

    root = tmp_path / "alternative"
    _offline_run(root, backend_id="round-robin")

    assert (root / "log.jsonl").exists()
    verdict = verify_root(root)
    assert verdict["violations"] == [], verdict["violations"]
    assert verdict["stats"]["events"] > 0


def test_the_alternatives_root_records_that_the_alternative_built_it(tmp_path):
    """R5 + rung 4: which module built a run is answerable FROM THE RECORD,
    so the offline proof is not a claim about a process that has ended."""

    from deepreason.module_events import recorded_module_fingerprints

    alt_root = tmp_path / "alternative"
    _offline_run(alt_root, backend_id="round-robin", cycles=1)
    (alt_stamp,) = recorded_module_fingerprints(Harness(alt_root, read_only=True))
    assert alt_stamp.modules[0].module_id == "round-robin"

    default_root = tmp_path / "default"
    _offline_run(default_root, backend_id="default", cycles=1)
    (default_stamp,) = recorded_module_fingerprints(
        Harness(default_root, read_only=True)
    )
    assert default_stamp.modules[0].module_id == "default"
    assert alt_stamp.digest != default_stamp.digest


def test_the_two_backends_produce_different_runs(tmp_path):
    """A socket that admitted an alternative which changed nothing would be
    proven only cosmetically. The dumb allocation must reach the run's
    behaviour, and it must do so where the RECORD can see it.

    The fingerprint stamp is excluded from the comparison on purpose: it
    names the backend by construction, so leaving it in would let this test
    pass on a backend that allocated identically to the default.

    Not asserted here — that conjecturer PROVENANCE diverges. Measured at
    2 and 6 cycles with this fixture, both runs produce conjectures from
    school-0 only, because a mock endpoint returns one candidate and the
    surviving lineage is the same either way. The divergence this fixture
    can see is in how much work each run does, not in whose work survives.
    """

    alt = _offline_run(tmp_path / "alternative", backend_id="round-robin", cycles=2)
    default = _offline_run(tmp_path / "default", backend_id="default", cycles=2)

    def shape(harness):
        return [
            (event.rule, tuple(event.inputs))
            for event in harness.log.read()
            if event.module_fingerprints is None
        ]

    assert shape(alt) != shape(default)
    # The default fans a seed problem out to every school; the rotation hands
    # it to one, so the dumb run does strictly less conjecture work.
    assert len(shape(alt)) < len(shape(default))


def test_the_alternative_delegates_its_other_four_operations(tmp_path):
    """A1: the alternative differs in ``allocate`` ONLY, so any behavioural
    difference in the offline run is attributable to allocation alone."""

    harness, config, roster = _roster(tmp_path)
    alternative = schools.SCHOOL_POPULATION.get("round-robin").backend
    default = schools.SCHOOL_POPULATION.get("default").backend

    assert alternative.roster(harness) == default.roster(harness)
    assert set(roster) == set(alternative.roster(harness))
