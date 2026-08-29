# Delivered: make the critic's byte-checked citation channel reachable, and stop it latching shut

Branch: `claude/deepreason-premise-invitation-7qs3kc` (pushed, tree clean)
Base: `origin/main` @ `2a5e984c8`

## What changed

Criticism can now bite the question more than once. The rule that decides
whether a critic is invited to name what a problem PRESUPPOSES used to close
that problem permanently the moment one presupposition was filed; it is now a
ladder — every invitation costs `PREMISE_INVITE_AFTER` (still 2) refuted
candidates, so a problem standing N filed presuppositions must accumulate
`2 × (N + 1)` before it may be asked again. One function changed:
`src/deepreason/premises.py::premise_work_invited`. With nothing filed, the new
rule is byte-for-byte the old one, so a run that never files a presupposition
sees no difference at all.

Second, the record can now tell a seat that was ASKED and said nothing from a
seat that was never asked. `src/deepreason/rules/crit.py::_file_attribution`
resolved the premise text before the invitation, so it returned early and left
no trace; it now resolves the invitation first and records exactly one
`premise-answer:{DECLINED|UNCITED|CITED}` Measure per invited dispatch. An
uninvited dispatch still records nothing — deliberately, because that silence is
the difference the receipt exists to record. The tag is declared in
`src/deepreason/signals.py` before it is emitted, through the signal contract's
own channel.

Third, a decision that cost no code: the `premise_evidence` field STAYS in the
wire contract when no invitation stands. Removing it honestly needs a second
contract id, which enters a closed enum in `cli/doctor.py`, flows into
`pair_inventory`, and moves a qualification subject digest — a frozen surface
and a ~14-minute qualification battery. There is no measured harm to buy with
that: 98 nulls in 98 dispatches, zero fabrications.

How it is proven. The gate is 4384 passed, 6 skipped, **0 failed** — the 4374
baseline plus exactly the ten tests this tranche added, ten of which were run
RED against the unchanged tree first (`proof/s4_red.txt`: 7 failed, 38 passed)
and GREEN after (`proof/s4_green.txt`: 45 passed), same command both sides.
Beyond the tests, `probes/p11_ladder_counterfactual.py` replays all four
committed technique roots read-only with `Harness.at(root, seq)` at every one
of their 98 critic dispatches: the shipped gate had a problem standing an
invitation at 11, the ladder at 19, and in the largest root the count goes from
2 of 44 to 10 of 44 — five of the new openings falling BEFORE seq 779, where
that run established that its own question was malformed and the shipped
channel had been shut for 593 events. Re-run against the changed tree, the
probe also calls the shipped predicate itself and reports
`"shipped_agrees_with_new": true` on all four roots, so the headline table is
the shipped rule replayed rather than a formula asserted about it.

No frozen surface moved (diff pasted empty across all seven paths plus the
frozen-adjacent `route_fingerprint`), and neither parallel window's cone was
written.

## Reconciliation

