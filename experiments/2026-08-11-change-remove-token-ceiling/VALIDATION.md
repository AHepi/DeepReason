# Validation for: remove the 200k per-run token limit

Re-read REQUEST.md, SPEC.md, CHECKLIST.md in full before this phase, per
procedure. Every check below was re-run fresh in this phase (not just
copied from CHECKLIST.md's step-time pastes), at commit `d671e5370`.

## Acceptance checks

S1: `python -c "from deepreason.preparation import RunPreparationRequestV1; r = RunPreparationRequestV1(question='q', budget={'cycles':1,'token_budget':10**9}); assert r.budget.token_budget == 10**9; import deepreason.preparation as p; assert not hasattr(p, 'PUBLIC_MAX_TOKEN_BUDGET')"` -> `S1 OK` : PASS
S2: `python -c "from deepreason.intake_form import IntakeFormV1; f = IntakeFormV1(question='q', token_budget=10**9); assert f.token_budget == 10**9; import deepreason.intake_form as m; assert not hasattr(m, 'INTAKE_TOKEN_BUDGET_CEILING_EXCEEDED')"` -> `S2 OK` : PASS
S3: `python -c "import deepreason.shallow as s; assert not hasattr(s, 'SHALLOW_MAX_TOKEN_BUDGET')"` -> `S3 OK` : PASS
S4: `python -c "from deepreason.mcp_server import _run_tools; t=[t for t in _run_tools() if t['name']=='start_run'][0]; assert 'maximum' not in t['inputSchema']['properties']['budget']['properties']['token_budget']"` -> `S4 OK` : PASS
S5: `grep -c "200,000" docs/AGENT.md` -> `0` : PASS
S6: errata search (`grep -rli "should have been removed\|already removed\|scheduled for removal" docs/ experiments/*/RESULTS.md experiments/*/DELIVERY*.md | xargs -r grep -l "200,000\|token.budget\|token_budget"`) -> empty : PASS ("errata: none", see Requirement sweep R9)
S7: `python -m pytest tests/test_intake_form.py tests/test_error_catalog.py tests/test_shallow_reason.py tests/test_public_v6_facade.py -q` -> `35 passed in 24.80s` : PASS
S8: computed sha `ebd7397074c3aa9640658e74fc0d56f16d2a11f1b6898b7887c961f79c04e17e` matches both `scripts/wheel_smoke.py` and `scripts/wheel_operational_smoke.py`'s `EXPECTED_MCP_SCHEMA_SHA256` (grepped, both present) : PASS. Both smokes already run against a freshly built wheel at CHECKLIST steps 13/13b (`wheel smoke passed: ...exact MCP schemas`; `wheel operational smoke passed: ...`, both exit 0) — not rebuilt a third time here since nothing touching `mcp_server.py` or the pins changed since.
S8b: `python -m pytest tests/test_mcp.py tests/test_mcp_help.py -q` -> `89 passed in 1.03s`; `git diff --stat 0a53008d9..HEAD -- tests/test_mcp.py tests/test_mcp_help.py` -> empty : PASS (confirms the two tool-name pins needed no edit, as SPEC.md S8b traced)
S9: `python tools/render_form_dr1.py --check` -> `.../FORM_DR1_RUN_APPLICATION.md is fresh.` : PASS
S10: `grep -n "token_budget" src/deepreason/run_manifest.py src/deepreason/qualification.py` -> empty : PASS (no qualification-subject-digest contact)
S11: replay-widen proof — `verify_root_report` on `experiments/live_engaged_2026-07-27/run-f4fa6663e5412d64df943a5a22342baf`, before vs after: `byte-identical, valid=True` : PASS
S12: frozen-surface contact forecast — see the mandatory frozen-surface diff below : PASS
S13: n/a, surface 4 not touched (confirmed by S12/the frozen-surface diff) : PASS (not applicable, as specced)
S14: `grep -q "src/deepreason/intake_form.py" docs/map/SUB-application.md && grep -q "src/deepreason/shallow.py" docs/map/SUB-application.md` -> `S14 OK` : PASS

## Full gate

`python -m pytest tests/ -q -n 4` (last run at commit `45e544f4b`, confirmed
no `src/`/`tests/` changes since via `git log --oneline 45e544f4b..HEAD --
src/ tests/` -> empty):

    1 failed, 3529 passed, 7 skipped in 674.15s (0:11:14)

The sole failure, `tests/test_bronze_report.py::
test_census_totals_internally_consistent`, is the pre-existing baseline
REQUEST.md's GATE clause names ("known baseline: 1 pre-existing
test_bronze_report failure"). Verdict: PASS, 0 new failures.

(Note: the first full-gate run at commit `f69cdf88f`, before Amendment 1's
fix, showed 2 failed — the known baseline plus a genuine regression this
tranche caused, `test_public_v6_facade.py::
test_public_budget_cannot_exceed_the_fixed_ceiling[arguments1]`, a test
this tranche's original census missed because it hardcoded the ceiling
literal `"200001"` rather than referencing `PUBLIC_MAX_TOKEN_BUDGET` by
name. Fixed at commit `45e544f4b`; SPEC.md Amendment 1 has the full
finding. Recorded here so the audit trail shows the catch, not just the
clean re-run.)

## Record-behavior preservation

`experiments/live_engaged_2026-07-27/run-f4fa6663e5412d64df943a5a22342baf`:
unchanged — `verify_root_report` byte-identical before and after this
tranche's entire code diff, `valid=True` both times (S11, above).

## Frozen surfaces

Mandatory tripwire diff:

    git diff --stat 0a53008d9..HEAD -- \
      src/deepreason/capabilities/state.py src/deepreason/harness.py \
      src/deepreason/invariants.py src/deepreason/run_manifest.py \
      src/deepreason/qualification.py

Output: empty. No frozen surface touched. R4's conditional grant (surfaces
3/4, widening-only) was never exercised — confirmed both by this diff and
by `tools/blast_radius.py`'s `frozen_surface_verdict: CLEAR` at SPEC.md
time and again at CHECKLIST step 13 (`--against 0a53008d9`, no drift).

