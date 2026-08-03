# Reproduction

Form: record-replay **and** offline unit reproduction (both; the first costs
nothing and the second isolates the variable).

Artifact: `experiments/2026-08-03-fix-attached-evidence-integrity/repro_attached_evidence.py`

    python -m pytest experiments/2026-08-03-fix-attached-evidence-integrity/repro_attached_evidence.py -q -s

It lives in the tranche directory, not in `tests/`, so the gate stays green
across this phase. This repo has no `xfail` convention (zero occurrences under
`tests/`), so committing a deliberately-red test to encode the defect would
have introduced one. The permanent regression test is `dr-implement-fix`'s to
write.

Two v6 manifest-bound roots are built from the existing gate fixtures
(`_evidence_manifest`, `_commitment`, `_write_qualification`,
`_record_converged_stop`, `admit_sources`). They differ in exactly one line:
whether the single cycle-time conjecture carries
`Ref(target=<source_record_id>, role="mention")`. Everything else — the
dossier, the manifest, the terminal stop, the token accounting — is identical.

Current output:

    control  (conjecture does NOT cite the source): []
    repro    (conjecture DOES cite the source): [{'check': 'attached-evidence',
      'detail': 'bound source src-a7b17a1063413cfec12df194df73083127c3757a
                 lacks one reliability-dependent candidate evidence artifact'}]
    reliability-dependent candidate evidence artifacts present: 1

    committed run-0a3e93d6 violations: [{'check': 'attached-evidence',
      'detail': 'bound source src-56d86e9b3a1d59413e02c76cdf675f84f6288fa7
                 lacks one reliability-dependent candidate evidence artifact'}]

    2 passed in 59.95s

Confirms diagnosis: yes — citing the source is the whole cause. One variable
was changed and the verdict flipped, while the artifact the finding names as
missing was present in both roots (`reliability-dependent candidate evidence
artifacts present: 1`), so the finding's detail text is false on its face. The
synthetic root reproduces the committed root's verdict byte-for-byte in check
name and detail shape.

Post-fix expectation:

    control  -> []            (unchanged; the fix must not disturb it)
    repro    -> []            (the citation stops mattering)
    committed run-0a3e93d6 violations: []   -> valid flips False to True

    and a NEW case, to be added with the fix: a root with TWO
    import-role reliability-dependent candidate evidence artifacts for one
    bound source still reports exactly one `attached-evidence` violation.
    The uniqueness demand is real and must survive; only the predicate that
    selects the candidate set is wrong.

Production code untouched in this phase.

## Map finding, surfaced by `REC-change-a-seam` Step 1 (operator prompt)

Naming both sides as IDs — which the recipe insists on before any design — shows
the agreement this defect broke is **`DR-SUB-periphery` × `DR-SUB-verification`**:
`evidence/render.py` (periphery) writes the import-time triple, `invariants.py`
(verification) reads it. That seam is undocumented, and worse, the map currently
asserts it does not exist:

- `INDEX.md`'s seam matrix has no `periphery` row at all, and INDEX states that
  a pair absent from the table entirely "is a pair with no measured import
  traffic at all".
- `SUB-periphery.md`'s `Seams-undocumented:` lists seven pairs; verification is
  not among them.
- `SUB-verification.md`'s `Seams-undocumented:` lists ten pairs; periphery is
  not among them.

Both sides therefore declare the other a non-interaction. The traffic is real
but invisible to the coupling metric because every `deepreason.evidence` import
in `invariants.py` is FUNCTION-LOCAL (lines 827 and 2053; no module-level
import exists — checked by `ast`). This is precisely the class INDEX already
warns about for its five uncounted seams: "coupling metrics cannot see them, so
nothing but a written seam will tell the next reader they exist."

A reader who trusted the map would conclude `invariants.py` has no business
knowing what `evidence/render.py` builds — and would have no document telling
them the candidate-evidence triple is a contract between the two. That absence
is a plausible part of why the predicate was written on `mention` alone.

Consequence for the next phase: `REC-change-a-seam` Step 7 applies — the seam
document is created as part of the change, before the code, and the matrix and
both `Seams-undocumented:` lines are corrected. This falls inside the operator's
documentation grant recorded in GOAL.md.
