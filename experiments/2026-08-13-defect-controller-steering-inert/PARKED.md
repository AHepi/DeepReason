# Parked — found during this tranche, deliberately NOT worked

## P1 — criticism dispatch vastly under-serves criticism-coverage debt

WHAT: in the grounded-extension root, the scheduler emitted 5,026
`criticism.coverage-debt.v1` records naming 469 distinct subjects, while
dispatching `Crit` only 16 times and `Spawn` 2,894 times. Debt accumulated
~314x faster than it was serviced, and generation kept spawning against it.

Measured, not inferred:

    R=experiments/2026-08-12-live-grounded-extension-expansion/run
    grep -o 'criticism.coverage-debt.v1' $R/log.jsonl | wc -l   # 5026
    # rule census: Spawn 2894, Crit 16, Conj 42

NUMBER CORRECTION for whoever picks this up: the tranche brief said "380
criticism-coverage-debt records". The committed log holds 5,026 debt
records over 469 distinct subject digests; 380 matches neither figure. Use
the measured numbers and re-derive before quoting them.

Why parked: this tranche's one goal is that the steering loop fires. Debt
servicing is a scheduler problem-selection question with its own evidence
and its own blast radius (`CRIT_DEBT_CEILING`, `ARG_CRIT_PER_CYCLE` are
TRIBUNAL-ledger knobs the controller may never touch, so the two defects
cannot even share a fix).

### Ready-to-send prompt

```
Defect tranche: criticism dispatch under-serves criticism-coverage debt by
~300x on compiled-config runs. Route through deepreason-orchestrator;
diagnosis from the typed record BEFORE code.

SETUP (fresh container): git fetch origin main && git checkout -B
claude/crit-debt-dispatch-<slug> origin/main; pip install -e .
--break-system-packages -q; pip install pytest pytest-xdist jsonschema
--break-system-packages -q. Use `python -m pytest`, never bare pytest.
Read CLAUDE.md in full; load dr-drive-harness, dr-explain-to-operator.

EVIDENCE (measured on the committed root; verify then extend): in
experiments/2026-08-12-live-grounded-extension-expansion/run (run id
8e22d0431fd2b98dc915c66f2f3ccc6dc43184b4c326ff5d388a7c013a80989d, 12,991
events, stop_reason budget_exhausted, 8 cycles recorded in run-status.json
across both epochs) the rule census is Spawn 2,894 / Measure 6,556 /
Control 3,380 / Register 85 / Conj 42 / Crit 16 / Scratch 14 / Refl 4, and
`grep -o 'criticism.coverage-debt.v1' log.jsonl | wc -l` returns 5,026 over
469 distinct subject digests. Only 245 artifacts reached accepted against
16 refuted, so the acceptance rate is a function of criticism never being
dispatched, not of the conjectures being good.

TRAP, recorded so you do not repeat it: the log's 3,380 rule="Control"
events are workflow TRANSACTION records (control.event.v3 — 2,702
work_transition, 666 provider_result, and eight lifecycle records). They
are not criticism and not steering. Do not count them.

SECOND TRAP: this root's zero token-steering records are a DIFFERENT,
already-fixed defect (experiments/2026-08-13-defect-controller-steering-
inert/). Do not re-diagnose it; read that tranche's DIAGNOSIS.md first so
you do not attribute the criticism shortfall to an inert controller.

ONE GOAL: criticism dispatch is proportionate to recorded coverage debt on
a compiled-config run — i.e. the record shows debt being SERVICED (Crit
dispatch responding to the debt pool) rather than accumulating unbounded.
Name the selection mechanism with file:line and a record pointer before
proposing anything. Likely territory, unverified: Scheduler._select_problem
ranking (see docs/map/CON-scheduler-ranking.md), ARG_CRIT_PER_CYCLE /
CRIT_DEBT_CEILING metering, and the standing-recrit pool described in
docs/map/SUB-scheduler.md Traps ("Accepted-by-neglect, and rationing free
criticism") — that trap is the cheapest first read and may already name
this failure.

SCOPE LINE: the token-steering controller is OUT of scope (fixed
separately). Any envelope/knob finding is PARKED with a ready prompt.

CONSTRAINT: CRIT_DEBT_CEILING, ARG_CRIT_PER_CYCLE, MIN_ATTACKS_FOR_RITUAL
and ATTACK_ENTROPY_FLOOR are TRIBUNAL_LEDGER knobs (controller.py:51-58) —
the steering controller may never write them, so a fix must not route
through the controller.

TESTS: regression naming this run id in the docstring; ring while
iterating, full gate at the boundary; docs_verify full; map moves
same-commit. Old roots replay byte-unchanged. Deliver R-by-R with pasted
PROOF.
```

## P2 — the map owns none of the control-plane files (closed in part by this tranche)

WHAT: no `docs/map/SUB-*.md` `Owns:` line names
`src/deepreason/controller.py`, `ops.py`, `config.py`, `referee.py`,
`control_events.py` or `v6_policy.py`. `SUB-periphery.md` says in prose it
covers "everything no other map document owns", but its machine-checked
`Owns:` list does not enumerate them, so no `check:` authenticates any
claim about them.

This tranche closes the gap for the files it touches (map moves in the same
commit as the code). The remaining files stay unowned and stay parked.

### Ready-to-send prompt

```
Change tranche: close the map's control-plane ownership gap. Route through
dr-change-orchestrator.

Operator authority: this prompt. Requirement: every file under
src/deepreason/ is named by exactly one map document's `Owns:` line. Today
these are named by none: ops.py, config.py, referee.py, control_events.py,
v6_policy.py (controller.py was adopted by
experiments/2026-08-13-defect-controller-steering-inert/). Verify the full
set yourself rather than trusting this list:

  comm -23 <(ls src/deepreason/*.py | sort) \
           <(grep -h "^Owns:" docs/map/SUB-*.md | tr ',' '\n' \
             | sed 's/^Owns://' | tr -d ' ' | grep '\.py$' | sort)

Decide per file whether it joins an existing document or earns a new one,
add a `check:` that would FAIL if the claim regressed (docs_verify --audit
refuses checks that cannot fail), and run `python tools/docs_verify.py`
full plus `--links` and `--audit`. Read docs/map/SCHEMA.md before writing.
No src/ change is expected; if one is needed, that is a stop.
```
