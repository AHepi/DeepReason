"""One refused criticism batch must not end the run, and the choice is configuration.

Operator instruction, 2026-09-06, verbatim: "ok do P1. And ensure config is
plugged in so that it can affect token allocation during a run."

Regression (parked P1,
`experiments/2026-09-06-defect-budget-exhausted-classification/PARKED.md`):
`Scheduler._arg_crit`'s direct batch road -- the one a run with no criticism
policy takes, and the one live run
`run-c3f3bf10bc57d63e224a9f1c68bf1057` took -- caught only
`(SchemaRepairError, EndpointError)`, while its foreign-school sibling also
caught `WorkBudgetDenied` and recorded a typed coverage outcome. So one
criticism batch the token budget refused ended the whole run, even where the
budget could still afford other work.

The second half of the instruction is held to a MEASUREMENT rather than a
branch: `test_the_knob_changes_what_the_run_spends` drives one real
`TokenMeter` through the same scenario under two settings of the one field and
asserts different spend. A field nothing can be shown to change is the
"customization point that requires a code edit" the modularity law forbids.
"""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.budget import (
    TokenBudgetExceeded,
    TokenMeter,
    budget_denial_exhausted,
)
from deepreason.llm.endpoints import MockEndpoint
from deepreason.ontology import (
    Commitment,
    Problem,
    ProblemProvenance,
    Provenance,
)
from deepreason.runtime.criticism_budget_policy import (
    CRITICISM_BUDGET_POLICIES,
    DEFAULT_CRITICISM_BUDGET_POLICY,
    POLICY_DROP,
    POLICY_SHRINK,
    POLICY_STOP,
    STOP_SIGNAL,
    STOP_WARNING,
    resolve_policy,
    split_batch,
)
from deepreason.runtime.criticism_dispatch import (
    CRITICISM_DISPATCH_SIGNAL,
    OUTCOME_COMPLETE,
    OUTCOME_CUT_TOKEN_BUDGET,
)
from deepreason.scheduler.scheduler import Scheduler
from deepreason.workflow.transaction import WorkBudgetDenied

TERMINAL = SimpleNamespace(work_id="sha256:" + "d" * 8)


def _scheduler(root, **config_kwargs):
    harness = Harness(root)
    harness.register_commitment(
        Commitment(id="k-moon", eval="predicate:'moon' in content")
    )
    harness.register_problem(
        Problem(
            id="pi-tides",
            description="explain the tides",
            criteria=["k-moon"],
            provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
        )
    )
    adapter = LLMAdapter(
        {
            "conjecturer": MockEndpoint(lambda _p: json.dumps({"candidates": []})),
            "argumentative_critic": MockEndpoint(lambda _p: json.dumps({"cases": []})),
        },
        harness.blobs,
        retry_max=1,
    )
    config = Config(VS_K=1, N_SCHOOLS=0, FUZZ_N=0, **config_kwargs)
    return harness, Scheduler(harness, adapter, config)


def _targets(harness, count):
    return [
        harness.create_artifact(
            f"the moon pulls the sea, reading {index}",
            provenance=Provenance(role="conjecturer"),
            problem_id="pi-tides",
        ).id
        for index in range(count)
    ]


def _declarations(harness):
    rows = []
    for event in harness.log.read():
        inputs = [str(value) for value in (event.inputs or ())]
        if inputs and inputs[0] == CRITICISM_DISPATCH_SIGNAL:
            rows.append(inputs)
    return rows


def _run_pass(monkeypatch, tmp_path, *, dispatch, targets=4, **config_kwargs):
    """One criticism pass over `targets` admitted artifacts, offline."""

    harness, scheduler = _scheduler(tmp_path / "run", **config_kwargs)
    ids = _targets(harness, targets)
    seen: list[tuple[str, ...]] = []

    def _batch(_harness, target_ids, *_args, **_kwargs):
        seen.append(tuple(target_ids))
        return dispatch(tuple(target_ids))

    monkeypatch.setattr(
        "deepreason.scheduler.scheduler.crit_argumentative_batch", _batch
    )
    return harness, scheduler, ids, seen


def _always_denies(*, exhausted):
    def dispatch(_batch):
        raise WorkBudgetDenied(TERMINAL, budget_exhausted=exhausted)

    return dispatch


# --------------------------------------------------------------------------
# R1 -- a refusal the ceiling could still afford does not end the run
# --------------------------------------------------------------------------


def test_a_refusal_with_budget_remaining_leaves_the_cycle_alive(tmp_path, monkeypatch):
    """P1, inverted.  The pass ends; the run does not."""

    _harness, scheduler, ids, seen = _run_pass(
        monkeypatch, tmp_path, dispatch=_always_denies(exhausted=False)
    )
    scheduler._arg_crit(ids)          # must not raise

    assert seen, "no batch was ever attempted"


