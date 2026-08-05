# Diagnosis: three independent discards, one shared consequence

Primary cause: `scripts/wheel_operational_smoke.py` treats its typed
failure record as its ONLY output channel, and that record is
deliberately closed and payload-free. Every piece of evidence that does
not fit the closed vocabulary is therefore dropped rather than routed
elsewhere — the child's output on timeout, an assertion's message, and
the temp directory itself. The record's closure is correct and must
stay; what is missing is a second, human-facing channel beside it.

Evidence (reproduced, `repro.py`, 3 of 3 present):

- `_run`'s `except subprocess.TimeoutExpired` raises
  `OperationalSmokeFailure(...) from None` without reading
  `TimeoutExpired.stdout`/`.stderr`. Behaviourally confirmed: a child
  that printed `CHILD-STDOUT-MARKER` and `CHILD-STDERR-MARKER` before
  hanging surfaced neither.
- One `except AssertionError` handler, binding no name (AST), so the
  message and traceback are unreachable.
- `if succeeded and args.keep:` gates retention on success.

Why the record cannot simply grow a `detail` string: the smoke asserts
via `_assert_no_disclosure` that neither the repository path nor
`TEST_CREDENTIAL` appears in any collected output or state file, and
`tests/test_wheel_operational.py::test_v4_diagnostic_fields_types_and_allowlists_are_closed`
pins the v4 field set. Raw child output in a machine-readable record is
exactly the disclosure that assertion exists to prevent.

Implicated code (3 sites):
- `_run`, `except subprocess.TimeoutExpired` (~1475)
- `main`, `except AssertionError` (~3610)
- `main`/`_finalize_operational_smoke`, the `--keep` guard (~3621)

Falsifiable prediction: after the fix, `repro.py` reports 0 of 3
concealments, and a real failing run names its assertion on stderr while
the typed record's field set is unchanged.

Ruled out: that the record should carry the payload. Its closure is
load-bearing (disclosure guarantee + pinned schema), so the fix adds a
channel rather than widening the record.
