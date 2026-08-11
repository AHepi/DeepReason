# Spec for: v1.7 harness spec amendment + docs/INDEX.md (Q1+Q2 approved execution)

Traces: every item cites R/C numbers. Both items were already designed
in `experiments/2026-08-11-spec-drift-measurement/` (DRIFT_TABLE.md,
DOCS_REORG_PROPOSAL.md) and approved by the operator this window; this
SPEC formalizes execution, not new design.

## Items

S1 (R1, C1): new file `docs/harness-spec-v1.7-amendment.md`, in the
same "amends... does not replace or modify" style as v1.4-v1.6 (each
prior amendment's own opening "Status and scope" section is the
template). Documents the six real-on-main, spec-silent surfaces
`DRIFT_TABLE.md` measured: seats/`seat-bindings.v1` (the typed schema,
`seat_events.py`), `conjecturer.turn.v7` (wire contract, `llm/wire.py`/
`run_manifest.py`), `candidate_checker` (`llm/wire.py`/`oracle.py`),
school-seat routing (`resolve_school_role_lease`, `llm/firewall.py`),
adjudication-blindness/blind-same-model-judge structure
(`verification/report.py`), config referee (`verification/report.py`/
`llm/roles.py`). Explicitly excludes `LEGACY_CRITICISM_ENABLED`/
`SCHOOL_SEATS_ENABLED` (adjudication-branch-only, not real on main —
re-confirmed this tranche, see M1) per R1's own scope.
accept: `test -f docs/harness-spec-v1.7-amendment.md`; the file's
opening section states "amends" and explicitly does not modify v1.3-v1.6
(grep for "does not" near "amend"); each of the six surfaces appears at
least once with a concrete file/symbol citation (not prose-only).

S2 (R1, C1): same commit as S1 — update `CLAUDE.md`'s directory-map
line (line 311, `docs/ specs (harness v1.3 + v1.4/v1.5/v1.6 ...`) to
also list v1.7, in the SAME style E13's own fix used ("v1.3 +
v1.4/v1.5/v1.6/v1.7 amendments — read ALL amendments"). Prevents
immediately reproducing E13 (a stale spec listing) the moment v1.7
exists.
accept: `grep -q "v1.4/v1.5/v1.6/v1.7" CLAUDE.md`.

S3 (R2, C2): new file `docs/INDEX.md`, a top-level navigation page
distinct from `docs/map/INDEX.md`, per `DOCS_REORG_PROPOSAL.md`'s
proposed reorganization step 1: sections for Reference (→ `docs/map/`,
the spec series including v1.7), Explanation (→ per-experiment
`RESULTS.md`, pointing OUT to `experiments/*/RESULTS.md` rather than
duplicating), Decisions (→ `docs/proposals/`), Corrections (→
`docs/ERRATA.md`/`ERRATA_EXECUTOR.md`, named as their own genre per
the proposal's own finding that they fit no standard cleanly). Adds
ONLY this one file; moves nothing (C2).
accept: `test -f docs/INDEX.md`; it links (relative path, exact
strings) to `docs/map/INDEX.md`, `docs/harness-spec-v1.3.md`,
`docs/ERRATA.md`, `docs/ERRATA_EXECUTOR.md`, `docs/proposals/`; `git
diff --stat` shows zero renames (no `R` status lines) for this commit.

## Assumptions (operator may override)

A1: v1.7's own internal section numbering/headers follow v1.6's
established pattern (Status and scope → dated technical sections) —
smallest-reasonable reading of "same style," no operator words needed
to pick a formatting convention already established four times over.

A2: `docs/INDEX.md`'s content is a genuinely NEW navigational page
(links + one-line descriptions), not a copy or summary of any existing
document's content — this keeps it from becoming a second place any of
the underlying documents' facts could drift out of sync with, which is
exactly what R2/the operator's original "messy repo" complaint was
about.

## Out of scope (explicit)

- Q3 (per-role qualification scope) and Q4 (intake tool default
  scope) — explicitly deferred by the operator's own words ("Leave
  three and four for another window"); zero touches to
  `experiments/2026-08-11-change-qualification-messages-s4b/` or any
  `src/` file this tranche.
- Any file MOVE or rename under `docs/` (`DOCS_REORG_PROPOSAL.md`'s
  steps 3-4, standalone-report relocation and ADR-style renaming) —
  the proposal itself recommends these as a separate future tranche,
  not bundled with the index (C2).
- Documenting `LEGACY_CRITICISM_ENABLED`/`SCHOOL_SEATS_ENABLED` in
  v1.7 — explicitly deferred to a later amendment per R1's own scope,
  gated on the adjudication branch's merge (re-verified still unmerged
  this tranche, M1).

