"""§9.9's authority audit, as an executable replay program (R2, R3).

    Standing is render authority and nothing else. It is derived, never stored
    (C4); it is content and edge-structure, never a type (C3); it appears in
    packs and schedules, never in label computation (C5, §6); every object
    realizing it — the frame assertion, its reach case, its subject's
    commitments, the succession rulings — is attackable and reinstateable
    (N1, P6). Methodological privilege without epistemic privilege: the
    background frames every conjecture in its scope and can be dragged into
    court by any of them.  (§9.9)

IT MUST BE ABLE TO FAIL, or it is decoration — `docs_verify --audit`'s own
standard, applied to a program rather than to a doc check. Five clauses, five
seeded-violation tests, each constructing a record that violates exactly one.
"""

import pytest

from deepreason.calculus import audit, operations
from deepreason.calculus.standing import consulted
from deepreason.ontology import (
    Commitment,
    Interface,
    Problem,
    ProblemProvenance,
    Provenance,
    Status,
    Warrant,
    WarrantType,
)

TIDES = {
    "schema": "declarative-scope.v1",
    "predicate": {"op": "contains",
                  "args": [{"field": "description"}, {"text": "tides"}]},
}

LAG = Commitment(id="observation:tidal-lag@v1", eval="program:json-wf",
                 observation_valued=True)


@pytest.fixture
def framed(harness):
    """One consulted frame, its subject carrying an observation-valued
    commitment, over one framed problem."""
    harness.register_commitment(LAG)
    subject = harness.create_artifact(
        "b: the lunar theory of tides",
        interface=Interface(commitments=[LAG.id]),
        provenance=Provenance(role="conjecturer"),
    )
    case = harness.create_artifact(
        "reach record: three lineages cite the lunar theory",
        provenance=Provenance(role="seed"),
    )
    promotion = operations.ensure_promotion_problem(
        harness, subject.id, "promote or refuse this candidate background"
    )
    assertion = operations.file_frame_assertion(
        harness, problem=promotion, subject_ref=subject.id, scope=TIDES,
        reach_case_refs=(case.id,),
        departure_protocol="declare which of its commitments you break with",
    )
    harness.register_problem(
        Problem(
            id="what-governs-the-tides",
            description="what governs the tides at the equinox",
            criteria=[],
            provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
        )
    )
    return subject, case, assertion


def _clause(report, name):
    return next(c for c in report.clauses if c.name == name)


# --- the audit passes on a real record -------------------------------------------


def test_the_audit_passes_on_a_well_formed_record(framed, harness):
    report = audit.authority_audit(harness)
    assert report.ok, report.violations
    assert [c.name for c in report.clauses] == list(audit.CLAUSES)
    assert all(c.ok for c in report.clauses)


def test_the_audit_passes_vacuously_on_a_record_with_no_standing(harness):
    """The absence-tolerant path: a root that never promoted anything has no
    authority to audit, and that is a pass with nothing checked rather than a
    failure. Every root written before Rung 4 is this root."""
    report = audit.authority_audit(harness)
    assert report.ok and report.grants == 0


def test_the_audit_is_a_pure_read(framed, harness):
    """An audit that changed the record it audits would be an intervention."""
    before = (
        {a: s.value for a, s in sorted(harness.state.status.items())},
        sorted(harness.state.att),
        sorted(harness.state.dep),
        harness._next_seq,
    )
    audit.authority_audit(harness)
    after = (
        {a: s.value for a, s in sorted(harness.state.status.items())},
        sorted(harness.state.att),
        sorted(harness.state.dep),
        harness._next_seq,
    )
    assert after == before


def test_the_audit_is_deterministic(framed, harness):
    first = audit.authority_audit(harness)
    second = audit.authority_audit(harness)
    assert first.model_dump_json() == second.model_dump_json()


# --- C4: derived, never stored -----------------------------------------------------


def test_c4_re_derives_standing_rather_than_reading_it_back(framed, harness):
    subject, _, _ = framed
    clause = _clause(audit.authority_audit(harness), "C4-derived")
    assert clause.ok and clause.checked >= 1
    assert audit.stored_standing_fields(harness) == ()


