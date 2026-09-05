"""Every criticism pass says on the record whether it ran in full.

Implements R4/R5 of `experiments/2026-09-04-change-evidence-states/REQUEST.md`.

The reading in `deepreason.views.evidence_states` may treat "nothing landed" as
evidence only when the pass that produced that nothing actually looked at
everything it planned to. Without this declaration a budget-truncated pass and
an exhaustive one leave the same trace, and an artifact nobody got to would read
as a survivor.

The declaration rides `record_measure` — the existing notice channel — so no new
record object kind exists and the harness's frozen event application is
untouched.
"""

from __future__ import annotations

import json

from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.ontology import Commitment, Problem, ProblemProvenance
from deepreason.runtime.criticism_dispatch import (
    CRITICISM_DISPATCH_SIGNAL,
    OUTCOME_COMPLETE,
    OUTCOME_CUT_BUDGET,
    OUTCOME_CUT_CALL,
    OUTCOME_CUT_SEAT,
    OUTCOMES,
)
from deepreason.scheduler.scheduler import Scheduler


def _problem(harness: Harness) -> None:
    harness.register_commitment(Commitment(id="k-moon", eval="predicate:'moon' in content"))
    harness.register_problem(
        Problem(
            id="pi-tides", description="explain the tides", criteria=["k-moon"],
            provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
        )
    )


def _conjecture(prompt: str) -> str:
    return json.dumps(
        {"candidates": [
            {"content": f"moon account {i} {hash(prompt) % 997}", "typicality": 0.5}
            for i in range(3)
        ]}
    )


def _quiet_critic(prompt: str) -> str:
    return json.dumps({"attack": False, "case": ""})


def _declarations(harness: Harness) -> list[dict]:
    out = []
    for event in harness.log.read():
        inputs = [str(value) for value in (event.inputs or ())]
        if inputs[:1] == [CRITICISM_DISPATCH_SIGNAL]:
            out.append({
                "cycle": inputs[1], "outcome": inputs[2],
                "planned": int(inputs[3]), "dispatched": int(inputs[4]),
                "targets": inputs[5:],
            })
    return out


def _run(tmp_path, *, config, roles, cycles=2):
    harness = Harness(tmp_path / "run")
    _problem(harness)
    adapter = LLMAdapter(roles, harness.blobs, retry_max=2)
    Scheduler(harness, adapter, config).run(cycles)
    return harness


def test_a_clean_pass_declares_itself_complete(tmp_path):
    """Nothing capped it and no call was dropped, so the absence of a landed
    attack is a measurement rather than a gap."""

    harness = _run(
        tmp_path,
        config=Config(VS_K=3, N_SCHOOLS=0, FLOOR=0, ARG_CRIT_PER_CYCLE=None),
        roles={
            "conjecturer": MockEndpoint(_conjecture),
            "argumentative_critic": MockEndpoint(_quiet_critic),
        },
    )
    declarations = _declarations(harness)
    assert declarations, "a criticism pass filed nothing"
    assert all(d["outcome"] == OUTCOME_COMPLETE for d in declarations), declarations
    assert all(d["dispatched"] == d["planned"] for d in declarations)
    assert all(len(d["targets"]) == d["dispatched"] for d in declarations)


def test_one_declaration_per_criticism_pass(tmp_path):
    """`step` calls `_arg_crit` once per cycle, so two cycles file two
    declarations — never one summary, never one per target."""

    harness = _run(
        tmp_path,
        config=Config(VS_K=3, N_SCHOOLS=0, FLOOR=0, ARG_CRIT_PER_CYCLE=None),
        roles={
            "conjecturer": MockEndpoint(_conjecture),
            "argumentative_critic": MockEndpoint(_quiet_critic),
        },
        cycles=2,
    )
    declarations = _declarations(harness)
    assert len(declarations) == 2, declarations
    assert [d["cycle"] for d in declarations] == ["0", "1"]


def test_a_ration_that_truncates_the_targets_declares_cut_budget(tmp_path):
    """`ARG_CRIT_PER_CYCLE=1` against three admitted candidates leaves two
    targets the pass never looked at. Reading their silence as survival is
    exactly the mistake the declaration exists to prevent."""

    harness = _run(
        tmp_path,
        config=Config(VS_K=3, N_SCHOOLS=0, FLOOR=0, ARG_CRIT_PER_CYCLE=1),
        roles={
            "conjecturer": MockEndpoint(_conjecture),
            "argumentative_critic": MockEndpoint(_quiet_critic),
        },
    )
    declarations = _declarations(harness)
    assert declarations
    assert any(d["outcome"] == OUTCOME_CUT_BUDGET for d in declarations), declarations