def test_the_record_says_what_the_token_budget_cut(tmp_path, monkeypatch):
    """A reader must not mistake 'nobody attacked it' for 'the critics found
    nothing'.  That is the whole purpose of the dispatch declaration, and a new
    way of ending a pass short has to add its own member rather than inherit
    `complete` by silence."""

    harness, scheduler, ids, _seen = _run_pass(
        monkeypatch, tmp_path, dispatch=_always_denies(exhausted=False)
    )
    scheduler._arg_crit(ids)

    rows = _declarations(harness)
    assert len(rows) == 1, rows
    assert rows[0][2] == OUTCOME_CUT_TOKEN_BUDGET
    assert rows[0][2] != OUTCOME_COMPLETE
    # Nothing was attacked, so the declaration names nothing.
    assert rows[0][4] == "0"
    assert rows[0][5:] == []


def test_a_partly_refused_pass_names_only_what_it_actually_attacked(
    tmp_path, monkeypatch
):
    """The declaration used to report the first N of the eligible list, which
    names the wrong artifacts once a pass can succeed out of order."""

    def dispatch(batch):
        # Only single targets are affordable, so the pass reaches every
        # artifact but reaches them by shrinking rather than in one call.
        if len(batch) > 1:
            raise WorkBudgetDenied(TERMINAL, budget_exhausted=False)
        return []

    harness, scheduler, ids, seen = _run_pass(
        monkeypatch, tmp_path, dispatch=dispatch, targets=4, CRIT_BATCH_K=4
    )
    scheduler._arg_crit(ids)

    rows = _declarations(harness)
    named = rows[0][5:]
    assert named == [batch[0] for batch in seen if len(batch) == 1]
    assert sorted(named) == sorted(ids)
    # The shrink really happened: batches of 4 and of 2 were tried and refused.
    assert any(len(batch) == 4 for batch in seen)
    assert any(len(batch) == 2 for batch in seen)


# --------------------------------------------------------------------------
# The boundary the policy may not cross
# --------------------------------------------------------------------------


@pytest.mark.parametrize("policy", CRITICISM_BUDGET_POLICIES)
def test_a_spent_ceiling_still_ends_the_pass_under_every_policy(
    tmp_path, monkeypatch, policy
):
    """The operator's law of 2026-08-29 is not a configuration option.

    A refusal on an exhausted budget must keep leaving `_arg_crit`, because the
    cycle loop above is what turns it into the clean `budget_exhausted`
    terminal.  No setting of this field may absorb it.
    """

    _harness, scheduler, ids, _seen = _run_pass(
        monkeypatch,
        tmp_path,
        dispatch=_always_denies(exhausted=True),
        CRITICISM_BUDGET_DENIAL_POLICY=policy,
    )
    with pytest.raises(WorkBudgetDenied):
        scheduler._arg_crit(ids)


def test_stop_the_run_keeps_the_old_behaviour_and_warns_about_it(
    tmp_path, monkeypatch
):
    """A gate is always switchable, and switching one is never silent."""

    harness, scheduler, ids, _seen = _run_pass(
        monkeypatch,
        tmp_path,
        dispatch=_always_denies(exhausted=False),
        CRITICISM_BUDGET_DENIAL_POLICY=POLICY_STOP,
    )
    with pytest.raises(WorkBudgetDenied):
        scheduler._arg_crit(ids)

    warned = [
        [str(value) for value in (event.inputs or ())]
        for event in harness.log.read()
        if (event.inputs or [None])[0] == STOP_SIGNAL
    ]
    assert warned == [[STOP_SIGNAL, POLICY_STOP, STOP_WARNING]]


# --------------------------------------------------------------------------
# R2 -- the knob is configuration, and it is LIVE
# --------------------------------------------------------------------------


def _metered_dispatch(meter, *, chars_per_target, cap, settle):
    """A dispatch that asks a REAL meter to pay for it.

    Only the provider call is stubbed: the reservation, the refusal and the
    verdict on whether the ceiling is spent are the meter's own arithmetic.
    """

    def dispatch(batch):
        prompt = "x" * (chars_per_target * len(batch))
        try:
            reservation = meter.reserve(prompt_text=prompt, max_tokens=cap)
        except TokenBudgetExceeded as error:
            raise WorkBudgetDenied(
                TERMINAL, budget_exhausted=budget_denial_exhausted(error)
            ) from error
        reservation.settle(settle)
        return []

    return dispatch