def test_c4_fails_when_standing_is_stored(framed, harness):
    """SEEDED VIOLATION. A state that carried a standing map could disagree
    with the log that implies it, and the audit must say so."""
    harness.state.__dict__["standing"] = {"anything": "background"}
    try:
        report = audit.authority_audit(harness)
        assert not report.ok
        assert not _clause(report, "C4-derived").ok
        assert any("stored" in v for v in report.violations)
    finally:
        harness.state.__dict__.pop("standing", None)
    assert audit.authority_audit(harness).ok


# --- C3: content and edge structure, never a type ------------------------------------


def test_c3_finds_one_body_schema_realizing_standing(framed, harness):
    clause = _clause(audit.authority_audit(harness), "C3-content-not-type")
    assert clause.ok
    assert clause.detail["schemas"] == ["poietic.frame-assertion.v1"]


def test_c3_fails_when_a_second_schema_realizes_standing(framed, harness, monkeypatch):
    """SEEDED VIOLATION. Instrument standing is a `bounded` VALUE of a field,
    not a second record type (C3). A second schema in the consulted set is
    standing having become a type."""
    real = audit.grant_schemas

    def two(_harness):
        return ("poietic.frame-assertion.v1", "poietic.instrument-standing.v1")

    monkeypatch.setattr(audit, "grant_schemas", two)
    report = audit.authority_audit(harness)
    assert not report.ok
    assert not _clause(report, "C3-content-not-type").ok
    monkeypatch.setattr(audit, "grant_schemas", real)
    assert audit.authority_audit(harness).ok


# --- C5: absent from label computation ------------------------------------------------


def test_c5_is_a_differential_over_the_labels(framed, harness):
    clause = _clause(audit.authority_audit(harness), "C5-absent-from-labels")
    assert clause.ok
    assert clause.detail["compared"] == len(harness.state.artifacts)


def test_c5_fails_when_a_grant_moves_a_label(framed, harness, monkeypatch):
    """SEEDED VIOLATION, and the most important of the five: standing reaching
    a label is the whole thing §9.9 denies. The seed makes the counterfactual
    labelling differ from the real one, which is exactly what a label that
    consulted standing would produce."""
    real = audit.labels_without_standing

    def poisoned(harness_, grants):
        labels = dict(real(harness_, grants))
        labels[sorted(labels)[0]] = Status.REFUTED.value
        return labels

    monkeypatch.setattr(audit, "labels_without_standing", poisoned)
    report = audit.authority_audit(harness)
    assert not report.ok
    assert not _clause(report, "C5-absent-from-labels").ok
    monkeypatch.setattr(audit, "labels_without_standing", real)
    assert audit.authority_audit(harness).ok


# --- N1: every realizing object is attackable -------------------------------------------


def test_n1_names_all_four_kinds_of_realizing_object(framed, harness):
    subject, case, assertion = framed
    clause = _clause(audit.authority_audit(harness), "N1-attackable")
    assert clause.ok
    realizers = set(clause.detail["realizers"])
    assert assertion.id in realizers          # the frame assertion
    assert case.id in realizers               # its reach case
    assert LAG.id in realizers                # the subject's commitments
    # §9.9 names four kinds; this record has no succession, so three are
    # FOUND and four are DECLARED. A clause that reported only what it found
    # would report full coverage of a record that had none.
    assert clause.detail["kinds_declared"] == [
        "assertion", "commitment", "reach-case", "succession-ruling",
    ]
    assert clause.detail["kinds_found"] == ["assertion", "commitment", "reach-case"]


def test_n1_fails_when_a_realizer_is_not_a_registered_artifact(framed, harness,
                                                              monkeypatch):
    """SEEDED VIOLATION. A realizing object that is not an artifact is not a
    legal `Warrant.target`, so nothing could ever attack it — authority without
    exposure, which is what N1 forbids."""
    real = audit.realizing_objects

    def ghost(harness_, grants):
        found = dict(real(harness_, grants))
        found["a-realizer-that-is-not-on-the-record"] = "assertion"
        return found

    monkeypatch.setattr(audit, "realizing_objects", ghost)
    report = audit.authority_audit(harness)
    assert not report.ok
    assert not _clause(report, "N1-attackable").ok
    monkeypatch.setattr(audit, "realizing_objects", real)
    assert audit.authority_audit(harness).ok


