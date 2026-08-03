# Verification

Fix commit: `2456da55`. All commands below re-run at that HEAD.

## Criterion command + output

GOAL.md criterion 1 (regression pins the disposition, verdict R):

    python -m pytest tests/ -k attached_evidence -q
    -> 6 passed, 2 skipped, 3289 deselected in 48.22s

GOAL.md criterion 2 (full gate; run pre-commit on the identical tree):

    python -m pytest tests/ -q -n 4
    -> 3290 passed, 7 skipped in 661.41s   # 0 failed

GOAL.md criterion 3 (45-root instrument; sweeps in the session scratchpad):

    python tools/root_sweep.py <before>/<after>
    -> 42 rows each (the committed-tree census; ERRATA E5 corrects the
       handover's 45), 11 ERROR rows each, diff BYTE-IDENTICAL.
       No root's valid, att, or epistemic_checks_passed moved. None.

Also part of the gate for this tranche (map moved with the code):

    python tools/docs_verify.py          -> 46 documents, 756 checks, 0 failed
    python tools/docs_verify.py --audit  -> 0 findings
    python tools/docs_verify.py --coverage -> 6 seams swept, 0 findings

## Historical roots re-checked

    triage  run-0a3e93d6 (the defect root):
        before: ['attached-evidence']  ->  after: []          (verify_root)
        verify_post_commit_report.valid: True
        verify_root_report.valid: False — unchanged and correct: the
        root's own stored terminal summary records integrity-invalid
        (run-result-verification), and stored records are frozen evidence.
        ERRATA E8 records that FIX.md predicted this flip in the wrong
        instrument.
    orbit   run-6472629d (known-good, same ladder):    [] -> []
    engaged run-f4fa6663 (known-good, 1 REFUTED):
        ['foreign-criticism'] -> ['foreign-criticism'] — pre-existing
        completion-channel debt class, present in the byte-identical
        before-sweep; untouched by this change.

## Live attempt

None, per GOAL.md: the committed root is the repro, the fix is
reader-only, and the `env` credentials did not survive the rollback. The
offline regression is the proof; a live run could add nothing about this
path that the committed record does not already show.

## Verdict: PASS

## Residue (honest)

- The defect root's sweep row stays `valid=False` forever, on its stored
  terminal summary. That is the record system working, not residue of the
  defect — but anyone reading the sweep must know the flip shows in
  `verify_root` / `verify_post_commit_report` instead (ERRATA E8).
- The 11-vs-14 census delta (which three raising roots the report layer
  routes to a verdict path) remains undiagnosed — handover item 2, PARKED.
- The three rollback-eaten workspace roots of ERRATA E5/E7 are gone;
  turmite/jolt live evidence now exists only as prose citations and their
  committed audits/results.
- Whether any OTHER "exactly one artifact shaped like X" demand exists
  elsewhere in verify_root with a model-reachable predicate was checked
  only for this finding's block; a systematic audit of the remaining 217
  fail() sites was not in scope.