| R | Operator's words (short) | Disposition | Proof |
|---|---|---|---|
| R1 | "a problem can invite premise work more than once under a stated rule" | **done-with-assumption A1** | `13ed9b50f`; VALIDATION S1 — `4 passed, 25 deselected`; probe: epoch 6 open dispatches 2 → 10, `shipped_agrees_with_new: true` on all four roots |
| R2 | "(1) THE LATCH … Should the gate reopen … Say why, and price the cost of re-asking" | **done** | `ANSWERS.md` §(1): the rule; all three named alternatives refuted on measurements; price read from the prompt bytes — 589 chars invitation + 3 550 legend = ~1 035 tokens per invited dispatch, ~8 300 tokens for epoch 6's eight extra openings, ~1.1 % of that run's 772 482 |
| R3 | "(2) THE EMPTY-REFS SILENCE … should be typed … probably worth doing even if nothing else here is" | **done** — agreed in writing, and strengthened | `9b4801d2f`; `ANSWERS.md` §(2): four indistinguishable cases, not two; VALIDATION S2/S3 — `4 passed`, `1 passed`, `19 passed`; `test_an_uninvited_dispatch_records_no_disposition` proves silence still means never-asked |
| R4 | "(3) THE UNINVITED SCHEMA FIELD … Decide whether the field should be ABSENT" | **done** — decided NO | `ANSWERS.md` §(3), four reasons, two read from source; acceptance output is the EMPTY diff: `git diff --stat origin/main -- llm/contracts.py llm/wire.py` → nothing |
| R5 | "a regression test drives a run where the channel opens after a late refutation" | **done** | `test_a_late_refutation_reopens_the_channel_in_the_real_loop` drives `Scheduler.step` three times; mutation-proven `proof/s4_red.txt` → `proof/s4_green.txt` |
| R6 | "full gate 0 failed; map moved in the same commit" | **done** | `4384 passed, 6 skipped in 879.80s` — 0 failed; commits `13ed9b50f` and `9b4801d2f` each carry their own map documents |
| R7 | "Note in SPEC.md that any live re-measurement of M2 waits until both tranches are merged" | **done** | `SPEC.md` §"R7 — live re-measurement of M2"; repeated in `ANSWERS.md` §R7 |
| R8 | "the optional planted-presupposition probe … is NOT authorized in this window — park it" | **done** — parked unstarted | `PARKED.md` P14, with a ready-to-send prompt |
| R9 | "DELIVERY: per the brief's end state, R-by-R with pasted proof" | **done** | this table |
| C1 | "Do NOT lower PREMISE_INVITE_AFTER as the whole fix" | **honoured** | `PREMISE_INVITE_AFTER == 2`, asserted in VALIDATION S1; the ladder is a reopen rule, not a threshold change |
| C2 | "Do NOT treat the live probe as showing the seat 'will not cite'" | **honoured** | `ANSWERS.md` §R8; nothing in the design rests on that reading, and P14 names the experiment that would settle it |
| C3 | "If any frozen surface or committed digest pin turns out to move, STOP and report" | **honoured** | `blast_radius` verdict CLEAR before design; frozen-surface diff pasted empty after. Nothing to stop for — and R4's answer is NO precisely because the alternative WOULD have moved one |
| C4 | "Do not touch either cone or their tranche directories" | **honoured** | parallel-cone diff pasted empty; `llm/packs.py` read for its `DISCLOSED_ON_DROP` set, never written |
| C5 | "nothing here may let critic prose skip criticism or change what counts as evidence" | **honoured** | the receipt is on its own tag namespace, so the M2 census counts exactly what it counted; `test_a_declined_invitation_moves_no_status` asserts no status moves and no artifact is minted |
| C6 | "ERRATA numbering collisions likely at merge — mint from the tail and note it" | **honoured** | minted from the tail at `2a5e984c8` as E57, with the renumber instruction written into the entry itself; the collision DID occur and the instruction was executed at the merge into `25a3a0687` — the entry is now **E61** |
| C7 | "gate baseline 4374 … docs_verify baseline 4 — a delta beyond four is a finding" | **honoured** | gate 4384 = 4374 + 10 new tests, 0 failed; docs_verify exactly 4, delta ZERO |
| C8 | "Never work around a REFUSED_* or typed stop" | **honoured** | none encountered |
| C9 | operator law: gates optional with warnings, behaviour deterministic yet configurable | **honoured, with A4 open** | the ladder is deterministic given a configuration and adds no gate; but its cadence is still a module constant, which the modularity law wants configurable — parked as P16 rather than resolved silently |

No requirement is deferred and none is not-done.

## Assumptions the operator may override

- **A1** — the reopen rule is the multiplicative ladder, not "any new refutation
  reopens". The bare version is unbounded: on epoch 6 it would have re-invited
  on 42 of 44 dispatches, ~43 000 tokens, and the brief asked for the cost of
  re-asking to be priced.
- **A2** — the disposition gets its own `premise-answer:` namespace. Forced, not
  chosen: `premise-citation:` IS the M2 census's definition, and C5 forbids
  moving it.
- **A3** — no committed digest pin moves. Verified, not assumed.
- **A4** — `PREMISE_INVITE_AFTER` stays a module constant. The modularity law
  wants it configurable and frozen surface 4 stands in the way. Parked as P16.
- **A5** — the disposition is derived from the same lookup the filing gate uses,
  not from the invitation the pack carried, so the record holds one answer to
  one question.

**Two budget overruns, flagged rather than absorbed.** The spec's own ceiling
was 233 changed lines; the tranche came in at 416, and its source sub-ceiling of
60 came in at 73. Both are recorded as dated amendments in `SPEC.md` with
`tools/diff_budget.py`'s output pasted, not by rewriting the headline to match
the diff. The overrun is where a ceiling is least alarming and I want you to be
able to check that claim rather than take it: the whole of the first is
regression tests, which R5/R6 mandate; of the source overrun's 73 insertions,
**10 are executable statements** and the other 63 are the signal declaration's
required semantics prose and two docstrings naming the run ids the change
answers to. The mis-estimate was mine, in my own spec.

