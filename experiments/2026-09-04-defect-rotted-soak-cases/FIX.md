# FIX — three changes, each the smallest that closes its defect

## F-A — builders ask the policy for the toolchain, never pin one runner

Four builders, five cases (`build_manifest_pc1.py` serves both `pc1` and
`split-legs`):

    experiments/2026-08-25-change-constructive-frontier/build_manifest_pc1.py
    experiments/2026-08-25-poietics-program/build_manifest_pr1.py
    experiments/2026-08-26-pc2-rematch/build_manifest_pc2.py
    experiments/2026-08-27-pc2b-symmetric-reasoning/build_manifest_pc2b.py

`engaged_local_simulation_toolchain` → `engaged_simulation_toolchain`, at the
import and the call site. This is not a new mechanism: it is the call the four
healthy builders already make, and `engaged_simulation_toolchain` exists
precisely to dispatch on the runner choice.

Why this and not the alternatives, both of which were considered and rejected:

- **Setting `DEEPREASON_SIMULATION_RUNNER=local` in the soak** would make every
  case compile without touching a builder — and would make the soak drive a
  shape the launch does not use. `build_manifest_pc2b.py`'s own comment states
  the constraint: "The soak must drive THIS shape; restating the shape there
  would let the instrument and the launch drift apart." A soak that passes by
  configuring away the difference is the failure this instrument exists to
  refuse.
- **Changing the default runner back to local** would fix nine cases by
  reverting a deliberate decision made elsewhere, on the authority of a broken
  test fixture. Out of scope and wrong.

The comment at the call site is updated in the two builders that carry one,
because it stated a constraint that was no longer the binding one. It now says
the toolchain must match the POLICY'S identity and that the identity follows
the runner choice — the fact the code cannot show.

## F-B — every declared assertion is emitted, applicable or not

`scripts/cycle_soak.py`:

- A5/A6 gain an `else` branch. When a case does not carry the in-run
  evaluation, both are emitted with `"applicable": False` and a detail naming
  which cases do carry them.
- `_render` prints `[N/A ]` for those rows, and when any assertion was not
  evaluated it prints a census line: *"7 assertions declared, 5 EVALUATED, 2
  not applicable to this case — a green exit describes the 5 that ran, never
  the 7."*
- `_verdict` ignores non-applicable rows when counting failures, so an `N/A`
  row can never turn a red run green, and can never be mistaken for a pass.

This is the docs_verify remedy applied one instrument over: *an opener the
grammar cannot parse is now a loud failure, never a skip.*

## F-C — a new assertion, A7, and readers that stop dropping records

`_attempt_facts` silently `continue`d past any attempt record it could not
parse. That moves every count it feeds in the PASSING direction —
`attempts_without_complete_lease` can only be raised by a record the reader
actually read — so an unreadable record made D2 more likely to pass, not less.

- Unreadable records are counted (`unreadable_records`) rather than dropped.
- **A7-record-fully-read** fails when that count is non-zero.
- The repair-preparation reader keeps its skip for `KeyError`/`TypeError`,
  which is a well-formed record of a different kind, and counts only
  `OSError`/`JSONDecodeError` — genuinely unreadable bytes. The distinction is
  in the code as a comment, because it is a judgement the code cannot show.

## F-D — builders load in isolation

`_case_module` now scopes its `sys.path` insert and evicts every module it
pulled in from under `experiments/` afterwards. Modules from `src/` are left
cached — they are the same objects for every case, and re-importing them per
case would be slower without being truer.

Deliberately NOT done: renaming the three colliding `question.py` /
`criteria.py` modules. That would edit three committed experiment directories
to work around a loader defect that is now fixed at the loader. The collision
is real but it is no longer reachable, and the regression test asserts that.

## Acceptance

1. All nine cases compile, individually and in one process.
2. A5/A6 appear in every report; the carriers evaluate them.
3. A7 fires on an unreadable record and is silent on a readable one.
4. Every change mutation-proven in BOTH directions.
5. Full gate 0 failed; docs_verify at baseline; both wheel smokes green.
6. `--case epoch3` still exits 0 (`docs/AUDIT_BASELINES.md:210`).
