"""The wander cap: a floor on the operator-seeded lineage's share of attention.

The measurement (W6, `experiments/2026-08-26-run-anatomy-program/W6-token-flow/`,
P-C1 ARM H, 702 789 tokens):

    the operator's seed question         61 calls   373 903   53.2 %
    audit:ritual, spawned by the run    203 calls   289 676   41.2 %

`audit:ritual` -- "audit the critic: adjudication-ritual flags sustained
(§11.3)" -- appeared at log seq 345 of 3 200 and then spawned
`disc:audit:ritual`. Before it the run spent 100 % of its budget on the
operator's question; after it, 48.3 %. Nothing was unlawful. There was simply
no floor.

Operator, 2026-08-26 (tranche instruction): "the operator-seeded lineage gets a
declared budget-share FLOOR ... self-spawned problem lineages beyond the
floor's complement are deprioritized by the existing attention/allocation
machinery, with a typed disclosure when throttling engages -- attention only,
never labels (the efficiency-never-evidence boundary; mutation-prove it)."

Tranche: experiments/2026-08-26-change-f3-channels-and-wander-cap/ (S9-S14, S16).
"""

import json

import pytest

from deepreason import wander
from deepreason.config import Config
from deepreason.llm.adapter import LLMAdapter
from deepreason.ontology import Problem, ProblemProvenance, Rule
from deepreason.scheduler.scheduler import Scheduler


# --- S9: the policy, as arithmetic ----------------------------------------- #


def test_the_shipped_policy_engages_below_the_floor_and_not_at_it():
    """The boundary is >=, not >: a run exactly AT its floor is not in
    violation of it, and throttling there would make the floor a target."""
    at = wander.LineageReading(cycles=10, seed_worked=5, other_worked=5, floor=0.5)
    below = wander.LineageReading(cycles=10, seed_worked=4, other_worked=6, floor=0.5)

    assert wander.decide(Config(), at).engaged is False
    assert wander.decide(Config(), below).engaged is True
    assert wander.decide(Config(), below).share == pytest.approx(0.4)


def test_an_empty_record_is_not_a_violation():
    """Before the first cycle the share is 1.0, not 0.0.

    A run that has worked nothing has not yet failed its floor. Treating an
    empty record as a violation would throttle cycle 0 -- the one cycle the
    operator's question is guaranteed outright by the scheduler's oldest
    tie-break rule (selfstudy run-9175f0ec, which spent a whole 200k budget in
    a connection problem that won cycle 0 on the bare id).
    """
    empty = wander.LineageReading(cycles=0, seed_worked=0, other_worked=0, floor=0.9)

    decision = wander.decide(Config(), empty)
    assert decision.engaged is False
    assert decision.share == 1.0


def test_the_policy_is_selected_by_id_and_a_typo_discloses():
    """The VERSIONED layer: a different throttle is a configuration.

    And an unknown id falls back to the shipped default and SAYS SO, rather
    than refusing -- the all-configurations law. A typo must not be terminal
    for a run that is otherwise entirely lawful.
    """
    reading = wander.LineageReading(
        cycles=10, seed_worked=1, other_worked=9, floor=0.5
    )

    assert wander.decide(Config(), reading).policy_id == "wander-cap.v1"
    off = wander.decide(
        Config(ATTENTION_ALLOCATION_POLICY="open-lineage.v1"), reading
    )
    assert off.policy_id == "open-lineage.v1" and off.engaged is False

    typo = wander.decide(Config(ATTENTION_ALLOCATION_POLICY="wander-cap.v2"), reading)
    assert typo.policy_id == "wander-cap.v1"
    assert typo.fallback_from == "wander-cap.v2"
    assert typo.engaged is True


def test_a_floor_change_is_pure_configuration():
    """Two Config values, two decisions, no source edit anywhere."""
    reading = wander.LineageReading(
        cycles=10, seed_worked=4, other_worked=6, floor=0.0
    )
    strict = wander.reading_from(
        Config(SEED_PROBLEM_BUDGET_FLOOR=0.9), cycles=10, seed_worked=4
    )
    loose = wander.reading_from(
        Config(SEED_PROBLEM_BUDGET_FLOOR=0.1), cycles=10, seed_worked=4
    )

    assert wander.decide(Config(), strict).engaged is True
    assert wander.decide(Config(), loose).engaged is False
    assert reading.floor == 0.0  # the reading carries the floor, not the policy


