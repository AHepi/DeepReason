# Parked — successor questions (lane B, ultracode batch 2)

Parked at the SPEC boundary, 2026-08-30, before any implementation code exists.
Five entries. Four are operator DECISIONS that block or shape work already
specified (`SPEC.md` §Questions for operator); one is a genuine future tranche.

A STOP is a phase boundary: this file and the two artifacts beside it were
committed and pushed at the moment the parks were made, not when the answers
arrive (`experiments/2026-08-29-ultracode-batch-2/SETUP.md`, and batch 1's
recorded loss).

---

## P9B-1 .. P9B-5 — the operator decision block

WHAT: five questions the implementer may not decide. Q1 and Q5 BLOCK spec items
outright (S14, S15, S19, S24); Q3 makes S9 and S13 provisional; Q2 and Q4 change
what gets built, not whether. Full reasoning, both roads and a recommendation
for each are in `SPEC.md`; the block below is the shortest answerable form.

```
DeepReason — successor questions (P9 law, 2026-08-29). SPEC.md is committed on
branch claude/b2-lane-B at experiments/2026-08-30-change-successor-questions/.
No implementation code exists yet. Five decisions, each answerable in a word:

Q1 FROZEN SURFACE 4 — GRANT? Two new Config fields need two unconditional
   four-space data.pop lines in run_manifest.py::_versioned_source_config_data
   (insertions only, 25 -> 27, nothing else in the file). Without them the
   qualification subject digest moves and ~40 tests go red. You have called this
   line "the documented recipe"; this is the written request the discipline
   requires. GRANT / REFUSE.

Q2 WHERE THE WARNING IS PRINTED. Enabling the minting flag must emit your words
   "may cause critics to fully consume conjecturer role".
   Road A: on the compile-notice stream the CLI already prints to stderr —
           costs ONE MORE LINE inside run_manifest.py (a second frozen contact).
   Road B: declared on the destination registry (outside run_manifest.py) and
           recorded on the run's own append-only record — zero extra frozen
           contact, but today's CLI does not print it.
   Recommended: B, plus A only if you widen Q1's grant by that one line. A / B / BOTH.

Q3 MAY CRITICISM WRITE TO THE WORKSHOP? SEAM-rules-x-scratch says "Never widen
   the criticism side to close the asymmetry ... Overturning it is an operator's
   call". Your P9 law is that call, but it does not say which half survives.
   Road A: rules/crit.py dispatches the route directly (~20 lines, matches the
           shipped premise-channel precedent, but is a workaround of that rule's
           letter and needs this lane's cone widened).
   Road B: a reader OUTSIDE rules/ walks what the criticism already recorded and
           routes it; crit.py takes a zero-line diff, the asymmetry survives
           as written (~60 lines, more failure modes).
   Recommended: B. A / B.

Q4 HOW STRONG IS "never outrank the seed"? A minted successor loses a rank TIE
   to your seed question by construction, in both selection modes, today, with
   no code change. It can still out-AGE a seed that has already been worked,
   because the age term precedes the seed term.
   Recommended: take the tie guarantee now; park strict domination as its own
   tranche against a pinned scheduler socket. TIE / STRICT.

Q5 CONFIRM THIS SUPERSESSION SENTENCE (it rewrites a tripwire founded on your
   2026-08-15 ruling): "The P9 law of 2026-08-29 supersedes the 2026-08-15
   decommissioning ruling FOR THE SUCCESSOR TRIGGER ALONE — one producer,
   outside rules/, gated by a per-run flag defaulting OFF — while the website
   development pipeline itself stays decommissioned." CONFIRM / AMEND.
```

---

## P9B-6 — strict domination of the seed question over minted problems

WHAT: `Scheduler._select_problem`'s rank key gives the seed question the
tie-break but not strict priority; a freshly minted problem that has never been
worked can outrank a seed that has. This tranche proves the tie half (S18) and
does not touch the scheduler. Only becomes work if Q4 answers STRICT.

Ready-to-send prompt for its future runner:

