# Reproduction

Form: **record-replay** (form 1) — the artifact reads a real built wheel
and needs no provider call. Paired with the smoke's own typed failure.

Artifact: `experiments/2026-08-05-fix-smoke-entry-point-reader/repro.py`

## Current output — the instrument itself

    $ python scripts/wheel_smoke.py ; echo rc=$?
    File "scripts/wheel_smoke.py", line 146, in inspect_wheel
      raise AssertionError(f"unexpected console entry points: {sorted(observed)}")
    AssertionError: unexpected console entry points:
      ['deepreason = deepreason.cli.main:main',
       'deepreason-mcp = deepreason.mcp_server:main',
       'epub = deepreason.admission.adapters_epub:MANIFEST',
       'pdf = deepreason.admission.adapters_pdf:MANIFEST']
    rc=1

## Current output — the artifact, on the same wheel bytes

    $ python .../repro.py deepreason-0.1.0-py3-none-any.whl

    FLAT parse (today's reader):
      entries: 4
      equals the 2 required console scripts? False
      -> this is the AssertionError the smoke raises

    SECTIONED parse:
      [console_scripts] -> 2 entry/entries
      [deepreason.admission.adapters] -> 2 entry/entries
      console_scripts equals the 2 required? True

    adapters group present and non-empty? True

Confirms diagnosis: **yes.** DIAGNOSIS.md predicted the flat parse would
yield four entries and fail the equality while a sectioned parse would
yield exactly the two required console scripts and put the adapters in
their own group. Both halves hold on real wheel bytes, so the defect is
entirely in how one file is parsed — no packaging, no `src/` module and
no wheel content is implicated.

## Post-fix expectation

- `python scripts/wheel_smoke.py` → exits 0, having run PAST line 146
  into `_check_mcp`, which has not executed since 2026-07-26. Whatever
  it then reports about the MCP tool set and schema sha is new
  information, not a regression: those pins are unmeasured rather than
  known-good, so a mismatch there is expected work, not a second defect.
- `python -u scripts/wheel_operational_smoke.py` → exits 0. Status
  currently unknown; it has never been reached in this session.
- `repro.py` keeps printing the same two parses — it is a measurement of
  the two algorithms, not an assertion about the tree, so it does not
  invert. What inverts is `wheel_smoke.py`'s exit code.
- The adapters group gains an assertion (DIAGNOSIS.md's second finding),
  so the fix does not trade one blind spot for another.