# --- S10/S16: the offline stub run with an aggressive self-spawner --------- #


def _seed_problem(harness, pid="the-operators-question"):
    return harness.register_problem(
        Problem(
            id=pid,
            description="what governs the tides",
            criteria=[],
            provenance=ProblemProvenance.model_validate(
                {"trigger": "seed", "from": []}
            ),
        )
    )


def _spawn(harness, n, source):
    """One self-spawned problem, of the kind W6 measured.

    `audit-critic` is not decoration: it is the exact trigger the run that
    burned 41.2 % of its budget used, recorded in that root's own provenance
    as `{"trigger": "audit-critic"}`.
    """
    return harness.register_problem(
        Problem(
            id=f"audit:ritual:{n}",
            description=f"audit the critic: adjudication-ritual flags ({n})",
            criteria=[],
            provenance=ProblemProvenance.model_validate(
                {"trigger": "audit-critic", "from": [source]}
            ),
        )
    )


def _scheduler(harness, **config_kwargs):
    """A scheduler with NO seats: selection is attention and reaches no
    provider, so an empty adapter is the honest fixture."""
    return Scheduler(harness, LLMAdapter({}, harness.blobs), Config(**config_kwargs))


def _drive(scheduler, harness, seed, cycles):
    """Drive selection against a spawner that mints a new problem every cycle.

    The scheduler's own `_select_problem` is under test, driven the way a run
    drives it -- selecting, then advancing the cycle counter -- so the
    candidacy gate, the counters and the disclosure all run for real. The
    spawner is deliberately AGGRESSIVE: without a floor the growing pool of
    never-worked self-spawned problems out-ages the seed on every cycle.
    """
    picked = []
    for n in range(cycles):
        _spawn(harness, n, seed.id)
        problem = scheduler._select_problem()
        # Selection STASHES its decision and writes nothing -- it is a
        # read-only ranking function and a replay harness refuses writes. The
        # cycle body emits, so the driver does too, in the same order.
        scheduler._disclose_wander()
        picked.append(None if problem is None else problem.id)
        scheduler._cycles += 1
    return picked


def test_the_floor_holds_against_an_aggressive_self_spawner(harness):
    seed = _seed_problem(harness)
    scheduler = _scheduler(harness, SEED_PROBLEM_BUDGET_FLOOR=0.5)

    picked = _drive(scheduler, harness, seed, cycles=20)

    seed_share = picked.count(seed.id) / len(picked)
    assert seed_share >= 0.5, (seed_share, picked)
    assert scheduler._seed_cycles == picked.count(seed.id)


def test_without_the_cap_the_same_spawner_starves_the_seed(harness):
    """The control arm, and the reason the test above is not vacuous.

    If the seed lineage held its share anyway, the cap would be proving
    nothing. The same graph under `open-lineage.v1` is what shows the pressure
    is real.
    """
    seed = _seed_problem(harness)
    scheduler = _scheduler(
        harness,
        SEED_PROBLEM_BUDGET_FLOOR=0.5,
        ATTENTION_ALLOCATION_POLICY="open-lineage.v1",
    )

    picked = _drive(scheduler, harness, seed, cycles=20)

    uncapped_share = picked.count(seed.id) / len(picked)
    assert uncapped_share < 0.5, (uncapped_share, picked)


