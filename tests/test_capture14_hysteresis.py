"""§14.7's hysteresis controller, and Theorem 14.1.

Implements R11 and R12 (v2 calculus program, Rung 8).

    §14.7  A deterministic hysteresis controller may enter a diversify-attention
    mode when a registered threshold predicate T_enter(D) holds and leave only
    when a stricter recovery predicate T_exit(D) holds. The mode may alter
    lineage quotas, render slices, retrieval balance, critic budgets, and
    variation budgets. It may not add or remove attack edges, dependency edges,
    or labels directly.

    Theorem 14.1  Two states with identical A_L, att_L and dep_L, but different
    diagnostic values or attention modes, have identical labels.

The theorem is EXHIBITED here, not assumed: the differential runs one scripted
record twice, once with the controller in each mode, and compares every label,
every edge and every warrant.
"""

import pathlib

import pytest

from deepreason.capture import hysteresis
from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.ontology import (
    Interface,
    Provenance,
    Rule,
    Status,
    Warrant,
    WarrantType,
)


def _script(harness):
    """One scripted record with attacks, a reinstatement and a validity node.

    Deliberately the same shape in both arms of the differential -- the arms
    differ ONLY in the controller's mode, which is what makes the comparison a
    test of Theorem 14.1 rather than of two different records.
    """
    made = []
    for i in range(4):
        made.append(
            harness.create_artifact(
                f"conjecture {i}",
                provenance=Provenance(role="seed"),
                rule=Rule.CONJ,
            )
        )
    nu = harness.create_artifact("nu: sound", provenance=Provenance(role="critic"))
    critic = harness.create_artifact(
        "critic: against 0",
        provenance=Provenance(role="critic"),
        warrants=[
            Warrant(
                id="w-0",
                target=made[0].id,
                type=WarrantType.ARGUMENTATIVE,
                validity_node=nu.id,
            )
        ],
    )
    nu2 = harness.create_artifact("nu: also sound", provenance=Provenance(role="critic"))
    harness.create_artifact(
        "critic: against the critic",
        provenance=Provenance(role="critic"),
        warrants=[
            Warrant(
                id="w-1",
                target=critic.id,
                type=WarrantType.ARGUMENTATIVE,
                validity_node=nu2.id,
            )
        ],
    )
    return made


def _snapshot(harness):
    """Everything Theorem 14.1 says may not move."""
    return {
        "labels": {a: s.value for a, s in sorted(harness.state.status.items())},
        "att": sorted(harness.state.att),
        "dep": sorted(harness.state.dep),
        "warrants": sorted(
            (w.id, w.target, w.validity_node, w.type.value)
            for w in harness.warrants.values()
        ),
    }


def _always_alarmed():
    """A config whose bands every diagnostic trips, so entry is decidable
    without hand-forging a diagnostic vector."""
    return Config(
        CAPTURE14_ENTER_K=1,
        CAPTURE14_EXIT_K=0,
        CAPTURE14_SC_CEILING=-1.0,   # SC above -1 is always "in band"
        ATTACK_ENTROPY_FLOOR=2.0,    # ATH below 2.0 is always "in band"
        CRIT_DEBT_CEILING=-1.0,
        LAMBDA_FLOOR=2.0,
    )


def _never_alarmed():
    return Config(
        CAPTURE14_ENTER_K=6,
        CAPTURE14_EXIT_K=5,
        CAPTURE14_SC_CEILING=2.0,
        ATTACK_ENTROPY_FLOOR=-1.0,
        CRIT_DEBT_CEILING=2.0,
        LAMBDA_FLOOR=-1.0,
    )


# --- Theorem 14.1 -------------------------------------------------------------


