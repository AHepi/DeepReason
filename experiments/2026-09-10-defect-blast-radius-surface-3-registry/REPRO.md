# Reproduction

Form: unit-test (two layers — a disposable fixture repo, and the real tree)

Artifact: `tests/test_blast_radius.py`, four tests, all RED on the pre-fix tree:

  - `test_frozen_surface_direct_contact_on_a_file_inside_a_directory_scoped_surface`
  - `test_symbol_indirect_contact_reaches_inside_a_directory_scoped_surface`
  - `test_real_registry_reports_contact_for_every_path_of_frozen_surface_3`
    (parametrized; RED on both `verification/` paths, GREEN on `invariants.py`)

The fixture layer gains a `src/deepreason/verification/report.py` stand-in and
two near-misses beside it. The real-tree layer runs the tool against this
repository, because the defect `docs/ERRATA.md` E88 records is in the
registry's CONTENTS, not in its computation — a fixture-only registry test
would have stayed green throughout the whole life of the defect, which is
precisely how the defect survived to be found by hand.

Current output (`proof/repro_red.txt`, verbatim tail):

    FAILED tests/test_blast_radius.py::test_frozen_surface_direct_contact_on_a_file_inside_a_directory_scoped_surface
    FAILED tests/test_blast_radius.py::test_symbol_indirect_contact_reaches_inside_a_directory_scoped_surface
    FAILED tests/test_blast_radius.py::test_real_registry_reports_contact_for_every_path_of_frozen_surface_3[src/deepreason/verification/report.py]
    FAILED tests/test_blast_radius.py::test_real_registry_reports_contact_for_every_path_of_frozen_surface_3[src/deepreason/verification/contained.py]
    4 failed, 23 passed

and the failure text is the predicted one, not an error:

    assert 'CLEAR' == 'CONTACT'
      - CONTACT
      + CLEAR
    {..., 'frozen_surface_contacts': [], ...}

Confirms diagnosis: yes — the tool answers cleanly (exit 0, well-formed JSON,
empty contact list) for a file inside frozen surface 3, while the same run over
`src/deepreason/invariants.py` — the one path of that surface the registry
happens to hold — passes. The failure is selective by registry membership,
which is what a one-path-per-surface registry predicts and what a broken
comparison would not.

Three companion assertions are GREEN today and must STAY green, so the fix
cannot buy CONTACT by loosening the comparison:

  - `test_frozen_surface_clear_when_no_target_matches` (pre-existing) — the
    exact-match pin on single-file surfaces.
  - `test_directory_scoped_surface_matches_only_on_a_path_boundary` (new) —
    `src/deepreason/verification_notes.py` and
    `src/deepreason/rules/verification/report.py` must both stay CLEAR. A
    mutation to a bare `startswith("…/verification")` flags the first; a
    mutation to a basename or trailing-segment comparison flags the second.
  - `test_real_registry_still_reports_clear_for_a_file_outside_every_surface`
    (new) — `scheduler/scheduler.py` on the real tree stays CLEAR, so the
    widening cannot be the degenerate "everything is CONTACT".

Post-fix expectation: `pytest tests/test_blast_radius.py -q` reports 0 failed
with all 27 tests green, `python tools/blast_radius.py --self-test` prints
SELF-TEST PASS with a directory-scope case of its own, and
`python tools/blast_radius.py --files src/deepreason/verification/report.py`
returns `frozen_surface_verdict: "CONTACT"` with a DIRECT row naming
replay-validation record formats.

Production code untouched this phase: the diff is `tests/` only.
