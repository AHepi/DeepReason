"""Q3 ROAD B: the production dispatch site, and the asymmetry it preserves.

Operator law, 2026-08-29: a filled successor question "goes to scratchpad by
default, linked to the problem it was proposed under". As delivered, nothing in
production called `route` -- the channel was built, tested and mutation-proved,
and a live run recorded the field and routed nothing. That gap is one call site
wide, and WHERE that site lives was the operator's Q3 decision.

Road B, taken: a reader OUTSIDE `src/deepreason/rules/` walks what criticism
already recorded and routes what it finds. `DR-SEAM-rules-x-scratch` rule 6 --
"Never widen the criticism side to close the asymmetry ... Overturning it is an
operator's call, not an implementer's" -- therefore survives AS WRITTEN, and
the first test below is the measurement of that, not a claim about it.

What is asserted here:

- `rules/crit.py` takes a ZERO-LINE DIFF, measured with `git diff --stat`;
- a recorded successor question reaches the scratchpad, linked to the problem,
  through the PRODUCTION entry rather than a hand call to `route`;
- dispatch is IDEMPOTENT over an unchanged record, which is what makes a
  resumed run safe -- a module flag would forget and double-route;
- both wire shapes are read: the single critic's top-level field and the
  batch's per-case fields;
- a proposal whose link cannot be established is DISCLOSED, never guessed and
  never silently dropped;
- the minting road is still off unless a run switches it on, and still refuses
  to invent a target it cannot resolve.
"""

from __future__ import annotations

import json
import subprocess

from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.ontology import Commitment, Problem, ProblemProvenance, Rule
from deepreason.ontology.event import LLMCall
from deepreason.ontology.artifact import Provenance
from deepreason.successor import dispatch_recorded_proposals, recorded_proposals
from deepreason.successor.reader import DISPATCH_RECEIPT_PREFIX

PROBLEM_ID = "pi-successor-dispatch"
QUESTION = "what would settle whether the solar term is measurable at all?"
OTHER_QUESTION = "and what would a null result look like?"


class _Defaults:
    """A configuration naming nothing: the shipped defaults."""


class _Minting:
    SUCCESSOR_MINTING_ENABLED = True


def _seed(harness) -> Problem:
    harness.register_commitment(
        Commitment(id="k-tide", eval="predicate:'tide' in content")
    )
    return harness.register_problem(
        Problem(
            id=PROBLEM_ID,
            description="explain the tide table for this harbour",
            criteria=["k-tide"],
            provenance=ProblemProvenance.model_validate(
                {"trigger": "seed", "from": []}
            ),
        )
    )


def _target(harness, text: str = "the tide peaks twice daily"):
    """A candidate addressing the seed problem: what a critic criticises."""
    return harness.create_artifact(
        text,
        provenance=Provenance(role="conjecturer"),
        problem_id=PROBLEM_ID,
    )


def _critic_call(harness, raw: dict) -> LLMCall:
    return LLMCall(
        role="argumentative_critic",
        model="m",
        endpoint="e",
        prompt_ref=harness.blobs.put(b"prompt"),
        raw_ref=harness.blobs.put(json.dumps(raw).encode()),
    )


def _record_criticism(harness, target_id: str, raw: dict, case: str = "fails at neap"):
    """Exactly what `rules/crit.py::_observe_case` leaves on the record: a
    critic-role artifact carrying the LLM call, plus the scrutiny Measure that
    links it to its target. Built here rather than by calling `crit.py`,
    because a test that drove the real critic would need a provider."""
    critic = harness.create_artifact(
        case,
        provenance=Provenance(role="critic"),
        rule=Rule.CRIT,
        llm=_critic_call(harness, raw),
    )
    harness.record_measure(inputs=["scrutiny", target_id, critic.id])
    return critic


def _receipts(harness, prefix: str) -> list[list[str]]:
    return [
        list(event.inputs)
        for event in harness.log.read()
        if event.inputs and event.inputs[0].startswith(prefix)
    ]


def _blocks(harness) -> list:
    return list(harness.scratch_state.blocks.values())


# --- the asymmetry survives, and this is the measurement -------------------- #


