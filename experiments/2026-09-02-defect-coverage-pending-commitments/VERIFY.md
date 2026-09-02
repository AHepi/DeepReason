# Verification

Verdict: **PASS (offline). No live run attempted — GOAL.md does not demand
live proof and the executor window places live reasoning runs out of scope.**

## Criterion commands + output (GOAL.md, run verbatim)

    $ python -m pytest tests/test_coverage_pending_commitments.py -q
    17 passed in 0.90s

    $ python -m pytest tests/test_coverage_pending_commitments.py -q -k fails_still_lowers
    2 passed, 15 deselected in 0.25s

    $ python -m pytest tests/test_coverage_pending_commitments.py -q -k status_unchanged
    1 passed, 16 deselected in 3.27s

    $ python -m pytest tests/test_formalism_optional_rank.py -q
    12 passed in 0.44s          # was 11; EXTENDED by one parametrized road,
                                # not weakened -- no assertion was removed

    $ python -m pytest tests/ -q -n 4
    4689 passed, 6 skipped in 1533.29s (0:25:33)

Criterion 1 was RED before the fix (`9 failed, 8 passed`) and is GREEN now.
Criteria 2 and 3 were GREEN before and remain GREEN — they are the controls that
separate this repair from "put everyone on the frontier".

### Mutation proofs (rule 3 of the durable-test discipline)

Each was broken, watched go red, and restored:

| mutation | result |
|---|---|
| put OVERRUN back in the denominator (the defect) | `9 failed, 8 passed` — exactly the original RED set |
| also drop FAIL from the denominator (over-eager repair) | `7 failed, 10 passed` — incl. `test_fails_still_lowers_coverage` and `test_pending_commitments_do_not_inflate_a_score_either` |
| the new parametrized architecture road in `test_formalism_optional_rank.py` | `[undecidable]` FAILED, `[screened-out]` passed — the two roads are genuinely different and only the new one catches this defect |
| `is_import_admission` → `return False` (undo the import-role exclusion) | `test_the_frontier_does_not_move_...` FAILED — the rewritten assertion can still fail |
| restored | `28 passed`, then `6 passed`, then the full gate |

## Criterion 6 — the offline re-scoring, reported as a measurement

`rescore.py` opens each root `read_only=True` and computes BOTH formulas from
raw verdicts in one run, then asserts the shipped `pareto_scores` agrees with
the new one. Full transcripts in `measurements/`. **No committed root was
modified**; the P-S1 and P-A1 roots were read from throwaway git worktrees.

    root                        survivors  frontier BEFORE  frontier AFTER   installed-code check
    P-S1 9e48a36b1dec91ee            98      58 (58/58 minted)  98 (all)      shipped == NEW
    P-A1 4565139800f5ca02            11       7 ( 7/7  minted)  11 (all)      shipped == NEW
    P-R1 poietics-program            58      40 (40/40 minted)  58 (all)      shipped == NEW

Every seed-answering artifact moves onto the frontier on all three roots:
P-S1 40/40, P-A1 4/4, P-R1 18/18. Before the fix, **zero** of them were on it.

## Historical roots re-checked (ladder step 2)

The fix changes a READER, so both halves of step 2 were run: the target
behaviour must move, and everything else must not.

| root | `verify_root` | frontier under the fix |
|---|---|---|
| P-S1 `9e48a36b1dec91ee` | **0 violations** | 58 → 98 (the defect, repaired) |
| P-A1 `4565139800f5ca02` | **0 violations** | 7 → 11 (the defect, repaired) |
| P-R1 poietics | **0 violations** | 40 → 58 (the defect, repaired) |
| known-good: grounded-extension `2026-08-12` | **0 violations**, 304 artifacts / 12 991 events | **233 → 233, composition IDENTICAL** (successor 99, connection 87, seed 47) |

The known-good root is the control that matters: it is the root the 2026-08-30
sibling tranche was measured on, its survivors carry no OVERRUN commitments, and
the fix is a **complete no-op** there. The change moves exactly the roots that
carry undecided commitments and nothing else.

