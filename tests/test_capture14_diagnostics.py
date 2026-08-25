"""§14's six capture diagnostics, over a fixed SEQUENCE-NUMBER window.

Implements R8 and R9 (v2 calculus program, Rung 8, RIDER 2 / R48). The six are
`docs/POIETIC_CALCULUS_FORMALIZED.md` §14.1-§14.6, and the property that makes
them different from every capture instrument already on this tree is the
window:

    W_m(n) = {max(1, n-m+1), ..., n}

a span of SEQUENCE NUMBERS. Not wall-clock (§15.1: "wall-clock time ... do not
enter verdicts or serialization") and not an event count (which is what
`harness.recent_semantic_events` and `capture/detection.py` use, and which is
why those are a different family -- V-6).

Written before the module existed, and run RED first: a test that has never
failed has never been shown to be able to.
"""

import ast
import pathlib
from decimal import Decimal

import pytest

from deepreason.capture import diagnostics as d14
from deepreason.config import Config
from deepreason.ontology import (
    Commitment,
    Interface,
    Problem,
    ProblemProvenance,
    Provenance,
    Ref,
    Rule,
    Status,
    Warrant,
    WarrantType,
)


# --- builders ----------------------------------------------------------------


def _conj(harness, text, *, commitments=(), refs=(), problem_id=None):
    """A CONJECTURE registration. `Rule.CONJ` is what `rules/conj.py` uses for
    a candidate; `create_artifact`'s default `Rule.REGISTER` is the bookkeeping
    path, and §14.1's C_{m,n} is the former."""
    return harness.create_artifact(
        text,
        interface=Interface(commitments=list(commitments), refs=list(refs)),
        provenance=Provenance(role="seed"),
        rule=Rule.CONJ,
        problem_id=problem_id,
    )


def _warrant(harness, target_id, note, *, commitment=None, verdict=None, nu=None):
    """Register nu + a critic carrying one warrant. Returns (critic, nu, wid)."""
    if nu is None:
        nu = harness.create_artifact(
            f"nu: the attack {note!r} is sound and relevant",
            provenance=Provenance(role="critic"),
        )
    wid = f"w-{note}"
    warrant = Warrant(
        id=wid,
        target=target_id,
        type=WarrantType.ARGUMENTATIVE,
        validity_node=nu.id,
        commitment=commitment,
        verdict=verdict,
    )
    critic = harness.create_artifact(
        f"critic: {note}",
        provenance=Provenance(role="critic"),
        warrants=[warrant],
    )
    return critic, nu, wid


def _cfg(**kw):
    return Config(**kw)


# --- the window --------------------------------------------------------------


def test_the_window_is_a_span_of_sequence_numbers(harness):
    """W_m(n) = {max(1, n-m+1) .. n}, inclusive at both ends."""
    for i in range(10):
        _conj(harness, f"c{i}")
    n = harness._next_seq - 1
    w = d14.window(harness, 4)
    assert list(w) == [n - 3, n - 2, n - 1, n]


def test_the_window_clamps_at_the_first_seq_rather_than_running_negative(harness):
    """§14 writes `max(1, ...)` for 1-based sequence numbers; this log is
    0-based, so the clamp is at 0 and the run's first registration is IN the
    window. A literal 1 would drop it from every window a run ever computes."""
    _conj(harness, "only")
    w = d14.window(harness, 500)
    assert min(w) == 0 and max(w) == harness._next_seq - 1


def test_the_window_is_not_an_event_count(harness):
    """The discriminating property. `recent_semantic_events` EXCLUDES Control
    receipts and split-call carriers, so an event window and a sequence window
    over the same record cover different things. This test fails the moment
    the six are re-based on the event window."""
    for i in range(6):
        _conj(harness, f"c{i}")
    harness.record_measure(inputs=["probe", "1"])
    harness.record_measure(inputs=["probe", "2"])
    w = d14.window(harness, 3)
    # Three SEQUENCE numbers, and the last three seqs are the two measures plus
    # one conjecture -- so the sequence window sees ONE conjecture. An event
    # window of 3 over the same record excludes neither measure and would see
    # a different set; the two instruments are not interchangeable.
    assert len(list(w)) == 3
    assert len(d14.conjectures(harness, w)) == 1
    assert len(harness.recent_semantic_events(3)) == 3


# --- §14.1 stream contraction ------------------------------------------------