## Map delta

changed: `docs/map/CON-problem-layer-lifecycle.md` (the producer section now
states the ladder, with the measured before/after), `docs/map/CON-criticism-source.md`
(a new Traps entry on the disposition receipt and a "where to change what" row),
`docs/map/SEAM-scheduler-x-rules.md` (the premise-layer row).
created: none — the pair this change spans (`scheduler × rules`) already had its
seam document.
new checks: **4** — two on the ladder (the four behavioural tests; an arithmetic
pin on `refuted >= after * (standing + 1)` plus `PREMISE_INVITE_AFTER == 2`) and
two on the receipt (the four disposition tests; an AST pin that the invitation
lookup is the FIRST statement of `_file_attribution`, which is the thing that
would silently regress). All four were RUN before being written down.
left stale: `SEAM-rules-x-scratch.md` — `--stale` lists it because it owns
`crit.py`. Left, with the reason: its concern is the criticism/scratchpad
separation, this change adds no scratch import and no pack parameter, both its
enforcing tests are green, and its pinned `render_crit_pack` /
`render_batch_crit_pack` parameter lists are unchanged. The other seven entries
`--stale` lists are all from earlier tranches and predate this branch.

`docs_verify` 4 failed (the baseline exactly, delta zero), `--audit` 0 findings,
`--links` 0 dangling, `--coverage` 2 findings both naming files outside this
cone.

## Errata

**E61** (minted as E57; renumbered at merge — see below) — the audit named the wrong statement as the cause of the citation
channel's silence. `AUDIT_REPORT.md` §F-B and the P11 prompt both locate the
record's blindness at `_check_premise_citations`'s empty-refs return. The
mechanism is real and the conclusion is right, but it explains **1 of the 98
dispatches**: on the other 97 `_file_attribution` returned before the checker
was ever reached. A reader taking the sentence at face value would have fixed
the citation checker and changed nothing for 97 dispatches; the fix that works
is an ORDERING fix one function up. Minted from the tail at `2a5e984c8` with a
renumber instruction inside the entry, per C6. The collision occurred: a
third window had taken E57 for the capability-cycle heartbeat entry, and
E58–E60 were taken by merge time, so this entry became **E61** at the merge
into `25a3a0687`. Both E57 entries were kept whole.

## No live evidence segment is owed

No live run happened: this is an offline design tranche, and R7 says a live
re-measurement of M2 waits for P10. The `probes/` directory holds the tranche's
own re-runnable evidence, and every committed run root it reads was read
READ-ONLY out of `origin/claude/spec-to-code-technique-k5209o` into a scratch
directory. No committed root was written or modified.

## Parked (not done, not promised)

Three entries, each with a ready-to-send prompt in `PARKED.md`:

- **P14 — the planted-presupposition probe.** The only experiment that separates
  "the seat declines the channel" from "the seat sees nothing wrong with the
  question". Explicitly not authorized in this window; not started.
- **P15 — the batch-unanimity rule.** Measured here and outside the brief's
  three questions: every critic dispatch in these roots is a batch, and the
  invitation is withheld unless every target in the batch answers ONE problem.
  On the epoch-5 root a problem stood an invitation at 9 of 10 dispatches and
  only 3 packs carried it. So the ladder raises how often the channel COULD
  open, and this rule still decides how often it is actually seen.
- **P16 — `PREMISE_INVITE_AFTER` is not reachable as configuration.** The
  2026-08-26 modularity law says every behaviour a run can vary must be
  reachable as configuration or a registered artifact, never by editing code.
  This constant is a code edit, and the reason is frozen surface 4.

**Recommended next: P15.** It is the only one of the three that changes how
often the channel this tranche opened is actually exercised — the ladder raised
the number of dispatches where a problem stands an invitation from 11 to 19
across the four roots, and the unanimity rule is what decides how many of those
19 a seat ever sees. P14 measures a seat's behaviour on a channel whose
frequency is still being fixed, and P16 is a frozen-surface request that should
wait until someone actually wants a different cadence.

---

# Segment 2 — 2026-08-29: delivered on the MERGED state, against current main

**Why this segment exists.** The segment above is true and is not withdrawn,
but it delivered the tranche against its own base, `2a5e984c8`. Current main is
`25a3a0687`, 176 files ahead of that base, and a delivery certified on a tree
that is 176 files behind certifies a tree that will never ship. `VALIDATION.md`
segment 2 re-ran every `SPEC.md` acceptance check, the full gate and
`docs_verify` on the merged tree and returned **PASS**; this segment closes the
tranche on that state.