def test_the_throttle_never_loses_a_cycle(harness):
    """A floor may not empty the pool.

    Every cycle must still select SOMETHING: a gate that could return None to
    protect a lineage would be spending cycles to save them.

    With the floor at 1.0 the cap is as aggressive as it can be, and the shape
    it produces is worth stating exactly rather than rounding off. Cycle 0 is
    never throttled (an empty record is not a violation) and neither is the
    cycle after it, because a share of 1/1 is not BELOW a floor of 1.0. From
    the first cycle the seed does not win on age, the share drops under the
    floor and the gate holds every cycle thereafter. One self-spawned cycle,
    then seeded work forever -- which is what a floor of "all of it" means for
    a scheduler that also may not starve anything.
    """
    seed = _seed_problem(harness)
    scheduler = _scheduler(harness, SEED_PROBLEM_BUDGET_FLOOR=1.0)

    picked = _drive(scheduler, harness, seed, cycles=12)

    assert all(pid is not None for pid in picked), picked
    events = _measures(harness, "allocation.wander-throttled.v1")
    assert events, "the floor never engaged, so this proves nothing"
    # Once engaged, every later cycle is seeded work.
    first_throttled = next(
        i
        for i, reading in enumerate(
            _measures(harness, "allocation.seed-lineage-share.v1")
        )
        if float(reading[1]) < 1.0
    )
    assert set(picked[first_throttled:]) == {seed.id}, picked
    assert picked.count(seed.id) >= len(picked) - 1, picked


def test_a_throttle_with_no_seeded_work_left_yields(harness):
    """The gate holds candidacy only while seeded work exists.

    With no seed problem at all the floor can never be met, so a gate that
    filtered unconditionally would select nothing forever. It must yield.
    """
    root = harness.register_problem(
        Problem(
            id="not-a-seed",
            description="a problem the run invented",
            criteria=[],
            provenance=ProblemProvenance.model_validate(
                {"trigger": "audit-critic", "from": []}
            ),
        )
    )
    scheduler = _scheduler(harness, SEED_PROBLEM_BUDGET_FLOOR=0.9)

    picked = _drive(scheduler, harness, root, cycles=6)

    assert all(pid is not None for pid in picked), picked
    assert scheduler._seed_cycles == 0


# --- S11: the typed disclosure and the attackable policy artifact ---------- #


def _measures(harness, tag):
    return [
        list(event.inputs)
        for event in harness.log.read()
        if event.inputs and event.inputs[0] == tag
    ]


def test_the_share_signal_is_emitted_every_cycle(harness):
    seed = _seed_problem(harness)
    scheduler = _scheduler(harness, SEED_PROBLEM_BUDGET_FLOOR=0.5)

    _drive(scheduler, harness, seed, cycles=8)

    readings = _measures(harness, "allocation.seed-lineage-share.v1")
    assert len(readings) == 8
    assert all(len(r) == 3 for r in readings)
    assert all(0.0 <= float(r[1]) <= 1.0 for r in readings)
    assert {r[2] for r in readings} == {"0.500000"}


def test_the_throttle_discloses_once_per_engagement(harness):
    """Emitted on the TRANSITION, not every cycle.

    One decision must not read as fifty in the record, and a reader counting
    throttle events is counting decisions.
    """
    seed = _seed_problem(harness)
    scheduler = _scheduler(harness, SEED_PROBLEM_BUDGET_FLOOR=0.5)

    _drive(scheduler, harness, seed, cycles=20)

    events = _measures(harness, "allocation.wander-throttled.v1")
    assert events, "the throttle never engaged, so this test proves nothing"
    assert len(events) < 20
    tag, policy_id, disclosure = events[0]
    assert policy_id == "wander-cap.v1"
    assert "floor" in disclosure and "share" in disclosure


def test_the_engaged_policy_is_a_registered_attackable_artifact(harness):
    """Calculus P6: a limit nobody can contest is a status privilege.

    The same design `controller.py::_emit_policy` and `capture/hysteresis.py`
    already carry -- and the ONE artifact the evidence differential excludes.
    """
    seed = _seed_problem(harness)
    scheduler = _scheduler(harness, SEED_PROBLEM_BUDGET_FLOOR=0.5)

    _drive(scheduler, harness, seed, cycles=20)

    bodies = []
    for event in harness.log.read():
        if event.rule != Rule.REFL:
            continue
        for aid in event.outputs:
            artifact = harness.state.artifacts.get(aid)
            content = getattr(artifact, "content_ref", "") or ""
            if content.startswith("inline:"):
                try:
                    body = json.loads(content[len("inline:"):])
                except ValueError:
                    continue
                if body.get("schema") == "allocation.wander-cap.v1":
                    bodies.append((aid, body, artifact))

    assert bodies, "the throttle engaged but registered no policy artifact"
    aid, body, artifact = bodies[0]
    assert artifact.provenance.role.value == "controller"
    assert body["policy"] == "wander-cap.v1"
    assert body["share"] < body["floor"]
    # Attackable means it is IN the graph like any other artifact.
    assert aid in harness.state.artifacts


