# Fix: `continue` and `amend` re-derive the record and refuse, typed, on a SECURITY-channel finding — and `results --verify` stops contradicting them

Guarantee restored: a committed root whose RE-DERIVED replay verdict carries any
SECURITY-channel finding is refused by both `continue` and `amend` with a typed
code naming the failed checks, before either verb writes anything into it; every
other root — including one that is incomplete, mid-repair, or written by an
older version — continues and amends exactly as today.

## The design decision, answered as a rule (PARKED.md F9 Q-A)

**The gate's question is: does re-deriving this record produce a finding on the
SECURITY channel?** Not "is the record valid". The two differ, and the
difference is the whole tranche.

Stated as a rule rather than a list: the verification subsystem sorts every
finding into one of five channels, and exactly one of them — `security` — means
*this record claims an authority it was not granted, or its route/attempt
provenance does not reconstruct*. That is what tampering looks like. The other
four mean the record is incomplete (`integrity`), unfinished (`completion`),
weakly grounded (`epistemic`), or slow/odd (`operational`) — none of which is
evidence of a breach, and three of which name states the product supports on
purpose and that `amend` exists to REPAIR. The gate therefore refuses on the
security channel and is silent on the rest. Membership is READ from
`verification/report.py:119-129` (`_SECURITY_CHECKS`), never added to; the
channel taxonomy stays the verification subsystem's to define, which is exactly
why the gate asks it rather than re-implementing it.

Q-B (**is `amend` gated at all?**): YES, on the same narrowed question, matching
the law's literal words. The 2026-08-30 reason for doubting it — that gating
amend locks out the repair roads — was an artifact of choosing the FULL
violation set. Under the narrowing, `amendment-chain` (a staged amendment
mid-recovery) and `attached-evidence` (a bound but unintroduced source) are both
`integrity`, so both repair roads stay open. MEASURED, not argued: the three
amend-path files run `65 passed` with the gate evaluated 48 times and refused 0.

Q-C (**do incomplete roots fail the gate?**): the question dissolves.
`run-input`, `run-manifest-hash`, `terminal-authority` and `open` are all
`integrity`. A v1-manifest root — which `verify_root` cannot even open — yields
the single check `open`, on the integrity channel, so it passes the gate
untouched and no exception-arm special case is needed.

## Why NOT the public accessor, priced

`verify_root_report(root).security_valid` is the public, no-private-import road,
and it is REJECTED on measured grounds, both recorded in `proof/`:

  1. **It refuses a lawful root.** On
     `experiments/2026-08-12-live-grounded-extension-expansion/run`,
     `verify_root` reports ZERO violations while the report reports 495 SECURITY
     findings — 494 `transaction-authority` from the DERIVED stream, each
     reading `exceeds frozen authority: unknown v6 task kind
     'defended_trial_step'`. That is version skew, not tampering, and refusing
     it would contradict the 2026-08-14 law that old runs owe the future
     nothing. (`proof/big_root_channels.json`.)
  2. **It costs 2x for zero extra coverage of the thing being gated.** Same
     root: `verify_root` 356.76 s, `verify_root_report` 668.26 s. The report
     runs the whole legacy verifier first (`verification/report.py:1148`) and
     then adds its own passes, so narrowing the QUESTION buys no compute on
     that road.

The gate therefore reads `verify_root`'s own violation list. Equivalence with
the report's own classification is not assumed — it is pinned by a new test
(below): for any root, the gate's answer equals
`{f.check for f in verify_root_report(root).security if f.source == "legacy"}`,
which holds by the report's construction at `verification/report.py:1161-1162`.
That equivalence is what lets `results --verify` answer from the report it has
ALREADY computed, at no extra cost, and still agree with the gate.

## Change sites (exhaustive)

  - `src/deepreason/runtime/continuation.py` — NEW: `security_channel_checks`
    (pure, over a violation list) and `record_security_checks(root)` (re-derives
    via `verify_root`), plus one refusal-message builder shared by both verbs.
    NEW call site inside `prepare_continuation`, placed after the
    `parse_limit`/`ContinuationRequest` pair (~:427-431) and immediately BEFORE
    the `run-stops/` history write (~:434), raising
    `ValueError("CONTINUE_RECORD_NOT_VERIFIED: <check names>")`.
  - `src/deepreason/amendment/apply.py` — NEW call site at the END of
    `_amend_locked`, immediately before `directory.mkdir` (:527), raising
    `AmendmentError("AMEND_RECORD_NOT_VERIFIED", ...)`. Imported
    function-locally, matching the file's existing idiom (:112 already imports
    from `deepreason.runtime.*` this way).
  - `src/deepreason/application/results.py` — compute the report ONCE in
    `results_summary` when `verify=True` and thread it into both `_verification`
    and `_terminal`; `_terminal` gains one key,
    `record_security_violations` (the sorted check names on `--verify`, a typed
    absence otherwise) and folds it into `amend_ready`; one new
    `ABSENCE_REASONS` member; one renderer line.