def test_rules_crit_takes_a_zero_line_diff():
    """The whole point of road B. If this goes red, the criticism side was
    widened after all and `DR-SEAM-rules-x-scratch` rule 6 was overturned by an
    implementer rather than by the operator."""
    diff = subprocess.run(
        ["git", "diff", "--stat", "origin/main", "--", "src/deepreason/rules/crit.py"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert diff.stdout.strip() == "", diff.stdout


def test_the_dispatch_site_is_outside_rules():
    """The reader's own location, asserted rather than assumed: a module that
    drifted into `rules/` would pass every other test in this file."""
    import deepreason.successor.reader as reader

    assert "/deepreason/rules/" not in reader.__file__.replace("\\", "/")
    assert reader.__name__ == "deepreason.successor.reader"


def test_no_module_under_rules_imports_the_successor_package():
    """The blunter half. `crit.py` importing `deepreason.successor` late, from
    inside a function body, would leave the `git diff` test above red -- but a
    NEW module under `rules/` would not, and this catches that."""
    import pathlib

    rules = pathlib.Path("src/deepreason/rules")
    offenders = [
        str(path)
        for path in rules.rglob("*.py")
        if "deepreason.successor" in path.read_text(encoding="utf-8")
    ]
    assert offenders == [], offenders


# --- the channel is LIVE: recorded -> routed -------------------------------- #


def test_a_recorded_question_reaches_the_scratchpad_linked_to_its_problem(tmp_path):
    """R2, end to end through the PRODUCTION entry. Before road B this was
    provable only by calling `route` by hand."""
    harness = Harness(tmp_path / "run")
    _seed(harness)
    target = _target(harness)
    _record_criticism(harness, target.id, {"attack": True, "successor_question": QUESTION})

    assert dispatch_recorded_proposals(harness, _Defaults()) == 1

    blocks = _blocks(harness)
    assert len(blocks) == 1, blocks
    assert blocks[0].provenance.origin == PROBLEM_ID
    assert blocks[0].provenance.actor == "llm"
    assert QUESTION in json.dumps(blocks[0].body.model_dump(mode="json"))

    routed = _receipts(harness, "successor-question:")
    assert routed == [["successor-question:ROUTED", "scratchpad.v1", PROBLEM_ID]], routed


def test_an_unfilled_field_dispatches_nothing_at_all(tmp_path):
    """The uninvited-dispatch rule reaching the reader: silence in the record
    means "nothing was proposed", never "something was dropped"."""
    harness = Harness(tmp_path / "run")
    _seed(harness)
    target = _target(harness)
    _record_criticism(harness, target.id, {"attack": True})

    assert recorded_proposals(harness) == ()
    assert dispatch_recorded_proposals(harness, _Defaults()) == 0
    assert _blocks(harness) == []
    assert _receipts(harness, DISPATCH_RECEIPT_PREFIX) == []


def test_dispatch_is_idempotent_over_an_unchanged_record(tmp_path):
    """Idempotence is BY THE RECORD, which is what makes a resume safe: a flag
    on the reader module would be rebuilt empty and re-route everything."""
    harness = Harness(tmp_path / "run")
    _seed(harness)
    target = _target(harness)
    _record_criticism(harness, target.id, {"attack": True, "successor_question": QUESTION})

    assert dispatch_recorded_proposals(harness, _Defaults()) == 1
    for _ in range(3):
        assert dispatch_recorded_proposals(harness, _Defaults()) == 0
    assert len(_blocks(harness)) == 1
    assert len(_receipts(harness, "successor-question:")) == 1


def test_a_second_criticism_is_picked_up_by_the_next_walk(tmp_path):
    """Idempotent is not inert: the walk routes what is NEW since last time."""
    harness = Harness(tmp_path / "run")
    _seed(harness)
    first = _target(harness)
    _record_criticism(harness, first.id, {"attack": True, "successor_question": QUESTION})
    assert dispatch_recorded_proposals(harness, _Defaults()) == 1

    second = _target(harness, "the tide is semidiurnal here")
    _record_criticism(
        harness,
        second.id,
        {"attack": True, "successor_question": OTHER_QUESTION},
        case="fails at spring",
    )
    assert dispatch_recorded_proposals(harness, _Defaults()) == 1
    assert len(_blocks(harness)) == 2


def test_the_batch_shape_is_read_case_by_case(tmp_path):
    """Both wire shapes reach the record, so the reader must read both. A
    reader that only understood the single contract would silently drop every
    question the batch path produced -- which is the path the scheduler uses."""
    harness = Harness(tmp_path / "run")
    _seed(harness)
    target = _target(harness)
    _record_criticism(
        harness,
        target.id,
        {
            "cases": [
                {"target_alias": "SRC_001", "attack": True, "successor_question": QUESTION},
                {"target_alias": "SRC_001", "attack": False},
                {"target_alias": "SRC_001", "attack": True, "successor_question": OTHER_QUESTION},
            ]
        },
    )

    proposals = recorded_proposals(harness)
    assert [p.question for p in proposals] == [QUESTION, OTHER_QUESTION], proposals
    assert dispatch_recorded_proposals(harness, _Defaults()) == 2
    assert len(_blocks(harness)) == 2


# --- what it refuses to guess ----------------------------------------------- #


def test_a_question_with_no_resolvable_problem_is_disclosed_not_dropped(tmp_path):
    """The law's own condition -- "linked to the problem it was proposed
    under" -- can fail. When it does, the reader records the failure. A
    silently dropped proposal would be indistinguishable from one never
    written."""
    harness = Harness(tmp_path / "run")
    _seed(harness)
    # A target addressing NO problem: `problem_id=None` on registration.
    orphan = harness.create_artifact(
        "an artifact addressing nothing", provenance=Provenance(role="conjecturer")
    )
    _record_criticism(harness, orphan.id, {"attack": True, "successor_question": QUESTION})

    assert dispatch_recorded_proposals(harness, _Defaults()) == 0
    assert _blocks(harness) == []
    unlinked = _receipts(harness, f"{DISPATCH_RECEIPT_PREFIX}UNLINKED")
    assert len(unlinked) == 1, unlinked


def test_an_unresolvable_target_still_routes_and_says_so(tmp_path):
    """The honest boundary of road B, asserted rather than left in prose. A
    call that criticised SEVERAL artifacts has no recoverable alias table --
    it is call-local and never recorded -- so the PROBLEM resolves (every
    target of one call comes from one problem's candidate set) and the TARGET
    does not. Routing proceeds; minting cannot, and the record says which."""
    harness = Harness(tmp_path / "run")
    _seed(harness)
    first = _target(harness)
    second = _target(harness, "the tide is semidiurnal here")
    critic = harness.create_artifact(
        "fails at neap",
        provenance=Provenance(role="critic"),
        rule=Rule.CRIT,
        llm=_critic_call(
            harness,
            {
                "cases": [
                    {"target_alias": "SRC_001", "attack": True, "successor_question": QUESTION}
                ]
            },
        ),
    )
    harness.record_measure(inputs=["scrutiny", first.id, critic.id])
    harness.record_measure(inputs=["scrutiny", second.id, critic.id])

    [proposal] = recorded_proposals(harness)
    assert proposal.problem_id == PROBLEM_ID
    assert proposal.target_id is None

    assert dispatch_recorded_proposals(harness, _Minting()) == 1
    assert len(_blocks(harness)) == 1, "the default road is unaffected"
    assert _receipts(harness, f"{DISPATCH_RECEIPT_PREFIX}ROUTED_TARGET_UNRESOLVED")
    assert [p for p in harness.state.problems if p.startswith("succ:")] == []


# --- the minting road is unchanged by having a caller ----------------------- #


def test_dispatch_mints_nothing_with_the_gate_off(tmp_path):
    """A production caller must not become a way to switch a gate on."""
    harness = Harness(tmp_path / "run")
    _seed(harness)
    target = _target(harness)
    _record_criticism(harness, target.id, {"attack": True, "successor_question": QUESTION})

    dispatch_recorded_proposals(harness, _Defaults())

    assert [p for p in harness.state.problems if p.startswith("succ:")] == []
    assert _receipts(harness, "successor-minting-gate:") == []
    assert len(_blocks(harness)) == 1, "routing still happened"


def test_dispatch_mints_once_with_the_gate_on(tmp_path):
    """And the second road works from the same site, when a run asks for it."""
    harness = Harness(tmp_path / "run")
    _seed(harness)
    target = _target(harness)
    _record_criticism(harness, target.id, {"attack": True, "successor_question": QUESTION})

    dispatch_recorded_proposals(harness, _Minting())

    minted = [p for p in harness.state.problems if p.startswith("succ:")]
    assert len(minted) == 1, minted
    problem = harness.state.problems[minted[0]]
    assert problem.description == QUESTION
    assert list(problem.provenance.from_) == [PROBLEM_ID, target.id]
    # And the gate's own warning reached the record, from the same walk.
    assert _receipts(harness, "successor-minting-gate:ENABLED")


def test_the_shipped_config_selects_the_scratchpad_and_leaves_minting_off():
    """Read through the real `Config`, not a stub: the Q1 grant made both
    fields real, so the shipped defaults are now a measurable fact about an
    unconfigured run rather than a `getattr` fallback."""
    from deepreason.successor import minting_notices, resolve

    assert resolve(Config()).id == "scratchpad.v1"
    assert minting_notices(Config()) == ()


def test_the_shipped_config_has_the_scratch_WORKSPACE_off_and_says_so(tmp_path):
    """The honest reading of "goes to scratchpad by default", measured rather
    than assumed, because it is easy to over-read.

    The DESTINATION default is the scratchpad -- `resolve(Config())` proves
    that above. But `Config().scratchpad.enabled` is False in the shipped
    defaults, and that is a different switch owned by a different subsystem. A
    run that has not turned the scratch workspace on therefore routes to a
    destination that cannot accept the question, and gets a typed UNAVAILABLE
    disclosure instead of a silent discard -- which is exactly what
    `route` promises and what the all-configurations law requires.

    So the channel is live end to end on any run whose workspace is on, and
    typed-and-visible on any run whose workspace is off. Neither is silence.
    """
    harness = Harness(tmp_path / "run")
    _seed(harness)
    target = _target(harness)
    _record_criticism(harness, target.id, {"attack": True, "successor_question": QUESTION})

    assert Config().scratchpad.enabled is False, "the premise of this test"
    dispatch_recorded_proposals(harness, Config())

    assert _blocks(harness) == []
    unavailable = _receipts(harness, "successor-question:UNAVAILABLE")
    assert unavailable == [
        ["successor-question:UNAVAILABLE", "scratchpad.v1", PROBLEM_ID]
    ], unavailable
    assert [p for p in harness.state.problems if p.startswith("succ:")] == []


def test_a_run_with_the_scratch_workspace_on_gets_the_block(tmp_path):
    """The other half of the pair above, through the real `Config` rather than
    a stub, so "live" is measured on the object a run actually carries."""
    harness = Harness(tmp_path / "run")
    _seed(harness)
    target = _target(harness)
    _record_criticism(harness, target.id, {"attack": True, "successor_question": QUESTION})

    config = Config().model_copy(
        update={"scratchpad": Config().scratchpad.model_copy(update={"enabled": True})}
    )
    dispatch_recorded_proposals(harness, config)

    blocks = _blocks(harness)
    assert len(blocks) == 1, blocks
    assert blocks[0].provenance.origin == PROBLEM_ID
    assert [p for p in harness.state.problems if p.startswith("succ:")] == []


# --- the hook point that carries it into production ------------------------- #


def test_the_channel_is_armed_whatever_the_import_order(tmp_path):
    """MEASURED, not assumed, and it caught a real defect in this tranche.

    The first version had `successor/__init__.py` register the hook on import,
    so the channel was armed only if something had already imported
    `deepreason.config` -- importing `deepreason.scheduler.scheduler` alone left
    the registry EMPTY and the channel silently dead. A channel that works by
    import accident is exactly the defect Q3 was answered to close, so the hook
    is DECLARED in `aftercycle` and resolved lazily instead.

    Each subprocess imports ONE module and nothing else. A shared interpreter
    would prove nothing here, because an earlier test's imports would arm it.
    """
    import sys

    for module in (
        "deepreason.aftercycle",
        "deepreason.loop",
        "deepreason.scheduler.scheduler",
    ):
        probe = subprocess.run(
            [
                sys.executable,
                "-c",
                f"import {module}\n"
                "from deepreason.aftercycle import after_criticism_hooks\n"
                "print(after_criticism_hooks())",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        assert "successor-questions" in probe.stdout, (module, probe.stdout)


def test_no_deciding_package_names_the_hooks_channel():
    """The reason the hook point exists at all. `scheduler` is a DECIDING
    package, and the law-line rule forbids those from naming the successor
    machinery with an empty exception list -- so the scheduler names
    `aftercycle` (a hook point) and could not reach the channel if it tried."""
    import pathlib

    for package in ("scheduler", "adjudication", "informal", "rules", "workflow", "workflows"):
        root = pathlib.Path("src/deepreason") / package
        if not root.exists():
            continue
        offenders = [
            str(path)
            for path in root.rglob("*.py")
            if "deepreason.successor" in path.read_text(encoding="utf-8")
        ]
        assert offenders == [], offenders


def test_the_scheduler_fires_the_hook_after_a_criticism_pass(tmp_path):
    """The hook point is wired, not merely defined. Asserted over the SOURCE of
    the method the criticism pass ends with, because driving a real cycle needs
    a provider; the behaviour behind it is `run_after_criticism`'s, which the
    tests above cover directly."""
    import inspect

    from deepreason.scheduler.scheduler import Scheduler

    arg_crit = inspect.getsource(Scheduler._arg_crit)
    assert "_run_after_criticism_hooks()" in arg_crit, arg_crit[-400:]
    runner = inspect.getsource(Scheduler._run_after_criticism_hooks)
    assert "run_after_criticism" in runner


def test_a_failing_hook_is_reported_and_never_kills_the_cycle(tmp_path):
    """Advisory means advisory. A destination that cannot accept a question
    already discloses through `route`; an UNFORESEEN failure must not be able
    to end a reasoning cycle either."""
    from deepreason.aftercycle import (
        register_after_criticism,
        run_after_criticism,
        unregister_after_criticism,
    )

    seen = []

    def _explode(harness, config):
        raise RuntimeError("the advisory channel fell over")

    register_after_criticism("test-explodes", _explode)
    try:
        harness = Harness(tmp_path / "run")
        _seed(harness)
        failed = run_after_criticism(
            harness, _Defaults(), on_error=lambda name, exc: seen.append((name, str(exc)))
        )
    finally:
        unregister_after_criticism("test-explodes")

    assert "test-explodes" in failed, failed
    assert seen and seen[0][0] == "test-explodes", seen
