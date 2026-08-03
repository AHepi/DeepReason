# Implementation log

Change applied exactly as FIX.md specified; this file is the receipts.

## Change sites touched

- `src/deepreason/invariants.py` — the `candidates` comprehension gains
  `artifact.provenance.role == "import"`, with a comment stating the
  constraint (import provenance is the writer's discriminator; a mention is
  just a citation — stress-triplet run-0a3e93d6). Finding name, detail
  string, return shape: unchanged.
- `tests/test_attached_evidence_citation.py` — NEW. Three cases:
  1. `test_a_conjecture_citing_the_bound_source_leaves_the_root_valid` —
     the live failure shape, offline;
  2. `test_the_committed_triage_root_verifies_clean` — record replay of the
     committed repro root, read-only;
  3. `test_a_duplicate_import_candidate_still_fails_uniqueness` — the
     narrowing must not weaken the demand it narrows.
- `experiments/2026-08-03-fix-attached-evidence-integrity/repro_attached_evidence.py`
  — assertions inverted to the post-fix expectation (REPRO.md preserves the
  pre-fix output).
- Map, same commit: `docs/map/SEAM-periphery-x-verification.md` (NEW, with
  `Sweep:` header), `INDEX.md` (matrix row, "last six" prose), 
  `SUB-periphery.md` (+`Seams:`), `SUB-verification.md` (+`Seams:`, +Trap),
  `SEAM-harness-x-verification.md` (+Trap, +stated reason for having no
  `Sweep:` header per SCHEMA.md's sanctioned omission).

## Scope extensions during implementation (operator documentation grant)

Re-running every map check on the clean post-rollback checkout surfaced two
pre-existing failure classes that BLOCKED the mandated docs_verify green.
Both were repaired under the operator's standing "fix documentation as you
go" grant, outside GOAL.md's original touch list, and are ledgered in
`docs/ERRATA.md` (started this session at the operator's request):

- E3/E4: the pre-v6 census check and prose went stale-false when the
  stress-triplet roots were committed (42/25 → 45/28 tracked). Numbers
  corrected in `SEAM-harness-x-verification.md` and `INV-frozen-surfaces.md`.
- E7: four checks in `SEAM-harness-x-verification.md`, `SUB-adjudication.md`
  and `SEAM-adjudication-x-rules.md` opened the turmite/jolt live roots,
  whose homes their ladders gitignore — verifiable only on the machine that
  ran them. Repointed at the committed orbit root `run-6472629d`; run ids
  kept in prose as history.
- Environment restoration, not code: `jsonschema` had to be reinstalled
  (rollback casualty); it alone accounted for two of the six docs_verify
  failures.

## Red before, green after

Regression test BEFORE the code change:

    FAILED tests/test_attached_evidence_citation.py::test_a_conjecture_citing_the_bound_source_leaves_the_root_valid
    FAILED tests/test_attached_evidence_citation.py::test_the_committed_triage_root_verifies_clean
    2 failed, 1 passed in 47.20s
    (the duplicate-candidate case passes under both predicates — it is the
    guard-survival case, red would have meant the demand was citation-shaped)

AFTER:

    3 passed in 45.11s

## Rings outward

    tests/test_chaos_invariants.py tests/test_r0_terminal_verification.py
    tests/test_verifier_registry.py tests/test_cli_verifiers.py
    tests/test_evidence_dossier.py tests/test_evidence_dossier_replay.py
    -> 37 passed in 2.86s

    tests/test_amendment_chain_integrity.py tests/test_amendment_epochs.py
    tests/test_replay.py tests/test_persistence_invariants.py
    tests/test_torn_append.py
    -> 71 passed in 176.57s

    python tools/docs_verify.py --links    -> 0 dangling, 46 documents
    python tools/docs_verify.py --coverage -> 6 seams swept, 0 findings
                                              (periphery x verification now
                                              among the swept)

## Full gate

    python -m pytest tests/ -q -n 4
    -> 3290 passed, 7 skipped in 661.41s (0:11:01)   # 0 failed
    (baseline 3287 + the 3 regression cases)

    GOAL.md's exact criterion-1 command:
    python -m pytest tests/ -k attached_evidence -q
    -> 6 passed, 2 skipped, 3289 deselected

    python tools/docs_verify.py         -> 46 documents, 756 checks, 0 failed
    python tools/docs_verify.py --audit -> 0 findings
    python tools/docs_verify.py --coverage -> 6 seams swept, 0 findings

## Root sweep (frozen-surface instrument 2)

    tools/root_sweep.py before (pre-change code, in-memory since process
    start) and after (fresh process, fixed code): 42 rows each, 11 ERROR
    rows each, and the two files diff BYTE-IDENTICAL.

FIX.md's predicted delta (run-0a3e93d6 valid False -> True in the sweep) was
wrong about the instrument — `docs/ERRATA.md` E8. The sweep reads
`verify_root_report`, which binds the root's own stored terminal summary
(frozen evidence: `run-result-verification`, "RunResult v2 records an
integrity-invalid verification summary"), so that row correctly stays
valid=False forever. The fixed reader's verdict on the same bytes:

    verify_root(run-0a3e93d6)                -> {"violations": []}
    verify_post_commit_report(run-0a3e93d6)  -> valid: True, integrity: []

Zero movement across all 42 rows satisfies GOAL criterion 3 in its strongest
form: no recorded root moved at all, in the sweep instrument.