## Frozen-surface contact forecast

None expected, checked against `docs/map/INV-frozen-surfaces.md`'s five
named surfaces plus `route_fingerprint`: S1/S2 touch only
`docs/harness-spec-v1.7-amendment.md` (new) and `CLAUDE.md` (prose);
S3 touches only `docs/INDEX.md` (new). None of `capabilities/state.py`,
`harness.py`, `invariants.py`, `run_manifest.py`, `qualification.py`,
`llm/firewall.py` is in this tranche's target file list at all — no
`src/` file is touched, so contact is impossible by construction, not
merely unlikely.

## Blast-radius census

`docs/harness-spec-v1.3.md`: 4 hits outside this tranche's own files
(`src/deepreason/verification/report.py:1033`, `src/deepreason/
cli/main.py:1097`, `tests/test_adjudication_blindness.py:8`,
`scripts/e31_benchmark/sealed.py:88`) — all cite v1.3 specifically
(section 11.3, per the test's own docstring) — MUST NOT MOVE; S1 does
not edit v1.3, only adds a new v1.7 file, so none of these four is
touched.

`CLAUDE.md` line 311 (`docs/ specs (harness v1.3 + v1.4/v1.5/v1.6...`):
1 hit, the line itself — EXPECTED TO MOVE (S2's own target, adding
"/v1.7").

`docs/INDEX.md`: 0 hits in `tests/`/`docs/map/` (grep confirmed,
new file, nothing references it yet) — no census entry to classify.

`v1.7`/`v1\.7` anywhere in `tests/`, `docs/map/`, `CLAUDE.md`: 0 hits
before this tranche — confirms no pre-existing reference this tranche
could silently satisfy or contradict.

## Measurements

M1: `git merge-base --is-ancestor $(git ls-remote origin
claude/adjudication-judge-seats-optins-4nb7ov | cut -f1) HEAD; echo $?`
→ re-run this tranche, still non-zero (not an ancestor) — the
adjudication branch remains unmerged, confirming R1's exclusion of
`LEGACY_CRITICISM_ENABLED`/`SCHOOL_SEATS_ENABLED` is still correct as
of execution time, not just at design time.

M2: `grep -n "harness v1.3" CLAUDE.md` → line 311 confirmed unchanged
since `DRIFT_TABLE.md`'s design-time read; S2's edit target is current.

## Budget

S1: ~90-130 lines (a new amendment file, six surfaces, v1.6-comparable
length per surface documented). S2: ~1 line (CLAUDE.md line 311 edit).
S3: ~40-60 lines (a navigation page, six sections, a few lines each).

    python3 -c "print(sum([130, 1, 60]))"  # -> 191

Total: ~191 lines, 2 commits (S1+S2 together, same commit per the map-
moves-with-code convention since S2 is CLAUDE.md's own spec-listing
line reacting to S1's new file; S3 separately, since it is an
independent artifact with no shared file). Frozen surfaces touched:
none.

Rubric: 6/6 yes — every R has a spec item with a machine-decidable
accept (R1→S1+S2, R2→S3, R3→Out of scope, explicit); blast-radius
census pasted and every hit classified; frozen-surface contact
forecast recorded (none, verified against all 5+1 surfaces); no named
mechanism needed tracing (this tranche invents no new mechanism, it
formalizes prior design); measurements pasted for the two load-bearing
claims (branch still unmerged, CLAUDE.md line unchanged); nothing
untraceable to an R/C number.
