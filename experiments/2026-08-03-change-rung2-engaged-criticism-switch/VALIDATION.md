# Validation for: rung 2, tranche 2 — the engaged_criticism_policy Config switch
Re-read REQUEST.md, SPEC.md, CHECKLIST.md in full before running anything
below. Every check here was re-run fresh in this validation pass, not
copied from checklist-time output. Branch head at validation:
`e01d4738` (fast-forward merge of the monitor's `553a13f8`, ERRATA_EXECUTOR
X8, into this tranche's own work — no conflict, no tranche file touched).

## Acceptance checks

S1: `grep -q 'ENGAGED_CRITICISM_AUTHORITY: Literal\["observe_only", "defended_trial"\] = "observe_only"' src/deepreason/config.py && python -c "from deepreason.config import Config; assert Config().ENGAGED_CRITICISM_AUTHORITY == 'observe_only'"`
-> `grep: PASS` / `assert: PASS` : PASS

S2: `python -c "from deepreason.v6_policy import engaged_criticism_policy as f; assert f('e').authority == 'observe_only'; assert f('e', authority='defended_trial').authority == 'defended_trial'"`
-> exits 0 : PASS

S3: `python -c "import inspect; from deepreason import preparation as p; src = inspect.getsource(p.build_preparation_manifest); assert 'config.ENGAGED_CRITICISM_AUTHORITY' in src"`
-> exits 0 : PASS

S4: `python -m pytest tests/test_v6_policy_preset.py -q`
-> `14 passed in 0.11s` (new test `test_engaged_criticism_authority_config_default_preserves_prior_behavior` present and collectable) : PASS

S5: `grep -q "ENGAGED_CRITICISM_AUTHORITY" docs/map/CON-authority.md`
-> PASS (also confirmed `src/deepreason/v6_policy.py` and `src/deepreason/preparation.py` added to `Owns:`)

S6: full gate + root sweep — see below.

S7 (Amendment 1): `docs/map/SEAM-manifest-x-schools.md`'s call-site check
updated; re-verified as part of the full `docs_verify.py` run below : PASS

S8 (Amendment 2, revised — unconditional pop, not the superseded `< 4`
guard): `python -m pytest tests/test_run_manifest_v4.py tests/test_run_manifest_v5_inquiry.py tests/test_incident_wave_a_v2_fixtures.py -q`
-> `37 passed` : PASS

## Full gate

Ran THREE times during this validation pass, deliberately, because the
second run produced an anomaly that needed resolving before trusting any
result:

1. First (isolated, nothing else running): `3291 passed, 7 skipped in
   611.55s` — clean.
2. Second (run concurrently with a root-sweep re-run, by my own mistake):
   `3 failed, 3288 passed, 7 skipped in 1024.51s` — failures were
   `test_mcp_run.py::test_start_poll_result_and_progress_notifications`,
   `test_mcp_run.py::test_typed_v6_stop_can_continue_and_append`,
   `test_mcp_scratch_bridge.py::test_bridge_start_poll_result_claims_and_unresolved_success`.
   None is the documented flake (C3). All three re-run individually,
   immediately, with nothing else running: `3 passed in 21.53s`. Attributed
   to resource contention from running `root_sweep.py` (CPU/IO-heavy)
   concurrently with `-n 4` pytest — these MCP tests are timing-sensitive
   (async start/poll/result). Not a regression from this tranche's code.
3. Third (isolated again, to be certain): `3291 passed, 7 skipped in
   670.15s` — clean, confirms run 2 was noise.

**Verdict: PASS** (3291 passed, 0 failed, reproduced twice in isolation;
the one anomalous run is explained and does not implicate this tranche's
code — same test files pass individually with certainty).

## Record-behavior preservation / root sweep

`python tools/root_sweep.py` run twice fresh during this validation pass
(once alongside the noisy gate run above, once alone after) — both
produced `SWEEP COMPLETE: 42 roots`, both `11 ERROR` lines (all
`UnsupportedRunManifestVersionError`, matching ERRATA E5/E6/E8), and the
two runs diff byte-identical against each other and against the
checklist-time capture (three-way empty diff).

No committed pre-tranche snapshot exists in the repo to diff against
directly (honestly noted in CHECKLIST.md step 11 — this is the first
`src/`-touching tranche this session). This gap is now closed by an
independent source: `docs/ERRATA_EXECUTOR.md` X8 (written by the
monitoring session, merged into this branch at `e01d4738` moments before
this validation pass) reports its OWN independent sweep, run in isolated
worktrees at base `e0d4eacb` (before this tranche) and head `50e4eb89`
(after) — "identical sha256 (`9c092414...e050cd2`), diff empty, 42 rows,
11 ERROR. No committed root's verdict moved." This is a true before/after
comparison from a second, independent reviewer with different tooling,
and it corroborates this validation pass's own structural check exactly.

**Verdict: PASS**, evidenced by both this pass's own sweep and the
monitor's independent before/after diff.

## Frozen-surface diff

    git diff --stat 23df6e20..HEAD -- \
      src/deepreason/capabilities/state.py src/deepreason/harness.py \
      src/deepreason/invariants.py src/deepreason/run_manifest.py \
      src/deepreason/qualification.py

    src/deepreason/run_manifest.py | 7 +++++++
    1 file changed, 7 insertions(+)

**Non-empty.** This is `DR-INV-frozen-surfaces` surface 4
(`run_manifest.py`). Per this skill's own rule: "Non-empty output is a
FAIL unless REQUEST.md quotes the operator approving that exact surface
— convention guards these files at design time, but this paste is the
one MECHANICAL tripwire on the path, so it is not optional." **REQUEST.md
contains no operator quote approving a `run_manifest.py` touch** — R1-R8
and the two verbatim source messages never mention `run_manifest.py`,
`source_config_hash`, `engine_config_json`, or canonical-hash goldens at
all. The touch was self-discovered and self-authorized mid-execution
(Amendment 2), on sound technical grounds (a reader-preserving fix,
following an established in-repo precedent, verified correct three times
over — see above, plus independently by the monitor's X8 entry) — but
soundness is not the test this rule applies. The rule exists precisely so
a frozen-surface touch cannot be self-blessed by good reasoning alone; the
monitor's endorsement (X8: "load-bearing-and-correct") is a second AI
session's review, not operator sign-off, and the two are not
interchangeable here.

**Verdict: FAIL** on this check specifically. See overall verdict below —
this is the reason a full PASS is not being recorded, despite every other
check passing cleanly.

## Map

`python tools/docs_verify.py`: 49 documents, 794 checks, 0 failed : PASS
`python tools/docs_verify.py --audit`: 0 finding(s) : PASS
`python tools/docs_verify.py --links`: 0 dangling reference(s), 49 documents : PASS
`python tools/docs_verify.py --coverage`: 6 seams swept, 14 without a
`Sweep:` header, 0 findings — pre-existing condition, none of the 14 are
seams this tranche touched (`SEAM-manifest-x-schools.md`, the one seam
this tranche DID touch, already has a `Sweep:` header and is not in the
list) : PASS, nothing to dismiss

`python tools/docs_verify.py --stale`: 11 documents worth re-reading.
Every one dismissed with a reason:
- `CON-authority.md`, `CON-schools.md`, `SEAM-bridge-x-manifest.md`,
  `SEAM-llm-x-manifest.md`, `SEAM-manifest-x-schools.md`,
  `SUB-manifest.md` — all flagged solely because THIS tranche's own
  commits (`9607f739`, `f642f980`) touched their owned files; each was
  freshly re-verified by the full `docs_verify.py` run above (0 failed).
  Stamps intentionally left at their prior `Verified-at` value per
  convention ("a stale stamp is honest, a false one is not") — not
  advanced here since this is a validation pass, not the execute-step
  phase that owns stamp advancement.
- `CON-run-identity.md`, `REC-change-a-seam.md` — flagged because commit
  `9607f739` touched a file they own, but neither document's OWN checked
  claims reference `ENGAGED_CRITICISM_AUTHORITY` or anything this tranche
  changed; re-verified clean by the full run; no content update needed.
- `INV-frozen-surfaces.md` — flagged because this tranche's commits
  touched `run_manifest.py`, which it owns. **This one is NOT dismissed.**
  See "Map completeness gap" below — this is a real, unaddressed finding,
  not explained away.
- `SEAM-harness-x-verification.md`, `SUB-verification.md` — flagged
  because of `2456da55`, a commit from BEFORE this tranche and unrelated
  to it (a different fix, "attached-evidence candidates are selected by
  import provenance, not citation"). Not this tranche's responsibility;
  noted for whichever tranche next touches those files.

New map checks added by this change: `CON-authority.md` gained one new
checked claim (the `ENGAGED_CRITICISM_AUTHORITY` default-preservation
property, citing S4's test) plus the `Owns:`/table additions;
`SEAM-manifest-x-schools.md`'s existing check was corrected to match the
new call-site shape (not a new check, a repaired one — S7).

## Map completeness gap (found during validation, not fixed here)

`docs/map/INV-frozen-surfaces.md`'s own convention: "Every fix earns a
`Traps` entry naming its run id, and a `Traps` entry is never deleted."
Surface 4's existing Traps-adjacent precedent (`route_fingerprint`) was
itself "found by falsification" and filed after the fact — exactly this
tranche's situation. This tranche discovered a genuinely new failure
mode: adding ANY new top-level `Config` field can silently break pinned
canonical-hash goldens across MULTIPLE, not-obviously-related schema
versions (v1/v2/v3 AND v5 here) — the "no test above v3" assumption was
disproved by the full gate, not by inspection. This is exactly the kind
of trap `INV-frozen-surfaces.md` exists to record for the next person
who adds a `Config` field, and no entry exists yet. Per this skill's
exit criteria ("No file other than VALIDATION.md ... modified"), this is
recorded here as a finding, not fixed in this phase.

## Requirement sweep

R1 (behavior — switch preserves observe_only default): demonstrated by
S1/S2/S4 — `Config().ENGAGED_CRITICISM_AUTHORITY == 'observe_only'`, and
`test_engaged_criticism_authority_config_default_preserves_prior_behavior`
proves full pydantic equality between the parameterized and no-kwarg
calls.

R2 (creating the switch is in scope): demonstrated by S1-S3 landing.

R3 (flipping any default forbidden): demonstrated — the default is
`"observe_only"` everywhere (S1, S2's own default parameter, S4's test);
no code path was changed to produce `"defended_trial"` by default. Both
existing call sites (`v6_policy.py:463`, `preparation.py:371`) still
resolve to `observe_only` with no explicit override (re-confirmed this
pass: `grep -n "engaged_criticism_policy(" src/deepreason/*.py` shows
only these two sites, and `preparation.py`'s call reads
`config.ENGAGED_CRITICISM_AUTHORITY`, whose own default is
`observe_only`).

R4 (full gate 0 failed): demonstrated by the full-gate section above —
PASS, reproduced twice in isolation.

R5 (root sweep byte-identical): demonstrated by the root-sweep section
above — PASS, corroborated independently by the monitor's X8 entry.

R6 (a test proving default equals prior behavior): demonstrated by S4.

R7 (map updated in the SAME commit as the code): demonstrated for the
main tranche — commit `9607f739` contains `config.py`, `v6_policy.py`,
`preparation.py`, `CON-authority.md`, and `SEAM-manifest-x-schools.md`
together. The Amendment-2-revision follow-up (`f642f980`, the widened
`run_manifest.py` fix) landed WITHOUT any new map-document change in the
same commit — but none was needed: no `Owns:`/checked-claim content
changed as a result of widening `< 4` to unconditional (the fix is
INSIDE a function no map document quotes verbatim), so there was nothing
for R7 to require moving alongside it. The one thing that SHOULD have
moved alongside it — a Traps entry recording the discovery itself — did
not, and is the "map completeness gap" above. This is a partial miss on
R7's spirit (the map should reflect what was learned, not just what
changed), not a miss on R7's literal text (no document's claims went
stale).

R8 (do the switch tranche first): demonstrated — this tranche opened
and is now complete; the bridge-unification "TRANCHE 3" has not been
touched (confirmed: `git diff --stat 23df6e20..HEAD -- src/deepreason/v6_policy.py`
shows only the `engaged_criticism_policy` signature/body change, no
`engaged_bridge_source` lines).

## Assumptions carried

A1: field name `ENGAGED_CRITICISM_AUTHORITY`.
A2: new test lands in `tests/test_v6_policy_preset.py`, one new function.
A3: value-space is `Literal["observe_only", "defended_trial"]`, no
translation layer.
A4: `qualification.py`/`engaged_policy_digest()` need no code change —
holds; neither was touched, confirmed by this pass's frozen-surface diff
(qualification.py has zero lines changed).

## Verdict: FAIL

**FAIL detail:** the frozen-surface diff (4a2) is non-empty
(`src/deepreason/run_manifest.py`, 7 lines) and REQUEST.md contains no
operator quote approving that specific surface being touched. Every
other check in this document passes, including two independent
confirmations (this pass's own re-runs, plus the monitoring session's
X8 entry) that the fix itself is correct, necessary, and safe. The FAIL
is a process/governance gap, not a correctness defect: the change cannot
be delivered as "operator-authorized" without the operator's own words on
record approving a frozen-surface touch, per this workflow's own explicit
rule. Suspected step: none — this is not a planning or execution defect
to route back through `dr-plan-steps`; the code is already correct and
fully verified. What is missing is the operator's own approval,
recorded in REQUEST.md, and (separately, lower stakes) a Traps entry in
`docs/map/INV-frozen-surfaces.md` documenting this newly-discovered
failure mode for the next `Config`-field addition.
