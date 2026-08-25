# CHECKLIST — Rung 7: wounds, falls, and succession

Authority: `SPEC.md` (S1-S11, A1-A10), which cites `REQUEST.md` (R1-R9,
G1-G7, C-*). One step per `dr-execute-step` invocation. A step is done
only when its DONE-CRITERION output is pasted under it.

Gate discipline (C-GATE): the RING while iterating, the full gate at each
`[COMMIT]` boundary marked GATE. `python tools/blast_radius.py` and
`python tools/diff_budget.py 053c129ac --ceiling 700 --paths src` run at
every `[COMMIT]`. Map documents move in the SAME commit as their code
(C-MAP).

---

## Step 1 — the frame entry's recognition (S1; R2, G2, G7)

Add to `src/deepreason/calculus/standing.py`: `FallenFrame`,
`fallen_frames`, `unseparated_fallen_frames`, `framed_problem_ids`.
`consulted()`, `StandingGrant`, `frame_assertions` and
`consultability_of` are NOT touched. Export the new names from
`calculus/__init__.py`.

DONE-CRITERION:
`python -c "from deepreason.calculus import fallen_frames, framed_problem_ids, unseparated_fallen_frames; import inspect; from deepreason.calculus.standing import consulted, StandingGrant; assert str(inspect.signature(consulted)) == '(harness)'; print('ok')"`

**DONE 2026-08-24.**

```
DONE-CRITERION step 1: consulted() and StandingGrant unchanged; four new names import
33 passed in 39.08s        # tests/test_calculus_standing.py tests/test_calculus_frame_assertions.py
```

## Step 2 — tests for the frame entry, RED first (S1, S2; G2, G3)

Write `tests/test_calculus_cascade_frame_entry.py`. It must be RED
against step 1's tree (the marking function does not yet read the frame
entry) and green after step 3. Covers: fall marks, revocation marks,
contestation marks NOTHING, an unseparated fallen assertion marks
nothing, a scope that no longer compiles admits nothing, and the
structural assertions for G2 (one marking function) and G3 (no stored
grade, exactly one assigning function).

DONE-CRITERION: the RED run pasted (`python -m pytest
tests/test_calculus_cascade_frame_entry.py -q` — failures naming the
missing frame entry, not import errors).

**DONE 2026-08-24 — RED, as designed.** Four failures, every one naming the
missing frame entry; no import error, no collection error.

```
FAILED tests/test_calculus_cascade_frame_entry.py::test_a_fall_marks_every_problem_the_frame_carried
FAILED tests/test_calculus_cascade_frame_entry.py::test_a_revocation_marks_with_the_weaker_grade
FAILED tests/test_calculus_cascade_frame_entry.py::test_the_frame_entry_is_read_not_reimplemented
FAILED tests/test_calculus_cascade_frame_entry.py::test_the_mark_is_reversible_by_the_same_computed_predicate
4 failed, 9 passed in 3.49s
```

## Step 3 — ONE marking function, both entries (S2; R2, G2, G3)

Rewrite `premises.py::premise_orphaned` as: collect `(problem_id,
status)` pairs from both entries, then ONE grading step. Function-local
import of `deepreason.calculus.standing`. Narrow `DR-SUB-calculus`'s
`premises.py` trap check to the claim it was always about, in this same
commit, with the narrowing's reason written down.

DONE-CRITERION: `python -m pytest
tests/test_calculus_cascade_frame_entry.py tests/test_premise_channel.py
tests/test_premise_channel_loop.py -q` — 0 failed.

**DONE 2026-08-24.** GREEN, and the ring with it.

```
tests/test_calculus_cascade_frame_entry.py ..... 14 passed in 4.01s
tests/test_premise_channel.py tests/test_premise_channel_loop.py
tests/test_calculus_cascade_frame_entry.py ..... 49 passed in 7.45s
ring (premises + standing + frame assertions + render + separation + closure):
129 passed in 44.50s
diff budget: {"areas": {"src": 191}, "ceiling": 700, "verdict": "WITHIN"}
```

**One design point the tests forced, recorded rather than absorbed.** σ can
admit the assertion's OWN promotion problem, because the two are about the same
subject — and marking it would deprioritize in scheduling the one problem D-1
requires to stay on the frontier when a frame falls. The entry excludes exactly
that problem, and `test_a_fallen_frame_does_not_orphan_its_own_promotion_problem`
proves σ admits it, so the exclusion is what does the work rather than the
scope.

