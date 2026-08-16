# Parked — not this tranche's goal

## P1 — the `manifest x run-identity` seam has no document

WHAT: `docs/map/CON-run-identity.md` lists `manifest x run-identity`
under `Seams-undocumented:`, and this tranche's whole diagnosis lives in
that seam (dossier bytes → `run_input_digest` → `manifest.sha256`). The
coupling is now written down in `CON-run-identity.md`'s prose and Traps,
which is enough for the next reader; a full `SEAM-manifest-x-run-identity.md`
is a separate authoring job with its own checks.

Ready-to-send prompt:

```
Change tranche: write docs/map/SEAM-manifest-x-run-identity.md, the seam
CON-run-identity.md has listed under Seams-undocumented since it was
written. Route through dr-change-orchestrator. One goal: the seam
document exists, conforms to docs/map/SCHEMA.md, and carries executable
`check:` lines that would fail if the coupling changed. The coupling to
describe is already traced and committed:
experiments/2026-08-16-defect-manifest-sha-doc-coupling/DIAGNOSIS.md —
evidence dossier bytes -> evidence_dossier_digest -> run_input_digest ->
run_manifest.py:3507 -> manifest.sha256, with the A-probe/B-probe pair
proving that path is the ONLY one. Do not change any code; do not
re-open the frozen manifest surface. End state: the seam document
committed, INDEX.md's seam matrix updated in the same commit,
`python tools/docs_verify.py --links` clean, docs_verify at the
3-failure shallow-clone baseline.
```