```
Route: deepreason-orchestrator (class: regression-risk — proposal only, stop
after FIX.md unless the operator says otherwise).

One goal: decide, and if the operator wants it, implement, whether the
operator's SEED question should STRICTLY dominate every spawned or minted
problem in Scheduler._select_problem, rather than only winning rank TIES.

Evidence pointers, all committed:
- src/deepreason/scheduler/scheduler.py, the LIVENESS_QUEUE rank tuple: first
  term is -(age * weight), second is `p.provenance.trigger != SpawnTrigger.SEED`.
  A never-worked problem is maximally aged, so the seed term never decides.
- The round-robin pool's key puts the seed term FIRST, so the two modes do not
  hold the same guarantee in the same strength.
- docs/map/CON-scheduler-ranking.md pins the promise with a two-occurrence grep;
  tests/test_controller.py::test_operator_question_outranks_spawns_at_cycle_zero
  is the regression. Both must stay green or move deliberately.
- The existing mitigation is the wander cap — a CANDIDACY gate under
  Config.SEED_PROBLEM_BUDGET_FLOOR, not a rank term (F3, 2026-08-26).
- The motivating history: selfstudy run-9175f0ec spent a whole 200k-call budget
  inside a connection problem that won cycle 0, while the operator's own
  question terminated budget_denied having made zero provider calls.
- experiments/2026-08-30-change-successor-questions/SPEC.md Q4 states both
  readings and why this was not decided in that tranche.

End state: FIX.md naming which of the two sort keys changes, what the new term
is, which of the two map checks and which regression must be re-derived, and a
measurement showing the change does not starve non-seed problems entirely.
```

---

## Status update — 2026-08-30, after implementation

The lane implemented every in-scope item and left the four parks above
untouched. Two consequences of the parks are now facts on the branch rather
than forecasts, and both are recorded here so the operator's answer is priced
against what actually exists.

**Q1 (frozen surface 4) is still unanswered, and the channel works without it.**
`resolve` and `minting_enabled` read their selector by `getattr(config, FIELD,
<default>)`, so the shipped defaults are correct with NO `Config` field in
existence: an unconfigured run routes to the scratchpad and does not mint.
What a REFUSED grant costs is therefore narrow and nameable — a run cannot
CHANGE either default, so R4's per-run switch and R6's configurable surface stay
parked while everything else is delivered. `src/deepreason/run_manifest.py` and
`src/deepreason/config.py` both take a zero-line diff in this tranche.

**Q3 (may criticism write to the workshop) is still unanswered, and it is what
stops the channel from firing in a live run.** `route` and `mint` are built,
tested and mutation-proved, but NOTHING IN PRODUCTION CALLS THEM: the granted
cone gives `rules/crit.py` OUTPUT SCHEMA ONLY, and Road B's reader is not a spec
item. So a live run today records the field on the criticism output and routes
nothing. That is the honest state, it is stated in DELIVERY.md as the tranche's
largest residue, and the fix is one dispatch site whose LOCATION is exactly what
Q3 decides.

---

## P9B-7 — one guard test is left RED, by design and by the rules

WHAT: `tests/test_decommissioned_pipeline_stays_out.py::test_no_source_file_produces_a_successor_problem`
fails on this branch. It scans `src/deepreason` for four literal spellings of a
SUCCESSOR producer and asserts ZERO hits; `successor/mint.py:88` is now one.

WHY IT IS NOT SILENTLY FIXED: the rewrite is spec item S19, and S19 is GATED on
Q5 — the scope of a superseded operator ruling. An implementer may not decide
that scope, and evading the scan (resolving the trigger through a variable, say)
would be worse than leaving it red: it would disarm an alarm the operator
installed rather than answer it.

BASELINE, so the delta is unambiguous:
`python -m pytest tests/test_decommissioned_pipeline_stays_out.py tests/test_h1_no_spawn_from_refutation.py -q`
gave `10 passed in 0.34s` before this tranche and gives `1 failed, 9 passed`
after. The four protected-channel tests and all five H1 tests are byte-unchanged
and green. Captured at `proof/predicted_red_decommissioned_tripwire.txt`.

THE EDIT, ready to apply the moment Q5 answers CONFIRM — it is four lines:

```
In tests/test_decommissioned_pipeline_stays_out.py, replace the final assertion
of test_no_source_file_produces_a_successor_problem

    assert hits == [], hits

with

    # Operator law 2026-08-29 (P9) supersedes the 2026-08-15 ruling FOR THIS
    # TRIGGER ALONE: exactly one producer, at this path, outside rules/ and
    # outside scan_spawns. The website development pipeline itself stays
    # decommissioned, which is what the four channel tests below still check.
    assert [h.split(":")[0] for h in hits] == [
        "src/deepreason/successor/mint.py"
    ], hits

and add to the test's docstring the supersession sentence Q5 confirms. This is
a strictly MORE specific claim than "zero": it still fails the moment a second
producer appears anywhere, and it additionally fails if the one producer MOVES.
```

---

## Audit disposition — 2026-08-30, after the adversarial skeptic pass

The pass `HANDOFF-lane-B.md` called "the single most important thing on this
page" ran in the pickup window and returned **35 reproduced findings** (3
blocking, 20 major, 12 minor), recorded in full with commands and output in
`FINDINGS.md`.

**All 35 are disposed.** Thirty-four are REPAIRED in this branch — in
`tests/` (fourteen new tests, including the six-file suite's new
`test_successor_wire_carry.py`), in `src/deepreason/successor/` (two false
claim strings), in the seven map documents (five checks that never ran, a false
`Verified-at:` on all seven, two checks that could not fail), in `proof/` (two
transcripts that declared a diff and carried none, one void exit capture), and
in `DELIVERY.md`/`VALIDATION.md` (ten falsified numbers, each corrected with
its original wording kept beside it). One is parked below, and it is parked
because it is an operator decision rather than a defect.

### P9B-8 — a registry row may still declare an `enforcement` nothing performs

WHAT: `SuccessorDeclaration.enforcement` is documented as naming "where the row
is actually READ, so a declaration can never claim a switch no consumer
consults". Nothing verifies that. Audit F12 found the shipped `minting.v1` row
declaring `Config.SUCCESSOR_MINTING_ENABLED` — an attribute `Config` does not
carry and, while it forbids extras, cannot be given. The string is now true,
and the property is still unenforced, so the next row can reintroduce exactly
this defect.

WHY IT IS NOT FIXED HERE: the natural check — "every gate row names a real
`Config` field" — cannot pass today, because Q1 is unanswered and NO successor
`Config` field exists. Writing a check that must fail, or weakening it until it
passes, would both be worse than parking it. This is the same defect class
`DR-INV-evidence-channels` already carries a check for, so the shape is known.

READY TO APPLY THE MOMENT Q1 IS GRANTED AND THE FIELDS LAND — in the same
commit as those fields, not later:

```
def test_every_gate_row_names_a_real_config_field():
    """Regression (audit F12): minting.v1 declared enforcement naming
    Config.SUCCESSOR_MINTING_ENABLED, which Config did not carry."""
    from deepreason.config import Config
    from deepreason.successor.registry import GATES
    for row in GATES.values():
        named = [w.strip(".,;'\"") for w in row.enforcement.split() if w.isupper()]
        for field in named:
            assert field in Config.model_fields, (row.id, field)
```

### What the audit did NOT change, and must not be read as having changed

- **Q1, Q2, Q3, Q4 and Q5 are all still open**, and the audit touched none of
  them. It sharpened the PRICE of two:
  - Q1 is now known to cost more than "the ability to change a default". With
    no `Config` field and `extra_forbidden` in force, R3's "movement elsewhere"
    is provable only against a stub object; a real run cannot re-aim the
    destination at all. `DELIVERY.md`'s R3 row is downgraded to
    done-with-assumption A5 accordingly.
  - Q2 is wider than the Q2 block states: neither typed disclosure has a caller
    anywhere in `src/`, so the operator's warning text reaches no stream and no
    record today (audit F13).
- **P9B-7 stands exactly as written.** The one red guard test is still red,
  still gated on Q5, and its four-line rewrite is still ready to apply. The
  audit was asked to say whether that rewrite is correct and found nothing
  against it.
- **P9B-6 stands.** Strict domination is still a future tranche, live only if
  Q4 answers STRICT. Audit F11 found the delivered LIVENESS_QUEUE arm of the
  TIE proof was vacuous and it is now repaired, so the tie half is proven where
  it previously only appeared to be — which makes Q4 a cleaner decision, not a
  different one.
- **No frozen surface was touched**, by the lane or by the repair. Re-derived
  against all seven paths, not recalled.