def test_theorem_14_1_two_modes_one_record_identical_labels(tmp_path):
    """THE gate obligation. The two arms differ only in the controller's mode.

    The controller's OWN policy artifact is excluded from the comparison, for
    the reason `allocation.py`'s differential excludes its own: a policy having
    a status is the design (P6, it must be attackable), not a leak.
    """
    snapshots = []
    policies = []
    for name, config in (("normal", _never_alarmed()), ("diversify", _always_alarmed())):
        harness = Harness(tmp_path / name)
        _script(harness)
        before = _snapshot(harness)
        decision = hysteresis.step(harness, config)
        after = _snapshot(harness)
        policy_id = None if decision is None else decision["policy"]
        policies.append((name, decision))
        # The policy artifact is the ONLY thing the step may add.
        for key in ("labels",):
            after[key] = {
                a: s for a, s in after[key].items() if a != policy_id
            }
        assert after == before, f"{name} moved something Theorem 14.1 forbids"
        snapshots.append(after)

    assert snapshots[0] == snapshots[1]
    modes = {name: (None if d is None else d["mode"]) for name, d in policies}
    assert modes["normal"] != modes["diversify"], (
        "the two arms did not actually differ in mode, so the differential "
        "compared a record with itself and proved nothing"
    )


def test_the_module_constructs_no_edge_no_label_and_no_warrant():
    """Structural, mirroring `DR-INV-signal-contract`'s check on allocation.py.

    `create_artifact` IS present and only for the policy itself; nothing that
    mints a warrant, an attack edge or a label may be.
    """
    source = pathlib.Path(hysteresis.__file__).read_text()
    for forbidden in (
        "att_add",
        "dep_add",
        "Warrant(",
        "register_fail_warrant",
        "_adjudicate",
        "state.status[",
    ):
        assert forbidden not in source, forbidden


# --- the hysteresis itself ----------------------------------------------------


def test_entry_needs_the_enter_predicate_and_exit_needs_a_stricter_one(tmp_path):
    harness = Harness(tmp_path / "run")
    _script(harness)
    alarmed = _always_alarmed()
    calm = _never_alarmed()

    first = hysteresis.step(harness, alarmed)
    assert first is not None and first["mode"] == "diversify"
    assert hysteresis.mode(harness) == "diversify"

    # The SAME alarmed state does not re-enter -- a mode already held is held.
    again = hysteresis.step(harness, alarmed)
    assert again is None or again["mode"] == "diversify"
    assert hysteresis.mode(harness) == "diversify"

    left = hysteresis.step(harness, calm)
    assert left is not None and left["mode"] == "normal"
    assert hysteresis.mode(harness) == "normal"


def test_a_state_that_enters_does_not_immediately_leave(tmp_path):
    """The asymmetry IS the hysteresis. Under one config, a state that trips
    T_enter must not simultaneously satisfy T_exit -- or the controller
    chatters across the boundary every cycle."""
    harness = Harness(tmp_path / "run")
    _script(harness)
    config = _always_alarmed()
    entered = hysteresis.step(harness, config)
    assert entered is not None and entered["mode"] == "diversify"
    for _ in range(3):
        hysteresis.step(harness, config)
        assert hysteresis.mode(harness) == "diversify"


def test_the_asymmetry_cannot_be_configured_away():
    """`Config` refuses a symmetric or inverted pair, so no configuration
    turns the controller into a toggle."""
    with pytest.raises(ValueError):
        Config(CAPTURE14_ENTER_K=2, CAPTURE14_EXIT_K=2)
    with pytest.raises(ValueError):
        Config(CAPTURE14_ENTER_K=2, CAPTURE14_EXIT_K=3)


# --- the policy artifact (R12) --------------------------------------------------


