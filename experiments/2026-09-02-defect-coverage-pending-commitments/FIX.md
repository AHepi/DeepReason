# Fix: a verdict of OVERRUN leaves the coverage denominator

Guarantee restored: **a commitment the harness did not decide changes no
artifact's coverage coordinate — "not measured" is neither a pass nor a fail —
while a commitment that was decided and FAILED still lowers it.**

## The design, and why it is the smallest correct one

`pareto_scores`' own docstring already states the rule this fix completes: an
OMITTED axis is the typed "not measured", and `capture.pareto.frontier` drops
an absent axis from the pairwise comparison rather than reading it as 0.0. The
2026-08-30 tranche applied that rule to the WHOLE axis (an artifact with an
empty battery gets no `coverage` key). This fix applies the identical rule one
level down, to the DENOMINATOR: a commitment with no verdict leaves the
evaluable set exactly as an unmeasured axis leaves the comparison. One notion
of unknown, not two.

**Only the reader changes.** Nothing written to the record moves: `programs.
evaluate` keeps returning OVERRUN, `workloads/text.py` keeps minting
`program:reasoning_observation_pending`, no commitment, event, digest or
manifest field is touched. Committed roots stay byte-identical and replay
exactly as before; the only thing that changes is what a ranking reader
computes from them.

**No fourth verdict.** `docs/map/SEAM-evaluation-x-ontology.md:202` carries an
executable check asserting that `programs.py`, `oracle.py`, `measures/**` and
`informal/**` never mention the token `Verdict`, and that `ontology.Verdict`'s
three values equal `programs`' three. Introducing a "pending" verdict would
break that check and split one vocabulary into two. The fix reads the verdict
that already exists.

## OVERRUN uniformly means "no verdict obtained", and every other consumer already reads it that way

| site | what it does with OVERRUN |
|---|---|
| `rules/act.py:15-17` | "a spec defect, not the candidate's fault: measure only" |
| `rules/crit.py:893-897` | refuses the criticism — "produced no verdict" |
| `rules/crit.py:1145-1147` | `QUARANTINE_TICK`, `continue` — skipped, not a violation |
| `programs.py:313-317` | "an operational overrun, never a failed proof or a warrant" |
| `scheduler/scheduler.py:236-240` | **counts it as a non-pass — the sole dissenter, and the defect** |

This holds under BOTH readings of the verdict. `programs.py:8-11` says the
verdict is "reserved" for deterministic budget bounds; all three OVERRUN
literals in that same file are instead "cannot decide yet" (see ERRATA below).
Neither reading makes OVERRUN a refutation: a check that blew its step budget
is as unmeasured as one awaiting evidence. So a single uniform rule is correct
and no per-reason discrimination is needed — which is what GOAL.md demanded
("Do not invent a second notion of 'unknown'").

## The defect is five families wide, not one

The live roots only exercise `reasoning_observation_pending`, but every
evaluable battery program that can return OVERRUN depresses coverage today:

1. `reasoning_observation_pending` — `programs.py:307` (the 129/10/65 OVERRUNs on the three roots)
2. the four `lean_*` — `programs.py:319`, registered `:446-457`. **A Lean-backed
   conjecture whose kernel check is deferred to the pinned external verifier is
   penalised for being formally backed** — R-g's *protection* inverted into a
   penalty, in the same axis, in the opposite direction from F1.
3. `reasoning-envelope-wf` — `workloads/text.py:285`, a char-limit overrun: an
   oversized artifact lowers its own coverage
4. the six `promotion_*` blob programs — `calculus/promotion.py`, OVERRUN at 15
   sites (`subject-not-in-environment`, `scope-does-not-compile`,
   `budget-exhausted`, `rigidity-unmeasured`, …)
5. `dataset_oracle` — `oracle.py`, OVERRUN at 13 sites (missing/mismatched
   sidecar, payload bound, unparseable spec)

One rule closes all five.

## Change sites (exhaustive)

- `src/deepreason/scheduler/scheduler.py:225-241` — replace the battery
  comprehension + generator-expression numerator with one pass that evaluates
  each evaluable commitment once, keeps the verdicts that are not OVERRUN, and
  emits `coverage = passes / decided` only when `decided` is non-empty. Same
  number of `programs.evaluate` calls as today.
- `src/deepreason/scheduler/scheduler.py:202-219` — docstring: state the rule
  as passes over what was DECIDED, and say why OVERRUN leaves the set.
- `src/deepreason/programs.py:8-11` — module docstring: one sentence, correcting
  "the ``overrun`` verdict is reserved for [deterministic bounds]" to what the
  file's own three OVERRUN literals do. The fix's correctness keys on this
  sentence; leaving it contradicting the code would be leaving a landmine.

Map, in the SAME commit (`docs/map/SCHEMA.md`; a separate "update docs" commit
is the commit that gets dropped):

