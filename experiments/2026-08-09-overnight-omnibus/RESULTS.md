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

(pending — runs in flight as of this segment's drafting)

## Block D — qualification battery re-sampling

(pending — runs in flight as of this segment's drafting)

## Block E — end-of-night overlay sweep

(pending — runs last, after A-D)

## Omnibus decision table

(filled in at the end: every number, its block, what it decides)

## Failure ledger

(ledgered S6-style; budget 15)

## Residue

(what remains unproven, honestly stated)