def test_the_policy_is_an_ordinary_attackable_artifact(tmp_path):
    """Policy-as-artifact, exactly as `Controller._emit_policy` already does:
    registered, replayable, and a legal warrant target."""
    harness = Harness(tmp_path / "run")
    _script(harness)
    decision = hysteresis.step(harness, _always_alarmed())
    assert decision is not None
    policy_id = decision["policy"]
    assert policy_id in harness.state.artifacts
    assert harness.state.status[policy_id] is Status.ACCEPTED

    nu = harness.create_artifact("nu: the policy is unjustified",
                                 provenance=Provenance(role="critic"))
    harness.create_artifact(
        "critic: this policy over-reads a single window",
        provenance=Provenance(role="critic"),
        warrants=[
            Warrant(id="w-policy", target=policy_id,
                    type=WarrantType.ARGUMENTATIVE, validity_node=nu.id)
        ],
    )
    assert harness.state.status[policy_id] is Status.REFUTED


def test_the_policy_states_its_bands_its_precision_and_its_vector(tmp_path):
    """A recorded artifact that does not say what it read is not reviewable,
    and `config_referee` is what reviews it (R12)."""
    harness = Harness(tmp_path / "run")
    _script(harness)
    decision = hysteresis.step(harness, _always_alarmed())
    body = hysteresis.policy_body(harness, decision["policy"])
    assert body["mode"] == "diversify"
    assert body["precision"] == Config().CAPTURE14_PRECISION
    assert set(body["bands"]) == set(hysteresis.BAND_NAMES)
    assert body["vector"]["m"] == Config().CAPTURE14_WINDOW
    assert body["enter_k"] == 1 and body["exit_k"] == 0


def test_the_four_absent_levers_are_disclosed_with_a_resolution_each(tmp_path):
    """§14.7 names five levers; this tree has one. Disclose, never fake --
    `allocation.open_loop_signals`'s established shape, applied to levers."""
    harness = Harness(tmp_path / "run")
    _script(harness)
    decision = hysteresis.step(harness, _always_alarmed())
    body = hysteresis.policy_body(harness, decision["policy"])
    assert set(body["adjustments"]) == {"render_slices"}
    assert set(body["no_lever"]) == {
        "lineage_quotas",
        "retrieval_balance",
        "critic_budgets",
        "variation_budgets",
    }
    for lever, resolution in body["no_lever"].items():
        assert resolution and isinstance(resolution, str), lever
    assert "allocation" in body["no_lever"]["critic_budgets"].lower()


# --- the one lever that exists ---------------------------------------------------


def test_diversify_widens_the_slice_budgets_and_normal_does_not(tmp_path):
    harness = Harness(tmp_path / "run")
    _script(harness)
    config = _always_alarmed()
    assert hysteresis.slice_budgets(harness, config) == (
        config.FRAME_SLICE_ATTACKERS,
        config.FRAME_SLICE_DEPARTURES,
    )
    hysteresis.step(harness, config)
    widened = hysteresis.slice_budgets(harness, config)
    assert widened[0] > config.FRAME_SLICE_ATTACKERS
    assert widened[1] > config.FRAME_SLICE_DEPARTURES


def test_slice_budgets_fall_back_to_config_on_a_record_with_no_policy(tmp_path):
    """The absence-tolerant reader (SPEC.md §10): every root written before
    this rung has no policy, and must read exactly as it did."""
    harness = Harness(tmp_path / "run")
    _script(harness)
    config = Config()
    assert hysteresis.mode(harness) == "normal"
    assert hysteresis.slice_budgets(harness, config) == (
        config.FRAME_SLICE_ATTACKERS,
        config.FRAME_SLICE_DEPARTURES,
    )


def test_the_widened_budgets_are_the_ones_the_policy_authorised(tmp_path):
    """Replay determinism: the render must not re-derive a widening, it must
    read the one the record says was authorised."""
    harness = Harness(tmp_path / "run")
    _script(harness)
    config = _always_alarmed()
    decision = hysteresis.step(harness, config)
    body = hysteresis.policy_body(harness, decision["policy"])
    authorised = body["adjustments"]["render_slices"]
    assert hysteresis.slice_budgets(harness, config) == (
        authorised["attackers"],
        authorised["departures"],
    )