## Map and instrument gates

    docs_verify (full)     6 failed — ALL pre-existing baselines (docs/AUDIT_BASELINES.md
                           records "5 OR 6 failed" on this container's shallow clone):
                             SEAM-llm-x-rules.md:54       unparseable check, parked P3
                             CON-run-identity.md:211/213/215  shallow-clone git history
                             INV-frozen-surfaces.md:181   claim rotted, parked P-D3
                             CON-run-identity.md:298      TIMEOUT at the 300 s ceiling,
                                                          an expensive check on files this
                                                          tranche does not touch
                           The run BEFORE this fix's map edits reported 8: the same 6 plus
                           SUB-ontology.md:124 and SUB-scheduler.md:408, both of which are
                           `test_import_role_survivors.py`. Both re-run GREEN now (6 passed;
                           8 passed). Delta closed; zero regressions attributable here.
    docs_verify --links    0 dangling reference(s), 74 documents
    docs_verify --audit    1 finding — the documented baseline (SEAM-llm-x-rules.md:54)
    diff_budget            {"verdict": "WITHIN", "total_insertions": 40, "ceiling": 150}
                           scheduler.py 29, programs.py 11
    full gate              4689 passed, 6 skipped, 0 failed

The two pre-authorized known-not-mine baselines the executor window named — the
bc-dependent map check and
`test_the_shipped_qualification_subject_digest_does_not_move` — **did not fire
at all**. Recorded as not-observed rather than as passed-over.

## Live attempt

**None.** Out of scope by the executor window, and unnecessary: GOAL.md's
criterion is decidable offline, and the three roots supply the live evidence
already. Per `dr-drive-harness`, the offline regression is the proof of
correctness in any case.

## Residue (honest)

1. **On these three roots the frontier becomes the ENTIRE survivor set.** This
   is a real result and it should not be read as "the fix put everyone on the
   frontier". The mutation control proves a genuine FAIL still dominates a
   passing sibling, and the known-good root's frontier does not move at all.
   What it means is narrower and worth stating plainly: on these three roots
   `hv` and `reach` have ZERO entries and **no commitment failed anywhere**, so
   once the spurious penalty is removed there is no measured variance left for
   any axis to discriminate on. The axis was not narrowing attention correctly
   before — it was narrowing it BACKWARDS. Whether a future run's frontier is
   usefully narrow now depends on `hv`, measurable on v6 only since
   `5f34e4d00`, and **no run has yet been observed with a measured `hv` and this
   coverage rule together.** That measurement is not made here.
2. **Only one of the five OVERRUN families is exercised by any committed root.**
   All 204 OVERRUN verdicts across the three roots are
   `observation requires registered evidence`. The four `lean_*` programs, the
   `reasoning-envelope-wf` char-limit overrun, the six `promotion_*` blob
   programs and `dataset_oracle` are covered by the same single rule and by the
   unit tests, but **no committed root demonstrates them**. The claim that a
   formally-backed conjecture was penalised for being formal is derived from
   code (`programs.py:310-322`, `:446-457`), not from a live root.
3. **`frontier_delta` feeds `StopMetrics`,** so a longer frontier can move the
   `converged` stop decision (`stop.py:163-188`; the `stuck` path is reached only
   behind the escape ladder at `:203-209`). Disclosed in FIX.md, pinned as
   status-neutral by `test_status_unchanged_by_the_coverage_axis` — but **not
   measured in a live setting**, because no run was launched.
4. Parked, with ready-to-send prompts in `PARKED.md`: P1 a `predicate:` that
   RAISES is recorded FAIL (a different shape — it WAS evaluated); P2 `hv`/`reach`
   still emitting 0.0 (owned by the 2026-08-30 park L3); P3 the problem-population
   skew (a spawn-rule question this tranche does not touch); P4 the undeclared
   `pytest-xdist`/`jsonschema` deps, hit a third time.

## Errata

**`docs/ERRATA.md` E70**, landed in the fix commit `29a50acf7` rather than this
one, because the map rule requires a document correction to move in the same
commit as the code that falsifies it. It records three committed map claims that
defined the axis as passes over EVALUABLE commitments — `SUB-scheduler.md`,
`CON-conjecture-kinds.md`, and `SUB-periphery.md`'s flatly-false "exactly the set
of prose conjectures" — plus the `programs.py` module docstring's "the `overrun`
verdict is reserved for" deterministic bounds, contradicted by all three of that
file's own OVERRUN literals.
