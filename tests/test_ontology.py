"""Ontology sanity: the one schema round-trips (spec §1)."""

from deepreason.ontology import (
    Artifact,
    Commitment,
    Event,
    Interface,
    Problem,
    ProblemProvenance,
    Provenance,
    Ref,
    Rule,
    SpawnTrigger,
    Warrant,
    WarrantType,
)


def test_artifact_round_trip():
    a = Artifact(
        id="deadbeef",
        content_ref="inline:hello",
        codec="utf8",
        interface=Interface(commitments=["c1"], refs=[Ref(target="x", role="dependence")]),
        provenance=Provenance(role="seed"),
    )
    assert Artifact.model_validate_json(a.model_dump_json()) == a


def test_compute_id_deterministic_and_content_sensitive():
    interface = Interface(commitments=["c1"])
    id1 = Artifact.compute_id("inline:x", "utf8", interface)
    assert id1 == Artifact.compute_id("inline:x", "utf8", Interface(commitments=["c1"]))
    assert id1 != Artifact.compute_id("inline:y", "utf8", interface)
    assert id1 != Artifact.compute_id("inline:x", "json", interface)
    assert len(id1) == 64  # sha256 hex


def test_artifact_has_no_kind_field():
    # Untypedness (Def 3.2, §0): dispatch is on interface structure only.
    assert "kind" not in Artifact.model_fields


def test_warrant_round_trip():
    w = Warrant(id="w1", target="a1", type=WarrantType.ARGUMENTATIVE, validity_node="v1")
    assert Warrant.model_validate_json(w.model_dump_json()) == w


def test_problem_provenance_alias():
    p = Problem(
        id="p1",
        description="seed problem",
        provenance=ProblemProvenance.model_validate(
            {"trigger": SpawnTrigger.SEED, "from": []}
        ),
    )
    assert p.provenance.trigger is SpawnTrigger.SEED


def test_event_round_trip():
    e = Event(seq=0, ts="2026-01-01T00:00:00Z", rule=Rule.REGISTER)
    assert Event.model_validate_json(e.model_dump_json()) == e


def test_commitment_defaults():
    c = Commitment(id="c1", eval="predicate:true")
    assert c.observation_valued is False
    assert c.budget.steps == 100_000
