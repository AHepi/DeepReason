# Goal: four instruments assert a root census that expires; make the readers state a claim that cannot
Class: defect
Observed: at branch head `6ad6c42c`, four instruments fail against a
tree whose committed evidence is correct. Two tests —
`tests/test_module_fingerprints.py::test_every_committed_root_reads_as_having_no_module_fingerprints`
and `::test_the_census_of_committed_roots_is_unchanged` — fail with
`2 failed, 3336 passed, 7 skipped`; two map checks —
`docs/map/SEAM-harness-x-verification.md:253` (pins `len(R)==45`,
`28/14/3`; actual `47`, `30/14/3`) and
`docs/map/SEAM-manifest-x-schools.md:271` (pins `len(roots)==42`; actual
`44`) — fail under `python tools/docs_verify.py` (`51 documents, 815
checks, 2 failed`). All four bisect to one commit, `f6d41bff` (rung 5's
A/B arm A): the same two tests report `20 passed` at `a4c52c5b` and
`2 failed, 18 passed` at `f6d41bff`, reproduced at rung 7's tranche base
`2cc3fd50` in a clean detached worktree. Evidence:
`experiments/2026-08-04-change-rung7-authority-as-declared-policy/PARKED.md`
P1 and `DELIVERY.md`.

Success criterion (machine-decidable):

    python -m pytest tests/ -q -n 4
    -> ends "0 failed" (3338 collected today; the count may rise if the
       fix adds tests, and no existing assertion may be weakened)

    python tools/docs_verify.py
    -> "docs_verify: 0 failed"

    python tools/docs_verify.py --audit
    -> "0 finding(s)"          (no check may be repaired by making it vacuous)

    python tools/docs_verify.py --links
    -> "0 dangling reference(s)"

In scope (3):
- `tests/test_module_fingerprints.py` — the two failing tests
- `docs/map/SEAM-harness-x-verification.md` — the 45/28/14/3 census check
- `docs/map/SEAM-manifest-x-schools.md` — the 42-root census check

NOT in scope: the run roots themselves. The operator's instruction is
explicit — "The rung-5 roots are correct committed evidence; fix the
READERS." No root is renamed, retired, deleted, gitignored, or edited,
and no root's `verify_root` verdict may move. Also not in scope: the
`Verified-at:` stamps of any map document whose full check set this
tranche does not re-run, and rungs 6/7b/7c, which remain deferred.

Budget: <=150 changed lines, 1 commit, ~2 hours.
Stop conditions inherited from orchestrator: yes

## Map preflight (resolved ids)

- `DR-SEAM-harness-x-verification` — owns one failing census check.
- `DR-SEAM-manifest-x-schools` — owns the other.
- `DR-CON-schools` — owns `module_events.py`, the module the failing
  tests guard (rung 4 added it to this document's `Owns:`).
- `DR-SEAM-schools-x-scheduler` — owns the stamp's write site
  (`Scheduler._record_module_fingerprints`).
- `DR-INV-frozen-surfaces` — read before designing: this tranche must
  not touch any of the five surfaces, and `invariants.py` /
  `verification/` (surface 3) is adjacent to the census checks'
  subject matter.

Note for `dr-diagnose`: the census disagreement is between three
DIFFERENT instruments that are each internally correct — `git ls-files`
+ `/log.jsonl` (47), `tools/root_sweep.py` over `experiments/` (42+2),
and direct manifest load (45→47). `docs/ERRATA.md` E5 and E8 already
record this family of confusion. The goal is not to reconcile them into
one number; it is to stop asserting a number that a future committed
root will invalidate again.