Branch: `lane/a-p11` @ `43f03855d`, working tree clean, 13 commits ahead of
`origin/main` (= `25a3a0687`).

**Deviation from `dr-deliver-change` step 1, stated rather than silently taken:
NOT PUSHED, and no pull request opened.** This tranche was closed inside a
parallel batch whose orchestrator owns integration and the push. The skill's
exit criterion "everything pushed" is therefore met by the orchestrator, not
here, and the branch head exists only locally at the time of writing. Every
other exit criterion is met in this worktree.

## What this stage changed

One commit of substance beyond the merge and the validation record:

**`43f03855d` — the fourth new map check is now EXECUTED, not decoration.**
`VALIDATION.md` segment 2 finding F1 measured that the AST pin at
`CON-criticism-source.md:170` — the claim that the invitation lookup is the
FIRST statement of `_file_attribution` — was authored in the multi-line form,
which `tools/docs_verify.py:47` does not parse, so the verifier never ran it.
The claim was TRUE; it was simply unchecked, which is precisely what the map's
re-derivation authentication exists to prevent. Converted to the single-line
form and mutation-proven before being trusted:
`proof/s10_check_form_mutation.txt` records the parser going from 13 parsed
checks to 14, and the check exiting 1 (`AssertionError: text = (premise_text or
'').strip()`) when the statement order is regressed, then 0 when restored. That
document's `Verified-at` advanced to `499886a3e`, the commit its `Owns:` file
was checked against; `--stale` no longer lists it. No source, test or behaviour
was touched, so the pytest gate cannot be affected and was not re-run.

The map-delta line in segment 1 — "new checks: 4 … All four were RUN before
being written down" — was true as written (all four were run by hand) but would
have led a reader to assume all four are run by the verifier. Three were. As of
`43f03855d`, four are.

## Reconciliation on the merged tree

Deliberately a list, not a second markdown table: `SPEC.md` S8's acceptance
check is `grep -c '^| R[1-9]' DELIVERY.md` = 9, written when one delivery table
was foreseen. A second table would make that 18 and turn a passing check red for
a reason that has nothing to do with the work. The check is left exactly as
written and measuring exactly what it was written to measure; the reconciliation
below is complete regardless of its shape. Each entry re-anchors segment 1's
disposition to evidence taken on the merged tree.

- **R1** — "a problem can invite premise work more than once under a stated
  rule". **done-with-assumption A1**, re-anchored: `VALIDATION.md` segment 2 S1,
  `4 passed, 25 deselected`, and `PREMISE_INVITE_AFTER == 2` unchanged. The
  counterfactual pricing (epoch 6: 2 open dispatches under the old latch, 10
  under the ladder) is INHERITED, not re-derived — see Residue below.