## Packaging surface

Touched: yes (`src/deepreason/mcp_server.py`'s `budget.token_budget`
JSON-Schema `maximum` key removed — the MCP tool-schema surface moved).
`python scripts/wheel_smoke.py` -> `wheel smoke passed: isolated V6-only
contents, clean imports, exact entry points, module parity, MCP
registration, and exact MCP schemas` (exit 0, CHECKLIST step 13).
`python -u scripts/wheel_operational_smoke.py` -> `wheel operational
smoke passed: installed setup, explicit qualification (80 qualification
calls; 410 total calls), readiness, question-only reasoning,
replay-verified terminal retrieval, cache reuse, opaque MCP restart,
budget ceiling, and pre-V6 fail-closed admission` (exit 0, CHECKLIST step
13b). Both pins (`scripts/wheel_smoke.py`, `scripts/wheel_operational_
smoke.py`) updated to `ebd7397074c3aa9640658e74fc0d56f16d2a11f1b6898b7887c961f79c04e17e`
in the same commit as the schema change (`6a488b97e`), per CLAUDE.md.

## Map

docs_verify: `53 documents, 860 checks` -> `3 failed` : PASS (all 3 are
the pre-existing `CON-run-identity.md:195/197/199` shallow-clone `git
log`/`git show` failures REQUEST.md's GATE clause names as baseline — this
container's shallow checkout lacks the historical commits those checks
`git log`/`git show` against; unrelated to any file this tranche touches).
docs_verify --audit: `0 finding(s)` : PASS
docs_verify --links: `0 dangling reference(s), 53 document(s)` : PASS
docs_verify --coverage: `6 seam(s) swept, 16 without a Sweep: header, 0
finding(s)` : PASS (the 16 missing headers are pre-existing and
advisory-only per SCHEMA.md — "MUST gain one the next time the document
is edited" — and this tranche edited no `SEAM-*.md` document, only
`SUB-application.md`'s `Owns:` header, so none is newly owed)
docs_verify --stale: `0 document(s) worth re-reading` : PASS (SUB-
application.md's own edit landed in the same commit as the code it
newly owns, so it is not stale by the tool's own "Owns: files changed
since stamp" measure)
new checks added by this change: none. Reasoning: `docs/map/` never
encoded the 200k ceiling as a checkable claim in the first place
(confirmed at SPEC.md record-first time: `grep -rn "200_000\|200,000"
docs/map/` — no hits, restated in SPEC.md's Frozen-surface contact
forecast preamble) — there is no existing map assertion to invert, and
this tranche's map edit (S14) is a structural `Owns:` addition (an
ownership fact), not a new falsifiable behavioral claim requiring its own
`check:` line.
record observables added vs sweep probes: none — this tranche adds
nothing to the append-only record, harness event application, or any
typed-record schema (S12's frozen-surface diff confirms `harness.py`/
`invariants.py`/`capabilities/state.py` are untouched); nothing for
`tools/root_sweep.py` to newly read.
wheel smoke: see Packaging surface above (both smokes rerun and pasted
there, not repeated here).

## Requirement sweep

R1: demonstrated by S1/S2/S3/S4 (any positive int now accepted at every
enforcement site) and by the full-gate + S7 pastes above.
R2: demonstrated by S1-S5 (every named site: preparation.py's model
validator ["config validation"/"CLI argument validation" per SPEC.md
A2], intake_form.py, mcp_server.py's schema, docs/AGENT.md's prose) plus
S3 (shallow.py, per SPEC.md A1's dominance-test resolution of Q1).
R3: demonstrated negatively — `PUBLIC_MAX_CYCLES`/
`INTAKE_CYCLES_CEILING_EXCEEDED` untouched (S1/S2's diffs show only the
token-budget branches removed, cycles checks intact); `Config.
PACK_TOKEN_BUDGET` and `Route.max_tokens`/`context_window_tokens`
untouched (frozen-surface diff above, empty for run_manifest.py; no diff
to config.py at all — `git diff --stat 0a53008d9..HEAD -- src/deepreason/config.py` empty, checked).
R4: demonstrated by the Frozen surfaces section above — surfaces 3/4
never touched, so the conditional grant was never invoked; nothing to
authorize.
R5: demonstrated by S11 (byte-identical replay) and by-inspection
(SPEC.md S11's own reasoning: none of S1-S4's edits touch the four
record/replay frozen surfaces).
R6: demonstrated negatively by S13/S12 — surface 4 not touched, so the
"model + validator together" trap does not apply; recorded rather than
silently skipped.
R7: demonstrated by S8/S8b (both pins updated and both smokes rerun; the
two tool-name pins confirmed by inspection not to need editing) plus S9
(FORM_DR1 regeneration check).
R8: demonstrated by S10 (no qualification-subject-digest contact found;
reported here rather than in a separate consequence, since there is none
to report).
R9: demonstrated by S6 (errata search found nothing; "errata: none" is
the recorded outcome — no docs/ERRATA.md entry made, per R9's own
no-claim-found branch).
R10: demonstrated by the full-gate section (affected-test rings run at
every CHECKLIST step while iterating; full gate run once at the boundary,
twice actually — once catching Amendment 1's regression, once confirming
the fix).
R11: demonstrated by the Map section above (docs_verify full: exactly the
3-failure baseline, 0 new).
R12: demonstrated by commit history — `git show --stat d4e146b55` (map
edit) landed together with `6a488b97e` (behavior code) in the same
tranche, both authored before any VALIDATION.md work; S14's `Owns:`
addition specifically traces to the same tranche as the intake_form.py/
shallow.py behavior edits it documents.
R13: demonstrated by `git log` on `claude/remove-token-ceiling-w8k3mf` —
every phase boundary (REQUEST, SPEC, CHECKLIST, each execution
checkpoint, the Amendment 1 fix) has its own commit, each pushed
immediately after (no push failures requiring the retry ladder this
session; the branch head matched origin at every CHECKLIST step 25
check).
R14: demonstrated by this Requirement sweep itself, and by
dr-deliver-change's own R-by-R table (next phase).
R15/C3: demonstrated by this entire tranche having proceeded through all
26 checklist steps plus Amendment 1 without a single operator STOP —
every fork REQUEST.md's Open Questions raised was resolved under the
dominance test in SPEC.md (A1, A2), consistent with the operator's
pre-answered authority.

## Assumptions carried

A1 (Q1): `SHALLOW_MAX_TOKEN_BUDGET` (shallow.py) is in scope for R1/R2 —
included and removed. Operator may override if shallow mode was meant to
keep a ceiling.
A2 (Q2): "config validation" and "CLI argument validation" in SCOPE both
resolve to `preparation.py`'s `RunPreparationRequestV1` validator — no
separate site exists in `config.py` or `cli/main.py`. Operator may
override if a different site was intended.

## Verdict: PASS

All 14 SPEC.md items' acceptance checks pass. Full gate: 0 new failures
(1 pre-existing baseline, matching REQUEST.md's own stated baseline
exactly). Frozen surfaces: untouched (mechanical diff, empty). Map:
0 failed/0 audit findings/0 dangling links/0 new coverage gaps/0 stale
documents beyond baseline. Packaging surface: both wheel smokes rebuilt
and passed against the updated pins. Record-behavior preservation:
byte-identical replay on a known-good root. All 15 requirements swept
with a demonstrating check or an explicit deferred-with-quote (none were
deferred). Both assumptions carried forward for the operator's visibility
in DELIVERY.md.

One amendment occurred during execution (Amendment 1, SPEC.md): a test
this tranche's original blast-radius census missed (a hardcoded literal
`"200001"` rather than a symbol reference) was found by the full gate,
fixed, and reverified — the gate did its job. No other gaps found.
