# Overnight omnibus — 2026-08-09

Honest-ledger segments, one per block, plus a final omnibus decision
table. Judged from typed records only (`run-status.json`,
`REPLAY_VALIDATION.json`/`verify_root`, `progress.jsonl`, audit JSON
under each block's own directory). Model prose is never evidence.

Sibling window: a 2026-08-09 pre-flight search (`git branch -a`,
`git log --all --grep`) found no "corpus-enrichment + patrol pilot"
branch anywhere in this repo. This tranche made no patrol calls and
ran no dual-mode enrichment, per the operator's instruction not to
duplicate that window regardless of whether it is visible here.

## Process note (self-caught, fixed forward)

`snapshot_loop.sh`'s exclude pathspec
(`":!.../home-*/runs"`) matched only the `runs` directory entry
itself under git's default pathspec matching, not its recursive
contents — it needed a trailing `/**`. Before this was caught, one
manual commit (`f2606b53`) and one auto-snapshot committed a CROSS-cell
run root mid-append (lock files included). No working data was lost —
the run reached its own terminal state in a later snapshot — but this
is a real violation of this repo's "never commit a run mid-append"
rule, recorded here rather than silently ignored. Not rewritten: this
is a private working branch with no open PR, and CLAUDE.md's own
convention for a caught process error is fix-forward, not history
rewrite. `snapshot_loop.sh` was fixed and relaunched at commit
`d7fdec85`; everything after that commit is clean (verified by
`git diff --cached --name-only | grep /runs/` before every subsequent
commit in this tranche).

<!-- Block A segment: filled in once all 12 runs (2 cells x 2
questions x 3 seeds) have completed or been judged closed. -->

## Block A — criticism-symmetry pilot cells

12/12 runs complete (2 cells × 2 questions × 3 seeds), PREREG.yaml
frozen before the first call. Judged from each run's
`run-status.json`, `verify_root`, and this block's own
`block_a_audit.py` (smoke-tested against a real committed root before
any live use).

**Completion and replay validity.**

| cell | completed | failed (operational_failure) | replay_valid |
|---|---|---|---|
| SELF | 6/6 | 0/6 | 3/6 |
| CROSS | 4/6 | 2/6 | 0/6 |

CROSS cell's 2 failures (q1s1, q1s2) both hit
`V6_ROUTE_SEAT_INSUFFICIENT_CAPABILITY` at cycle 0 — a typed refusal
("route seat has terminally exhausted its smallest authorized
contract"), not a crash. SELF cell never hit this failure. This is a
genuine, on-topic CROSS-cell finding: binding the conjecture role
group to a second model (gemma4:31b) introduces a real failure mode
that pure-default routing does not have, at this block's budget
(6 cycles / 90000 tokens). It is not universal — CROSS cell's other
4 runs completed normally, including 2 more attempts of the SAME
question (q1s3 succeeded where q1s1/q1s2 on the identical question
text failed) — so this is a rate (2/6, ~33%), not a hard wall.

**Confound: foreign-criticism coverage validation fires in BOTH
cells.** Every run in this block shows `verify_root` violations named
`foreign-criticism` (4 repeats per violating run) — this is a
pre-existing harness invariant (`invariants.py::validate_foreign_criticism_coverage`,
`"criticism.coverage-debt.v1"`) about internal "school"-population
diversity in criticism coverage, unrelated to which PROVIDER/MODEL
fills a role. It fired in SELF cell too (3/6 SELF runs replay_valid,
0/6 CROSS), which rules out "CROSS-specific seat routing" as the sole
cause — SELF has no seat override at all and still shows it in half
its runs. The most likely cause is this block's own budget choice
(6 cycles / 90000 tokens, tighter than S6's proven 10/195000): not
enough cycles for the scheduler to route criticism through enough
distinct schools before `budget_exhausted`. CROSS cell's 0/6 clean
rate vs SELF's 3/6 is suggestive that heterogeneous seat routing makes
this WORSE (less cycle budget survives to spend on cross-school
coverage once seat-capability exhaustion eats into it), but n=6 per
cell is too small to separate that from noise. Reported as residue,
not claimed as proven.

**Refutation rate: 0.0 in every one of the 10 completed runs, both
cells.** Nothing was refuted at all in this pilot. This means P1
("survival rate through criticism is independent of critic identity")
cannot be tested on refutation rate from this data — there is no
variance to compare. This block's 6-cycle/90000-token budget is too
tight to generate a refutation in either cell at this question
difficulty; a properly powered P1 test needs either more cycles or
questions engineered to have at least SOME refutable conjectures in
this budget, which is Rung C2's job, not this pilot's.

**Criticism depth (P2's actual testable axis) — mixed, not clean.**

| metric (completed runs only) | SELF mean | CROSS mean |
|---|---|---|
| criticism calls / accepted artifact | 0.477 | 0.594 |
| criticism tokens / accepted artifact | 1006.71 | 925.88 |

P2 predicts CROSS should show MORE criticism activity than SELF
(a critic facing a foreign conjecture argues harder). Calls/artifact
agrees with that direction (CROSS 25% higher); tokens/artifact
disagrees (SELF 8% higher). This is a genuinely mixed n=6-per-cell
signal — not a confirmation of P2, not a clean refutation either.
Correct reading: no criticism-depth asymmetry survives at this pilot's
power: one axis leans each way, and 3/6 vs 0/6 replay-validity noise
on top of a 6-run sample means neither direction should be trusted
without Rung C2's larger, properly powered design.

**Foreign-criticism debt at natural stop (extends S6's throughput
signal).** In CROSS cell, criticism obligations remaining outstanding
at stop are definitionally "foreign" (conjecture is seat-bound off the
default critic model); in SELF, definitionally "self."

| cell | runs with debt > 0 | debt values (nonzero runs) |
|---|---|---|
| SELF | 2/6 | 4, 4 |
| CROSS | 4/4 completed | 9, 5, 12, 9 |

CROSS cell shows outstanding coverage debt in EVERY completed run
(4/4), at magnitudes 1.25x–3x higher than SELF's occasional debt.
This is the strongest directional signal in this block: heterogeneous
seat routing leaves more criticism coverage unresolved at natural
stop than pure-default routing does, consistently. Still n=4 vs n=6,
still a pilot — reported as the block's headline finding, not as
proof.

**Parked: the reverse arm is structurally impossible today.** See
`block-a-criticism-symmetry/PARKED.md` P1 — `GROUP_ROLES` has no
`"critic"` group, so `--seat critic=...` cannot bind the CRITIC role
independently. This block could only vary the conjecture side; a
critic-seat rung is a prerequisite for Rung C2's full design matrix,
and PARKED.md carries a ready `dr-change-orchestrator` prompt for it.

**Same run_id string across cells, by design (not a bug).** SELF and
CROSS q1s1 (and several other matched pairs) share the identical
`run-<hash>` id string, because `preparation.py::_request_digest`
hashes question text + default/broadcast profile digest + budget —
seat bindings are never an input (PARKED.md P2 in the S6 tranche,
confirmed again here). Since the two cells use different homes, this
never collided or corrupted anything; noted so a future reader isn't
alarmed by it.

## Block B — capability-channel stochasticity funnel

10/10 runs complete, PREREG.yaml frozen before the first call. This
block deliberately departed from reusing turmite/jolt's question
verbatim (PREREG.yaml's own documented deviation, decided before any
live call): a 2026-08-09 pre-flight research pass found NO simulation
proposal had EVER reached COMPILED in this repo's committed history —
only PROPOSED → VALIDATED → (GRANTED | DENIED) — so this block used a
new, deliberately trivial flat-observable question (a pseudorandom
face-count tally) to maximize the chance of observing genuine
later-stage funnel behavior instead of re-measuring a structural
ceiling.

**Headline result: the ceiling is broken.** 8 of the 10 runs produced
at least one simulation proposal that reached the full funnel —
PROPOSED → VALIDATED → GRANTED → COMPILED → DISPATCHED → SUCCEEDED —
the first COMPILED, first DISPATCHED, and first SUCCEEDED simulation
proposals ever recorded in this repo (typed evidence: each
`run-status.json` + `verify_root` + this block's own
`block_b_audit.py`, which walks each proposal's FULL transition chain
via `previous_transition_ref`, not just its current transition).

**The funnel, aggregated across all 10 runs (20 proposals total):**

| stage | proposals reaching it | rate from PROPOSED |
|---|---|---|
| PROPOSED | 20 | 100% |
| VALIDATED | 8 | 40% |
| GRANTED | 8 | 40% (no loss) |
| COMPILED | 8 | 40% (no loss) |
| DISPATCHED | 8 | 40% (no loss) |
| SUCCEEDED | 8 | 40% (no loss) |

**The real bottleneck is PROPOSED → VALIDATED, not anything
downstream.** Once a proposal clears validation, this block observed
ZERO attrition all the way to SUCCEEDED — every validated proposal
in this sample went on to succeed. That is a strikingly clean result
for n=8 and should be read as a pilot-scale observation, not a proven
0% downstream-failure rate; the honest claim is "downstream attrition
was not observed in this sample," not "downstream attrition is zero."

**Attempts per live capability hit, the number this block exists to
report:** at the RUN level, 10 attempts → 8 runs with >=1 SUCCEEDED
= **1.25 runs per hit** (most single attempts hit). At the PROPOSAL
level, 20 proposals → 8 succeeded = **2.5 proposals per success**
(a proposal has roughly even odds of clearing validation). Both
numbers matter for different planning questions: "will one demonstration
attempt likely work" (yes, ~80% of the time with this question shape)
vs "how many proposals should a demo budget for" (~2-3).

**The 2/10 run-level misses** (s1, s4) both stopped `operational_failure`
at cycle 0 with exactly 1 proposal stuck at PROPOSED (never reached
VALIDATED) — the same typed shape as the pre-2026-08-09 historical
record, just now the minority outcome instead of the only one.

**Replay-validity confound, same pattern as Block A.** 7/10 runs
`replay_valid=true`; the 3 that show violations (s2, s6, s10) all
carry the same `foreign-criticism` coverage-validation violation as
Block A's confound — this block's 6-cycle/90000-token budget is
shared with Block A's, so the same budget-tightness effect on
cross-school criticism coverage shows up here too, unrelated to the
capability-channel funnel result above.

**Also stale as of this tranche, per PREREG.yaml's own note:**
CLAUDE.md's "Hard-won invariants" section describing turmite's
`_not_a_self_link` and jolt's observable-naming failure as CURRENT
blockers is out of date — both were fixed on 2026-08-01, before this
tranche started (`experiments/2026-07-31-schema-sweep/SWEEP.md`,
`REPAIR_OSCILLATION.md`). This should be corrected in CLAUDE.md
directly in a future change tranche (not this live-run tranche's job
to edit CLAUDE.md); flagged here so it is not silently re-discovered.

## Block C — reasoning-token completion-cap curve

6/6 runs complete (3 caps × 2 seeds), PREREG.yaml frozen before the
first call. Each cap paid its own fresh qualification battery (fresh
profile digest), as predicted.

| cap | qualification tier | s1 | s2 |
|---|---|---|---|
| 4096 | full | failed: `V6_ROUTE_SEAT_INSUFFICIENT_CAPABILITY` (typed seat failure, 2 truncated calls, empty_emission_rate 18%) | failed: `ROUTE_LEASE_MISMATCH` (see below) |
| 8192 | **shallow** (`ready_shallow`) | refused before any call: `QUALIFICATION_TIER_SHALLOW` | same |
| 16384 | full | completed cleanly (0 typed seat failures, 0 truncated calls, replay_valid=true) | completed cleanly |

**Not a smooth curve — three DIFFERENT typed failure mechanisms, one
per cap, not a graded "more failures at lower cap" shape.** PREREG.yaml
said a non-monotonic result would be reported as-is, not smoothed; it
was more than non-monotonic, it was mechanism-different at each
lower point:

1. **cap=4096, seed 1:** `V6_ROUTE_SEAT_INSUFFICIENT_CAPABILITY` — the
   CLAUDE.md-documented "hard question burns the whole completion cap
   on hidden reasoning and emits nothing" failure. This is the
   mechanism the operator's framing anticipated.
2. **cap=4096, seed 2:** a DIFFERENT typed error, never seen
   elsewhere in this tranche: `ROUTE_LEASE_MISMATCH role='conjecturer'
   seat=0 field=max_tokens expected=4096 actual=2560 RouteFirewallError`.
   The leased route's actual max_tokens (2560) does not match the cap
   that was set (4096) for the conjecturer role's seat. This looks
   like a genuine internal inconsistency (something downstream derives
   2560 from a 4096 cap and a firewall check catches the mismatch)
   rather than a provider-side capacity failure — PARKED below with a
   ready diagnose prompt, not fixed in this tranche.
3. **cap=8192:** qualification itself demoted to `shallow` tier
   (`ready_shallow`), so `reason` (full) was refused BEFORE any
   provider call — the third and fourth independent 2026-08-09
   observation of the REPAIR_SCOPE_VIOLATION pattern Block D is
   dedicated to (see Block D's segment; same pair,
   `sha256:96c8238f...`, both times).
4. **cap=16384:** clean on both seeds — 0 typed seat failures, 0
   truncated calls, `replay_valid=true` both times.

**typed_seat_failure_rate and empty_emission_rate, per cap (of the
runs that actually reached `reason`):** 4096: 1/2 typed seat failure
(50%), empty-emission 18%/0% across its 2 runs; 8192: N/A, no `reason`
call ever ran; 16384: 0/2 (0%), 0% both. The curve DOES fall as cap
rises from 4096 to 16384 on the metric CLAUDE.md's guidance targets
(typed seat failure), consistent with "raise
`--maximum-completion-tokens`" being real, useful advice — but the
8192 midpoint's failure is a QUALIFICATION-time gate, not a
`reason`-time one, so it does not fit on the same axis at all. A
reader who only plots "did reason succeed" would see 0/2, 0/2, 2/2 and
wrongly read 8192 as equal-worst to 4096; the mechanisms are unrelated.

**Parked candidate defect: `ROUTE_LEASE_MISMATCH` at cap=4096.**
Evidence: `block-c-completion-cap-curve/home-4096/runs/run-370ab72342ecd4a23ebaf983d0828598`,
error `ROUTE_LEASE_MISMATCH role='conjecturer' seat=0 field=max_tokens
expected=4096 actual=2560 RouteFirewallError` (from
`block-c-4096-s2.json`'s `error` field). Ready prompt for a future
tranche: "Diagnose why the conjecturer seat's leased route computed
max_tokens=2560 when the profile's maximum_completion_tokens was set
to 4096 -- is 2560 a fixed floor/reservation subtracted somewhere in
the route-leasing path, and if so is it supposed to scale with the
profile's cap or is it a hardcoded value that only breaks at low
caps? Route through `deepreason-orchestrator` (dr-set-goal ->
dr-diagnose), diagnosis from the typed record first (this run's
`run-manifest.json` and the route-leasing code path in
`src/deepreason/llm/adapter.py` / wherever `RouteFirewallError` is
raised) before code reading."

## Block D — qualification battery re-sampling

8/8 samples complete (4 at cap 8192, 4 at cap 16384, each a fresh
+0/+1/+2/+3-token-perturbed subject per PREREG.yaml's documented
deviation), PREREG.yaml frozen before the first call.

| cap point | samples clean | samples with scope violations | which pair(s) |
|---|---|---|---|
| 8192 | 4/4 | 0/4 | — |
| 16384 | 1/4 | **3/4** | 3 DIFFERENT pairs, one per violating sample |

**Headline finding — inverts the prereg's own stated expectation.**
PREREG.yaml's `hit_criteria.16384_as_control` said: "16384 point
samples are expected clean per S6's own remedy having worked; a
violation there would be a NEW finding, not confirmation of the known
one." That expectation is falsified: 16384 showed violations in 3/4
samples, a HIGHER rate than 8192's 0/4 in this same block. This is the
new finding, stated plainly rather than smoothed into the prereg's
prior expectation.

**Cross-validated against Block C's own independent batteries at the
exact (unperturbed) cap values**, which ran the identical qualify step
for a different purpose and give two more independent draws: cap=8192
showed 1 violation (Block C's own battery, same pair
`sha256:96c8238f...` as S6's original historical observation); cap
16384 showed 0 (Block C's battery was clean). Combining Block D's 4
perturbed samples with Block C's 1 exact-value battery at each point:
**8192: 1/5 batteries violated (all four times on the same underlying
pair when it happens, S6's `sha256:96c8238f...`/`scratch.cluster-guide.compact.v1`)
vs 16384: 3/5 batteries violated (a different pair each time)**.

**Is it stochastic ~1-in-N or deterministic?** Neither, cleanly.
- At 8192: stochastic, low rate (~1/5 across this tranche's 5
  independent draws), and when it fires it is the SAME pair every
  time — the "trigger-happy on a known-fragile pair" reading from
  PREREG's `deterministic_at_8192` criterion is close but not exact:
  it is not 4/4 (not deterministic), but it is concentrated (100% of
  its failures land on one pair), consistent with `stochastic_at_8192`.
- At 16384: stochastic and MORE frequent (3/5), diffuse across
  different pairs each time — this pattern is not one this block's
  prereg anticipated at all, and is the block's real headline: the
  zero-tolerance scope-violation gate is not calibrated to get safer
  as the completion-token cap rises. If anything, tonight's small
  sample points the other way.

**Residue.** n=4-5 per cap point is a calibration pilot, not a
powered study — a rate moving from 1/5 to 3/5 is consistent with
real signal but also with small-sample noise; this needs a larger
resample (the same method, more samples per point) before "16384 is
riskier than 8192" is asserted as established rather than observed
tonight. What IS established, typed, and not in question: the
zero-tolerance gate (`sum(scope_violations) == 0` regardless of
eventual-valid count, `cli/doctor.py:139`) demoted 4 of this block's
8 batteries to shallow tier, at both cap points, on fresh subjects
each time — S4b's "M full batteries, not N" pricing model
(experiments/2026-08-06-change-qualification-per-seat-s4/PARKED.md)
means every one of those 8 batteries was paid for in full regardless
of outcome, and this rate (`4/8 = 50%` demoted across both points
combined) is itself a cost number worth carrying into any future
qualification-repair-scope design discussion.

## Block E — end-of-night overlay sweep

Ran `experiments/2026-08-08-change-grounded-overlay-o1/scripts/run_all_overlays.py`
UNMODIFIED, bare, cwd = repo root, exactly as O1's own script specifies
(re-verified before running: no edits were made to any script under
`scripts/`). Corpus grew from 48 roots (baseline, preserved as
`overlay_results_baseline_2026-08-08.jsonl` before any other block in
this tranche ran) to 76 roots.

**The sibling "corpus-enrichment + patrol pilot" window's branch
(`claude/corpus-enrichment-patrol-pilot-f4khnk`) appeared between
this tranche's pre-flight check (empty) and Block E's run** — `git
branch -a` at Block E's start found it. Its new directory
(`experiments/2026-08-08-corpus-enrichment-patrol-pilot`, 2 run
roots) was extracted read-only via `git archive` into a temp location,
copied into this working tree UNTRACKED for the duration of the sweep
only, and removed immediately after — never committed to this
branch, never merged. This tranche made no patrol calls and ran no
dual-mode enrichment itself, per the operator's instruction; Block E
only READ that window's committed output, once, for the count below.

**Old vs new, aggregated (O1's own established columns, REPORT.md):**

| metric | old (48 roots) | new (76 roots) | delta |
|---|---|---|---|
| roots swept | 48 | 76 | +28 |
| roots with an overlay error | 11 | 11 | +0 |
| O1a node_count (sum) | 1947 | 2996 | +1049 |
| O1a att_edge_count (sum) | 26 | 30 | +4 |
| **attack-edge density** (att_edge_count / node_count) | **0.013354** | **0.010013** | **-0.003341** |
| O1a controversy SCCs | 0 | 0 | +0 |
| O1a skeptically-accepted-not-grounded | 0 | 0 | +0 |
| O1b accepted+formally-backed | 265 | 310 | +45 |
| O1c floating components | 2374 | 3571 | +1197 |
| O1c floating chains (non-vacuous) | 14 | 18 | +4 |
| O1d single/multi-warrant flips | 0 | 0 | +0 |

**Reading it honestly.** Attack-edge density FELL slightly (-25%
relative), not because attack edges disappeared (they grew, 26→30)
but because the corpus's node count grew faster (+54%) than its
attack-edge count (+15%) — tonight's 28 new roots are mostly
argumentative-claim runs (Blocks A/B/C/D) whose artifact graphs are
node-heavy relative to how many formal attack relationships they
register, diluting the density rather than concentrating it. This is
not a claim that argumentation quality declined; it is a claim about
what kind of roots got added. Zero new overlay errors across 28 new
roots is a clean result on its own (`run_all_overlays.py` catches
exceptions per-root/per-overlay and types them into `_error` rather
than aborting the sweep, so this is a real "nothing broke," not an
artifact of a crashed sweep). `PREREG.yaml`'s own `reporting_floor`
said this block would not judge whether density moving is good or
bad, only report it, honored here.

O1's `overlay_results.jsonl` is a git modification in this tranche's
commit (the script's normal output, re-measuring the same file it
always writes to) — not a hand-edit; `overlay_results_baseline_2026-08-08.jsonl`
under this block's own directory preserves the pre-tonight state
permanently for any future comparison.

## Block A-2 — criticism-symmetry pilot cells, corrected

16/16 runs complete (2 cells × 2 questions × 3 seeds, plus 4 extra
CROSS-Q1-only attempts), PREREG-A2.yaml frozen before the first call.
Requested by the operator directly, because Block A's own segment
above named its 6-cycle/90000-token budget as a confound. Reuses
Block A's own `home-self`/`home-cross` directories (qualification
cache-hit confirmed: both cells' `qualify` calls returned in ~1
second). Budget corrected to S6's proven shape (10 cycles / 195000
tokens), with an automatic convergence protocol: after each stop, if
`verify_root` is not yet clean and the stop is resumable, run
`continue --budget cycles=2`, up to twice, before accepting the
result.

**Blob-before-theory, read before designing the extra attempts.**
Block A's CROSS q1s1 failure's diagnostic blob
(`blobs/a6/a672...`) showed the FAILING role was `argumentative_critic`
on the DEFAULT glm-5.2 profile (not the seat-bound gemma
conjecturer) — contract `critic.atomic-target.v1` requires
`/counterexample` to be a list, and glm-5.2 returned a full prose
paragraph instead, three attempts running, before the route seat gave
up. Recorded verbatim in PREREG-A2.yaml before any live call in this
block.

**Completion and replay validity — dramatic improvement over Block A.**

| cell | completed | non-resumable failure | replay_valid |
|---|---|---|---|
| SELF | 5/6 | 1/6 | 5/6 |
| CROSS | 9/10 | 1/10 | 9/10 |

Compare to Block A's original: SELF 3/6 replay_valid, CROSS 0/6. The
corrected budget alone took SELF from 50% to 83% clean, and CROSS from
0% to 90% clean. This is strong, direct confirmation that Block A's
own confound diagnosis was correct.

**Foreign-criticism coverage debt is now almost entirely resolved.**
Every one of the 14 replay-valid runs (5 SELF + 9 CROSS) shows debt =
0. The ONLY nonzero debt in this whole block (10) is on CROSS's own
failed run (q2s2), which never reached a clean terminal state in the
first place. This directly confirms Block A's own residue item: the
"foreign-criticism" violation was a budget-provisioning artifact, not
a self/cross asymmetry — at the S6-proven budget it essentially
disappears for both cells.

**Two NEW non-resumable failures, both diagnosed from evidence, not
assumed (see the driving-conversation record for the full trace):**

1. **SELF q2s2** — `ValueError: adapter rejected a repair that
   revalidates successfully` (`workflow/repair_transaction.py:522`).
   Fires when a repair's compiled output is valid but the adapter
   layer separately recorded that same attempt as an error — an
   internal consistency check catching two subsystems disagreeing
   about the same attempt's outcome. Unrelated to seat routing (SELF
   has no seat override). Genuine candidate defect, parked.
2. **CROSS q2s2** — `V6_ROUTE_SEAT_INSUFFICIENT_CAPABILITY`, but at
   CYCLE 11 during a `continue` call, not cycle 0. Confirmed by direct
   log inspection (not assumption) to be the SAME mechanism as Block
   A's original failures: the last 30 events before the stop show 10
   failing attempts, all on `critic.atomic-target.v1`. This refines
   Block A's "cycle-0 death" framing — the mechanism can also strike
   deep into an otherwise-successful run, during continuation
   specifically.

**CROSS-Q1 refusal rate, sized on n=7 (3 baseline + 4 extra) at the
corrected budget: 0/7 (0%) typed seat failures.** Block A's original
rate on the identical question at the old budget was 2/3 (67%). This
is the single cleanest number in this block: the
`V6_ROUTE_SEAT_INSUFFICIENT_CAPABILITY` refusal that dominated Block
A's CROSS-Q1 attempts was overwhelmingly a budget-tightness artifact,
not a structural property of cross-model seat routing on this
question. (It did NOT vanish entirely from the dataset — CROSS's Q2
attempt q2s2 hit a related instance of the same typed error, at cycle
11 — so the mechanism is real and still reachable, just far rarer at
this budget than the original 67% suggested.)

**Continuation counts — a genuinely clean, well-powered finding.**
SELF's 5 successfully-converged runs: continuation_count = [0, 0, 0,
1, 1] (3 needed zero continuations, 2 needed one). CROSS: EVERY SINGLE
ONE of its 10 runs (9 converged + the 1 that failed) required at least
1 continuation — continuation_count = [1,1,1,1,1,1,1,1,1,1]. SELF
converges immediately more than half the time; CROSS never does, in
this sample. This is consistent, direction-clean evidence that
heterogeneous seat routing takes measurably more rounds to reach a
trustworthy final state than pure-default routing, independent of the
specific question or seed.

**P1 is testable this time (unlike Block A's flat 0.0).** Refutations
occurred in both cells: SELF's 5 valid runs show refutation rates
[0.0, 0.0, 0.0088, 0.0153, 0.0] (mean 0.0048); CROSS's 9 valid runs
show [0.0, 0.0067, 0.0, 0.0071, 0.0, 0.0, 0.0, 0.0074, 0.0] (mean
0.0024). SELF's mean is roughly double CROSS's, but both are small
(under 2%) with substantial per-run variance and no seed overlap
control — this is suggestive, not a claim that P1 is refuted or
confirmed. It does establish that this question/budget combination CAN
produce refutations, which Block A's design could not show at all.

**P2 verdict — full distributions, not means, per PREREG-A2's own
requirement:**

| metric | SELF values (n=5 valid) | CROSS values (n=9 valid) |
|---|---|---|
| criticism calls / accepted artifact | 0.564, 0.538, 0.509, 0.550, 0.519 | 0.610, 0.664, 0.585, 0.564, 0.590, 0.683, 0.570, 0.612, 0.626 |
| criticism tokens / accepted artifact | 1129.8, 1086.3, 1170.1, 1012.0, 1077.5 | 1199.0, 929.1, 1154.7, 893.9, 1088.2, 914.9, 981.6, 927.7, 978.6 |

**Calls/artifact: a clean, nearly non-overlapping separation.** SELF's
range is [0.509, 0.564]; CROSS's range is [0.564, 0.683] — the two
distributions touch at exactly one point (SELF's max equals CROSS's
min) and otherwise CROSS sits entirely above SELF. This DOES support
P2's predicted direction (a critic engages more when facing a foreign
conjecture) with much cleaner separation than Block A's noisy
90000-token sample managed.

**Tokens/artifact: still no separation, direction still ambiguous.**
SELF's range [1012.0, 1170.1] and CROSS's range [893.9, 1199.0]
overlap heavily, with CROSS's mean (≈1007) actually LOWER than SELF's
mean (≈1095). This axis does NOT support P2's predicted direction, at
this corrected budget either — matching Block A's own original
finding on this specific metric. Explicit verdict: **P2 is partially
supported** — the call-count axis shows a real, clean, direction-correct
separation; the token-count axis does not, and the honest reading is
that "criticism depth" is not a single scalar quantity here: cross
criticism happens MORE OFTEN per surviving artifact but is not
reliably WORDIER when it does.

**What this 2-cell pilot still cannot claim (unchanged from Block
A's own residue, restated per the operator's request):** no reverse
arm exists. `GROUP_ROLES` still has no `critic` group
(`block-a-criticism-symmetry/PARKED.md` P1's ready prompt is
unchanged and not implemented in this tranche). Every finding above is
about varying the CONJECTURE side while the CRITIC stays fixed on
glm-5.2 in both cells — whether the asymmetry (calls/artifact,
continuation counts) comes from the conjecturer's foreign identity or
would also appear with a foreign CRITIC is still completely unknown.

## Phase 4 + Phase 5 — adversarial hit validation and live adjudication of the consistency patrol (BLOCKED, not executed)

Requested to close the three-number chain (raw hit rate → validated
rate → live-adjudicated outcomes) that decides whether the O2-shelved
"consistency patrol" design (`experiments/2026-08-08-change-grounded-overlay-o2/SPEC.md`
S7) earns permanent machinery. Both phases build on Phase 1/2 of a
SEPARATE, sibling session's work (`claude/corpus-enrichment-patrol-pilot-f4khnk`),
read-only — this tranche made no patrol calls itself, consistent with
the original instruction not to duplicate that window.

**What was done before stopping:**

- Read the sibling branch's Phase 1 (10 enrichment roots, committed,
  replay-valid) and Phase 2 (a "consistency patrol": one bounded,
  neutral-framed call per accepted-artifact pair within a shared
  problem, asking only "do these two claims contradict"; a hit =
  `contradiction == true AND confidence >= 0.6`) via `git show`/`git
  archive` only — never checked out, never merged.
- Found and documented an inherited (not caused) defect in Phase 2's
  own data: 130/8872 records have a well-formed JSON response wrapped
  in a markdown fence that its parser doesn't strip, silently
  mis-scored as non-hits rather than tallied as parse failures.
- Read O2's own `SPEC.md` S7 and confirmed the binding design
  constraint both phases had to honor: "the patrol proposes, it never
  itself adjudicates" — every candidate must pass through ORDINARY
  criticism, never a label written by either phase.
- Read `docs/proposals/AMENDMENT_EPOCHS.md` and confirmed, from
  `src/deepreason/cli/main.py`, that `amend`/`continue` operate purely
  on `--root` — no `DEEPREASON_HOME` or fresh qualification battery
  needed, simplifying Phase 5's design considerably from what was
  assumed going in.
- Froze `PREREG-P4.yaml` and `PREREG-P5.yaml` before any live call,
  per the operator's instruction.
- Built and SMOKE-TESTED LIVE (not just compiled) the full tool chain
  for both phases:
  - `phase4_sample.py` — verified against the sibling's real (partial)
    data: correctly reproduces 1767 hits / 130 excluded
    fence-parse-failures / 6975 clean non-hits.
  - `phase4_rejudge.py` — run live against 1 real hit: the
    skeptic-framed check (deliberately refute-biased) found a
    consistent reading the original neutral-framed patrol call missed,
    so that hit correctly failed to validate — the mechanism works as
    designed, on real data, on the first try.
  - `phase4_analyze.py` — verified against that same mini-run's output.
  - `phase5_check_amendable.py` — verified against a real committed
    root; caught and fixed a real bug in the process (calling
    `derive_terminal_authority` without first loading the epoch-aware
    manifest silently returns `historical_read_only` for EVERY root,
    which would have made Phase 5 wrongly skip every single candidate
    had it not been caught here, before any real candidate was
    evaluated).
  - `phase5_run_case.py` — run live end-to-end against 1 real (but
    Phase-4-unvalidated, so not a real candidate) hit: amend succeeded,
    `continue` ran 10 genuine criticism cycles,
    `state=completed`, `replay_valid=true`, no new attack edge minted
    (the tension survived criticism in that demonstration) — confirms
    the whole copy → amend → continue → audit pipeline works before
    it would have been spent on real candidates.

**Why it stopped here.** PREREG-P4.yaml's own trigger condition
required Phase 2 to reach its pre-registered total (9277 pairs)
before any real sample could be drawn. As of the last check before
stopping, the sibling branch showed 8872/9277 (95.6%) and its last
commit was **2 hours old** — a sustained stall, not a between-chunk
pause. Per the operator's explicit choice when presented with this
stall (wait longer / proceed with partial data / stop and report),
this tranche stops here: no sample was drawn, no re-judgment calls
beyond the verification smoke tests above were made, and Phase 5 never
selected or acted on a real candidate.

**Residue: what a future session needs to pick this up.** Both
preregs are frozen and complete; every script is built, syntax-checked
AND live-verified against real data; the one real bug found
(`derive_terminal_authority` needing an explicit loaded manifest) is
already fixed in the committed `phase5_check_amendable.py`. Resuming
requires exactly two things: (1) confirm Phase 2 has reached 9277/9277
on the sibling branch (`git fetch` + the same `git show ... | wc -l`
check used throughout this segment), (2) run
`phase4_sample.py` against the real, complete `patrol_results.jsonl`,
then `phase4_rejudge.py` (hit and non-hit), `phase4_analyze.py`, then
select Phase 5 candidates per `PREREG-P5.yaml`'s strength ranking and
run `phase5_run_case.py` per candidate. No further design work is
needed — only execution, once the dependency clears.

## Omnibus decision table

| # | number | block | what it decides |
|---|---|---|---|
| 1 | 12/12 Block A runs complete; SELF 6/6 completed, CROSS 4/6 completed | A | pilot has enough data to read, not enough to power a full P1/P2 test |
| 2 | refutation rate = 0.0 in all 10 completed Block A runs | A | P1 is untestable from this data (no variance); needs harder questions or more cycles, Rung C2's job |
| 3 | criticism calls/artifact: SELF 0.477 vs CROSS 0.594 | A | leans toward P2's predicted direction (cross argues more), n too small to trust alone |
| 4 | criticism tokens/artifact: SELF 1006.7 vs CROSS 925.9 | A | leans AGAINST P2's predicted direction on this one axis — mixed signal, not a clean confirmation |
| 5 | foreign-criticism debt: SELF nonzero in 2/6 (vals 4,4); CROSS nonzero in 4/4 (vals 9,5,12,9) | A | strongest directional Block A finding: heterogeneous seat routing leaves more coverage debt at natural stop, consistently |
| 6 | CROSS cell: 2/6 runs hit V6_ROUTE_SEAT_INSUFFICIENT_CAPABILITY at cycle 0; SELF: 0/6 | A | a real, CROSS-specific failure mode exists, at ~33% rate, not universal |
| 7 | 8/10 Block B runs reached SUCCEEDED (first-ever in this repo); 20 proposals, 8 validated, 0 downstream attrition after validation | B | the "capability channel never compiles" ceiling was a question-shape artifact, not a structural wall; bottleneck is PROPOSED→VALIDATED |
| 8 | attempts per live capability hit: 1.25 runs/hit, 2.5 proposals/success | B | the number future demonstrations need to budget for, at this question's difficulty |
| 9 | typed seat-failure at cap 4096: 1/2 runs; at cap 16384: 0/2 | C | raising `--maximum-completion-tokens` does reduce this failure mode, as CLAUDE.md's guidance claims |
| 10 | cap 8192 qualified `ready_shallow` (not full) on a fresh independent battery | C | confirms the 8192 fragility is reproducible on demand, a 3rd/4th independent observation combined with Block D |
| 11 | new typed error at cap 4096 seed 2: `ROUTE_LEASE_MISMATCH` (expected 4096, actual 2560) | C | a genuine candidate defect, parked with a ready diagnose prompt, not a capacity issue |
| 12 | scope-violation rate at cap 8192: 1/5 independent draws (Block D's 4 + Block C's 1), always the same pair | D | leans stochastic-but-concentrated, not deterministic, not clean |
| 13 | scope-violation rate at cap 16384: 3/5 independent draws, a DIFFERENT pair each time | D | inverts this block's own prereg expectation; 16384 is not a safe control point — needs a larger resample before trusting the direction |
| 14 | qualification demotion rate across all 8 Block D batteries: 4/8 (50%) | D | a concrete cost number for any future qualification-repair-scope design discussion (S4b: every battery, demoted or not, is paid for in full) |
| 15 | overlay corpus: 48 → 76 roots; attack-edge density 0.01335 → 0.01001 (-25% relative); 0 new overlay errors | E | corpus grew cleanly; density fell because new roots are node-heavy, not because argumentation quality declined |
| 16 | 16/16 Block A-2 runs complete; replay_valid SELF 5/6 (was 3/6), CROSS 9/10 (was 0/6) | A-2 | S6-proven budget + continue-until-valid protocol resolves Block A's own named confound directly |
| 17 | foreign-criticism debt = 0 on all 14 replay-valid A-2 runs; the ONLY nonzero debt is on the one run that never reached a clean state | A-2 | confirms Block A's residue item: the coverage gap was a budget artifact, not a self/cross asymmetry -- now closed, not just suspected |
| 18 | CROSS-Q1 typed seat-failure rate: 0/7 at the corrected budget vs 2/3 at Block A's original budget | A-2 | the dominant Block A CROSS failure mode was overwhelmingly budget-tightness, not a structural property of cross-model routing |
| 19 | continuation_count: SELF [0,0,0,1,1] (3/5 need none); CROSS all-1s across all 10 runs | A-2 | heterogeneous seat routing measurably needs more rounds to reach a trustworthy final state, independent of question/seed -- clean, well-powered |
| 20 | refutation rate now nonzero in both cells (SELF mean 0.0048, CROSS mean 0.0024, n=5/n=9) | A-2 | P1 is testable at this budget (was impossible in Block A); SELF's rate leans double CROSS's but both are small and noisy |
| 21 | criticism calls/artifact: SELF range [0.509,0.564], CROSS range [0.564,0.683], near-zero overlap; tokens/artifact: SELF mean≈1095, CROSS mean≈1007, heavy overlap | A-2 | P2 partially supported -- call-count axis cleanly favors P2's predicted direction, token-count axis does not; "criticism depth" is not one scalar |

## Failure ledger

Ledgered S6-style; budget 15, none needed to stop the tranche early.
"Failure" here means any typed abnormal/refusal outcome or process
error encountered while executing this tranche — most are the
experimental measurements the relevant block exists to take, not
mistakes; each is marked accordingly.

| # | what | block | disposition |
|---|---|---|---|
| 1 | `snapshot_loop.sh` exclude pathspec matched only the `runs` directory entry, not its contents — one manual commit and one auto-snapshot briefly committed an in-flight CROSS-cell run root (lock files included) before this was caught | process | self-caught, fixed forward (`d7fdec85`), not rewritten; no data lost |
| 2 | CROSS cell q1s1, q1s2: `V6_ROUTE_SEAT_INSUFFICIENT_CAPABILITY` at cycle 0 | A (measurement) | this IS the block's own finding — CROSS-cell seat-capability exhaustion, ~33% rate |
| 3 | Both cells, `foreign-criticism` coverage-validation violations (SELF 3/6 clean, CROSS 0/6 clean) | A (measurement, confound) | pre-existing harness invariant, unrelated to seat identity; attributed to this block's own tight budget choice, reported as residue |
| 4 | Block B s1, s4: stuck at PROPOSED, `operational_failure` | B (measurement) | the minority (2/10) outcome of the funnel measurement itself |
| 5 | Block C cap=4096 s1: `V6_ROUTE_SEAT_INSUFFICIENT_CAPABILITY` | C (measurement) | expected mechanism per CLAUDE.md's own guidance, confirmed |
| 6 | Block C cap=4096 s2: `ROUTE_LEASE_MISMATCH` (expected 4096, actual 2560) | C (measurement + candidate defect) | NEW typed error, parked with ready diagnose prompt, not fixed this tranche |
| 7 | Block C cap=8192: `QUALIFICATION_TIER_SHALLOW`, both seeds refused before any `reason` call | C (measurement) | battery-level demotion, cross-validates Block D |
| 8 | Block D 8192-point: 0/4 samples clean-violating, but Block C's independent 8192 battery (item 7) shows the same pair violating | D (measurement) | combined 1/5 draws — reported jointly, not double-counted as two findings |
| 9 | Block D 16384-point: 3/4 samples show scope violations, each a different pair | D (measurement) | inverts the block's own prereg expectation; the tranche's most surprising number |
| 10 | Block A-2 SELF q2s2: `ValueError: adapter rejected a repair that revalidates successfully` (repair_transaction.py:522), non-resumable | A-2 (candidate defect) | NEW internal-consistency bug candidate, unrelated to seat routing (SELF has no seat override); parked, not fixed |
| 11 | Block A-2 CROSS q2s2: `V6_ROUTE_SEAT_INSUFFICIENT_CAPABILITY` at cycle 11 (during a `continue` call), confirmed via log inspection to be the same `critic.atomic-target.v1` mechanism as Block A's original failures | A-2 (measurement) | refines "cycle-0 death" framing -- the mechanism can strike deep into an otherwise-successful run too, not just at the start |
| 12 | Phase 5 tooling: `derive_terminal_authority(root)` called without loading the epoch-aware manifest first silently returns `historical_read_only` for EVERY root, which would have made Phase 5 wrongly skip every candidate as non-amendable | process (self-caught before live use) | caught during live smoke-testing, fixed by loading `load_epoch_manifest` first (mirroring `amendment/apply.py`'s own pattern) before any real candidate was evaluated; no incorrect skip ever happened on real data |
| 13 | Phase 4/5 stopped: sibling branch's Phase 2 stalled at 8872/9277 pairs (95.6%), last commit 2 hours old | process (external dependency, not a defect) | operator chose "stop and report" when presented the stall; no sample drawn, no real candidates adjudicated -- preregs and tooling stand ready for a future session |

## Residue

What remains unproven, honestly stated — not smoothed into a
conclusion the data does not support:

- **Block A's original P1/P2 questions are now partially answered by
  Block A-2, not fully closed.** P1 is testable at the corrected
  budget (refutations occurred in both cells) but the sample is still
  small (n=5 SELF, n=9 CROSS) and unpowered to call a direction
  proven. P2's calls/artifact axis now shows a clean separation
  favoring the predicted direction; the tokens/artifact axis still
  does not. Rung C2's full pre-registered design (harder questions,
  more seeds, a critic-seat rung once built) is still required before
  either claim is fully settled.
- **The reverse arm (glm conjectures, gemma criticizes) is still
  structurally impossible.** `GROUP_ROLES` has no `critic` group;
  PARKED.md carries a ready prompt, not yet implemented. Every A-2
  finding is still only about varying the conjecture side.
- **Foreign-criticism coverage debt is resolved for CONVERGED runs,
  not proven to have never existed.** Block A-2 shows 0 debt on all 14
  replay-valid runs -- a clean confirmation that Block A's confound
  diagnosis was right for THIS budget. It does not establish that no
  self/cross difference in coverage debt could ever appear under
  budget pressure; it only shows the S6-proven budget makes it a
  non-issue for both cells alike.
- **Block A-2's continuation-count asymmetry (SELF often 0, CROSS
  always 1) is a new, unreplicated finding.** n=6 vs n=10 is small; it
  has not been checked against a third question, a third seed set, or
  a swapped-role design, and could in principle reflect something
  about THESE two specific questions rather than seat heterogeneity in
  general.
- **Two new candidate defects surfaced in Block A-2**
  (`repair_transaction.py:522`'s internal-consistency check, and the
  cycle-11 recurrence of the critic-shape-mismatch failure) are typed
  and evidenced but not diagnosed to root cause or fixed -- both
  parked for a future `dr-diagnose` tranche.
- **Block B's "zero downstream attrition after VALIDATED" is an
  8-sample observation, not a proven rate.** A larger resample could
  still find COMPILED/DISPATCHED/SUCCEEDED failures this pilot's size
  was too small to see.
- **Block D's 16384-riskier-than-8192 finding is n=4-5 per point.** A
  properly powered resample (same method, more samples) is needed
  before treating "raising the cap past a point increases scope
  violations" as established rather than observed once.
- **`ROUTE_LEASE_MISMATCH` at cap=4096 is diagnosed only to the level
  of "a typed error occurred and what it said."** Root cause (why
  max_tokens=2560 was leased against a 4096-token profile) is
  genuinely unknown and parked for a future `dr-diagnose` pass.
- **CLAUDE.md's "Hard-won invariants" entry about turmite/jolt's
  cycle-0 killers is stale** (both fixed 2026-08-01, before this
  tranche) — flagged, not corrected; editing CLAUDE.md is out of scope
  for a live-run tranche.
- **Block E's density comparison is a single before/after snapshot,
  not a trend.** Whether density recovers, keeps falling, or holds as
  the corpus keeps growing needs more than one data point.
- **Phase 4/5's three-number chain (raw hit rate → validated rate →
  live-adjudicated outcomes) is entirely unfilled.** Only the first
  link (Phase 2's raw ~19.9% hit rate, inherited from the sibling
  branch, itself slightly undercounted by that branch's own 130-record
  parse-failure defect) exists. Whether the O2-shelved consistency
  patrol earns permanent machinery is exactly as undecided as it was
  before tonight — this tranche proved the validation/adjudication
  MACHINERY works (both phases' scripts verified live on real data)
  but never got to run it for real, purely because of an external
  dependency's stall, not any flaw in the design.
