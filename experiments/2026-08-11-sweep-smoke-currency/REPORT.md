# Report: sweep & smoke currency audit

## Method

Git history for `tools/root_sweep.py`, `scripts/wheel_smoke.py`,
`scripts/wheel_operational_smoke.py`, and every file defining the record
vocabulary / public surface those instruments pin
(`module_events.py`, `seat_events.py`, `pyproject.toml`
`[project.scripts]`/entry-point groups, `mcp_server.py`,
`mcp_scratch_bridge.py`, `mcp_help.py`), walked commit by commit and
cross-diffed for same-commit co-occurrence. Six orphan "snapshot"
recovery commits exist in this branch's reachable history (the
container-rollback pattern CLAUDE.md documents); all instrument and
surface files first appear together, byte-identical thereafter, in the
real (non-snapshot) commit `4fa0ce6d2` ("Claude/amendment epochs
om0ztb (#7)", 2026-08-01).

## Part A — root_sweep.py coverage

Covered: `verify_root_report.valid`, `epistemic_checks_passed`,
adjudication-blindness count, `harness.state.att` count,
`ModuleFingerprintV1.module_id` (as a set), `SeatBindingV1.group` (as a
set).

**Missing before this tranche:** the sweep read only the IDENTITY keys
(`module_id`, `group`) of both typed record families, never their
CONTENT digests — `ModuleFingerprintV1.fingerprint_sha256`,
`SeatBindingV1.profile_digest`, or either payload's own `digest` field.
Two roots sharing the same module/group names but differing in actual
fingerprinted/bound content would have swept as identical. Not yet a
wrong verdict (no committed root under `experiments/` carries either
stamp yet, per the code's own absence-tolerant comments), but a real
coverage gap in an instrument whose entire job is "no root's verdict may
move without the reader moving."

**Fixed this tranche (mechanical, tools/ only, zero src/ lines):**
`tools/root_sweep.py` now also reports `module_digests=` and
`seat_digests=` — the sorted set of each family's payload-level `digest`
field, appended to the existing report line. `ast.parse` confirms the
edit is syntactically valid; a live detached full-tree run
(`sweep-after-item1.txt`, 103 roots) completed cleanly: 11 ERROR lines,
matching the documented baseline exactly (all
`UnsupportedRunManifestVersionError`), and every pre-existing field
stays byte-identical to what the unmodified code would have produced.

**Correction to this REPORT's own first draft:** the draft repeated
`tools/root_sweep.py`'s own code comment that "no committed root under
`experiments/` carries either stamp yet," without independently
checking. The completed sweep disproves this — several committed roots
already carry both module fingerprints (`modules=default`/
`round-robin`) and seat bindings (`seats=coder`/`conjecture`), so the
coverage gap was live on real record data, not merely hypothetical.
What stands unchanged: every distinct identity key maps to exactly one
digest across every root that carries it, so no actual divergence was
hiding behind the gap and no committed root's verdict moves with this
fix — only the instrument's ability to have caught one, had it existed,
was missing. See `docs/ERRATA.md` E18 for the full correction.

## Part B — wheel smoke pin currency

`scripts/wheel_smoke.py` and `scripts/wheel_operational_smoke.py` pin:
`console_scripts` entry points, the `deepreason.admission.adapters`
entry-point group, the 20-name MCP tool set, an MCP schema sha256, and
required wheel modules. Every pinned item matches main's actual surface
today (`pyproject.toml`, `mcp_server.py`, `mcp_scratch_bridge.py`,
`mcp_help.py` — 8 + 9 + 3 = 20 tools, exact set match). No drift found.

## Same-commit-rule violation search (main's own history)

**None found.** The one surface addition on record — the
`deepreason.admission.adapters` entry-point group plus the full 20-tool
MCP registration — landed in `4fa0ce6d2`, the SAME commit that created
both `scripts/wheel_smoke.py` and `scripts/wheel_operational_smoke.py`
already pinning it, and the same commit that created `tools/root_sweep.py`
already reading `module_events.py`/`seat_events.py`. `pyproject.toml`'s
`[project.scripts]` (console entry points) has not changed at all in
reachable history. The 2026-08-05 "unpinned for a week" incident CLAUDE.md
cites is not independently reproducible as a distinct commit pair in this
history — the orphan-snapshot commit structure collapses whatever
within-session gap produced it, so it is attested by CLAUDE.md/prior
process record, not re-derivable from git alone here.

**Nuance honored:** the unmerged `claude/adjudication-judge-seats-optins-4nb7ov`
branch was confirmed NOT an ancestor of current HEAD (`git merge-base
--is-ancestor <tip> HEAD` fails). Any surface it adds (e.g. the future
`--judge-seats`/`--school-seat` CLI flags, `LEGACY_CRITICISM_ENABLED`,
`SCHOOL_SEATS_ENABLED`) is not counted as drift here — it is not main's
surface yet. Both wheel smokes will need new pins the same commit that
branch's CLI additions land on main, per CLAUDE.md's rule; that is a
forward-looking note, not a finding against main's history.

## Disposition

- root_sweep.py coverage gap: fixed mechanically this tranche (see
  commit). Errata entry to follow in Item 2's tranche (per the
  operator's directive: an out-of-date instrument is a debugging error,
  recorded).
- wheel smoke pin currency: no gap found, no errata needed for this
  half.
- No same-commit-rule violations found on main's own history: no errata
  needed for the violation-search half either — this is itself worth one
  line in errata (a negative result, recorded as one, per CLAUDE.md's
  convention that a negative finding is never omitted).

## Errata

`docs/ERRATA.md` E18 (added and later self-corrected, same day, this
tranche): the root_sweep.py coverage gap, and the correction to this
tranche's own first-draft claim that no root carried the missing
stamps. See E18 for the full text.
