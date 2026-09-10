# Goal: `tools/blast_radius.py` reports CONTACT for a change inside `src/deepreason/verification/`

Class: defect

Observed: `python tools/blast_radius.py --files src/deepreason/verification/report.py`
returns `"frozen_surface_contacts": []`, `"frozen_surface_verdict": "CLEAR"` and a
disclosure summary reading "This change touches none of the five frozen surfaces",
for a file inside frozen surface 3. The owning document's §3 heading is
"Replay-validation record formats — `invariants.py`, `verification/`"
(`DR-INV-frozen-surfaces`), and CLAUDE.md's third-lane section states the arithmetic
explicitly: five surfaces spanning seven paths, "because surface 3 covers both
`invariants.py` and `verification/`". Evidence:
`experiments/2026-09-10-defect-defended-trial-authority-census/proof/BLAST_RADIUS.txt`
(the CLEAR run, and the control run returning all five registry paths as `DIRECT`, so
the CLEAR is the registry's spelling and not the computation);
`experiments/2026-09-10-defect-defended-trial-authority-census/PARKED.md` P2;
`docs/ERRATA.md` E88, which already records that the registry's "verbatim" comment is
false and states that until this is fixed the document outranks the tool for any path
under `src/deepreason/verification/`.

Success criterion (machine-decidable):

    python tools/blast_radius.py --files src/deepreason/verification/report.py
    -> frozen_surface_verdict == "CONTACT", with a DIRECT contact whose surface names
       replay-validation record formats

    python tools/blast_radius.py --self-test
    -> SELF-TEST PASS, and the self-test carries a case that goes RED if a
       directory-scoped surface stops matching a file inside it

    pytest tests/test_blast_radius.py -q
    -> 0 failed

    pytest tests/ -q -n 4
    -> 0 failed

    python tools/docs_verify.py
    -> 0 failed

In scope: `tools/blast_radius.py` (the `FROZEN_SURFACES` / `FROZEN_ADJACENT`
registry, `_frozen_contacts`, the module docstring's honesty limits, the self-test),
`tests/test_blast_radius.py`, `docs/map/INV-frozen-surfaces.md` (the G6 section and
the 2026-09-10 grant entry's "until it is fixed" paragraph, which the fix falsifies).

NOT in scope: `src/deepreason/verification/` itself — this tranche changes what the
disclosure gate SAYS about that surface, never the surface. Also not in scope: the
`Owns:` header line of `docs/map/INV-frozen-surfaces.md`, and any other instrument
under `tools/` (`diff_budget.py`, `docs_verify.py`, `record_claims.py`).

Budget: <=150 changed lines, 1 commit, ~2 hours

Stop conditions inherited from orchestrator: yes

## Map preflight (ids resolved before scoping)

- `DR-INV-frozen-surfaces` — owns the five surfaces, the frozen-adjacent list, and
  (its "instruments" section, the G6 subsection) the blast-radius gate itself.
  Read first, per `INDEX.md`'s routing table row "know whether you are allowed to
  change it".
- `DR-SUB-verification` — the subsystem whose paths the registry spells narrowly.
  Read for what sits under `verification/`; NOT edited.
- Seam: none. `tools/blast_radius.py` is not a package; the map keeps `tools/`
  inside `DR-INV-frozen-surfaces`'s instruments section, so there is no
  `SEAM-` document for this pair and none is owed.
- Frozen surfaces touched by THIS tranche: none. `tools/` is not a frozen surface,
  so no grant is required (operator, this tranche's brief).