- **R2** — "(1) THE LATCH … Should the gate reopen … Say why, and price the cost
  of re-asking". **done**: `ANSWERS.md` §(1), unchanged by the merge; the three
  named alternatives refuted on measurements, the price read from prompt bytes
  (~1 035 tokens per invited dispatch, ~8 300 for epoch 6's eight extra
  openings, ~1.1 % of that run's 772 482).
- **R3** — "(2) THE EMPTY-REFS SILENCE … should be typed … probably worth doing
  even if nothing else here is". **done**, agreed in writing and strengthened:
  segment 2 S2 `4 passed, 12 deselected` plus `1 passed`, the census-namespace
  check OK, and S3 `19 passed` for the signal declaration.
- **R4** — "(3) THE UNINVITED SCHEMA FIELD … Decide whether the field should be
  ABSENT". **done**, decided NO. The acceptance output is an EMPTY diff, and it
  is now empty against CURRENT main: `git diff --stat 25a3a0687..HEAD --
  src/deepreason/llm/contracts.py src/deepreason/llm/wire.py` prints nothing.
- **R5** — "a regression test drives a run where the channel opens after a late
  refutation". **done**, and the mutation pair was RE-DERIVED on the merged tree
  rather than inherited: the three behaviour files reverted to `25a3a0687`
  content gave `7 failed, 38 passed` — byte-for-byte the seven failures in
  `proof/s4_red.txt` — and `45 passed` restored.
- **R6** — "full gate 0 failed; map moved in the same commit". **done**:
  `4443 passed, 6 skipped in 1181.46s`, **0 failed**. The count is 4443 rather
  than segment 1's 4384 because current main brings its own new tests; C7's
  4374 baseline was stated for `2a5e984c8` and does not transfer. What transfers
  is 0 failed. The map rode `13ed9b50f` and `9b4801d2f`, both inside the merge.
- **R7** — "Note in SPEC.md that any live re-measurement of M2 waits until both
  tranches are merged". **done**: `SPEC.md` §"R7", unchanged. Still owed, and
  still owed after this delivery: no live re-measurement happened here, and this
  batch is offline with no provider.
- **R8** — "the optional planted-presupposition probe … is NOT authorized in
  this window — park it". **done**, parked unstarted as P14;
  `grep -c "Ready-to-send prompt" PARKED.md` = 3, unchanged by this stage.
- **R9** — "DELIVERY: per the brief's end state, R-by-R with pasted proof".
  **done**: segment 1's table plus this re-anchored list, both with the
  instrument output pasted in `VALIDATION.md`.

Standing constraints, re-checked on the merged tree:

- **C1** (do not lower `PREMISE_INVITE_AFTER` as the whole fix) — honoured;
  the constant is still 2 and the change is a reopen rule.
- **C2** (do not read the live probe as "the seat will not cite") — honoured;
  nothing in the design rests on that reading.
- **C3** (STOP if any frozen surface or digest pin moves) — honoured. The diff
  `25a3a0687..HEAD` over all seven paths of the five frozen surfaces plus the
  frozen-adjacent `route_fingerprint` is EMPTY. Nothing to stop for.
- **C4** (parallel-window cones untouched) — honoured; that diff is empty too.
- **C5** (nothing may change what counts as evidence) — honoured; the receipt
  sits on its own `premise-answer:` tag family, so the M2 census counts exactly
  what it counted.
- **C6** (ERRATA collisions likely at merge — mint from the tail and note it) —
  honoured, and the predicted collision OCCURRED: this tranche's entry, minted
  as E57, is now **E61**, renumbered at the merge per the instruction written
  inside the entry itself. Both E57 entries kept whole.
- **C7** (a docs_verify delta beyond four is a finding) — honoured, delta ZERO.
- **C8** (never work around a REFUSED_* or typed stop) — honoured; none arose.
- **C9** (operator law: gates optional with warnings, behaviour deterministic
  yet configurable) — honoured with **A4 open**: the ladder is deterministic
  given a configuration and adds no gate, but its cadence is still a module
  constant, parked as P16 rather than resolved silently.

No requirement is deferred and none is not-done.

## Assumptions the operator may override

Unchanged from segment 1: **A1** the multiplicative ladder rather than "any new
refutation reopens" (the bare version would have re-invited on 42 of 44 epoch-6
dispatches, ~43 000 tokens); **A2** the `premise-answer:` namespace, forced by
C5; **A3** no committed digest pin moves — verified, not assumed; **A4**
`PREMISE_INVITE_AFTER` stays a module constant, which the modularity law wants
configurable (parked P16); **A5** the disposition derives from the same lookup
the filing gate uses. The merge introduced no new assumption.

## Map delta (merged tree)

changed: `docs/map/CON-problem-layer-lifecycle.md`,
`docs/map/CON-criticism-source.md`, `docs/map/SEAM-scheduler-x-rules.md`.
created: none — the `scheduler × rules` pair already had its seam document.
new checks: **4, all four now executed by the verifier** (segment 1 landed
three live and one inert; `43f03855d` made the fourth live and mutation-proved
it). Check total across the map: 1153 → 1154.

    $ python tools/docs_verify.py
    docs_verify [full]: 69 documents, 1154 checks, 4 workers
      FAIL CON-run-identity.md:200  (shallow clone: rename history absent)
      FAIL CON-run-identity.md:202  fatal: ambiguous argument '1637e808'
      FAIL CON-run-identity.md:204  fatal: ambiguous argument 'f304fec1'
      FAIL INV-frozen-surfaces.md:181  (pre-existing falsified transport_failure census)
    docs_verify: 4 failed

    $ python tools/docs_verify.py --audit
    docs_verify --audit: 0 finding(s)

    $ python tools/docs_verify.py --links
    docs_verify --links: 0 dangling reference(s), 69 document(s)

Exactly the four-failure baseline this lane was given, delta ZERO, and none of
the four names a file in this cone.

