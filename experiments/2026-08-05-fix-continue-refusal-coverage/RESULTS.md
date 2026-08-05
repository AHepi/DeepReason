# Results — the refusal gets a guard the gate runs

## 2026-08-05 — `CONTINUE_TYPED_STOP_REQUIRED` stops depending on a script no gate executes

**What was observed.** After the previous tranche made the operational
smoke green, the refusal it proves was still unguarded by anything
`pytest` runs. Repo-wide, `CONTINUE_TYPED_STOP_REQUIRED` appeared four
times: at its raise site (`runtime/continuation.py:352`), twice in
`scripts/wheel_operational_smoke.py`'s matcher, and once in a unit test
OF that matcher which never calls `prepare_continuation`. The only
end-to-end witness was a script CI runs and the gate does not.

That is not a hypothetical exposure. It is the mechanism by which
`2d4ca2e1` changed what a budget-exhausted stop authorizes on
2026-07-27 and left the full gate green until 2026-08-05.

**What the record showed, and how it changed the plan.** The parked
entry assumed a constructed fixture would be needed — build a
non-resumable terminal with the helpers that build the resumable twin.
A census of every git-tracked root carrying a `run-stop.json` said
otherwise:

    reason='budget_exhausted'     terminal receipt=yes   n=16
    reason='budget_exhausted'     terminal receipt=NO    n=7
    reason='operational_failure'  terminal receipt=NO    n=5

**Twelve of 28 committed roots were already in the state the raise site
guards.** Seven of them, copied to a temp directory and passed to
`prepare_continuation`, returned the exact refusal — and not
`CONTINUE_CHECKPOINT_REQUIRED` or any earlier guard, checked rather than
assumed. Record replay, the cheapest form available, on runs that really
stopped rather than fixtures asserting the state into existence.

**What was built.** One test in `tests/test_continuation.py`, placed
there because `DR-SUB-application`'s `Verify:` line runs that file, so
the guard is re-executed whenever the map document describing it is
re-verified. Witnesses are selected by property from each root's own
`run-stop.json` — a stop reason outside `RESUMABLE_STOP_REASONS` — never
by name, and each is copied before `prepare_continuation` sees it,
because that function opens a writable `Harness` before reaching the
refusal.

Five `operational_failure` roots qualify today. The seven receipt-less
`budget_exhausted` roots reach the same raise and were deliberately
excluded: their reason is now resumable, so selecting them would tie the
witness set to a historical accident instead of a property.

**The measurement that decided the design.** Selecting witnesses by
opening a `Harness` per root costs 63.3 s — 28 full replays — and reads
`terminal_lifecycle_decision is None`, the exact condition the code
under test branches on. Selecting from `run-stop.json` costs 0.11 s and
reads an independent fact, letting the refusal do the work: a root that
somehow gained a receipt raises a different error and fails loudly
rather than being quietly skipped. Cheaper and more honest were the same
choice. Total added gate time ~8 s.

**A correction, measured before it was relied on.** The proposed
mutation proof was a temporary `RESUMABLE_STOP_REASONS` widening. As a
proof OF THE REFUSAL that is vacuous: with the selection held fixed,
baseline and mutant both returned five refusals. Line 352 is reached
when `terminal_lifecycle_decision is None`, and the frozenset is
consulted at `lifecycle.py:273` inside `build_resumed_lifecycle`, which
only runs when a terminal decision exists — so on these roots it is
never read. It does kill the test, through the SELECTION, which reads
the same frozenset: the witness set empties and the guard fires. Both
mutations are therefore recorded, proving different things, neither
standing in for the other.

**Instruments.** Full gate 3340 passed / 7 skipped / 0 failed — 3339 plus
exactly the one test added. `docs_verify` 816 checks, 0 failed;
`--audit` 0 findings. Diff 96 changed lines against a ≤150 ceiling,
checked against `git diff --stat` per the rule added at `132bdbb9` — its
first application, and the plan-time estimate was low by ~30%, which is
the gap an estimate-only ceiling cannot see.

**The residue.**

- **X1 — the mirror-image gap.** A second guard
  (`lifecycle.py:273`, "terminal stop reason does not authorize
  continuation") fires when a receipt IS present but names a
  non-resumable reason. It has no test, and no committed root can
  witness it: all 16 roots carrying a receipt stopped on
  `budget_exhausted`. That is the guard that would fire if someone
  reverted owner decision 4a. Parked with a ready-to-send prompt and the
  scaffolding named.
- **The continuation half is still smoke-only.** `DR-SUB-application`'s
  Traps entry was rewritten rather than replaced, and says so in as many
  words instead of reading as fully resolved.
- **X2/X3** — the witness class grows only when runs fail, and the
  selection trusts the stop record over replayed state. Both have
  legible failure modes; both recorded.

Accepted does not mean true: what is established is that one refusal
now fails `pytest` if it stops refusing, on the five roots that witness
it today. Nothing here proves the continuation half, the receipt-present
path, or anything about a real provider.
