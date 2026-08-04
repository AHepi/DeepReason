"""Rung 3 tranche A: the school-population registry mechanics, and proof
that the default backend is a no-op wrapper around today's behavior."""

import pytest

from deepreason.capture import schools
from deepreason.capture.schools import (
    DefaultSchoolPopulationBackend,
    SchoolPopulationRegistry,
    SchoolPopulationRegistryError,
    UnknownSchoolPopulationBackend,
)
from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.ontology import Commitment, Problem, ProblemProvenance


def _seed_problem(harness, criteria=()) -> None:
    for cid in criteria:
        harness.register_commitment(Commitment(id=cid, eval="predicate:True"))
    harness.register_problem(
        Problem(
            id="pi-seed",
            description="a seed problem",
            criteria=list(criteria),
            provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
        )
    )


def test_register_and_resolve_a_backend():
    registry = SchoolPopulationRegistry()
    registration = registry.register(DefaultSchoolPopulationBackend(), backend_id="default")
    assert registration.backend_id == "default"
    assert registry.ids() == ("default",)
    assert registry.get("default") is registration
    assert registry.resolve("default") is registration


def test_unknown_backend_raises():
    registry = SchoolPopulationRegistry()
    with pytest.raises(UnknownSchoolPopulationBackend):
        registry.get("no-such-backend")


def test_duplicate_registration_raises():
    registry = SchoolPopulationRegistry()
    registry.register(DefaultSchoolPopulationBackend(), backend_id="default")
    with pytest.raises(SchoolPopulationRegistryError):
        registry.register(DefaultSchoolPopulationBackend(), backend_id="default")


def test_fingerprint_pinned_at_registration_and_rechecked_on_get():
    registry = SchoolPopulationRegistry()
    backend = DefaultSchoolPopulationBackend()
    registry.register(backend, backend_id="default")
    assert registry.fingerprint_is_pinned("default") is True
    assert registry.get("default").pinned_fingerprint == backend.fingerprint()


def test_default_backend_init_schools_matches_bare_function(tmp_path):
    config = Config(N_SCHOOLS=4)
    h1 = Harness(tmp_path / "bare")
    h2 = Harness(tmp_path / "backend")
    assert schools.init_schools(h1, config) == DefaultSchoolPopulationBackend().init_schools(
        h2, config
    )


def test_default_backend_roster_matches_bare_function(tmp_path):
    config = Config(N_SCHOOLS=4)
    h1 = Harness(tmp_path / "bare")
    h2 = Harness(tmp_path / "backend")
    schools.init_schools(h1, config)
    DefaultSchoolPopulationBackend().init_schools(h2, config)
    assert schools.roster(h1) == DefaultSchoolPopulationBackend().roster(h2)


def test_default_backend_allocate_matches_bare_function(tmp_path):
    config = Config(N_SCHOOLS=2)
    h1 = Harness(tmp_path / "bare")
    h2 = Harness(tmp_path / "backend")
    roster1 = schools.init_schools(h1, config)
    roster2 = DefaultSchoolPopulationBackend().init_schools(h2, config)
    _seed_problem(h1)
    _seed_problem(h2)
    problem1 = h1.state.problems["pi-seed"]
    problem2 = h2.state.problems["pi-seed"]
    assert schools.allocate(h1, problem1, roster1, config) == (
        DefaultSchoolPopulationBackend().allocate(h2, problem2, roster2, config)
    )


def test_default_backend_reseed_matches_bare_function(tmp_path):
    config = Config(N_SCHOOLS=2)
    h1 = Harness(tmp_path / "bare")
    h2 = Harness(tmp_path / "backend")
    roster1 = schools.init_schools(h1, config)
    roster2 = DefaultSchoolPopulationBackend().init_schools(h2, config)
    reseeded1 = schools.reseed(h1, "school-0", roster1["school-0"], reason="t")
    reseeded2 = DefaultSchoolPopulationBackend().reseed(
        h2, "school-0", roster2["school-0"], reason="t"
    )
    assert reseeded1 == reseeded2


def test_module_singleton_holds_the_default_backend_under_its_own_name():
    """Rung 3 pinned this registry at exactly one entry; rung 5 added the
    deliberately dumb `"round-robin"` alternative, which is what the socket
    was built for. The claim that survives is the one rung 3 actually needed:
    `"default"` is still registered, still the default implementation, and
    still what an unscoped `active_backend()` resolves to — an alternative
    joins the registry, it does not displace the default.
    """

    from deepreason.capture.schools import SCHOOL_POPULATION, active_backend

    assert "default" in SCHOOL_POPULATION.ids()
    assert isinstance(
        SCHOOL_POPULATION.get("default").backend, DefaultSchoolPopulationBackend
    )
    assert isinstance(active_backend(), DefaultSchoolPopulationBackend)