left stale: `SEAM-rules-x-scratch.md` — `--stale` lists it because it owns
`crit.py`. Left, with the reason recorded in segment 1: its concern is the
criticism/scratchpad separation, this change adds no scratch import and no pack
parameter, both its enforcing tests are green in the full run above, and its
pinned `render_crit_pack` / `render_batch_crit_pack` parameter lists are
unchanged. `CON-criticism-source.md` was on that list in segment 1 and is NOT
any more: its `Verified-at` now names `499886a3e`, the commit its owned file
was actually checked against. The other 14 documents `--stale` lists belong to
other tranches already on main.

## Errata

**No new errata entry this stage.** `E61` stands from segment 1 (the audit named
the wrong statement as the cause of the citation channel's silence; the
mechanism it named explains 1 of 98 dispatches, and the fix that works is an
ordering fix one function up). Nothing this stage examined turned out to be a
committed claim that is wrong: the F1 map claim was true-but-unchecked and is
now checked, and the segment-1 map-delta sentence it qualifies is corrected
above in the same document a reader will already be reading. `docs/ERRATA.md`
is also outside this lane's declared file cone, so a new entry would not have
been this lane's to mint.

## Parked (not done, not promised)

Unchanged — three entries, each with a ready-to-send prompt in `PARKED.md`:

- **P14 — the planted-presupposition probe.** The only experiment that separates
  "the seat declines the channel" from "the seat sees nothing wrong with the
  question". Explicitly not authorized; not started.
- **P15 — the batch-unanimity rule.** Every critic dispatch in these roots is a
  batch, and the invitation is withheld unless every target in the batch answers
  ONE problem. On the epoch-5 root a problem stood an invitation at 9 of 10
  dispatches and only 3 packs carried it.
- **P16 — `PREMISE_INVITE_AFTER` is not reachable as configuration**, which the
  2026-08-26 modularity law says it should be; the obstacle is frozen surface 4.

**Recommended next: P15.** It is the only one of the three that changes how
often the channel this tranche opened is actually exercised — the ladder raised
the dispatches where a problem stands an invitation from 11 to 19 across the
four roots, and the unanimity rule decides how many of those 19 a seat ever
sees. P14 measures a seat's behaviour on a channel whose frequency is still
being fixed; P16 is a frozen-surface request that should wait until someone
actually wants a different cadence.

## Residue — what this delivery does NOT prove

Recorded as inconclusive rather than implied, per the honest-ledger rule.

1. **The ladder counterfactual is INHERITED, not re-derived here.**
   `probes/p11_ladder_counterfactual.py` replays four committed technique roots;
   none is present in this checkout (the technique branch was read-only evidence
   and was never merged), and `find . -maxdepth 5 -type d -name
   'failed-epoch5-run-456885*'` returns nothing. So the headline pricing —
   epoch 6 going from 2 open dispatches to 10, `"shipped_agrees_with_new": true`
   on all four roots — stands as the executor's committed measurement in
   `probes/p11_ladder_counterfactual_shipped.json` and was not re-confirmed on
   the merged tree. It costs nothing load-bearing: no acceptance check depends
   on it, and the ladder's arithmetic is pinned by four live tests at
   `CON-problem-layer-lifecycle.md:173`.
2. **One inert check remains in `CON-criticism-source.md`, at line 146** — the
   pre-existing P4 contract pin on `premise_evidence`, in the same multi-line
   form. It arrived on main before this tranche and was left alone rather than
   swept into a delivery commit. It resolves when the separate window landing
   multi-line check support merges.
3. **`docs/ERRATA.md` carries two earlier numbering collisions from parallel
   minting** — a second E56 (~line 1545) and the E57 at ~line 1410. Observed
   during the merge, not this lane's to fix.
4. **R7's live re-measurement of M2 has not happened** and could not: this batch
   is offline with no provider. It remains owed once P10 and this tranche are
   both on main.
5. **The gate's duration is not a clean-box measurement.** 19:41 here against
   14:39 in segment 1, with other lanes' processes visible on the box.
   Contention changes duration, not verdicts, and the verdict is 0 failed — but
   the number is recorded as what it is.

## Verdict: DELIVERED

Every requirement in `REQUEST.md` is done or done-with-a-stated-assumption on
the MERGED state; the full gate is `4443 passed, 6 skipped`, **0 failed**;
`docs_verify` is at its exact four-failure baseline with delta zero and all four
of this tranche's map checks now executed; the frozen-surface and
parallel-window diffs are empty. Not pushed — the batch orchestrator integrates.
