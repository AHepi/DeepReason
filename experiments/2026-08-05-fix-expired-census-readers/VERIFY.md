# Verification

## Criterion command + output

GOAL.md's four success criteria, run verbatim at `0618a6e6`:

    $ python -m pytest tests/ -q -n 4
    3338 passed, 7 skipped in 700.52s (0:11:40)
    rc=0
    -> 0 failed. PASS

    $ python tools/docs_verify.py
    docs_verify [full]: 51 documents, 815 checks, 4 workers
    docs_verify: 0 failed
    rc=0
    -> PASS

    $ python tools/docs_verify.py --audit
    docs_verify --audit: 0 finding(s)
    -> PASS (no check was repaired by making it vacuous)

    $ python tools/docs_verify.py --links
    docs_verify --links: 0 dangling reference(s), 51 document(s)
    -> PASS

Also run, not required by GOAL.md:

    $ python tools/docs_verify.py --coverage
    6 seam(s) swept, 16 without a Sweep: header, 0 finding(s)

Test count is unchanged at 3338 — the fix restated assertions rather
than adding or removing tests, so the population is identical to the
one that reported `2 failed, 3336 passed` before it. No assertion was
weakened: the two tests now assert strictly MORE than before (the
presence half and its non-empty-witness guard are new).

## A corrupted measurement, and the correction

The first post-fix gate reported `3 failed, 3335 passed in 1200.07s`,
with three MCP thread-timing failures
(`test_mcp_run.py::test_start_poll_result_and_progress_notifications`,
`::test_typed_v6_stop_can_continue_and_append`,
`test_mcp_scratch_bridge.py::test_system_exit_progress_callback_cannot_strand_worker_locks`).
None was caused by this change, and the cause was **my own process
error**: I ran the 4-worker gate concurrently with `docs_verify`, which
itself spawns up to 16 workers running pytest checks, so the box was
oversubscribed and tests asserting on `thread.join(timeout=2)` /
`(timeout=5)` failed on timing.

Established rather than assumed:

    $ git diff --stat 575119f5..HEAD -- src
    (empty)                       # no src/ file changed since the gate
                                  # that showed all three passing

    # two of the three pass when re-run together, unloaded
    1 failed, 2 passed in 66.75s
    # the third passes alone, twice
    run 1: 1 passed in 11.70s
    run 2: 1 passed in 10.11s

    # the authoritative run, alone, nothing competing
    3338 passed, 7 skipped in 700.52s

This tranche touches exactly three files
(`tests/test_module_fingerprints.py` and the two map documents), none of
which can reach MCP worker locks. Recorded because a measurement taken
against a box I had loaded myself is the same class of mistake as
measuring a tree during a falsification pass, which `DR-SCHEMA` already
warns about — and because the corrupted number would otherwise sit in
the record unexplained.

## Historical roots re-checked

The fix changed no reader — `src/` is untouched — so no root's verdict
can move. Confirmed anyway on the two roots the defect was about, plus
one known-good:

| root | before | after |
|---|---|---|
| `run-9a6be78e…` (ab-home, default arm) | 1 stamp, `verify_root` 0 violations | unchanged |
| `run-9a6be78e…` (rr-home, round-robin arm) | 1 stamp, `verify_root` 1 `attempt-validity` violation | unchanged (P7, still parked) |
| `run-6472629d…` (stress-triplet orbit) | `verify_root` 0 violations | unchanged |

`repro.py` post-fix prints the same partition and all four properties
`True` — it is a measurement, not an assertion, so it does not invert;
what inverted is the instruments' verdicts, from red to green, with the
underlying claims never having changed.

## What the fix actually asserts now

- `tests/test_module_fingerprints.py` — the shared helper returns
  `(unstamped, stamped, refused)`, split by each root's OWN record. The
  renamed test asserts absence is valid on pre-feature roots (floor
  `> 20`), presence is well-formed on post-feature ones
  (`schema_`/`modules`/`digest`), and — the anti-vacuity guard — that at
  least one stamped witness exists. Mutation-proven: patching
  `recorded_module_fingerprints` to return `()` makes it fail at the
  witness assertion.
- `SEAM-harness-x-verification.md` — three non-empty kinds partitioning
  every git-tracked root. Mutation-proven twice (all-v6; drop one root).
- `SEAM-manifest-x-schools.md` — raising and no-manifest are non-empty
  and distinct, so conflating them gives a strictly larger baseline.
  Mutation-proven twice (no-manifest counted as raising; raising counted
  as v6).

Every surviving number is a dated measurement citing its commit and
marked do-not-re-pin.

## Verdict: **PASS**

Both of GOAL.md's end-state criteria are met — full gate 0 failed,
`docs_verify` 0 failed — with `--audit` 0 confirming the greenness was
not bought by weakening anything.

## Residue (honest)

- **The mutation-testing hazard I hit and did not fix.** A `src/`
  mutation applied inside a `git worktree` is NEVER loaded: the editable
  install resolves `deepreason` to `/home/user/DeepReason/src`
  regardless of which worktree pytest runs from. My first mutation proof
  passed spuriously for this reason and had to be redone in the main
  tree. Nothing in the skills or the map records this yet, and the
  falsification doctrine positively encourages worktrees. Parked as
  P1e — the next reader who mutation-proves from a worktree will get a
  green result that means nothing.
- **The cause is fixed; the class is not.** Four instances of "a reader
  asserts a census" were found and fixed. Nothing prevents a fifth being
  written tomorrow — `--audit` catches vacuous checks, not expiring
  ones. No linter or convention now distinguishes a count that is a
  property from a count that is a fact with an expiry date.
- **P1b, the workflow gap, is untouched** and is what let this reach a
  delivered tranche: `dr-deliver-change` measures before the
  live-evidence commits it enables. The monitoring session has since
  added a same-commit pin rule to `CLAUDE.md` and the skills
  (`20f2c8d1`) covering the packaging surface, which is adjacent but not
  the same gap.
- **P1a, ERRATA E5's misidentification**, is recorded and not corrected
  — `docs/ERRATA.md` was outside this tranche's scope. The prose this
  tranche wrote states the measured truth, so nothing shipped depends on
  E5, but the ledger still says the wrong thing.
- **P7 remains parked**, untouched and still visible in the
  `round-robin` arm's single `attempt-validity` violation.
