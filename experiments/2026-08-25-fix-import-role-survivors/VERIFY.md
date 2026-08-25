# Verification

## 1. Criterion command + output (GOAL.md, verbatim)

    $ python -m pytest tests/test_import_role_survivors.py -q
    ......                                                                   [100%]
    6 passed in 48.61s

    $ deepreason results experiments/2026-08-25-poietics-program/run
    ## Artifacts
      accepted / refuted / suspended: 419 / 104 / 0
      survivors (positions still standing at the end): 58
      frontier (the open edge of the inquiry): 40 artifacts, problem question-aa835741bebc4b4cb189f4b08bef649a

    $ python -m pytest tests/ -q -n 4
    4168 passed, 6 skipped in 852.76s (0:14:12)
    # baseline at 43f408506, measured in this session: 4162 passed, 6 skipped,
    # 0 failed. 4168 = 4162 + the 6 new tests. No test was weakened.

    $ python tools/docs_verify.py
    docs_verify: 3 failed
    # CON-run-identity.md:200, :202, :204 — all three are git-history checks
    # that cannot pass in a shallow clone. IDENTICAL to the baseline measured
    # at 43f408506 in this session, in FULL mode, before any change.
    $ python tools/docs_verify.py --audit
    docs_verify --audit: 0 finding(s)
    $ python tools/docs_verify.py --links
    docs_verify --links: 0 dangling reference(s), 64 document(s)

## 2. Mutation proof (required by the tranche instruction)

The authority in `src/deepreason/ontology/state.py::is_import_admission` was
replaced in place by `return False` — re-admitting every import-role record —
and restored from a scratch copy. Both outputs, verbatim:

    === MUTATED: is_import_admission always False (imports re-admitted) ===
    >       assert len(report["survivors"]) == 58
    E       AssertionError: assert 82 == 58
    FAILED tests/test_import_role_survivors.py::test_the_results_surface_reports_the_conjectures_and_not_the_dossier
    FAILED tests/test_import_role_survivors.py::test_the_writer_publishes_a_survivor_set_the_invariant_already_holds_over
    2 failed, 5 passed in 50.79s

    === RESTORED ===
    .......                                                                  [100%]
    7 passed in 51.46s

Stated honestly, because it bounds what the proof shows: the RED came from
`tests/test_import_role_survivors.py`, which carries the hard numbers.
`tests/test_results_command.py::test_results_summary_reports_artifact_survivor_
and_frontier_counts` stayed GREEN under the mutation and would — it compares the
surface against the same predicate, so it is a contract test, not a mutation
detector. The guarantee is pinned by the numbers, not by that comparison.

## 3. Reproduction inverted

`experiments/2026-08-25-fix-import-role-survivors/repro.py`, same script, same
committed root, before and after:

    BEFORE  The surface counts 24 of them, reporting 82 where the record supports 58.
    AFTER   The surface counts 0 of the 24 present, reporting 58 where the record supports 58.

## 4. Historical roots — targeted single-root replays, NOT a sweep

The root sweep is retired as an instrument (operator ruling 2026-08-22) and no
tranche may require it. What is run instead is what CLAUDE.md prescribes for a
reader change: targeted replays. Every git-tracked root publishing a survivor
set was read through `results_summary` and its reported count compared with its
stored one — 37 roots, one read each, no `verify_root` replay:

    roots publishing a survivor set: 37
      unchanged: 25   moved: 12   unreadable/absent: 0

       20 -> 18   2 import   2026-08-02-stress-triplet/home-orbit/.../run-6472629d
       62 -> 58   4 import   2026-08-02-stress-triplet/home-triage/.../run-0a3e93d6
      245 -> 233 12 import   2026-08-12-live-grounded-extension-expansion/run
       82 -> 58  24 import   2026-08-25-poietics-program/run
       45 -> 42   3 import   live_research_2026-07-29/narrow/.../run-7d8723fb
       24 -> 18   6 import   live_research_2026-07-29/openchallenge/.../completed-epoch2-run-9e9812fe
       10 ->  6   4 import   live_research_2026-07-29/openchallenge/.../completed-epoch3-run-9e9812fe
       20 -> 15   5 import   live_research_2026-07-29/openchallenge/.../run-27b80f26
       10 ->  6   4 import   live_research_2026-07-29/openchallenge/.../run-9e9812fe
       25 -> 22   3 import   live_research_2026-07-29/referee/.../run-d17935a4
       58 -> 48  10 import   live_research_2026-07-29/selfstudy/.../completed-epoch3-run-9175f0ec
       22 -> 12  10 import   live_research_2026-07-29/selfstudy/.../run-9175f0ec

