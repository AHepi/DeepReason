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

(pending — runs in flight as of this segment's drafting)

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

(pending — runs last, after A-D)

## Omnibus decision table

(filled in at the end: every number, its block, what it decides)

## Failure ledger

(ledgered S6-style; budget 15)

## Residue

(what remains unproven, honestly stated)