def test_the_open_policy_emits_the_reading_but_never_the_throttle(harness):
    """Selecting the null policy silences the event, not the reading.

    A run that turned the cap off should still be able to say what its share
    WAS -- the reading is a measurement, and only the throttle is a decision.
    """
    seed = _seed_problem(harness)
    scheduler = _scheduler(
        harness,
        SEED_PROBLEM_BUDGET_FLOOR=0.5,
        ATTENTION_ALLOCATION_POLICY="open-lineage.v1",
    )

    _drive(scheduler, harness, seed, cycles=12)

    assert len(_measures(harness, "allocation.seed-lineage-share.v1")) == 12
    assert _measures(harness, "allocation.wander-throttled.v1") == []


# --- S12: attention only, never labels ------------------------------------- #


def _epistemic_state(harness) -> dict:
    """Everything adjudication owns, with the controller's OWN artifacts out.

    An allocation policy is an ordinary registered artifact and therefore has
    a status of its own -- that is the design (P6), not a leak. The claim under
    test is that no OTHER artifact's label, and no edge, moves because the
    throttle ran. Identical in shape to the allocation suite's own helper.
    """
    controller_owned = {
        aid
        for aid, artifact in harness.state.artifacts.items()
        if artifact.provenance.role.value == "controller"
    }
    return {
        "status": {
            aid: status.value
            for aid, status in harness.state.status.items()
            if aid not in controller_owned
        },
        "att": sorted(
            edge for edge in harness.state.att if not set(edge) & controller_owned
        ),
        "dep": sorted(
            edge for edge in harness.state.dep if not set(edge) & controller_owned
        ),
        "carries": sorted(
            pair for pair in harness.state.carries if not set(pair) & controller_owned
        ),
        "artifacts": sorted(set(harness.state.artifacts) - controller_owned),
    }


def _scripted_epistemic_content(harness):
    """A conjecture, a critic's validity node, and an argumentative warrant.

    A differential over an empty graph proves nothing -- every label would be
    trivially equal -- so this puts a real adjudication in front of the
    comparison. The only criticism is PROSE, which is also what makes this the
    guard on "this doesn't demote prose as legitimate criticism".
    """
    from deepreason.ontology import Provenance, Warrant, WarrantType

    conjecture = harness.create_artifact(
        "x: the tides follow the moon", provenance=Provenance(role="conjecturer")
    )
    nu = harness.create_artifact(
        "nu: the attack is sound", provenance=Provenance(role="critic")
    )
    harness.create_artifact(
        "critic: the mechanism is not load-bearing",
        provenance=Provenance(role="critic"),
        warrants=[
            Warrant(
                id="w:attack:x",
                target=conjecture.id,
                type=WarrantType.ARGUMENTATIVE,
                validity_node=nu.id,
            )
        ],
        rule=Rule.CRIT,
    )
    return conjecture.id