**Every delta equals that root's own IMPORT count exactly. No root moved for
any other reason, and the 25 roots holding no import-role survivor are
byte-identical.** That is the property the fix had to have and it is measured,
not argued.

The last row is worth naming: **`run-9175f0ec` is the run that motivated the
invariant in the first place**, and it was itself over-reporting 22 survivors
where 12 are supported. The rule was installed for that run and the same run's
own results surface never got it.

## 5. The record is untouched

    $ git diff --stat 43f408506 -- experiments/2026-08-25-poietics-program/run
    (empty)

The stored survivor set is still 82 ids in every root above. The fix changed
what the reader COUNTS, never what the record HOLDS. `verify_root` re-derived
on the P-R1 root at HEAD: **valid, 0 violations**, unchanged.

Committed roots' REPORTED numbers do move — permitted under the 2026-08-14
operator law ("old runs do not need to be valid or returnable by the way"),
and stated here rather than discovered in review, as P4's prompt required.

## Verdict: **PASS**

Offline throughout. No live run was needed, attempted, or is owed: the defect
was captured in committed roots, the reproduction is a record replay, and the
proof is mutation-proven regression over the same bytes.

## Residue (honest)

- **The invariant is now enforced by one predicate, not by agreement between
  three.** What is NOT proven is that no fourth survivor derivation exists
  outside `src/`. The check that would decay is pinned
  (`test_one_authority_names_the_rule_and_every_survivor_surface_calls_it`
  asserts `ProvenanceRole.IMPORT` appears in neither consumer's file), but it
  names two files by hand, not the whole tree.
- **Two further derivations are known and deliberately unfixed** —
  `report.py::eval_report` and `loop.py::run_problem`, PARKED P1. Neither
  number moves on the P-R1 root today (0 of the 24 IMPORT survivors carries an
  `hv` or `reach` entry), so both are excluded by absence rather than by rule.
- **The `accepted` count is untouched and still includes import-role records**
  (435 accepted artifacts on the P-R1 root, 36 of them IMPORT). The invariant
  names survivors and this tranche took it literally. Whether "accepted" should
  mean the same thing is an authority question, not a reporting one, and was
  ruled out of scope in GOAL.md before any code was read.
- **The diff-budget gate returned EXCEEDED** against FIX.md's own ceiling and
  was disclosed and re-priced rather than outrun (FIX.md Amendment 1). `src/`
  came to 72 insertions across exactly the three change sites specified before
  implementation; the overrun is the regression test and six map documents.
- **A fifth and sixth map document turned out to pin the moved literal**
  (`SEAM-scheduler-x-rules`, `SEAM-capabilities-x-rules`), found by
  `docs_verify` in FULL mode. `--fast` held a stale PASS for one of them and a
  spurious FAIL for another — a live instance of the warning
  `dr-drive-harness` §4 already carries.
- **A discrepancy this tranche found and did not chase:** the P-R1 root's
  stored finding-family breakdown (completion 120, operational 22) and a fresh
  re-derivation (121/23) disagree. Re-derivation is identical at `43f408506`
  and at HEAD, so it predates this work entirely. PARKED P3.

## Errata

**errata: none.** Checked explicitly, document by document. CLAUDE.md's
invariant was stated correctly and violated by code, which is a defect and not
an erratum. `RESULTS.md` R1 and `PARKED.md` P4 of the poietics tranche quoted
the stored figures accurately and flagged the inflation themselves — this
tranche confirms them rather than correcting them.
`DR-CON-scheduler-ranking`'s socket promise was true of the ranking it governs;
what was wrong was its CHECK, which could not distinguish one site holding the
clause from another lacking it, and a weak check is not a false claim.
`DR-SEAM-capabilities-x-rules`'s sentence ("the scheduler excludes import-role
artifacts from its survivor count") was literally true and misleadingly narrow
at a seam about where import-role artifacts enter; it was tightened to name the
authority, which is a sharpening, not a correction.

## Closing line, for the operator

`deepreason results experiments/2026-08-25-poietics-program/run` now reports
**58 survivors** — the 58 conjectures — where it reported 82, and it can never
inflate again because the surface no longer decides what a survivor is: it asks
`ontology.state.is_import_admission`, the single place in the codebase that
names the rule, and a test fails if any survivor surface starts spelling the
rule out for itself.