def _measure(tmp_path, monkeypatch, *, policy, name):
    meter = TokenMeter(budget=5_000)
    harness, scheduler, ids, seen = _run_pass(
        monkeypatch,
        tmp_path / name,
        dispatch=_metered_dispatch(
            meter,
            chars_per_target=4_500,     # 1500 tokens of prompt bound per target
            cap=500,
            settle={"prompt_tokens": 500, "completion_tokens": 100},
        ),
        targets=4,
        CRIT_BATCH_K=4,
        CRITICISM_BUDGET_DENIAL_POLICY=policy,
    )
    scheduler._arg_crit(ids)
    attacked = sum(len(batch) for batch in seen if len(batch) < 4)
    return meter.total, attacked, _declarations(harness)


def test_the_knob_changes_what_the_run_spends(tmp_path, monkeypatch):
    """The operator's second sentence, held to a number.

    One scenario, one field, two settings.  A batch of four is priced beyond
    the whole ceiling, so it can never be served and is NOT exhaustion; halves
    of two fit.  `drop` abandons the work and spends nothing on it; `shrink`
    re-allocates the same targets into calls the budget can cover and spends
    accordingly.
    """

    dropped_spend, dropped_targets, dropped_rows = _measure(
        tmp_path, monkeypatch, policy=POLICY_DROP, name="drop"
    )
    shrunk_spend, shrunk_targets, shrunk_rows = _measure(
        tmp_path, monkeypatch, policy=POLICY_SHRINK, name="shrink"
    )

    # Allocation moved, and it moved because of the field alone.
    assert dropped_spend == 0
    assert shrunk_spend > dropped_spend
    assert shrunk_spend == 1_200            # two calls that fit, settled at 600

    # And the tokens bought criticism rather than being merely spent.
    assert dropped_targets == 0
    assert shrunk_targets == 4

    assert dropped_rows[0][2] == OUTCOME_CUT_TOKEN_BUDGET
    assert shrunk_rows[0][2] == OUTCOME_COMPLETE


def test_every_value_is_reachable_and_an_unknown_one_never_refuses(tmp_path):
    """The all-configurations law applied to a policy selector."""

    for value in CRITICISM_BUDGET_POLICIES:
        assert resolve_policy(Config(CRITICISM_BUDGET_DENIAL_POLICY=value)) == (
            value,
            None,
        )

    resolved, fell_back_from = resolve_policy(
        Config(CRITICISM_BUDGET_DENIAL_POLICY="no-such-policy.v9")
    )
    assert resolved == DEFAULT_CRITICISM_BUDGET_POLICY
    assert fell_back_from == "no-such-policy.v9"

    assert Config().CRITICISM_BUDGET_DENIAL_POLICY == DEFAULT_CRITICISM_BUDGET_POLICY


def test_splitting_a_batch_terminates():
    """What bounds the retry: every refusal either halves the batch or ends it."""

    assert split_batch(("a", "b", "c", "d")) == (("a", "b"), ("c", "d"))
    assert split_batch(("a", "b", "c")) == (("a",), ("b", "c"))
    assert split_batch(("a",)) == ()
    assert split_batch(()) == ()


def test_the_field_reaches_no_manifest_and_moves_no_digest():
    """The documented `Config` recipe's second half, measured not asserted.

    `Config` is serialized into every manifest's `engine_config_json` and
    hashed into `source_config_hash`, which the qualification subject embeds.
    Without the versioned-source drop, adding this field would move every
    subject digest and cost every home a ~14-minute battery.
    """

    from tests.test_reusable_qualification import _manifest, _profile

    manifest = _manifest(_profile())
    echo = json.loads(manifest.engine_config_json)
    assert [key for key in echo if "CRITICISM_BUDGET" in key] == []

    import pathlib

    source = pathlib.Path("src/deepreason/run_manifest.py").read_text()
    # At FOUR spaces and unconditional: an eight-space guard-scoped pop
    # contains this string as a substring while the hash has already moved
    # (DR-INV-frozen-surfaces, the ENGAGED_CRITICISM_AUTHORITY trap).
    assert '\n    data.pop("CRITICISM_BUDGET_DENIAL_POLICY", None)\n' in source


def test_the_scheduler_reads_the_policy_and_hard_codes_no_behaviour():
    """The modularity law's "enforced" clause: a check that goes red when the
    customization point stops being one."""

    import inspect

    source = inspect.getsource(Scheduler._dispatch_criticism_batches)
    assert "resolve_policy(self.config)" in source
    for literal in ("shrink-the-batch.v1", "drop-the-batch.v1", "stop-the-run"):
        assert literal not in source, literal