def test_labels_are_identical_whether_or_not_the_cap_engaged(tmp_path):
    """The load-bearing guard: two arms, the same scripted record.

    One arm runs the wander cap hard enough to throttle every cycle; the other
    runs the null policy and never throttles. If a throttle -- or anything
    derived from one -- ever reaches a label, a warrant or an edge, the two
    arms diverge here.
    """
    from deepreason.harness import Harness

    capped = Harness(tmp_path / "capped")
    uncapped = Harness(tmp_path / "uncapped")
    for harness, policy in ((capped, "wander-cap.v1"), (uncapped, "open-lineage.v1")):
        _scripted_epistemic_content(harness)
        seed = _seed_problem(harness)
        scheduler = _scheduler(
            harness,
            SEED_PROBLEM_BUDGET_FLOOR=0.9,
            ATTENTION_ALLOCATION_POLICY=policy,
        )
        _drive(scheduler, harness, seed, cycles=10)

    # The two arms really did behave differently, or this compares a thing
    # with itself.
    assert _measures(capped, "allocation.wander-throttled.v1")
    assert _measures(uncapped, "allocation.wander-throttled.v1") == []

    assert _epistemic_state(capped) == _epistemic_state(uncapped), (
        "the wander cap changed the epistemic record: allocation touches "
        "efficiency, never evidence"
    )


def test_the_wander_module_constructs_no_evidence():
    """The structural half of the guard.

    `DR-INV-signal-contract` requires this of `allocation.py` and of
    `capture/hysteresis.py`; the same standard applies to a third policy
    module. Unlike those two, `wander.py` may not even create the policy
    artifact -- the scheduler does that -- so its list is the strictest.
    """
    import pathlib

    source = pathlib.Path("src/deepreason/wander.py").read_text(encoding="utf-8")
    body = "\n".join(
        line for line in source.splitlines() if not line.strip().startswith("#")
    )
    for forbidden in (
        "create_artifact",
        "att_add",
        "dep_add",
        "Warrant",
        "Status",
        "_adjudicate",
        "register_fail_warrant",
    ):
        assert forbidden not in body, forbidden
    # And it imports no subsystem at all: a policy that had to be taught about
    # one has left the interface.
    assert "from deepreason" not in body
    assert "import deepreason" not in body


# --- S13: the phantom signals now carry values ----------------------------- #


def test_the_four_phantom_allocation_signals_are_emitted(tmp_path):
    """W5's structural silence, closed.

    Four of five `allocation.POLICY_SIGNALS` were declared, consumed in
    process, and emitted nowhere in `src/` -- so no committed root carries the
    numbers that moved a cap. None was struck: all four are genuinely
    consumed, and striking a consumed signal would make the registry LESS true.
    """
    from deepreason.controller import Controller
    from tests.test_route_lease_maxtokens_tuning import (
        LEASED_CAP,
        QUALIFIED_WINDOW,
        _log_conjecturer_calls,
        _seat,
    )

    harness, adapter, _lease, _endpoint = _seat(
        tmp_path, max_tokens=LEASED_CAP, context_window_tokens=QUALIFIED_WINDOW
    )
    controller = Controller(harness, adapter)
    _log_conjecturer_calls(harness, n=6, truncated=False)
    controller.step()

    truncation = _measures(harness, "allocation.seat-truncation.v1")
    repair = _measures(harness, "allocation.seat-repair.v1")
    assert truncation and repair
    for reading in truncation + repair:
        assert reading[1] == "conjecturer"  # keyed by SEAT INSTANCE
        assert 0.0 <= float(reading[2]) <= 1.0


def test_no_policy_referenced_signal_is_left_without_an_emit_site():
    """The census, as a test rather than as a one-off audit.

    Every name in `allocation.POLICY_SIGNALS` must appear as a literal at an
    emit site in `src/`. This is the check whose absence let four names sit
    declared-and-silent for months; it goes RED the day a fifth joins them.
    """
    import pathlib

    roots = [
        pathlib.Path("src/deepreason/controller.py"),
        pathlib.Path("src/deepreason/scheduler/scheduler.py"),
    ]
    emitted = "\n".join(p.read_text(encoding="utf-8") for p in roots)

    from deepreason import allocation

    for name in allocation.POLICY_SIGNALS:
        if name == "dropped-call":
            # The one that always had an emit site: the drop site tags it.
            continue
        assert f'"{name}"' in emitted, name


# --- P12: capability cycles, the denominator, and the silence -------------- #


