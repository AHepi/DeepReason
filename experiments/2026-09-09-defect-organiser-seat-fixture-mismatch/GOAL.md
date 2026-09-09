# Goal: tests/test_organiser_seat.py passes on main, with no assertion weakened

Class: defect

Observed: three tests in `tests/test_organiser_seat.py` fail on `origin/main`
(`d7c87473e`), reproduced here at `3 failed, 9 passed in 5.52s`:
`test_the_fixture_is_the_committed_attachment_byte_for_byte` (sha256 mismatch
on `01-conjectures.txt`), `test_admission_mints_one_block_per_room_record`
(12/46/36 expected, the attachment now mints 13/47/37), and
`test_the_organiser_brief_shows_the_whole_room_and_the_directive` (legend split
expected 7/13/12, measured 4/17/11). Recorded in
`experiments/2026-09-06-defect-budget-exhausted-classification/VERIFY.md`, gate
section: "3 failed, all in tests/test_organiser_seat.py, reproduced on
origin/main in a clean worktree".

Success criterion (machine-decidable):

    python -m pytest tests/test_organiser_seat.py -q
    12 passed, 0 failed

    python -m pytest tests/ -q -n 4
    0 failed

In scope: `tests/test_organiser_seat.py`; a new fixture helper under `tests/`
if one is needed; the `Traps` section of `docs/map/INV-seat-section-plugins.md`
(the map document that owns the organiser seat and carries
`check: python -m pytest tests/test_organiser_seat.py -q`).

NOT in scope: the attachment itself
(`experiments/2026-09-06-change-writers-room-organiser-testing/attachment/`)
and everything else under `experiments/`; anything under `src/`. The second
launch window was ENTITLED to move those bytes (SPEC Amendment 4, S38-S40);
the defect is that the tests pinned them.

Budget: <=150 changed lines, 1 commit, ~2 hours

Stop conditions inherited from orchestrator: yes

## Map preflight

- `docs/map/INDEX.md` -> `DR-INV-seat-section-plugins` (owns the organiser
  shell, its layout and `tests/test_organiser_seat.py` as one of its checks).
- `docs/map/INV-frozen-surfaces.md` read: no frozen surface is in scope. The
  five surfaces span `capabilities/state.py`, `harness.py`, `invariants.py`,
  `verification/`, `run_manifest.py`, `qualification.py`, plus the
  frozen-adjacent `route_fingerprint` in `llm/firewall.py`. This tranche
  touches `tests/` and one map document only.
- Seam: none crossed. The work is a test file and its fixture source.