**Placement is load-bearing, not incidental.** `amend`'s gate goes LAST in
`_amend_locked`, not inside `_require_terminal_stop` where the 2026-08-30
attempt put it: there it shadowed `AMEND_PENDING_CONFLICT` (:517) and
`AMEND_EVIDENCE_NOT_AUTHORIZED`, which were collisions 6 and 7. `continue`'s
goes after the argument parse so a typo in `--cycles` does not first buy a
multi-minute re-derivation, and before the first write so nothing lands in a
tampered root.

## The cone: this fix writes one file outside the declared cone

The declared cone is `application/text_runs.py`, `application/results.py`,
`workflow/lifecycle.py`, `amendment/`, tests, map, tranche dir.
`prepare_continuation` lives in `src/deepreason/runtime/continuation.py`, which
is not on that list. It is NOT a frozen surface (absent from all five in
`docs/map/INV-frozen-surfaces.md` and from `tools/blast_radius.py`'s
`FROZEN_SURFACES`; a blast-radius run over the proposed target set returns
`frozen_surface_verdict: CLEAR`), and there is no in-cone alternative:

  - `application/text_runs.py:1315` is the only in-`src` caller, but the
    acceptance probe imports `prepare_continuation` DIRECTLY
    (`forge_amend_ready.py:56`, called at :79), so a gate there leaves
    `jailbreak_open: true` and the fixed done-criterion unmet — as would five
    committed test files that import it the same way.
  - `workflow/lifecycle.py::build_resumed_lifecycle` never receives a root
    path, is reached only on the owned-control-plane branch, and runs AFTER
    `prepare_continuation` has already written `run-stops/`.

The 2026-08-30 tranche recorded this identical discrepancy (its SPEC.md A6) and
disposed of it by building there; the reverted commit `5fccb1e91` put its 46
lines in exactly this file. Recorded here as a scope note, not smuggled: the
fix writes `runtime/continuation.py`, and `docs/map/SUB-application.md` (which
`Owns:` `src/deepreason/runtime/`) is added to the map ids this tranche moves.

## The per-continue cost, honestly, for big roots

The gate costs ONE `verify_root` per `continue` and per `amend`. Measured on
this container (under some load; the ordering and magnitude are what matter):

| events | `verify_root` | ms/event |
|---|---|---|
| 300 | 12.48 s | 41.6 |
| 754 | 30.03 s | 39.8 |
| 1,576 | 43.12 s | 27.4 |
| 2,416 | 104.23 s | 43.1 |
| 3,200 | 161.00 s | 50.3 |
| 3,751 | 107.65 s | 28.7 |
| **12,991 (largest committed root)** | **356.76 s ≈ 5.9 min** | 27.5 |

Scaling is essentially linear (log-log exponent 0.91, r² 0.96), NOT superlinear
— so the honest headline is minutes, not hours. But the scatter is wide and
asymmetric: against a pooled linear rate the model UNDER-predicts individual
roots by up to 55-72%, so "about 30 ms per event, and budget half again on top"
is the truthful form. Peak RSS on the largest root is ~422 MB.

What that buys and costs, stated plainly rather than adjectivally:
  - `continue` and `amend` are OPERATOR actions taken once per decision, not
    per cycle, on a run that cost hours of provider calls to produce. A ~6
    minute integrity check before resuming the largest run in the repository is
    proportionate.
  - It is NOT free for the test suite. `tests/test_continuation.py::
    test_a_stop_with_no_typed_receipt_refuses_continuation` loops over 16
    COMMITTED roots and reaches the gate on each. The 2026-08-31 simulation
    priced that at roughly +8 minutes on the full gate. **This is a predicted,
    measurable consequence and `dr-verify-outcome` must report the actual
    number, not this estimate.** If the full gate's wall time grows past ~30
    minutes, that is a finding to report, not a thing to hide.
  - `deepreason results --verify` pays NOTHING extra: it answers from the
    report it already computes.
  - The DEFAULT `deepreason results` path pays nothing and therefore cannot
    know; it reports a typed absence rather than a guess.