def _capability_step_stub(index):
    """The shipped capability step's observable contract, and nothing else.

    `_simulation_capability_step` emits a `cycle` heartbeat naming the package
    or proposal it is working (`scheduler.py:1802`, `1950`, `2030`) and returns
    True to claim the cycle. A stub of exactly that lets `Scheduler.step()` run
    the SHIPPED capability branch -- the code under test -- without binding a
    seat or a capability controller.
    """

    def step(self):
        self.harness.record_measure(
            inputs=[
                "cycle",
                str(self._cycles),
                f"simulation-result:sha256:{index:064x}",
            ]
        )
        return True

    return step


def _drive_mixed(scheduler, harness, seed, plan, monkeypatch):
    """Drive a run whose cycles are a mix of capability and selection cycles.

    CAPABILITY cycles call the real `Scheduler.step()`; only
    `_simulation_capability_step` is stubbed, to the heartbeat-and-True above.
    The branch that early-returns is therefore exercised as it ships, which is
    the whole point -- the defect is in the branch, not in the step.

    SELECTION cycles are driven the way `_drive` above drives them, because
    `step()`'s selection path continues into conjecture and this fixture binds
    no seats. Same three-line contract: select, emit, advance.
    """
    taken = []
    for index, kind in enumerate(plan):
        if kind == "capability":
            monkeypatch.setattr(
                Scheduler, "_simulation_capability_step", _capability_step_stub(index)
            )
            scheduler.step()
            taken.append("capability")
            continue
        _spawn(harness, index, seed.id)
        problem = scheduler._select_problem()
        harness.record_measure(
            inputs=["cycle", str(scheduler._cycles), problem.id if problem else "-"]
        )
        scheduler._disclose_wander()
        scheduler._cycles += 1
        taken.append(problem.id if problem else "-")
    return taken


# Epoch 1's committed share trajectory, verbatim from
# `experiments/2026-08-28-audit-run-problems/probes/q3_cycle_accounting.json`
# (root `completed-epoch1-run-92e63dcb...a97e3`, 12 cycles, 12 readings,
# 5 throttles, zero capability cycles). The offline spawner below reproduces
# it exactly, which is what makes it usable as a bit-for-bit pin.
_EPOCH1_TRAJECTORY = [
    "1.000000",
    "1.000000",
    "0.500000",
    "0.333333",
    "0.500000",
    "0.400000",
    "0.500000",
    "0.428571",
    "0.500000",
    "0.444444",
    "0.500000",
    "0.454545",
]


def test_the_offline_spawner_reproduces_epoch_1_bit_for_bit(harness):
    """S3, the control: a run with NO capability cycles must not move.

    This is the arm the fix may not disturb. Epoch 1 is the live root where the
    cap was measured working -- 12 readings over 12 cycles, the throttle
    pulling the share back to the floor five times -- and it had zero
    capability cycles. Pinning its trajectory here makes any change to the
    non-capability path visible as a byte difference rather than as a
    plausible-looking number.
    """
    seed = _seed_problem(harness)
    scheduler = _scheduler(harness, SEED_PROBLEM_BUDGET_FLOOR=0.5)

    _drive(scheduler, harness, seed, cycles=12)

    readings = _measures(harness, "allocation.seed-lineage-share.v1")
    assert [r[1] for r in readings] == _EPOCH1_TRAJECTORY
    assert {r[2] for r in readings} == {"0.500000"}
    throttles = _measures(harness, "allocation.wander-throttled.v1")
    assert len(throttles) == 5
    assert throttles[0] == [
        "allocation.wander-throttled.v1",
        "wander-cap.v1",
        "wander-cap.v1: seed-lineage share 0.3333 below floor 0.5000",
    ]