- `docs/map/SUB-scheduler.md:55-60` — the `pareto_scores` bullet's coverage
  sentence; `:239-265` — a new Traps entry naming the three run ids
- `docs/map/CON-conjecture-kinds.md:91-92` — "`passes/evaluable-commitments`"
  is the wrong definition after this fix; `:225-241` — Traps
- `docs/map/SUB-evaluation.md` — what OVERRUN means to its consumers
- `docs/map/SUB-periphery.md:209-233` — the same-family Traps entry
- `docs/map/SEAM-evaluation-x-scheduler.md` — **NEW**. The map has no document
  and no INDEX.md matrix row for this pair, yet the whole defect lives on it:
  `pareto_scores` reaches `programs.evaluable` / `evaluate` / `PASS` through a
  FUNCTION-LOCAL import (`from deepreason import programs`), the exact traffic
  INDEX.md states its coupling metric cannot see, and the agreement is what a
  verdict MEANS to its only ranking consumer. This is the third recorded
  instance of that shape (`llm × verification`, `capabilities × channels`).
- `docs/ERRATA.md` — entries for the two committed map claims that become
  wrong, and for the `programs.py` docstring contradiction.

`check:` lines must be single-line and re-runnable, and must FAIL if the
behaviour regresses (`docs_verify.py --audit` refuses a check that cannot fail).

## Regression artifact

`tests/test_coverage_pending_commitments.py` (committed at `dr-reproduce`,
currently 9 failed / 8 passed) must invert to **17 passed**, with the 8
currently-green mutation controls still green. Plus:

- `tests/test_formalism_optional_rank.py` — EXTENDED, not weakened. Its
  `COMMITMENT_FREE_CAN_REACH_THE_FLOOR` table and the architecture test at
  `:146-161` stay exactly as they are and stay green; the annotation comment
  gains the pending case, since "a survivor carrying no evaluable commitment"
  is now one instance of the wider "a survivor with nothing DECIDED", and the
  architecture test gains an all-pending artifact alongside the commitment-free
  one so the table governs both roads.

### Amendment, at implement time: one more change site, found by `docs_verify`

`tests/test_import_role_survivors.py::test_the_frontier_does_not_move_because_every_dropped_member_was_dominated`
is the fixture the row below predicted, named now that the instrument found it.
It is reached by TWO map checks (`SUB-ontology.md:124`, `SUB-scheduler.md:408`),
which is why `docs_verify` reports it twice.

**What it asserts, and which half breaks.** Three assertions; only the second
fails.

    assert len(stored_frontier) == 40                      # PASSES -- reads the
                                                           # root's own committed
                                                           # run-result.json,
                                                           # which no fix edits
    assert list(report["frontier"]) == list(stored_frontier)   # FAILS: 58 vs 40
    assert not [a for a in imports if a in state.hv or a in state.reach]  # PASSES