def test_stream_contraction_is_one_when_every_conjecture_behaves_alike(harness):
    """Identical behavioural signatures collapse N_eff to 1, so SC = 1."""
    for i in range(4):
        _conj(harness, f"same shape {i}")
    w = d14.window(harness, 100)
    assert d14.stream_contraction(harness, w) == pytest.approx(1.0)


def test_stream_contraction_is_zero_when_every_conjecture_behaves_differently(harness):
    """Distinct signatures give N_eff = N, so SC = 0. Signatures are made
    distinct by the RELATION SHAPE and the verdict vector -- never by artifact
    identity, which would make every signature unique and SC identically 0."""
    a = _conj(harness, "plain")
    b = _conj(harness, "one mention", refs=[Ref(target=a.id, role="mention")])
    _conj(
        harness,
        "two mentions",
        refs=[Ref(target=a.id, role="mention"), Ref(target=b.id, role="mention")],
    )
    w = d14.window(harness, 100)
    assert d14.stream_contraction(harness, w) == pytest.approx(0.0)


def test_stream_contraction_ignores_artifact_identity(harness):
    """The instrument would be VACUOUS if identity entered the signature: every
    conjecture is content-addressed and therefore unique, so SC would read 0 on
    every record ever made. `docs_verify --audit`'s own standard -- a check
    that cannot fire is refused -- applied to a diagnostic."""
    _conj(harness, "alpha")
    _conj(harness, "beta")
    _conj(harness, "gamma")
    w = d14.window(harness, 100)
    assert d14.stream_contraction(harness, w) == pytest.approx(1.0)


def test_stream_contraction_is_absent_below_two_conjectures(harness):
    _conj(harness, "lonely")
    w = d14.window(harness, 100)
    assert d14.stream_contraction(harness, w) is None


# --- §14.2 attack-target entropy ---------------------------------------------


def test_attack_target_entropy_reads_newly_carried_attacks(harness):
    """V-6's discriminating test. §14.2 reads `carry_add` -- warrants newly
    carried inside the window. The shipped `criticism.attack-target-entropy.v1`
    reads the whole standing `att` relation. Re-carrying an EXISTING warrant on
    a second artifact is new carriage without a new warrant, and the two
    families must disagree about it."""
    from deepreason.scheduler.scheduler import attack_target_entropy as shipped

    a, b = _conj(harness, "a"), _conj(harness, "b")
    _warrant(harness, a.id, "one")
    _warrant(harness, b.id, "two")
    w = d14.window(harness, 100)
    # Two targets, evenly hit: normalised entropy 1.0 on both readings.
    assert d14.attack_target_entropy(harness, w) == pytest.approx(1.0)

    # Now let the window MOVE PAST both carriages. §14.2 reads new carriage, so
    # it goes absent; the shipped signal reads the whole standing relation, so
    # it does not move at all. This is V-6 as an observation rather than an
    # argument -- two quantities, not two implementations of one.
    for i in range(3):
        harness.record_measure(inputs=["probe", str(i)])
    narrow = d14.window(harness, 2)
    assert d14.attack_target_entropy(harness, narrow) is None
    assert len(harness.state.att) >= 2
    assert shipped(harness.state) == pytest.approx(1.0)


def test_attack_target_entropy_is_zero_on_a_single_target(harness):
    a = _conj(harness, "a")
    _warrant(harness, a.id, "one")
    _warrant(harness, a.id, "two")
    w = d14.window(harness, 100)
    assert d14.attack_target_entropy(harness, w) == pytest.approx(0.0)


def test_attack_target_entropy_is_absent_when_nothing_was_carried(harness):
    _conj(harness, "unattacked")
    w = d14.window(harness, 100)
    assert d14.attack_target_entropy(harness, w) is None


# --- §14.3 criticism debt ----------------------------------------------------


def test_criticism_debt_counts_only_artifacts_past_the_age_floor(harness):
    """`n - seq(a) >= h`. Below the floor an artifact has not had TIME to
    attract criticism, and counting it would measure the run's youth."""
    _conj(harness, "old")
    for i in range(8):
        harness.record_measure(inputs=["probe", str(i)])
    w = d14.window(harness, 100)
    assert d14.criticism_debt(harness, w, h=100) is None  # nothing old enough
    assert d14.criticism_debt(harness, w, h=2) == pytest.approx(1.0)


