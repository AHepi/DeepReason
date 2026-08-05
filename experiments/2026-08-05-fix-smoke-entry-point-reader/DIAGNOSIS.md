# Diagnosis: the smoke's entry-point reader has no section state, so every group collapses into `console_scripts`

Primary cause: `scripts/wheel_smoke.py::inspect_wheel` parses the
wheel's `entry_points.txt` — an INI-style file whose meaning is carried
entirely by its `[group]` headers — with a comprehension that discards
those headers and keeps every other non-blank line in one flat set. It
then compares that set for EQUALITY against the two console scripts. Any
entry point in any other group therefore reads as an unexpected console
script. `4940b5f7` added a legitimate second group and the reader has
been red ever since, on correct packaging.

Evidence:

- **The typed failure, reproduced today** (`python scripts/wheel_smoke.py`,
  rc=1):

      File "scripts/wheel_smoke.py", line 146, in inspect_wheel
        raise AssertionError(f"unexpected console entry points: {sorted(observed)}")
      AssertionError: unexpected console entry points:
        ['deepreason = deepreason.cli.main:main',
         'deepreason-mcp = deepreason.mcp_server:main',
         'epub = deepreason.admission.adapters_epub:MANIFEST',
         'pdf = deepreason.admission.adapters_pdf:MANIFEST']

  The error message names its own defect: two of the four "console
  entry points" it lists are not console entry points.

- **The artifact it misreads** (extracted from a freshly built
  `deepreason-0.1.0-py3-none-any.whl`):

      [console_scripts]
      deepreason = deepreason.cli.main:main
      deepreason-mcp = deepreason.mcp_server:main

      [deepreason.admission.adapters]
      epub = deepreason.admission.adapters_epub:MANIFEST
      pdf = deepreason.admission.adapters_pdf:MANIFEST

  Two groups, four entries. The reader's filter is
  `if line.strip() and not line.startswith("[")` — it SKIPS the headers
  rather than switching on them, so nothing downstream knows which
  group a line came from.

- **The packaging is correct, and is the thing the reader should be
  reading.** `pyproject.toml` declares
  `[project.entry-points."deepreason.admission.adapters"]` (epub, pdf)
  and `[project.scripts]` (deepreason, deepreason-mcp). The wheel
  reproduces both faithfully. Nothing about the build is wrong.

- **The blast radius is everything downstream of line 146.**
  `inspect_wheel` raises before `_check_mcp` is ever called, so the MCP
  tool set and schema sha the smoke exists to pin have not been
  exercised since the smoke last passed. This is why the operator's
  instruction pairs "fix the reader" with "update any stale pins they
  surface": the pins are not known-good, they are unmeasured.

Implicated code (1 site):

- `scripts/wheel_smoke.py`, `inspect_wheel`, the `observed = {...}`
  comprehension and the `observed != required_entries` comparison
  immediately after it (lines ~140-146).

Falsifiable prediction (what `dr-reproduce` must show):

    # Parsing the SAME entry_points.txt bytes with section state, and
    # comparing only the console_scripts group, must yield exactly the
    # two required entries -- while the flat parse yields four.
    flat parse   -> 4 entries, != required
    sectioned    -> {'deepreason = ...', 'deepreason-mcp = ...'} == required
    adapters     -> {'epub = ...', 'pdf = ...'}

If that holds, the fix is confined to how one file is parsed, and no
packaging, no `src/` module and no wheel content needs to move.

Ruled out: **that the adapters group should not be in the wheel.**
Checked — it is declared deliberately in `pyproject.toml` by
`4940b5f7`, whose subject is "Ship the first-party EPUB adapter under
the identical §3a contract", and both targets resolve to real modules
(`deepreason.admission.adapters_epub:MANIFEST`,
`adapters_pdf:MANIFEST`). Removing or renaming the group would make the
smoke green by deleting a shipped capability — fixing the evidence to
suit the instrument, which GOAL.md puts out of scope and the operator
excluded explicitly ("The pyproject packaging is correct").

## Second finding — carried into the fix, not parked

The smoke asserts console entry points by EQUALITY but asserts nothing
at all about the adapters group, so today's defect has a mirror image:
if `4940b5f7`'s adapters silently vanished from the wheel, the smoke
would go green rather than red. A reader that is being taught about
sections should pin both groups, or it trades one blind spot for
another. This is inside the same change site and the same one-line
concern, so it belongs in FIX.md rather than PARKED.md — recorded here
so the widening is visible rather than smuggled in.