The failing line compares a RE-DERIVATION under today's code against a value
STORED by the version that wrote the root. Under the operator's law of
2026-08-14 ("old runs do not need to be valid or returnable... new versions are
optimised for new functions") a stored result from an earlier version is owed no
agreement with a new reader, and this tranche's whole purpose is to publish a
different frontier. `SUB-scheduler.md` already records the same consequence for
the 2026-08-30 sibling fix ("publishes a LONGER frontier than it used to").

**But it is not merely a stale number, and saying so would be too convenient.**
Measured under the fix: of the 24 IMPORT-role members, **12 would now land on a
frontier they used to be dominated off**, because they carry evaluable
commitments that all evaluate OVERRUN — scored at the floor before, omitted now.
So the test's stated PREMISE ("all 24 are dominated points") stops being true,
and an honest update must say so rather than re-baseline the number.

**Its CLAIM survives intact, and that is what the update pins.** Measured:
the frontier over survivors and the non-import part of the frontier over
survivors ∪ imports are **identical**. Excluding import-role records still does
not reshape which real artifacts are retained — which is the thing the
2026-08-25 tranche was proving. In production nothing changes at all, because
`run_report` scores only `counts_as_survivor` members and imports are not among
them; CLAUDE.md's recorded invariant ("import-role admission records never count
as survivors") is untouched by this tranche.

**The update**: replace the stored-value comparison with the claim it was
standing in for — computed under whatever scoring is current, so it can never
again be hostage to a coverage-formula change — and keep both surviving
assertions. Strictly stronger as a guard of its own claim.

## Existing tests at risk

| test | verdict |
|---|---|
| `tests/test_formalism_optional_rank.py` (all 9) | **must keep passing.** Its pending commitment is `eval="observation"`, screened out by `evaluable` before the battery, so this fix cannot move it. Verified by running it. |
| anything asserting a numeric coverage or a frontier size | to be found by grep at implement time and judged individually: a fixture that depended on a pending commitment lowering coverage was depending on the defect. |
| `experiments/2026-08-27-audit-formalism-optional/repro_coverage_rank.py`, `experiments/2026-08-30-defect-formalism-rank-penalty/{measure_footprint,proof_equal_standing}.py` | committed evidence scripts of PAST tranches, not gate tests. Not modified; their historical output stands as the record of what those tranches measured. |

## Disclosed consequence (not a side effect to discover later)

`frontier_delta` is a `StopMetrics` input (`docs/map/SUB-scheduler.md:60-66`,
already recorded for the 2026-08-30 sibling fix), so a longer frontier can move
when a run decides it has converged. That is a SCHEDULING decision — when to
stop spending — not an acceptance, refutation or warrant, so it is inside
"allocation touches EFFICIENCY, never EVIDENCE". `tests/test_coverage_pending_
commitments.py::test_status_unchanged_by_the_coverage_axis` pins that no Status
moves. Nuance worth recording: `frontier_delta` drives the `converged` path
directly (`stop.py:163-188`) but reaches `stuck` only as one conjunct behind
the escape ladder (`stop.py:203-209`), so the converged path is the one
perturbed.

## Explicitly not changed

- **`programs.evaluable`** — the tempting neighbour. Excluding pending programs
  there would look smaller and be wrong: `evaluable` answers "can this kind of
  commitment be evaluated at all", is consumed by `rules/crit.py`,
  `measures/hv.py`, `measures/demarcation.py` and the anti-relapse guard, and a
  pending observation IS evaluable — it will decide once evidence lands. The
  defect is in the ranking arithmetic, not the classification.
- **`capture/pareto.py`** — already correct: it drops an absent axis
  symmetrically. GOAL.md admitted it only "if the denominator change is
  insufficient". It is sufficient.
- **`hv` and `reach` still emitting 0.0** for an unmeasured artifact — rowed
  STRUCTURAL-GAP by the 2026-08-27 audit and PARKED at
  `experiments/2026-08-30-defect-formalism-rank-penalty/PARKED.md` L3. Untouched.
- **Strict seed domination** — a parked tranche. The seed question keeps
  winning rank TIES and nothing here changes that.
- **The predicate-raises-scores-FAIL road** (`programs.py:558-559`): a
  `predicate:` whose body throws is recorded FAIL with an `error` detail, so a
  malformed predicate lowers coverage as if the claim were refuted. This fix,
  keyed on OVERRUN, deliberately does not touch it — that commitment WAS
  evaluated (it ran and threw), which is a different shape from "not measured",
  and deciding it is a question about predicate authoring. **PARKED** with a
  ready prompt.
- `llm/endpoints.py`, `application/text_runs.py`, `runtime/continuation.py` —
  owned by other live windows.

## Frozen-surface contact: NONE (checked, not assumed)

- No frozen path names `pareto`: `grep -rln "pareto"` over
  `run_manifest.py`, `qualification.py`, `invariants.py`, `verification/`,
  `capabilities/state.py`, `harness.py` returns nothing.
- `run_manifest.py`'s `coverage` hits are a different word — the `coverage`
  RETRIEVAL CHANNEL and `coverage_slot_every_n_packs`; its `frontier` hits are
  the `Literal["compact","standard","frontier"]` MODEL PROFILE
  (`llm/profiles.py:18`). `frontier` is a three-way collision and `coverage` a
  two-way one, which is why this was checked by reading rather than by grep count.
- `verification/report.py` reads `run-result.json` for schema and bounds only
  (`:177-240`); it never mentions `frontier`, `pareto` or `survivors`, so
  `verify_root` does not re-derive the frontier and cannot disagree with it.
- `frontier_size` has exactly one reader, `ui/terminal.py:44` — display only.

## Estimated diff

**Production code: ~28 lines across 2 files** (`scheduler/scheduler.py` ~25,
`programs.py` ~3) — well inside the 150-line budget. Tests and map documents
additional, as the workflow requires them to move in the same commit.

### Amendment, at implement time: the estimate was 28, the actual is 40

Measured with `git diff --numstat` over the two production paths: **40
insertions, 19 deletions**. The estimate is corrected here rather than left
standing, because `dr-implement-fix` gates on FIX.md's own number and a silently
exceeded estimate is the failure the gate exists to catch.

**No change site was added.** The three sites are exactly the three named above.
The whole 12-line overage is DOCSTRING PROSE: `pareto_scores`' docstring gained
the paragraph stating why OVERRUN leaves the denominator, with the three run ids
that show it, and `programs.py`'s module docstring gained the paragraph
correcting "reserved for" (both were already listed as change sites, and both
grew past what a one-line correction would have needed because the evidence is
what makes the rule re-derivable by the next reader).

GOAL.md's ceiling is **150 changed lines and it is not threatened** — 40
insertions is 27% of it. Recorded as an amendment, not a stop: a stop is owed
when the CEILING is exceeded, and it is not.

## Approval gate

GOAL.md class is `defect`; the production diff is ~28 lines; frozen-surface
contact is NONE, checked above. **Proceeds to `dr-implement-fix` without an
operator stop.**