def test_capability_cycles_do_not_dilute_the_floor(harness, monkeypatch):
    """Regression (P-T1 epoch 6, audit finding F-F, parked P12).

    Epoch 6 ran 24 cycles: 20 taken by the simulation capability step and 4 by
    problem selection. It emitted 4 seed-lineage-share readings. Each of the 20
    advanced `self._cycles` -- the share's denominator -- while
    `_seed_cycles` and `wander.decide` sat below an early return it never
    reached, so work that IS the operator's own experiment diluted the floor
    meant to protect the operator's question, invisibly.

    The rule this pins: a capability cycle selects no problem, so the throttle
    has no candidacy to restrict on it. It is therefore counted OUT of the
    policy's denominator and the share it reads is unchanged across it. What is
    NOT excluded is the disclosure: the reading is emitted on every cycle that
    advanced the counter, so 20 cycles of silence cannot be mistaken for
    20 cycles of stability.
    """
    seed = _seed_problem(harness)
    scheduler = _scheduler(harness, SEED_PROBLEM_BUDGET_FLOOR=0.5)

    plan = ["selection"] * 4 + ["capability"] * 20
    _drive_mixed(scheduler, harness, seed, plan, monkeypatch)

    assert scheduler._cycles == 24
    heartbeats = [
        list(event.inputs)
        for event in harness.log.read()
        if event.inputs and event.inputs[0] == "cycle"
    ]
    assert len(heartbeats) == 24

    readings = _measures(harness, "allocation.seed-lineage-share.v1")
    # No silence: one reading per cycle that advanced the counter.
    assert len(readings) == 24
    # The four selection cycles read exactly what epoch 6 recorded.
    assert [r[1] for r in readings[:4]] == [
        "1.000000",
        "1.000000",
        "0.500000",
        "0.333333",
    ]
    # And the twenty capability cycles moved the denominator not at all: two
    # seeded selection cycles out of four governed cycles is 0.5, at the floor,
    # for every one of them. Under the defect this figure is unrecorded; under
    # a denominator that counted capability cycles it would fall to 2/24.
    assert {r[1] for r in readings[4:]} == {"0.500000"}
    assert {r[2] for r in readings} == {"0.500000"}


def test_the_denominator_is_order_independent(harness, monkeypatch):
    """Interleaving must not change the accounting.

    Epoch 6's committed census gives the COUNTS -- 20 capability, 4 selection
    -- not the order they arrived in. If the share depended on where the
    capability cycles fell, this tranche could not state what epoch 6 would
    have recorded. It does not: the governed denominator counts selection
    cycles, and interleaving moves none of them.
    """
    seed = _seed_problem(harness)
    scheduler = _scheduler(harness, SEED_PROBLEM_BUDGET_FLOOR=0.5)

    plan = []
    for _ in range(4):
        plan.append("selection")
        plan.extend(["capability"] * 5)
    _drive_mixed(scheduler, harness, seed, plan, monkeypatch)

    readings = _measures(harness, "allocation.seed-lineage-share.v1")
    assert len(readings) == 24
    selection_readings = [
        r[1] for r, kind in zip(readings, plan) if kind == "selection"
    ]
    assert selection_readings == ["1.000000", "1.000000", "0.500000", "0.333333"]
    assert readings[-1][1] == "0.500000"


def test_a_capability_cycle_discloses_without_inventing_a_throttle(
    harness, monkeypatch
):
    """The throttle is an EVENT on a transition; a capability cycle is not one.

    The reading must be emitted on every cycle. The throttle record must not:
    a capability cycle restricts no candidacy, and a run that spent twenty
    cycles inside one experiment must not read as twenty throttling decisions.
    Because the governed counters cannot move across a capability cycle, the
    engagement state cannot transition on one either -- so this holds by
    construction, and this test is what says so out loud.
    """
    seed = _seed_problem(harness)
    scheduler = _scheduler(harness, SEED_PROBLEM_BUDGET_FLOOR=0.5)

    plan = ["selection"] * 4 + ["capability"] * 20
    _drive_mixed(scheduler, harness, seed, plan, monkeypatch)

    throttles = _measures(harness, "allocation.wander-throttled.v1")
    assert len(throttles) == 1
    assert throttles[0][2] == (
        "wander-cap.v1: seed-lineage share 0.3333 below floor 0.5000"
    )
    policy_artifacts = [
        event
        for event in harness.log.read()
        if event.rule == Rule.REFL
        for aid in event.outputs
        if "allocation.wander-cap.v1"
        in (getattr(harness.state.artifacts.get(aid), "content_ref", "") or "")
    ]
    assert len(policy_artifacts) == 1