Map moved in this commit: `DR-CON-problem-layer-lifecycle` (the second entry,
one marking function, the three conditions), `DR-SUB-calculus` (the NARROWED
`premises.py` trap check, with the narrowing's reason).

## Step 4 — Prop 9.6 end to end, with its mutation proof (S10; G1)

Write `tests/test_calculus_wound_persistence.py`: a wound on the
subject's own observation-valued commitment moves `status(b)` to
`REFUTED`, leaves the grant returned by `standing_of` byte-identical,
leaves the frame rendering, and produces NO cascade mark. Then the
MUTATION: in a scratch copy, make a wound touch standing; run RED;
restore; run GREEN. Both outputs pasted.

DONE-CRITERION: the RED output, the restore, and the GREEN output all
pasted in the step's record.

**DONE 2026-08-24.** Six proofs, then the mutation.

GREEN (shipped tree):

```
tests/test_calculus_wound_persistence.py ......   6 passed in 0.36s
```

MUTATION APPLIED — `standing.py::consultability_of` gains a clause making a
REFUTED subject remove its own standing, which is exactly what Prop 9.6
forbids:

```python
    if harness.state.status.get(body.subject_ref) is Status.REFUTED:
        return Consultability(False, FRAME_NOT_UNREFUTED, (body.subject_ref,))
```

RED:

```
FAILED tests/test_calculus_wound_persistence.py::test_a_wound_changes_status_and_leaves_standing_untouched
FAILED tests/test_calculus_wound_persistence.py::test_the_wound_renders_in_frame_across_the_scope
FAILED tests/test_calculus_wound_persistence.py::test_many_wounds_still_leave_standing_untouched
3 failed, 3 passed in 0.38s
```

RESTORED from the scratch copy — `git diff src/deepreason/calculus/standing.py`
prints nothing — then GREEN again:

```
......                                                                   [100%]
6 passed in 0.36s
```

The mutation kills three of the six: the end-to-end proposition, the in-frame
wound render, and the many-wounds quantitative form. The three it does NOT kill
are the ones a label-only test would have been satisfied by — which is why the
file checks the grant, the render and the cascade as well as the label.

## Step 5 — batch translation offers (S3; R3) `[COMMIT]` GATE

`premises.py::batch_translation_offers`, the
`premise.batch-translation-offered.v1` declaration in `signals.py`, the
scheduler's per-cycle receipt, and
`tests/test_premise_batch_offers.py`. Map: `DR-CON-problem-layer-lifecycle`
and `DR-INV-signal-contract` move in this commit.

DONE-CRITERION: `python -m pytest tests/test_premise_batch_offers.py
tests/test_signals.py -q` — 0 failed — plus the blast-radius and
diff-budget JSON for the commit.

**DONE 2026-08-24.**

```
tests/test_premise_batch_offers.py ...........        11 passed in 0.51s
tests/test_signal_contract.py tests/test_signals.py   19 passed in 3.66s
blast radius: {"frozen_surface_verdict": "CLEAR"}
diff budget:  {"areas": {"src": 300}, "ceiling": 700, "verdict": "WITHIN"}
```

**One near miss, recorded rather than absorbed.** The first `orphan_causes`
compared GRADE STRINGS to decide which cause explains a mark — a second place
where a grade was being decided, which
`test_there_is_no_second_marking_mechanism` caught in the same session. It now
expresses precedence on the LABEL, exactly as the marking function does, and
READS the grade from the mark, so the two cannot disagree.

Map moved in this commit: `DR-CON-problem-layer-lifecycle` (batch offers, the
sixth signal, the new entry points). `DR-INV-signal-contract` needed NO change —
it pins no signal count — and `DR-REC-add-signal`'s own gate
(`tests/test_signal_contract.py tests/test_signals.py`) is green, which is that
recipe's step 4.

## Step 6 — N3 at scale (S10; G4)

`tests/test_cascade_n3_at_scale.py`: ONE fall over a thousand problems;
the cascade marks them; a sample retires, another translates, another is
found independent; NOT ONE resolution asserts insolubility; attacking a
retirement returns its problem to the frontier. The laziness claim is
measured, not asserted: marking a thousand problems costs one derivation.

DONE-CRITERION: `python -m pytest tests/test_cascade_n3_at_scale.py -q`
— 0 failed, with the recorded wall time.

**DONE 2026-08-24.**

```
tests/test_cascade_n3_at_scale.py .......   7 passed in 11.15s
under the gate's own parallelism:           7 passed in 12.23s   (-n 4)
```

**Restructured mid-step for a real defect, not a style preference.** The first
version had tests that depended on earlier tests' mutations of a module-scoped
fixture. That passes serially and FAILS under `-n 4`, which scatters tests
across workers by default — the gate's own configuration. The fixture now
builds the final state and every test is a pure read, so the file is
order-independent by construction. Verified under `-n 4` above, not assumed.

## Step 7 — succession detection and the render exception (S4; R4)

`src/deepreason/calculus/succession.py` (detection, criteria,
`render_succession_context`) and the ONE suppression site in
`calculus/render.py::frame_slices`. `tests/test_calculus_succession.py`.

DONE-CRITERION: `python -m pytest tests/test_calculus_succession.py
tests/test_frame_render.py -q` — 0 failed.


**DONE 2026-08-24.**

```
tests/test_calculus_succession.py ..............   14 passed in 0.83s
ring (succession + frame render + standing + H1 + promotion closure/succession):
88 passed in 41.59s
```

**One fixture point the tests forced.** The narrow tides scope does NOT admit
the discrimination problem, so a suppression test written against it would have
looked green while the frame was merely out of scope. The rivalry fixture uses
a scope that DOES admit it, and the test asserts admission first — the
suppression is what does the work, not the scope.

## Step 8 — the trial's two roads and its record (S5, S6; R6-R9, G5)

The two GENERIC keywords on `informal/trial.py::pairwise_discriminate`
(`presentation`, `observer`); `program_road`, `run_succession_trial` and
the record in `calculus/succession.py`; the scheduler's succession branch.
`tests/test_calculus_succession_trial.py`, including the CONSTRUCTED
order-disagreement case.

DONE-CRITERION: `python -m pytest tests/test_calculus_succession_trial.py
tests/test_trial.py tests/test_scheduler*.py -q` — 0 failed.


**DONE 2026-08-24.**

```
tests/test_calculus_succession_trial.py ...................   19 passed in 0.84s
ring (succession trial + succession + trial + authority policy + scheduler +
frame render):                                               111 passed in 6.57s
tests/test_signals.py tests/test_signal_contract.py           19 passed in 3.73s
```

**The gate caught an undeclared signal, and that is the mechanism working.**
`succession.trial-flip-rate.v1` was emitted before it was declared;
`test_every_emitted_signal_is_registered` AST-scans the source tree and failed
on it. Declared through the typed channel per `DR-REC-add-signal` — name, unit,
producer-agnostic semantics, staleness bound — never by teaching a consumer
about succession.

`informal/trial.py` gained exactly two GENERIC keywords, `presentation` and
`observer`. Neither names succession and the module imports nothing from
`calculus`, so no new package edge exists and there is still ONE pairwise
instrument.

## Step 9 — anomaly conservation, proved (S7; R5) `[COMMIT]` GATE

`tests/test_calculus_anomaly_conservation.py`, all four limbs. Map:
`DR-SUB-calculus`, `DR-CON-standing-and-background` and
`DR-SEAM-calculus-x-rules` move in this commit.

DONE-CRITERION: `python -m pytest
tests/test_calculus_anomaly_conservation.py -q` — 0 failed — plus the
blast-radius and diff-budget JSON.


**DONE 2026-08-24.**

```
tests/test_calculus_anomaly_conservation.py ........   8 passed in 0.27s
ring (succession, trial, promotion, scheduler, signals, frame render):
145 passed in 11.11s
diff budget: {"areas": {"src": 893}, "ceiling": 700, "verdict": "EXCEEDED"}
```

**The diff budget EXCEEDED at this checkpoint — the workflow's own stop
condition.** 893 src insertions against the ledgered 700, with roughly 1000
projected at completion. Put to the operator with priced roads; the answer and
its disposition are ledgered as REQUEST.md Amendment 1.

Map moved in this commit: `DR-SUB-calculus` (succession, the render exception,
anomaly conservation, `Owns:` gains `succession.py`),
`DR-SEAM-calculus-x-rules` (the exception rides the seam without widening it,
plus its own trap row), `DR-CON-standing-and-background` (Prop 9.6 proved, the
second cascade entry).

## Step 10 — the promotion problem's wound-count rank (S8; C-D1)

`calculus/nomination.py::promotion_wound_counts`, one term in
`Scheduler._select_problem`'s `rank` AFTER the SEED term, and the same
term in the non-liveness pool sort. `tests/test_scheduler_promotion_rank.py`,
including the assertion that the operator's seed still wins every tie.

DONE-CRITERION: `python -m pytest tests/test_scheduler_promotion_rank.py
tests/test_scheduler*.py -q` — 0 failed.


**DONE 2026-08-24.**

```
tests/test_scheduler_promotion_rank.py ..........   10 passed in 1.48s
ring (promotion rank + scheduler + v6 deferral + route firewall + nomination
+ nomination live):                                 47 passed in 12.89s
```

Two fixture points the tests forced: `Scheduler` takes an adapter, and the
fixture passes an EMPTY one — selection reaches no provider, so if it ever
needed a seat this would fail rather than quietly succeed. And the constructor
records its own start-up events, so the "moves no label" snapshot is taken
AFTER construction, or it would assert something the test is not about.

## Step 11 — `cascade-integrity` in `verify_root` (S9; the §1 grant)

The three limbs at the END of `verify_root`, the name in
`_EPISTEMIC_CHECKS`, `tests/test_cascade_integrity.py`, and the
committed-root probe proving the check is additive. Map:
`DR-INV-frozen-surfaces` and `DR-SUB-verification` move in this commit.

DONE-CRITERION: `python -m pytest tests/test_cascade_integrity.py -q` —
0 failed — plus the committed-root probe output and the insertions/
deletions count for `invariants.py`.


**DONE 2026-08-24.**

```
tests/test_cascade_integrity.py ........   8 passed in 20.99s

git diff --numstat 053c129ac -- src/deepreason/invariants.py src/deepreason/verification/report.py
87      0       src/deepreason/invariants.py
1       0       src/deepreason/verification/report.py
```

**INSERTIONS ONLY — 87 and 1, zero deletions**, which is what the grant said it
would be. The committed-root probe
(`experiments/live_engaged_2026-07-27/run-f4fa6663e5412d64df943a5a22342baf`)
returns no `cascade-integrity` finding, so additive is proven against a root
that predates the layer rather than asserted.

**One correction the step turned up, and it was already wrong before this
tranche.** `DR-SUB-verification` claimed the epistemic checks "are not
`verify_root` findings at all". That stopped being true at Rung 4, when
`standing-integrity` began being emitted from `verify_root` into the epistemic
channel; `cascade-integrity` is the second. The row's own check pinned ONE
member by name, and a check that names one member cannot notice the set
growing. Corrected in this commit with a check over BOTH partitions, and
ledgered as `docs/ERRATA.md` E51.

Map moved in this commit: `DR-INV-frozen-surfaces` (the granted contact with
its three checkable facts), `DR-SUB-verification` (the corrected row).

## Step 12 — the axiom ledger (S10; G7)

`tests/test_calculus_axioms_rung7.py`: A6 preserved at the frame entry,
A9 preserved (the succession render and the trial record move no label),
and NO standing-layer spawn trigger exists (C-D1's absence). Map:
`DR-INV-axiom-basis` and `DR-CON-scheduler-ranking` move in this commit.

DONE-CRITERION: `python -m pytest tests/test_calculus_axioms_rung7.py -q`
— 0 failed.


**DONE 2026-08-24.**

```
tests/test_calculus_axioms_rung7.py .......   7 passed in 0.15s
  -k a6   2 passed
  -k a9   3 passed
```

Rung 7 PROVES none of the eleven axioms and preserves two. A6 is preserved by
calling Rung 3b's own predicate rather than re-deriving the graph condition, so
R64's "no edge, no warrant, no label" gains its fourth clause — "and no mark" —
from one definition rather than two. A9 is preserved across three new readouts,
and the trial record is the interesting one: it DOES write, because a
diagnostic nobody can attack is a diagnostic nobody can correct, and what makes
that still A9 is that it writes an artifact and a measure and never a status,
an edge or a warrant. The check pins the single writer by name.

The absence D-1 chose is asserted too: no crisis-problem spawn trigger exists,
and `SpawnTrigger` gained no member for one.

Map moved in this commit: `DR-INV-axiom-basis` (A6/A9 at Rung 7, and why A7
makes "carrying" computed), `DR-CON-scheduler-ranking` (the wound-count term
and its position after the seed term, with a check on the ORDER).

## Step 13 — boundary gate `[COMMIT]` GATE

Full gate, `docs_verify` FULL, both wheel smokes (C-PUBLIC: prove no
re-pin is owed), blast radius, diff budget against the 700 ceiling.

DONE-CRITERION: `python -m pytest tests/ -q -n 4` (0 real failures),
`python tools/docs_verify.py` (no NEW failures against the base's three),
`python scripts/wheel_smoke.py`, `python -u
scripts/wheel_operational_smoke.py`, and both tool JSONs — all pasted.


**DONE 2026-08-24.**

```
python -m pytest tests/ -q -n 4
4080 passed, 6 skipped in 1085.92s (0:18:05)

python scripts/wheel_smoke.py
wheel smoke passed: isolated V6-only contents, clean imports, exact entry
points, module parity, MCP registration, and exact MCP schemas

python -u scripts/wheel_operational_smoke.py
exit code 0

python tools/docs_verify.py
docs_verify [full]: 64 documents, 1048 checks, 4 workers
docs_verify: 3 failed        # all three CON-run-identity.md, shallow clone

python tools/diff_budget.py 053c129ac --ceiling 700 --paths src
{"areas": {"src": 1027}, "ceiling": 700, "verdict": "EXCEEDED"}   # Amendment 1

python tools/blast_radius.py ...
"frozen_surface_verdict": "CONTACT"   # surface 3 only, every row a reader
                                      # the grant names; qualification digest
                                      # and wheel pins both EMPTY
```

**0 real failures, and 104 more tests than the base carried.** The baseline
was 3974 passed / 2 failed (both the `-n 4` MCP-thread flakes); this run is
4080 passed / 0 failed, so the two flakes passed here as well.

**The three docs failures are the operator's own stated baseline** — "3
pre-existing shallow-clone failures (0 on a full clone)". Confirmed rather
than assumed: `git rev-parse --is-shallow-repository` is `true`, the clone
holds 85 commits, and `git cat-file -t 1637e808` returns "Not a valid object
name" for the revision the check pins.

**Three OTHER doc checks failed first, and all three were mine.** They are
recorded in their own commit: the `fail()` count pin (220 → 223), the parsed
rank tuple (the wound term), and the `consultability` proxy that grepped for a
STRING where the claim was about CALLERS. Each moved with the code rather than
being worked around.

**C-PUBLIC holds.** Both smokes green and `wheel_smoke_pins` empty in the
census — the public surface did not move, so no re-pin was owed and none was
made.

## Step 14 — the cycle soak, before any live launch (S11; G6)

`python -u scripts/cycle_soak.py --case epoch3`. The launch config is the
epoch3 shape and is already in the case table, so no case is added.

DONE-CRITERION: exit 0, with the soak's own summary pasted.


**DONE 2026-08-25.**

```
python -u scripts/cycle_soak.py --case epoch3
[soak] built root: manifest 814ff04708bd2a24…
[soak] qualified in 2.7s
[soak] driving 8 cycles …
  [PASS] A1-typed-terminal            state='completed' stop_reason='budget_exhausted'
  [PASS] A2-no-operational-failure    stop_reason='budget_exhausted'
  [PASS] A3-verify-root-clean         0 violation(s)
  [PASS] A4-cycles-reached            reached cycle 8 of 8 requested
  [PART] D1-seat-contract   zero repair attempts: the deterministic stub
                            always returns a schema-valid response
  [PASS] D2-route-lease     [PASS] D3-budget-auth    [PASS] D4-reservation-bound
[soak] exit 0 (clean)
```

**Exit 0, and no case was added** — the launch config is the epoch3 shape,
which the soak's case table already carries, so the CLAUDE.md law was satisfied
by running the instrument rather than by extending it.

`cascade-integrity` reported **0 violations** on a root the soak drove through
eight cycles. That is the check's first exposure to a real driven record rather
than a fixture, and it is silent there, which is what additive means.

The `[PART]` on D1 is the instrument's own recorded limit, not a failure: the
deterministic stub never returns an invalid response, so the repair path cannot
be reached offline. Read
`experiments/2026-08-23-change-cycle-soak-instrument/RESULTS.md` before treating
a green soak as full coverage — three of its four death assertions are asserted
rather than demonstrated.

## Step 15 — the live gate (S11; G6)

ONLY after step 14 is green: ask the operator for the `OLLAMA_API_KEY`
env file, launch detached, stage a fall on the resulting live root, and
judge on TYPED OUTCOMES ONLY — the mark appears with its grade, the
cascade fires, `verify_root` is clean.

DONE-CRITERION: the run id, the typed mark with its grade, the cascade's
own output, and `verify_root`'s verdict — all pasted.


**DONE 2026-08-25. L-6 PASS**, on a live root, judged on typed outcomes only.

```
subject (model-written): {"analogy":null,"claim":"The nocturnal urban heat
                          island is primarily an energy-bal…
seed problem:            question-4dd62735b90864a75220e09b302500bc
sigma:                   contains(description, "why")   -- from the seed's
                                                           own first word
carried: 1 problem, and it is the seed          frame renders before the fall: yes

PROP 9.6, LIVE
  subject_status_after_wound   Status.REFUTED
  assertion_status_after_wound Status.ACCEPTED
  standing_unchanged           true
  marks_after_wound            {}
  frame_still_renders          true

THE FALL
  assertion_status   Status.REFUTED
  fallen_frames      [{grade: "fall", label: "refuted"}]
  marks              {question-4dd62735…: "premise-refuted"}
  open_orphans       {question-4dd62735…: "premise-refuted"}
  batch_offers       [{grade: "premise-refuted", size: 1}]
  standing_after     []

verify_root          0 violations
```

**The mark appears with its grade, the cascade fires, verify_root is clean** —
the three things the instruction names, on a record a live model wrote.

**Two failures on the way, both recorded rather than tidied away.**

1. **The launch config was not the one the soak covered.** The first ladder
   built a profile through `deepreason setup`, and glm-5.2 qualified at the
   SHALLOW tier under it — `QUALIFICATION_TIER_SHALLOW`, full V6 reasoning
   refused. CLAUDE.md's law is that the soak must be green on the LAUNCH
   config, and `scripts/cycle_soak.py`'s epoch3 case is
   `experiments/2026-08-22-live-reach-rich-run/run-config.yaml` driven through
   that tranche's `build_manifest`. The ladder now uses exactly those two.

2. **Staging on the STOPPED root was refused by the harness, and the refusal
   was right.** `verify_root` reported
   `TERMINAL_POST_HORIZON_EVENT_UNAUTHORIZED`. Proven to be the staging's doing
   rather than the run's: replaying the log truncated to the last pre-staging
   sequence (525) gives **0 violations**, so the run as it stopped was clean
   and the post-horizon writes were mine. Rung 4's fixture note had said so in
   words — "writing to a terminalized root would be exercising a state no
   operator can reach" — and the record enforced it.

   **My own gate script hid it.** It compared violation counts BEFORE and AFTER
   staging, and "before" already carried the violation from a previous partial
   attempt, so a delta test returned PASS on a dirty record. The driver now
   tests the ABSOLUTE count, which is what L-6's "verify_root clean" says.
   `refused-post-horizon-l6-outcomes.json` keeps that refused output.

The fall is now staged INSIDE the run, on the open harness, which is the shape
Rung 4's `_framed_manifest_root` already used and for the same reason. The
staging runs in a `finally`: this config dies `operational_failure` at cycle 2
on every attempt, and a staging that only ran on the clean path would have
skipped the gate on exactly the runs that reached the frontier anyway. The run
recorded 69 accepted and 6 refuted artifacts before it died, which is a real
record whatever ended it.

## Step 16 — RESULTS.md and the §13 residue (G7)

The tranche's RESULTS.md segment, carrying §13's residue VERBATIM and the
honest ledger of what remains unproven.

DONE-CRITERION: the residue quoted verbatim, checked character for
character against `docs/COMPUTABLE_CALCULUS.md`.

**DONE 2026-08-25.** `RESULTS.md` carries the dated segment and the residue.

§13's residue, checked character for character against
`docs/COMPUTABLE_CALCULUS.md`:

> And a wounded background with no arriving rival frames forever — refuted,
> indicted in every pack, unreplaced, and never declared irreplaceable (N3).

Extracted programmatically from the source rather than retyped (the source is
line-wrapped across blank lines, so a hand copy is where a "verbatim" quote
silently stops being one).

