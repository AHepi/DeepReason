"""G-4/G-5: the capture cost of elevation, measured rather than vibed.

Implements R4 and R5 (v2 calculus program, Rung 8).

    G-5: promotion events logged with before/after conditioning diagnostics —
    "the capture cost of elevation is measured, not vibed".
    G-4: a frame slice is deliberate, scope-wide conditioning, the strongest
    the calculus ever applies.

An ELEVATION is the cycle in which a frame assertion is first CONSULTED. Two
records ride it: `before`, at the elevation, carrying the §14 vector and the
number of problems the new grant now frames; and `after`, at the next
diagnostics emission, carrying the same vector once the frame has conditioned
a cycle of generation.

Which elevations still owe an `after` is derived from the LOG, never from
process state — so a resumed run owes exactly what it owed before, and no
in-memory variable can disagree with the record.
"""

import pytest

from deepreason.capture import diagnostics as d14
from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.ontology import Problem, ProblemProvenance, Provenance

SIGNAL = "capture14.promotion-conditioning.v1"

TIDES = {
    "schema": "declarative-scope.v1",
    "predicate": {"op": "contains",
                  "args": [{"field": "description"}, {"text": "tides"}]},
}
WEATHER = {
    "schema": "declarative-scope.v1",
    "predicate": {"op": "contains",
                  "args": [{"field": "description"}, {"text": "weather"}]},
}


def _problem(harness, pid, description):
    return harness.register_problem(
        Problem(
            id=pid,
            description=description,
            criteria=[],
            provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
        )
    )


def _elevate(harness, name, scope):
    """Register a subject and file a consulted frame assertion over `scope`."""
    from deepreason.calculus import operations

    subject = harness.create_artifact(
        f"b: {name}", provenance=Provenance(role="seed")
    )
    case = harness.create_artifact(
        f"reach record for {name}", provenance=Provenance(role="seed")
    )
    # The promotion problem's own description is kept OUT of the scope
    # predicate: a promotion problem that fell inside its own candidate's
    # scope would be framed by the assertion addressed to it, and the
    # conditioning count would include the elevation's own paperwork.
    promotion = operations.ensure_promotion_problem(
        harness, subject.id, "promote or refuse this candidate background"
    )
    assertion = operations.file_frame_assertion(
        harness,
        problem=promotion,
        subject_ref=subject.id,
        scope=scope,
        reach_case_refs=(case.id,),
        departure_protocol="declare which of its commitments you break with",
    )
    return assertion


def _records(harness, phase=None):
    out = []
    for event in harness.log.read():
        if not event.inputs or event.inputs[0] != SIGNAL:
            continue
        if phase is None or event.inputs[1] == phase:
            out.append(list(event.inputs))
    return out


# --- the pair ------------------------------------------------------------------


def test_an_elevation_records_a_before(harness):
    _problem(harness, "tides-1", "what governs the tides at the equinox")
    assertion = _elevate(harness, "the lunar theory of tides", TIDES)

    assert _records(harness) == []
    d14.promotion_conditioning(harness, Config())
    before = _records(harness, "before")
    assert len(before) == 1
    assert before[0][2] == assertion.id


def test_every_elevation_gets_both_a_before_and_an_after(harness):
    """The gate obligation R15 names: G-5 diagnostics present on EVERY
    promotion event, not on the first one."""
    _problem(harness, "tides-1", "what governs the tides at the equinox")
    _problem(harness, "weather-1", "what governs the weather in June")
    first = _elevate(harness, "the lunar theory of tides", TIDES)

    d14.promotion_conditioning(harness, Config())          # first: before
    second = _elevate(harness, "the vortex theory of weather", WEATHER)
    d14.promotion_conditioning(harness, Config())          # first: after, second: before
    d14.promotion_conditioning(harness, Config())          # second: after

    befores = {r[2] for r in _records(harness, "before")}
    afters = {r[2] for r in _records(harness, "after")}
    assert befores == {first.id, second.id}
    assert afters == {first.id, second.id}


def test_an_after_is_recorded_at_most_once(harness):
    _problem(harness, "tides-1", "what governs the tides at the equinox")
    _elevate(harness, "the lunar theory of tides", TIDES)
    for _ in range(5):
        d14.promotion_conditioning(harness, Config())
    assert len(_records(harness, "before")) == 1
    assert len(_records(harness, "after")) == 1


def test_the_owed_set_is_derived_from_the_record_not_from_process_state(tmp_path):
    """A resumed run owes exactly what the log says it owes. The harness is
    reopened -- a fresh process, no carried state -- and the owed `after` is
    still found and still paid."""
    root = tmp_path / "run"
    harness = Harness(root)
    _problem(harness, "tides-1", "what governs the tides at the equinox")
    assertion = _elevate(harness, "the lunar theory of tides", TIDES)
    d14.promotion_conditioning(harness, Config())
    assert d14.owed_after(harness) == (assertion.id,)

    reopened = Harness(root)
    assert d14.owed_after(reopened) == (assertion.id,)
    d14.promotion_conditioning(reopened, Config())
    assert d14.owed_after(reopened) == ()
    assert {r[2] for r in _records(reopened, "after")} == {assertion.id}


# --- what the record actually says ------------------------------------------------


def test_the_before_states_the_size_of_the_conditioning_surface(harness):
    """The number G-4 is about: how much of the run this frame now sits on
    top of. It is the first number this harness has ever had for it."""
    from deepreason.calculus.standing import framed_problem_ids

    for i in range(3):
        _problem(harness, f"tides-{i}", f"what governs the tides, case {i}")
    _problem(harness, "weather-1", "what governs the weather in June")
    _elevate(harness, "the lunar theory of tides", TIDES)

    d14.promotion_conditioning(harness, Config())
    payload = d14.conditioning_payload(harness, _records(harness, "before")[0][3])
    assert payload["conditioned_problems"] == len(framed_problem_ids(harness, TIDES))
    assert payload["conditioned_problems"] == 3          # the weather problem is out
    assert payload["phase"] == "before"
    assert payload["vector"]["schema"] == "capture14-vector.v1"


def test_the_measurement_moves_no_label_and_no_edge(harness):
    """A measurement of conditioning is not a verdict on it. Nothing about the
    promotion is approved or impugned by measuring what it cost."""
    _problem(harness, "tides-1", "what governs the tides at the equinox")
    _elevate(harness, "the lunar theory of tides", TIDES)

    before = (
        {a: s.value for a, s in sorted(harness.state.status.items())},
        sorted(harness.state.att),
        sorted(harness.state.dep),
    )
    d14.promotion_conditioning(harness, Config())
    d14.promotion_conditioning(harness, Config())
    after = (
        {a: s.value for a, s in sorted(harness.state.status.items())},
        sorted(harness.state.att),
        sorted(harness.state.dep),
    )
    assert after == before


def test_a_record_with_no_promotion_records_nothing(harness):
    """The absence-tolerant path: a run that never elevates anything emits no
    conditioning record at all, which is every root written before this rung."""
    _problem(harness, "tides-1", "what governs the tides at the equinox")
    d14.promotion_conditioning(harness, Config())
    assert _records(harness) == []
    assert d14.owed_after(harness) == ()


def test_the_signal_is_declared():
    from deepreason.signals import declaration

    decl = declaration(SIGNAL)
    assert decl is not None
    assert decl.unit != "unspecified" and decl.staleness != "unspecified"