def test_the_age_floor_actually_discriminates(harness):
    """The vacuity this instrument was one line away from.

    `Provenance.event_seq` defaults to 0 and almost nothing sets it, so an age
    derived from it reads EVERY artifact as maximally old and the floor
    separates nothing. This test fails against that implementation: the same
    record must read `None` under a high floor and a number under a low one,
    with no other difference.
    """
    _conj(harness, "fresh")
    w = d14.window(harness, 100)
    assert d14.criticism_debt(harness, w, h=50) is None
    assert d14.criticism_debt(harness, w, h=0) == pytest.approx(1.0)
    assert d14.younger_than(harness, 50) != frozenset()
    assert d14.younger_than(harness, 0) == frozenset()


def test_criticism_debt_discounts_an_attacker_that_is_itself_refuted(harness):
    """LiveAttackers, not attackers: a refuted critic is not live criticism."""
    a = _conj(harness, "target")
    critic, _, _ = _warrant(harness, a.id, "against-a")
    assert d14._live_attackers(harness, a.id) == (critic.id,)

    _warrant(harness, critic.id, "against-the-critic")
    assert harness.state.status[critic.id] is Status.REFUTED
    assert (critic.id, a.id) in harness.state.att       # the EDGE survives
    assert d14._live_attackers(harness, a.id) == ()     # the CRITICISM does not

    # And the reinstated artifact is therefore counted as indebted: it is
    # unrefuted, it is old enough, and nothing live is arguing with it.
    w = d14.window(harness, 100)
    assert d14.criticism_debt(harness, w, h=0) == pytest.approx(1.0)


# --- §14.4 reinstatement rate ------------------------------------------------


def test_reinstatement_rate_counts_refuted_to_unrefuted_per_criticism(harness):
    a = _conj(harness, "target")
    critic, _, _ = _warrant(harness, a.id, "against-a")
    assert harness.state.status[a.id] is Status.REFUTED
    _warrant(harness, critic.id, "against-the-critic")
    assert harness.state.status[a.id] is Status.ACCEPTED
    w = d14.window(harness, 100)
    rate = d14.reinstatement_rate(harness, w)
    assert rate is not None and rate > 0.0


def test_reinstatement_rate_is_absent_without_criticism(harness):
    _conj(harness, "quiet")
    w = d14.window(harness, 100)
    assert d14.reinstatement_rate(harness, w) is None


# --- §14.5 validity-node attack rate -----------------------------------------


def test_validity_attack_rate_is_the_share_of_new_attacks_on_validity_nodes(harness):
    a = _conj(harness, "target")
    _, nu, _ = _warrant(harness, a.id, "against-a")
    _warrant(harness, nu.id, "against-the-validity-node")
    w = d14.window(harness, 100)
    # Two newly carried attacks; one of them targets a validity node.
    assert d14.validity_attack_rate(harness, w) == pytest.approx(0.5)


def test_validity_attack_rate_is_absent_when_nothing_was_attacked(harness):
    _conj(harness, "quiet")
    w = d14.window(harness, 100)
    assert d14.validity_attack_rate(harness, w) is None


# --- §14.6 exogenous grounding ratio -----------------------------------------


def test_exogenous_grounding_credits_a_budgeted_program_check(harness):
    kappa = Commitment(id="k:wf@v1", eval="program:json-wf")
    harness.register_commitment(kappa)
    a = _conj(harness, '{"claim": "x"}')
    nu = harness.create_artifact(
        '{"verdict": "fail"}',
        interface=Interface(commitments=[kappa.id]),
        provenance=Provenance(role="critic"),
    )
    _warrant(harness, a.id, "grounded", nu=nu)
    w = d14.window(harness, 100)
    assert d14.exogenous_grounding_ratio(harness, w) == pytest.approx(1.0)


def test_exogenous_grounding_rejects_a_closed_judgment_loop(harness):
    """A validity node that rests only on further judgments -- no program
    check, no evidence, no ruling -- is a closed loop, not an anchor."""
    a = _conj(harness, "claim")
    _warrant(harness, a.id, "ungrounded")
    w = d14.window(harness, 100)
    assert d14.exogenous_grounding_ratio(harness, w) == pytest.approx(0.0)


