# PARKED — noticed in this tranche, deliberately not fixed here

## P1 — four other roads still die on a budget refusal they could survive

**What.** `WorkBudgetDenied` is re-raised, correctly, by `rules/conj.py`,
`workflow/repair_transaction.py`, `bridge/transactional_adapter.py`,
`scratch/authoring.py` and `referee.py` — the refusal arrives with its durable
terminal already written, and a second transition after termination fails the
run. What each CALLER then does with it varies: `_maybe_config_referee`
absorbs it and returns, the criticism road now re-plans or drops it, and the
conjecture, bridge, scratch-authoring and repair roads still let it reach the
cycle loop. On a spent ceiling that is right — the run ends cleanly. On a
refusal the ceiling could still afford, those four roads still end a run that
could have carried on, which is the same defect this tranche fixed for
criticism.

Not fixed here because each road has a different right answer and a different
record obligation. Criticism had a sibling to copy (`_foreign_arg_crit`'s typed
coverage debt) and a declaration channel that already existed; conjecture has
neither, and "drop the conjecture" is not obviously better than stopping when
the conjecturer is the only thing generating content. That is a design
question with no evidence behind it yet.

Also not obvious: whether these should share ONE policy field or carry their
own. One field is simpler and matches "maximum configurable surface"; separate
fields let a run keep conjecturing while it stops criticising. Deciding that
without a live measurement would be guessing.

```
EXECUTOR WINDOW — DEFECT: four roads still die on a survivable budget refusal
Read CLAUDE.md. Load deepreason-orchestrator and pinker-write-for-readers.
GOAL: a token-budget refusal the ceiling could still have afforded does not end
the run on the conjecture, bridge, scratch-authoring or repair roads either;
a refusal on a SPENT ceiling still does, cleanly, as budget_exhausted.
Diagnose from the record first, then answer TWO design questions in FIX.md
before writing code: (a) what each road owes the record when it drops work --
criticism had `criticism.dispatch.v1` to declare into and the others may have
nothing, and an undeclared gap is worse than a stop; (b) whether these share
Config.CRITICISM_BUDGET_DENIAL_POLICY renamed, or carry their own fields --
price both against the modularity law and ASK the operator rather than
choosing. The pattern to follow is
experiments/2026-09-06-defect-criticism-budget-denial-policy/ (a registered
policy module, a resolver that never refuses, a typed warning on the setting
that can kill a run, and R2 held to a measured spend difference rather than a
branch). Regression tests for both sides of each road, mutation-proven.
OUT OF SCOPE: the criticism road, and what a spent ceiling does.
```

## P2 — inherited, still open

The predecessor tranche's P2 (three `tests/test_organiser_seat.py` failures on
`origin/main`, and two `docs_verify` rows from the same merged tranche that
`docs/AUDIT_BASELINES.md` does not list) is unchanged and still holds the gate
at 3 failed. Its ready-to-send prompt is at
`experiments/2026-09-06-defect-budget-exhausted-classification/PARKED.md`.