def test_no_critic_role_declares_cut_seat(tmp_path):
    """A pass with no argumentative critic to dispatch to made zero of the
    calls it planned, and says so with the count."""

    harness = _run(
        tmp_path,
        config=Config(VS_K=3, N_SCHOOLS=0, FLOOR=0),
        roles={"conjecturer": MockEndpoint(_conjecture)},
    )
    declarations = _declarations(harness)
    assert declarations
    assert all(d["outcome"] == OUTCOME_CUT_SEAT for d in declarations), declarations
    assert all(d["dispatched"] == 0 for d in declarations)
    assert any(d["planned"] > 0 for d in declarations)


def test_a_dropped_batch_declares_cut_call(tmp_path):
    """A critic whose output never parses has its batch dropped: the call was
    planned and not made, which is a cut however healthy the seat looked."""

    harness = _run(
        tmp_path,
        config=Config(VS_K=3, N_SCHOOLS=0, FLOOR=0, ARG_CRIT_PER_CYCLE=None),
        roles={
            "conjecturer": MockEndpoint(_conjecture),
            "argumentative_critic": MockEndpoint(lambda prompt: "not json at all"),
        },
    )
    declarations = _declarations(harness)
    assert declarations
    assert any(d["outcome"] == OUTCOME_CUT_CALL for d in declarations), declarations
    cut = [d for d in declarations if d["outcome"] == OUTCOME_CUT_CALL][0]
    assert cut["dispatched"] < cut["planned"]


def test_every_declared_outcome_is_in_the_closed_vocabulary(tmp_path):
    """The vocabulary is closed so a future road cannot inherit `complete` by
    silence. A declaration outside it never reaches the record."""

    harness = _run(
        tmp_path,
        config=Config(VS_K=3, N_SCHOOLS=0, FLOOR=0, ARG_CRIT_PER_CYCLE=1),
        roles={
            "conjecturer": MockEndpoint(_conjecture),
            "argumentative_critic": MockEndpoint(_quiet_critic),
        },
    )
    assert all(d["outcome"] in OUTCOMES for d in _declarations(harness))


def test_the_writer_refuses_an_outcome_outside_the_vocabulary(tmp_path):
    from deepreason.runtime.criticism_dispatch import declare_criticism_dispatch

    harness = Harness(tmp_path / "run")
    try:
        declare_criticism_dispatch(
            harness, cycle=0, outcome="ran_fine", planned=1, dispatched=1
        )
    except ValueError as exc:
        assert "ran_fine" in str(exc)
    else:  # pragma: no cover - the guard is the point of the test
        raise AssertionError("an unknown outcome reached the record")
    assert not _declarations(harness)


def test_the_declaration_adds_no_record_object_kind(tmp_path):
    """R5's whole reason for choosing this channel: it is a Measure event like
    the seat-retirement and trial signals, so nothing about the harness's event
    application or its object kinds moves."""

    harness = _run(
        tmp_path,
        config=Config(VS_K=3, N_SCHOOLS=0, FLOOR=0),
        roles={
            "conjecturer": MockEndpoint(_conjecture),
            "argumentative_critic": MockEndpoint(_quiet_critic),
        },
        cycles=1,
    )
    filed = [
        event for event in harness.log.read()
        if [str(v) for v in (event.inputs or ())][:1] == [CRITICISM_DISPATCH_SIGNAL]
    ]
    assert filed
    for event in filed:
        assert event.rule.value == "Measure", event.rule
        assert not event.outputs


def test_the_signal_is_declared_in_the_registry():
    """`REC-add-signal.md` step 2: a new signal ships with its meaning.

    `tests/test_signals.py`'s AST scan cannot see this one — it reads literal
    heads out of `record_measure(inputs=[...])` call sites, and this signal is
    emitted through a named constant in one writer rather than a literal at the
    call site. That blindness is PARKED as a finding about the scanner; it is
    not a licence to leave the signal undeclared, so the registration is
    asserted here directly.
    """

    from deepreason.signals import SIGNAL_DECLARATIONS, is_known

    assert is_known(CRITICISM_DISPATCH_SIGNAL)
    declaration = SIGNAL_DECLARATIONS[CRITICISM_DISPATCH_SIGNAL]
    assert declaration.unit != "unspecified"
    assert declaration.staleness != "unspecified"
    # Producer-agnostic by the contract: the semantics say what one occurrence
    # MEANS, never which subsystem emitted it.
    assert "scheduler" not in declaration.semantics
    # And what it is NOT evidence of, which is the field consumers get wrong.
    assert "never about any artifact" in declaration.semantics
