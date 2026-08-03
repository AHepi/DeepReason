# Results — attached-evidence integrity tranche

Dated, honest-ledger segments. Accepted does not mean true.

## 2026-08-03 — the defect, fixed and verified

What the record showed: stress-triplet triage `run-0a3e93d6` completed and
then failed its own replay validation — one `attached-evidence` violation,
rc=5, both instruments agreeing on the verdict and both wrong about the
cause. The finding said a bound source "lacks one reliability-dependent
candidate evidence artifact"; the artifact existed at seq 4 of the run's own
log. The candidate set was keyed on `mention -> source_record`, which is how
ANY artifact cites evidence, and the run's conjecture at seq 43 had cited its
evidence — the system working as designed, counted as a second candidate.

What was fixed (verdict R, reader-only, frozen surface 3 with operator
approval): the candidate comprehension in `verify_root` now also requires
`import` provenance — the writer's stamp, unreachable from rule-driven
creation. Uniqueness and dependence demands unchanged; finding name and
detail string byte-identical. One isolated variable in the reproduction:
add the citation, the verdict flipped; remove it, clean — and the artifact
named as missing present in both roots.

What the record now shows: `verify_root(run-0a3e93d6)` → zero violations;
`verify_post_commit_report` → valid. The stored `REPLAY_VALIDATION.json`
and run-result summary stay `valid: false` forever — frozen evidence of what
the defective reader believed on 2026-08-02 — so the sweep row does not move
(ERRATA E8: FIX.md predicted that flip in the wrong instrument). Before and
after sweeps: 42 rows, byte-identical. Full gate 3290 passed, 0 failed.
docs_verify 756 checks, 0 failed.

The map moved with the code: `SEAM-periphery-x-verification.md` now exists —
the writer-reader agreement this defect broke had no document, and both
sides' documents declared the pair a non-interaction because every import
between them is function-local (ERRATA E2). Traps entries in
`SUB-verification` and `SEAM-harness-x-verification` carry the lesson: a
demand for "exactly one artifact shaped like X" must key on a discriminator
the model cannot emit.

Documentation repair under the operator's grant, ledgered in the new
`docs/ERRATA.md` (E1–E8): the stale pre-v6 census (42/25 → 45/28, went false
the day the triplet roots were committed), and four map checks that pinned
claims to the gitignored turmite/jolt live roots — verifiable only on the
machine that ran them, repointed at the committed orbit root.

Residue: the sweep-visible verdict for run-0a3e93d6 is permanently
`valid=False` on its stored summary — cite the instrument with the number.
The 11-vs-14 census delta stays parked (handover item 2). The systematic
audit of other fail() predicates for model-reachable shapes was not done.
PARKED.md lists the rest.
