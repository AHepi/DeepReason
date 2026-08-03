# Fix: select attached-evidence candidates by the writer's discriminator (import provenance), not by citation

Guarantee restored: **citing attached evidence never changes a root's
integrity verdict** — the `attached-evidence` check judges only the
import-time triple that `attach_bound_evidence` registered, and still demands
exactly one reliability-dependent candidate per bound source.

## The change

`verify_root` currently builds the candidate set as every artifact carrying
`mention -> source_record` (`invariants.py:2156-2163`). The writer
(`evidence/render.py:146-159`) marks the real candidate with a discriminator
the reader ignores: `provenance.role == "import"`. Cycle-time artifacts can
never carry that role — `ProvenanceRole.IMPORT` is assigned only by trusted
import paths, never by rule-driven (conjecturer/critic/…) creation. Adding
that one conjunct to the comprehension makes the predicate select exactly what
the writer built, on every root in the corpus, while keeping both existing
demands intact: `len(candidates) != 1` (uniqueness — a writer that registered
two candidates for one source still fails) and the `dependence`-ref presence
(a candidate that lost its reliability dependence still fails).

`ProvenanceRole` is a `str` Enum (`ontology/artifact.py:43`), so the
comparison is `artifact.provenance.role == "import"` — same idiom the block
already uses for `ref.role == "mention"`. Verified live:
`Provenance(role='import').role == 'import'` is `True`.

Change sites (exhaustive):

- `src/deepreason/invariants.py:2156-2163` — add
  `artifact.provenance.role == "import"` to the candidate comprehension.
  ~2 lines. The finding NAME, the detail string, and the return shape are
  untouched (frozen format).
- `tests/test_evidence_dossier_replay.py` (or a new
  `tests/test_attached_evidence_citation.py`) — regression test, docstring
  "Regression (stress-triplet run-0a3e93d6): ...", three cases:
  1. a converged v6 root whose conjecture cites the source record verifies
     with zero `attached-evidence` findings (the repro, inverted);
  2. the committed root
     `experiments/2026-08-02-stress-triplet/home-triage/runs/run-0a3e93d6e8031e2e6d1d21dde2fa93cc`
     verifies with zero violations (record replay, read-only);
  3. NEW: a root given a second import-role artifact mentioning the same
     source record still reports exactly one `attached-evidence` violation —
     the uniqueness demand survives the narrowing.
  ~100 lines.
- `experiments/2026-08-03-fix-attached-evidence-integrity/repro_attached_evidence.py`
  — invert its assertions to the post-fix expectation (REPRO.md records the
  pre-fix output; the artifact must "show the defect's absence after the
  fix"). ~10 lines.

Documentation sites (operator grant in GOAL.md; same commit as the code, per
`REC-change-a-seam` Step 6):

- `docs/map/SEAM-periphery-x-verification.md` — NEW (Step 7). The agreement:
  the import-time triple per bound source and the reader's demand on it. With
  a check that pins the writer's discriminator to the reader's predicate, so
  they cannot drift apart silently again.
- `docs/map/INDEX.md` — seam matrix row for periphery × verification (an
  uncounted seam: the verifier's `deepreason.evidence` imports are
  function-local, invisible to the coupling metric).
- `docs/map/SUB-periphery.md`, `docs/map/SUB-verification.md` — remove the
  false non-interaction: add the seam to `Seams:`, and a Traps entry in
  SUB-verification for this failure mode.
- `docs/map/SEAM-harness-x-verification.md` — Traps entry (the defect was
  diagnosed through this seam's instruments; its Traps list is where the next
  reader of a `valid=False` verdict looks first).
- `python tools/docs_verify.py` must pass; `Verified-at:` advances only on
  documents whose checks were actually re-run.

Regression artifact: `repro_attached_evidence.py` must invert —
`repro` root violations `[{attached-evidence, ...}]` → `[]`; control stays
`[]`; committed root `[attached-evidence]` → `[]`. Plus new condition 3 above
(two import-role candidates → still exactly one violation).

Existing tests at risk: none found. No test under `tests/` creates a
cycle-time artifact citing a source record and then verifies — that is why the
gate never caught this. The four files touching `attach_bound_evidence` /
`attached-source-record` (`test_evidence_dossier.py`,
`test_evidence_dossier_replay.py`, `test_simulation_capability_v5.py`,
`test_v6_three_root_concurrency.py`) exercise the import triple without
downstream citation, and `test_amendment_chain_integrity.py:367` accepts
either `amendment-epoch` or `attached-evidence` on a tamper path this change
does not touch. All must keep passing unmodified.

Sibling checked (counters-count-one-thing rule):
`capabilities/audit.py:365-391` also walks artifacts for
`attached-source-record.v1`, but it selects the RECORDS by schema + source id
for the RESEARCH_SOURCE_AUDIT.md listing — a different predicate answering a
different question, with no uniqueness demand. No mirror-image bug. Not
touched.

Explicitly not changed:

- `evidence/render.py` — the writer is correct; it already supplies the
  discriminator. The record is law and this fix is reader-only.
- The `dependence`-ref demand and the `len == 1` demand — both catch real
  writer faults and survive verbatim.
- The detail string "lacks one reliability-dependent candidate evidence
  artifact" — frozen format; and under the narrowed predicate it becomes
  truthful (it fires only when the import-time candidate is missing,
  duplicated, or dependence-less).
- `first_llm_seq` ordering, source-record dedupe, dossier-union logic in the
  same block — not implicated by the repro.

## Frozen-surface declaration and the predicted verdict movement

This edits `invariants.py` — frozen surface 3. It is the sanctioned
direction: a READER fix with formats untouched. Predicted, per GOAL.md's
carve-out:

- `run-0a3e93d6...` flips `valid` False → True. That is the fix working: the
  root records correct behaviour and the reader stops mis-judging it.
- **No other root moves.** Every currently-valid root with attached evidence
  passes because its candidate set is exactly the import triple's candidate
  (orbit: set size 1). Narrowing the predicate cannot remove the import
  candidate from any set, and cannot add anything. A root that currently
  passes with a size-1 set passes after with the same set. The 45-root sweep
  before/after is the proof; `att` and `epistemic_checks_passed` are untouched
  by construction (this check contributes to neither).

Operator approval: given verbatim — the previous report stated this exact fix
("narrow the candidate predicate without dropping the uniqueness demand...
flips run-0a3e93d6 from valid=False to True... plus the seam document") and
the operator replied "Do it."

Estimated diff: ~112 lines of code and tests across 3 files (2 in
`invariants.py`, ~100 test, ~10 repro inversion) — within budget. Map
documents are additional under the operator's documentation grant (~180
lines, mostly the new seam document).