## A law tension, resolved explicitly rather than silently

The 2026-08-28 law says "Gates are always optional: with warnings." This gate is
NOT switchable, and that is deliberate: that law's enumerated gates
(qualification, criticism authority, judge invocation, admission screens) govern
how content is GENERATED and judged, while the 2026-08-29 P2 law names this one
a "Security boundary, not a convenience" and says in the operator's own words "I
don't want a jailbroken run to be continuable". A security boundary with an
off switch is not one. Recorded here so the reading is visible and can be
overruled; if the operator wants it switchable, that is a one-line change and a
new tranche.

## Regression artifact (what must invert)

  - `experiments/2026-08-30-change-checkpoint-hardening/proof/forge_amend_ready.py`
    -> `jailbreak_open: False`, with `arms.forged.amend` and
    `arms.forged.continue` BOTH `REFUSED`, and `arms.intact` BOTH still
    `ACCEPTED`. (Today: `jailbreak_open: True`, `proof/RED-forge_amend_ready.txt`.)
  - `experiments/2026-08-31-defect-jailbreak-gate-closure/proof/security_channel_separation.py`
    -> `separates: True` with `predicate_source: "shipped"` (today it reads
    `"definition"`, because the helper does not exist yet).

NEW conditions this fix must be tested against, each mutation-proven RED before
GREEN:
  1. A forged committed root refuses `continue`, typed, naming the checks.
  2. The same forged root refuses `amend`, typed.
  3. The refusal happens BEFORE any write: the forged root is byte-identical
     after the refused call (no `run-stops/` entry, no `run-epochs/NNN`).
  4. An INTACT copy of the same root still passes both verbs.
  5. A root with only `integrity` findings still passes both verbs (the
     collision guarantee, as a test rather than as a claim).
  6. The gate's answer equals the report's legacy-source security findings on a
     spread of roots including the forged one (the equivalence `results` relies
     on).
  7. `results --verify` on a forged root reports `amend_ready: False` and names
     the checks; on an intact root it is unchanged.

## Existing tests at risk

| test | why it is touched | disposition |
|---|---|---|
| `tests/test_results_command.py:504-511` exact-set golden on the `terminal` block | the block gains `record_security_violations` | PREDICTED fixture change: add the key to the literal set. The assertion is not weakened — it stays an exact-set equality. |
| `tests/test_results_command.py:416-446` (default path must not re-derive) | the report call moves from `_verification` into `results_summary` | MUST KEEP PASSING unchanged. The default path still never calls `verify_root_report`. |
| `tests/test_terminal_lifecycle_refusal_is_recorded.py:236` (an intact fresh root reports `amend_ready: True`) | `amend_ready` gains a conjunct | MUST KEEP PASSING unchanged — an intact root has an empty security set. |
| `docs/map/CON-run-identity.md:289` (`check:` asserting `verify_root` appears in NEITHER file) | it is a tripwire designed to fire when this gate lands, and says so in its own assertion message | REWRITTEN, never deleted, in the same commit — the Traps entry is rewritten to say the gate landed, and the check is inverted to assert the gate is PRESENT, so it stays a check that can fail. |
| the eight 2026-08-30 collisions | measured green under the narrowing (`8 passed`, gate reached 34 times, zero security findings; and `65 passed` / 48 evaluations / 0 refusals on the amend side) | MUST KEEP PASSING unchanged. If any goes red, that is the GOAL.md stop condition and the tranche stops with the priced fork. |

## Explicitly not changed

`src/deepreason/invariants.py` and `src/deepreason/verification/` — the replay
machinery is consumed by import and nothing is added to `_SECURITY_CHECKS`. The
tempting neighbour is promoting `open` to the security set so a record too
corrupt to replay is also refused; that is NOT done, because a legitimate
v1-manifest root produces the same check name and it would resurrect collision
2. The residue is recorded in PARKED.md rather than papered over.

## Estimated diff

~75 lines of production code across 3 files (continuation.py ~32,
apply.py ~8, results.py ~35), plus tests and map. Under the 150-line budget.
Class `defect`, no frozen surface edited -> proceed to `dr-implement-fix`.