def test_exogenous_grounding_credits_an_imported_evidence_item(harness):
    a = _conj(harness, "claim")
    nu = harness.create_artifact(
        "measured: the equinoctial lag is 42 minutes",
        provenance=Provenance(role="import"),
    )
    _warrant(harness, a.id, "evidenced", nu=nu)
    w = d14.window(harness, 100)
    assert d14.exogenous_grounding_ratio(harness, w) == pytest.approx(1.0)


def test_exogenous_grounding_is_absent_without_a_live_warrant(harness):
    _conj(harness, "quiet")
    w = d14.window(harness, 100)
    assert d14.exogenous_grounding_ratio(harness, w) is None


# --- A10: canonical rounding and declared precision ---------------------------


def test_canonical_rounding_is_half_even_at_the_declared_precision():
    """A10. HALF_EVEN, not HALF_UP: the tie-break must not drift a series
    upward, and it must be the same tie-break on every machine."""
    assert d14.canonical(0.1234565, 6) == Decimal("0.123456")
    assert d14.canonical(0.1234575, 6) == Decimal("0.123458")
    assert d14.canonical(0.5, 0) == Decimal("0")
    assert d14.canonical(1.5, 0) == Decimal("2")


def test_absence_renders_as_none_and_never_as_zero():
    """The reading error the six exist to prevent: a 0.0 that means 'no data'
    is indistinguishable from a 0.0 that means 'measured zero'."""
    assert d14.render(None, 6) == "none"
    assert d14.render(0.0, 6) == "0.000000"


def test_the_declared_precision_is_honoured(harness):
    assert d14.render(1 / 3, 2) == "0.33"
    assert d14.render(1 / 3, 8) == "0.33333333"


# --- the vector ---------------------------------------------------------------


def test_the_vector_states_the_window_it_was_computed_over(harness):
    """A number without its window is not re-derivable from the record."""
    _conj(harness, "a")
    _conj(harness, "b")
    v = d14.diagnostics(harness, _cfg())
    assert v.n == harness._next_seq - 1
    assert v.m == Config().CAPTURE14_WINDOW
    assert v.h == Config().CAPTURE14_AGE_FLOOR
    assert v.precision == Config().CAPTURE14_PRECISION


def test_the_vector_carries_exactly_six_diagnostics_in_a_fixed_order(harness):
    _conj(harness, "a")
    v = d14.diagnostics(harness, _cfg())
    assert len(d14.CAPTURE14_SIGNALS) == 6
    assert len(v.values()) == 6
    assert d14.CAPTURE14_SIGNALS == (
        "capture14.stream-contraction.v1",
        "capture14.attack-target-entropy.v1",
        "capture14.criticism-debt.v1",
        "capture14.reinstatement-rate.v1",
        "capture14.validity-attack-rate.v1",
        "capture14.exogenous-grounding-ratio.v1",
    )


def test_two_computations_over_one_record_are_byte_identical(harness):
    """A2/A10: a deterministic function of the record. Not `approx` -- BYTES."""
    a = _conj(harness, "a")
    _conj(harness, "b")
    _warrant(harness, a.id, "one")
    first = d14.diagnostics(harness, _cfg())
    second = d14.diagnostics(harness, _cfg())
    assert first.model_dump_json() == second.model_dump_json()


def test_every_diagnostic_has_a_declared_signal():
    """`DR-REC-add-signal`: emitted tags are declared, or the AST scan in
    tests/test_signals.py fails. Asserted here too, at the definition site."""
    from deepreason.signals import declaration

    for name in d14.CAPTURE14_SIGNALS:
        decl = declaration(name)
        assert decl is not None, name
        assert decl.unit != "unspecified" and decl.staleness != "unspecified"


# --- the property that makes them replayable ----------------------------------


def test_no_diagnostic_reads_wall_clock():
    """§15.1's "no hidden mutable input", enforced structurally.

    An AST scan rather than a grep: a grep for `datetime` misses
    `from datetime import datetime as dt`, and a grep for `.ts` hits every
    attribute ending in those two letters. Every import and every attribute
    access in the module is inspected.
    """
    source = pathlib.Path(d14.__file__).read_text()
    tree = ast.parse(source)
    forbidden_modules = {"time", "datetime", "random", "os"}
    imported = set()
    attributes = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
        elif isinstance(node, ast.Attribute):
            attributes.add(node.attr)
    assert not (imported & forbidden_modules), imported & forbidden_modules
    assert "ts" not in attributes, "a diagnostic read Event.ts"
    assert "now" not in attributes and "monotonic" not in attributes
