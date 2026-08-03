# Errata — corrections to committed documents

Started 2026-08-03 at the operator's request. One entry per discovered error
in a COMMITTED document: what the document said, what the record shows, where
it was corrected (or why it stands uncorrected). Entries are appended, never
rewritten — if a correction itself proves wrong, that is a new entry. Evidence
pointers only; no narrative.

Scope note: this ledger is for documents (handovers, map, RESULTS, specs).
Code defects have tranches; run roots are never edited at all. Findings
about the less-capable-executor infrastructure (the cross-cutting skills,
calibration blocks, and the 2026-08-03 handover program) have their own
ledger: `docs/ERRATA_EXECUTOR.md`.

---

## 2026-08-03

**E1 — handover line pointer, cosmetic.** `docs/HANDOVER_2026-08-02.md` cites
the rc=5 exit contract as `application/models.py:1258`; the stress-triplet
RESULTS.md cites `:1269`. Both point inside `run_result_exit_code` — 1258 is
the `def`, 1269 the `return 5` branch. No correction needed; recorded because
the two documents disagree and a reader diffing them should not go looking
for a third function. Evidence: `src/deepreason/application/models.py`
(`def run_result_exit_code`).

**E2 — the map declared periphery × verification a non-interaction.**
`INDEX.md`'s seam matrix had no periphery row (which INDEX itself defines as
"no measured import traffic at all"), and neither `SUB-periphery.md` nor
`SUB-verification.md` listed the other in `Seams-undocumented:`. The traffic
is real — `invariants.py` re-derives the attached-evidence triple that
`evidence/render.py` writes — but every import between the sides is
function-local, invisible to the coupling metric. Plausibly contributory to
the attached-evidence defect (tranche
`experiments/2026-08-03-fix-attached-evidence-integrity`): no document told
the reader's author what the writer guaranteed. Corrected 2026-08-03:
`SEAM-periphery-x-verification.md` created, matrix row added, both `Seams:`
lines fixed.

**E3 — the pre-v6 census check went stale-false the day it mattered.**
`SEAM-harness-x-verification.md` pinned the root census at
`len(R)==42, 25 v6 / 14 raising / 3 no-manifest` (Verified-at 9fa394d9).
Commit `3062454e` (2026-08-02) added the three stress-triplet roots, making
the true tracked census 45 / 28 / 14 / 3 — and nobody re-ran the document's
checks, so the map carried a failing check for a day while its stamp claimed
otherwise. Corrected 2026-08-03 (numbers updated, and the check now names
this incident). The general lesson is already SCHEMA.md law: a stamp advanced
without a re-run is the one dishonest state the system has.

**E4 — `INV-frozen-surfaces.md` census numeral.** Same staleness as E3 on the
prose side: "25 v6" → 28 after the triplet commit. Corrected 2026-08-03. Its
companion claim — that `verify_root_report` surfaces three of the 14 raising
roots as verdict rows rather than ERROR rows (the 11-vs-14 sweep delta) —
is NOT adjudicated here; that is the handover's open item 2, still parked in
`experiments/2026-08-03-fix-attached-evidence-integrity/PARKED.md`.

**E5 — the "45-root baseline" is not reproducible from the committed tree.**
`experiments/2026-08-02-stress-triplet/RESULTS.md` (sweep appendix) reports
"45 roots" from `tools/root_sweep.py`, and `docs/HANDOVER_2026-08-02.md`
says that baseline is "reproducible from it". On a clean checkout of the
same tree the instrument yields **42 rows**: it scans `experiments/` only,
and 42 = 39 prior + 3 triplet. The three no-manifest calibration roots under
`runs/jolt_positive_headroom_v3_1/` are outside its glob, so the appendix's
45 must have included three roots that existed only in that session's
working tree and did not survive the container rollback; they cannot now be
identified. What IS reproducible and was reproduced 2026-08-03: 11 ERROR
rows, and the three triplet rows byte-matching the appendix
(`triage valid=False epistemic_passed=True att=1 blind=0`, orbit and
workshop `valid=True epistemic_passed=False att=0 blind=1`). The per-root
claims stand; the headline count does not.

**E6 — run-0a3e93d6's recorded verdict was a reader artifact.**
`REPLAY_VALIDATION.json` in the committed triage root says `valid: false`
with one `attached-evidence` violation whose detail names a missing artifact
that exists (seq 4 of the root's own log). The root is evidence and is not
edited; the READER was wrong and was fixed in tranche
`experiments/2026-08-03-fix-attached-evidence-integrity` (verdict R;
DIAGNOSIS.md has the four-artifact proof). Post-fix, `verify_root` on the
unchanged bytes returns zero violations — the stored file remains as the
honest record of what the verifier believed on 2026-08-02, which is exactly
why callers assemble `REPLAY_VALIDATION.json` rather than the verifier
writing it: the verdict is a function of root bytes AND reader code, and
only the first is frozen.

**E7 — four map checks pinned claims to run roots that were never committed
(supersedes E5's "cannot now be identified").** The turmite and jolt ladders
gitignore their `home/` by design ("the typed outcome and the audit are
committed instead"), so `run-bc3e8797` (turmite) and `run-b4d6dfda` (jolt)
only ever existed in the session that ran them — and they are two of the
three extra rows in E5's 45-vs-42 sweep discrepancy. Four checks opened those
roots directly: `SEAM-harness-x-verification.md` (the read-only probe and the
521-file no-write pin), `SUB-adjudication.md` (the blindness trap), and
`SEAM-adjudication-x-rules.md` (whose prose called jolt "committed"). All
four could pass only on the machine that ran the ladders; every fresh clone
fails them. Corrected 2026-08-03: repointed at committed roots (orbit
`run-6472629d`, and the run ids kept in prose as history). The blindness trap
gained better evidence in the exchange — orbit is a post-detector root, so
the check now asserts the blindness finding FIRING rather than the defect era
it could no longer reproduce. Rule for the future, already implicit in
SCHEMA.md: a check may only open a root that `git ls-files` knows.

**E8 — FIX.md predicted the wrong instrument for the verdict flip.** The
attached-evidence tranche's FIX.md (committed `df0fd0fd`) predicted
run-0a3e93d6's sweep row would flip `valid` False → True. It does not, and
correctly not: the sweep reads `verify_root_report`, which also binds the
root's own STORED terminal summary — frozen evidence, written 2026-08-02 by
the then-defective reader — and refuses to call a root valid whose own
record says invalid (`run-result-verification`). The fixed reader's verdict
is visible in `verify_root` (0 violations, pinned by the regression test)
and in `verify_post_commit_report` (`valid: True`, the stored-summary-
excluded projection). Net effect: the before/after sweeps compare
byte-identical — the strongest possible frozen-surface outcome — and the
prediction error was about which instrument shows the flip, not whether the
defect is fixed. Same lesson as E4/E5: cite the instrument with the number.