def test_n1_is_true_of_a_really_attacked_realizer(framed, harness):
    """Not a monkeypatch: the assertion is REALLY attacked, and the audit still
    passes, because being attacked is what N1 says must be possible."""
    _, _, assertion = framed
    nu = harness.create_artifact("nu: the reach case is thin",
                                 provenance=Provenance(role="critic"))
    harness.create_artifact(
        "critic: this frame has not earned its standing",
        provenance=Provenance(role="critic"),
        warrants=[Warrant(id="w-fa", target=assertion.id,
                          type=WarrantType.ARGUMENTATIVE, validity_node=nu.id)],
    )
    assert harness.state.status[assertion.id] is Status.REFUTED
    assert consulted(harness) == ()
    report = audit.authority_audit(harness)
    assert report.ok, report.violations


# --- P6: reinstateable ---------------------------------------------------------------


def test_p6_every_realizer_is_reinstateable(framed, harness):
    clause = _clause(audit.authority_audit(harness), "P6-reinstateable")
    assert clause.ok and clause.detail["absorbing"] == []


def test_p6_fails_on_an_absorbing_status(framed, harness, monkeypatch):
    """SEEDED VIOLATION. Thm 12.3: no status absorbs. A realizer whose label
    survives the removal of every attack against it is one the record cannot
    take back — authority that criticism cannot reach."""
    _, _, assertion = framed
    nu = harness.create_artifact("nu: the reach case is thin",
                                 provenance=Provenance(role="critic"))
    harness.create_artifact(
        "critic: this frame has not earned its standing",
        provenance=Provenance(role="critic"),
        warrants=[Warrant(id="w-p6", target=assertion.id,
                          type=WarrantType.ARGUMENTATIVE, validity_node=nu.id)],
    )
    assert harness.state.status[assertion.id] is Status.REFUTED
    assert audit.authority_audit(harness).ok, "an attacked realizer is fine"

    real = audit.labels_without_attacks_on

    def sticky(harness_, targets):
        labels = dict(real(harness_, targets))
        for target in targets:
            labels[target] = Status.REFUTED.value
        return labels

    monkeypatch.setattr(audit, "labels_without_attacks_on", sticky)
    report = audit.authority_audit(harness)
    assert not report.ok
    assert not _clause(report, "P6-reinstateable").ok
    monkeypatch.setattr(audit, "labels_without_attacks_on", real)
    assert audit.authority_audit(harness).ok


# --- the audit's own falsifiability ------------------------------------------------------


def test_every_clause_has_a_seeded_violation_test():
    """`docs_verify --audit`'s standard, turned on this file: a clause with no
    seeded-violation test is a clause nobody has shown can fail."""
    import pathlib

    source = pathlib.Path(__file__).read_text()
    for name in audit.CLAUSES:
        stem = name.split("-")[0].lower()
        assert f"def test_{stem}_fails" in source, name


# --- on a committed live root ----------------------------------------------------------


def test_the_audit_runs_on_a_committed_live_root():
    """Regression (Rung 7 live gate L-6, committed at
    `experiments/2026-08-24-change-rung7-wounds-falls-succession/run/`).

    A root the harness really made, with a real fall on it: its one frame
    assertion is REFUTED, so `consulted()` is empty. That is precisely the case
    an audit built on live grants alone would pass VACUOUSLY, and the reason
    the realizer set is built from every DECLARED assertion instead — a refuted
    assertion still realizes standing, and P6 is the claim that its defeat can
    be undone.
    """
    import pathlib

    from deepreason.harness import Harness
    from deepreason.calculus.standing import declared_frame_assertions

    root = pathlib.Path(
        "experiments/2026-08-24-change-rung7-wounds-falls-succession/run"
    )
    if not (root / "log.jsonl").exists():
        pytest.skip("the committed Rung 7 root is not present in this checkout")

    harness = Harness(root, read_only=True)
    assert len(declared_frame_assertions(harness)) == 1
    report = audit.authority_audit(harness)
    assert report.ok, report.violations
    assert report.grants == 0, "the assertion is refuted; the audit is not vacuous"
    n1 = _clause(report, "N1-attackable")
    assert n1.checked >= 9, "the realizer set collapsed to the live grants"
    assert _clause(report, "C5-absent-from-labels").detail["compared"] == 68
