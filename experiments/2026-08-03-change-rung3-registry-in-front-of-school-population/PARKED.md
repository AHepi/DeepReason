# Parked — noticed or deferred during this tranche, deliberately not done

- **Tranche B: migrating call sites to resolve through `SCHOOL_POPULATION`.**
  Nothing live consumes the registry yet. `scheduler/scheduler.py`'s two
  call sites (`init_schools`, `allocate`) are the clearest candidates —
  they ARE "school population" in the rung's own sense. `capture/
  ladder.py`'s `roster`/`reseed` call sites (both inside the response
  ladder's live intervention logic) and `cli/main.py`'s `reseed` command
  (a manual write, same underlying action) are plausible but not
  pre-decided here — SPEC.md's own Q3 leaves this open for Tranche B's
  own `dr-spec-change`. `report.py`'s `roster()` call and `cli/main.py`'s
  read-only `schools` display command are plausibly OUT of scope for
  migration (pure diagnostics, no backend-dependent branching), but that
  too is Tranche B's decision, not this tranche's.
- **The full end-to-end offline-no-provider-run determinism test R7's
  own words describe** (reusing `tests/test_attached_evidence_
  citation.py`'s fixture pattern) — this tranche's S4 delivers a
  smaller-footprint, direct method-vs-bare-function equivalence proof
  instead, by explicit design (SPEC.md A2). The full end-to-end proof
  needs a live call site to exist first, so it belongs to Tranche B.
- **Rung 5's "one deliberately dumb alternative, swapped in"** — a
  separate, later rung. Registering a second backend now would be inert
  (nothing resolves against it) and would pre-empt rung 5's own scoped
  work; explicitly out of scope per SPEC.md.
- **`docs/map/SEAM-schools-x-scheduler.md` has no `Sweep:` header.**
  Most seam documents in this repo do carry one; this one does not,
  matching the majority pattern but not a deliberate choice worth
  defending — worth adding if/when Tranche B gives the document
  something concrete to sweep for (e.g. `SCHOOL_POPULATION` usage sites).
- **The pre-existing `Owns:` overlap between `docs/map/CON-schools.md`
  and `docs/map/SUB-periphery.md` for `capture/schools.py`.** Both
  documents already listed this file before this tranche (not
  introduced here) — `SUB-periphery.md` owns the whole `capture/`
  directory, `CON-schools.md` owns the file specifically for the schools
  concept. Per `docs/map/SCHEMA.md`'s own rule, an `Owns:` overlap is
  itself evidence of an undocumented seam; noticed during this tranche's
  validation pass (`--stale` flagged `SUB-periphery.md`), not resolved —
  outside this tranche's own scope and not requested.
