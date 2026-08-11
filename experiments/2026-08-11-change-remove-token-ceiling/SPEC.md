# Spec for: remove the 200k per-run token limit
Traces: every item cites R/C numbers. Untraceable items are bugs.

## Record-first findings (before design)

Grep/read sweep across `src/`, `docs/`, `tools/`, `tests/` (excluding
`experiments/*/runs/` — committed run data, never a site to edit) located
every enforcement site of a 200,000-token per-run ceiling:

1. `src/deepreason/preparation.py:96` — `PUBLIC_MAX_TOKEN_BUDGET = 200_000`,
   enforced in `RunPreparationRequestV1._public_budget_is_finite_and_bounded`
   (a `model_validator`). This is the ceiling for the public `deepreason
   reason` / MCP `start_run` path — the one SCOPE's "config validation" and
   "CLI argument validation" phrases both resolve to (see A2).
2. `src/deepreason/intake_form.py:35,164-174` —
   `INTAKE_TOKEN_BUDGET_CEILING_EXCEEDED` and
   `IntakeFormV1._token_budget_within_ceiling`, importing and re-enforcing
   the same `PUBLIC_MAX_TOKEN_BUDGET`. Named explicitly in SCOPE.
3. `src/deepreason/shallow.py:28,81-85` — a SEPARATE constant,
   `SHALLOW_MAX_TOKEN_BUDGET = 200_000`, enforced in `run_shallow_question`.
   Not named in SCOPE's site list but is the same shape of ceiling on the
   same quantity — resolved by A1 below.
4. `src/deepreason/mcp_server.py:49-59` — `_run_tools()` republishes
   `PUBLIC_MAX_TOKEN_BUDGET` as `"maximum"` in the MCP tool schema for
   `budget.token_budget`. Not itself an enforcement site (enforcement is
   `preparation.py`'s validator, reached downstream via
   `RunPreparationRequestV1` in `_start_run`, confirmed by reading the call
   path) but a site that STATES the ceiling to callers, per SCOPE's "any
   doc/map/check that states the ceiling."
5. `docs/AGENT.md:82` — prose: "with fixed public ceilings of 12 cycles and
   200,000 tokens."

Investigated and confirmed NOT sites (record beats the prose prediction,
per `dr-ask-the-right-question`):

- `src/deepreason/run_manifest.py` — `budget_policy` is a free-form
  `dict[str, Any]` with no fixed ceiling logic anywhere in the file
  (`grep -n "token_budget\|budget_policy" src/deepreason/run_manifest.py`
  shows only the free dict field and its pass-through). Frozen surface 4 is
  not touched. R4's conditional grant is therefore not invoked.
- `src/deepreason/invariants.py`, `capabilities/state.py`, `harness.py` —
  no token-ceiling logic; frozen surfaces 1-3 are not touched.
- `src/deepreason/config.py` — no per-run token ceiling (only
  `PACK_TOKEN_BUDGET = 2500`, a per-CALL prompt-rendering budget, explicitly
  OUT of scope per R3 "per-call completion caps ... are out of scope").
- CLI argument parsing (`cli/main.py`) — `deepreason reason --token-budget`
  and MCP `start_run` both pass straight through to
  `RunPreparationRequestV1` (traced: `cli/main.py:2227-2234`,
  `mcp_server.py:519-565`); there is no independent CLI-level ceiling check.
  The internal/host-only `deepreason run --token-budget` and `deepreason
  continue --token-budget` commands are ALREADY unbounded today (default
  `"unlimited"`, passed straight to `run_scheduler`/`ContinueTextRunIntentV1`
  with no upper-bound validator) — confirmed by reading
  `cli/main.py:440-465,2426-2444` and `application/models.py:34-49`
  (`RunBudgetIntentV1` only rejects negative values or non-positive
  `cycles`, and permits the literal `"unlimited"`). Nothing to remove there.

## Items

S1 (R1, R2). `src/deepreason/preparation.py` | before:
`PUBLIC_MAX_TOKEN_BUDGET = 200_000` exists and
`_public_budget_is_finite_and_bounded` rejects `token_budget >
PUBLIC_MAX_TOKEN_BUDGET` | after: the constant and its upper-bound branch are
removed; the validator keeps requiring `token_budget` to be a finite int
`>= 1` (the "must be a real number" half of R1's "any positive budget") and
keeps the untouched `cycles <= PUBLIC_MAX_CYCLES` check (R3: only the token
ceiling goes). `PUBLIC_MAX_TOKEN_BUDGET` is removed from `__all__`.
    accept: `python -c "from deepreason.preparation import RunPreparationRequestV1; r = RunPreparationRequestV1(question='q', budget={'cycles':1,'token_budget':10**9}); assert r.budget.token_budget == 10**9"` exits 0; `python -c "import deepreason.preparation as p; assert not hasattr(p, 'PUBLIC_MAX_TOKEN_BUDGET')"` exits 0.

S2 (R1, R2). `src/deepreason/intake_form.py` | before:
`INTAKE_TOKEN_BUDGET_CEILING_EXCEEDED` and `_token_budget_within_ceiling`
reject `token_budget > PUBLIC_MAX_TOKEN_BUDGET`, importing
`PUBLIC_MAX_TOKEN_BUDGET` from `preparation.py` | after: both removed; the
field's own `Field(gt=0)` constraint is the only positivity requirement
left (unchanged, already true today). Import narrows to `PUBLIC_MAX_CYCLES`
only (still used by the untouched cycles-ceiling validator).
    accept: `python -c "from deepreason.intake_form import IntakeFormV1; f = IntakeFormV1(question='q', token_budget=10**9); assert f.token_budget == 10**9"` exits 0; `python -c "import deepreason.intake_form as m; assert not hasattr(m, 'INTAKE_TOKEN_BUDGET_CEILING_EXCEEDED')"` exits 0.

S3 (R1, R2, A1). `src/deepreason/shallow.py` | before:
`SHALLOW_MAX_TOKEN_BUDGET = 200_000`, `run_shallow_question` rejects
`not 1 <= budget <= SHALLOW_MAX_TOKEN_BUDGET` | after: constant removed;
guard narrows to `budget < 1` (positive-only, same shape as S1/S2).
Removed from `__all__`.
    accept: `python -c "import deepreason.shallow as s; assert not hasattr(s, 'SHALLOW_MAX_TOKEN_BUDGET')"` exits 0; `python -c "from deepreason.shallow import run_shallow_question; import pytest" ` plus CHECKLIST-level test at S7.

S4 (R2). `src/deepreason/mcp_server.py` | before: `_run_tools()`'s `budget`
schema sets `"maximum": PUBLIC_MAX_TOKEN_BUDGET` on `token_budget` | after:
that key is removed (schema keeps `"minimum": 1`, no upper bound, matching
S1's actual enforcement). Import narrows to `PUBLIC_MAX_CYCLES` only.
    accept: `python -c "from deepreason.mcp_server import _run_tools; t=[t for t in _run_tools() if t['name']=='start_run'][0]; assert 'maximum' not in t['inputSchema']['properties']['budget']['properties']['token_budget']"` exits 0.

S5 (R2). `docs/AGENT.md:82` | before: "with fixed public ceilings of 12
cycles and 200,000 tokens." | after: states the surviving cycles ceiling
only and says plainly there is no token-budget ceiling, so the doc does not
describe removed behavior.
    accept: `grep -c "200,000" docs/AGENT.md` → `0`.

S6 (R9, errata check). Search performed across `docs/TOKEN_ECONOMY.md`,
every tranche `DELIVERY*.md`/`RESULTS.md` under `experiments/`, and
`docs/proposals/` for any claim that the 200k ceiling was already removed
or scheduled for removal
(`grep -rli "should have been removed\|already removed\|scheduled for
removal" docs/ experiments/*/RESULTS.md experiments/*/DELIVERY*.md`, plus
targeted reads of the 6 files matching a loose "ceiling"/"200,000" pattern
in `docs/`). No committed document makes that claim — the closest hit
(`docs/MINI_STRESS_REPORT.md`) is about an unrelated judge-list removal.
    accept (already run, pasted below): "errata: none" — recorded in
    DELIVERY.md per R9's own instruction for the no-claim-found branch; no
    `docs/ERRATA.md` edit.

S7 (R2, R7 consumer fixups — traced via S8's blast-radius census).
Update every test/catalog consumer of the removed constants so the gate
stays green:
  - `src/deepreason/error_catalog.py`: remove the
    `INTAKE_TOKEN_BUDGET_CEILING_EXCEEDED` `_entry(...)` block from
    `CATALOG` (dead code once S2 removes the only raise site).
  - `tests/test_intake_form.py`: drop the
    `INTAKE_TOKEN_BUDGET_CEILING_EXCEEDED` import and
    `test_token_budget_over_ceiling_raises`; replace
    `test_token_budget_at_ceiling_is_fine` with a regression asserting a
    large (formerly-over-ceiling) budget is now accepted.
  - `tests/test_error_catalog.py`: drop `INTAKE_TOKEN_BUDGET_CEILING_EXCEEDED`
    from the import and the `real` set; `test_catalog_covers_47_entries`
    becomes 46 (S7's catalog-entry removal is the only entry-count change
    in this tranche).
  - `tests/test_shallow_reason.py`: replace the assertion that
    `run_shallow_question("q", token_budget=10**9)` raises
    `SHALLOW_BUDGET_INVALID` with one asserting it is now accepted (mocked
    endpoint, matching the file's existing fixture pattern).
    accept: `python -m pytest tests/test_intake_form.py tests/test_error_catalog.py tests/test_shallow_reason.py -q` → `0 failed`.

S8 (R7). Blast-radius census + MCP schema-sha pins (`tools/blast_radius.py`
does not fingerprint schema CONTENT, only symbol-name references — see
Blast-radius census section below for why this item exists despite an
empty `wheel_smoke_pins` census). `scripts/wheel_smoke.py` and
`scripts/wheel_operational_smoke.py` each pin
`EXPECTED_MCP_SCHEMA_SHA256 = sha256(json.dumps(tools/list response,
sort_keys=True, separators=(",", ":")))`. S4 changes that response
(removing one schema key from one tool), so both constants move. Update
both to the freshly computed value in the SAME commit as S4 (CLAUDE.md:
"any commit changing that surface updates the pins and re-runs the smoke
in the same commit").
    accept: `python scripts/wheel_smoke.py` and `python -u
    scripts/wheel_operational_smoke.py` both exit 0 against a freshly
    built wheel (post S1-S4 code).

S8b (R7, named-mechanism check — see dr-spec-change step 2). SCOPE names
"ALL FOUR pin locations" including `tests/test_mcp.py::SUPPORTED_TOOLS` and
`tests/test_mcp_help.py::SUPPORTED_TOOL_NAMES`. By inspection (confirmed
against `experiments/2026-08-11-change-qualification-messages-s4b/
DELIVERY_ii.md`'s own account of "the four-pin lesson") these two pin the
MCP TOOL NAME SET, not schema content — they change only when a tool is
added or removed, never when an existing tool's `inputSchema` gains or
loses a property. This tranche adds/removes no tool. The named mechanism
("all four pins move together") does not reach this change; the PROPERTY
SCOPE actually wants — every pin that would go stale, updated — is
delivered by S8's two schema-sha pins alone. Recorded here rather than
silently skipped.
    accept: `python -m pytest tests/test_mcp.py tests/test_mcp_help.py -q`
    stays `0 failed` with zero edits to either file.

S9 (R7). `tools/render_form_dr1.py --check` — confirms `FORM_DR1_RUN_
APPLICATION.md`'s generated Parts A/B1/D are still fresh. `IntakeFormV1`'s
`token_budget` field's `description=` text ("D3: token budget.") is
untouched by S2 (only the validator function is removed), so no
regeneration is expected — this item runs the check to prove that rather
than assume it.
    accept: `python tools/render_form_dr1.py --check` exits 0.

S10 (R8). Qualification-subject-digest impact investigation. `token_budget`
is a per-run scheduler loop bound consumed by `run_scheduler`/
`TEXT_RUN_SERVICE.start`, never entering `compile_run_manifest` or
`qualification_subject_payload` — confirmed:
`grep -n "token_budget" src/deepreason/run_manifest.py
src/deepreason/qualification.py` → no hits in either file. None of S1-S4's
five touched files (`preparation.py`, `intake_form.py`, `shallow.py`,
`mcp_server.py`, `error_catalog.py`) is imported by `run_manifest.py` or
`qualification.py` (confirmed by the blast-radius census's own empty
`consumers.qualification_digest: []`). Conclusion for DELIVERY.md: no
qualification subject digest drift, no requalification consequence.
    accept: `grep -n "token_budget" src/deepreason/run_manifest.py
    src/deepreason/qualification.py` → empty output (already run, pasted
    above).

S11 (R5). Replay-widen proof. By-inspection: none of S1-S4's edits touch
`harness.py`, `invariants.py`, `capabilities/state.py`, or `run_manifest.py`
— the four record/replay frozen surfaces (`INV-frozen-surfaces.md`
surfaces 1-4) are entirely outside this tranche's target-file list (S12).
The touched code (`preparation.py`'s pre-run intake validator,
`intake_form.py`, `shallow.py`, `mcp_server.py`'s advertised schema) all
execute strictly BEFORE a run root exists (request validation, not record
writing or replay reading) and are never invoked by `verify_root`. Measured
proof, not just by-inspection: a targeted `verify_root_report` on one
committed, replay-valid root, run once before this tranche's code changes
and once after, must be byte-identical.
    accept: `python -c "from deepreason.verification.report import
    verify_root_report; import json; print(json.dumps(verify_root_report(
    '<a committed run root under experiments/>'), sort_keys=True))"` run
    before and after S1-S4, diffed byte-identical (CHECKLIST step; root
    chosen at execution time from a small ≤200k-budget committed root).

S12 (R4). Frozen-surface contact forecast — see dedicated section below.
`tools/blast_radius.py` reports `frozen_surface_verdict: CLEAR`,
`frozen_surface_contacts: []`, `frozen_adjacent_contacts: []` for the four
target files (`preparation.py`, `intake_form.py`, `shallow.py`,
`mcp_server.py`). Surfaces 3 and 4 are NOT touched; R4's conditional grant
to touch them is therefore not exercised by this tranche.

S13 (R6). Not applicable. Surface 4 (`run_manifest.py`'s Pydantic models
AND their validators) is not a target file (S12), so the "change the model
and its validator together" trap does not apply here — recorded so the
requirement is not silently unaddressed.

S14 (R2, map preflight follow-through). Map gap closure (found during map
preflight, recorded in REQUEST.md): `src/deepreason/intake_form.py` and
`src/deepreason/shallow.py` appear in no map document's `Owns:` list.
Add both to `docs/map/SUB-application.md`'s `Owns:` header (closest fit:
that document already owns `cli/` and `application/`, the direct siblings/
callers of both files — `intake_form.py` is the MCP-facing validation twin
of the CLI's own intake path, `shallow.py` is a `cli/main.py`-invoked
reduced-engine entry point). Per `SCHEMA.md`'s change rule this is a
structural `Owns:` addition with no new claim/check, so `Verified-at:` is
NOT advanced (honest-stamp rule: only advance it for claims actually
re-checked).
    accept: `grep -q "src/deepreason/intake_form.py" docs/map/SUB-application.md && grep -q "src/deepreason/shallow.py" docs/map/SUB-application.md` exits 0; `python tools/docs_verify.py --links` still exits 0.

## Process obligations (no separate code item; enforced at CHECKLIST/commit time)

R10: affected-test ring while iterating (S7/S8's own accept commands),
full gate once at the CHECKLIST boundary.
R11: `python tools/docs_verify.py` full run at the boundary (baseline: 3
pre-existing shallow-clone failures in `CON-run-identity.md`, unrelated to
this tranche — must not gain new failures).
R12: S14's map edit lands in the SAME commit as S1-S4's code.
R13: commit + push at every phase boundary, retry 2s/4s/8s/16s on network
failure.
R14: `dr-deliver-change`'s R-by-R reconciliation table, all 15 R's.
R15/C3: no operator STOP for any fork this SPEC's own record-first findings
already resolve (A1, A2 below) — consistent with the pre-answered
authority in REQUEST.md.

## Assumptions (operator may override)

A1 (Q1): `SHALLOW_MAX_TOKEN_BUDGET` (`shallow.py`) IS in scope for R1/R2.
Reasoning: SCOPE's site list is illustrative ("config validation,
run_manifest ..., the intake form ..., CLI argument validation, and ANY
doc/map/check that states the ceiling") not exhaustive, C1/C3 retire the
token-expense caution for every per-run ceiling without carving out
shallow mode, and `SHALLOW_MAX_TOKEN_BUDGET` is architecturally the same
shape of ceiling on the same quantity (a run's token budget), just for a
different entry point. Smallest-reasonable reading: include it. Assumed,
operator may override.

A2 (Q2): "config validation" in SCOPE resolves to `preparation.py`'s
`RunPreparationRequestV1` validator (S1), not to any per-run ceiling in
`config.py` — none exists there (only `PACK_TOKEN_BUDGET`, an explicitly
out-of-scope per-call value per R3). "CLI argument validation" resolves to
the same site: the CLI does not independently validate `--token-budget`,
it constructs a `RunPreparationRequestV1` that does. Assumed, operator may
override; recorded as a traced contradiction of the request's own
site-naming rather than an invented extra site.

## Questions for operator (STOP if non-empty)

(empty — both open questions from REQUEST.md resolved above under the
dominance test per C3/R15; no material ambiguity survives)

## Out of scope (explicit)

- `PUBLIC_MAX_CYCLES` / `INTAKE_CYCLES_CEILING_EXCEEDED` (the 12-cycle
  ceiling) — R3: "Per-call completion caps and all OTHER ceilings are out
  of scope; only the per-run token budget ceiling goes."
- `Config.PACK_TOKEN_BUDGET` (per-call prompt-rendering budget) — R3,
  per-call not per-run.
- Route `max_tokens` / `context_window_tokens` (provider completion caps,
  `run_manifest.py` `Route`) — R3, per-call not per-run.
- `RunBudgetIntentV1`'s `"unlimited"` literal path (`continue`/`run`
  commands) — already unbounded today; nothing to remove, not renamed or
  touched (R5's byte-identical-replay requirement makes touching an
  unrelated already-working path pure risk for zero benefit).
- Writing brand-new `docs/map/CON-*` or `SUB-*` documents for
  `intake_form.py`/`shallow.py` beyond the minimal `Owns:` addition (S14) —
  the map gap is closed at the ownership level the SCHEMA.md triage rule
  requires (isolated change, one owning document), not expanded into new
  seam analysis unrelated to R1-R15.

## Frozen-surface contact forecast

Tool-backed (Rung G6), run against the four planned target files and the
three ceiling-constant symbols:

    python tools/blast_radius.py \
      --files src/deepreason/preparation.py src/deepreason/intake_form.py \
              src/deepreason/shallow.py src/deepreason/mcp_server.py \
      --symbols PUBLIC_MAX_TOKEN_BUDGET SHALLOW_MAX_TOKEN_BUDGET \
                INTAKE_TOKEN_BUDGET_CEILING_EXCEEDED

    {
      "result_type": "BLAST_RADIUS_RESULT_V1",
      "targets": {
        "files": ["src/deepreason/preparation.py", "src/deepreason/intake_form.py",
                   "src/deepreason/shallow.py", "src/deepreason/mcp_server.py"],
        "symbols": ["PUBLIC_MAX_TOKEN_BUDGET", "SHALLOW_MAX_TOKEN_BUDGET",
                     "INTAKE_TOKEN_BUDGET_CEILING_EXCEEDED"]
      },
      "base": null,
      "frozen_surface_contacts": [],
      "frozen_adjacent_contacts": [],
      "reachability": [
        {"symbol": "PUBLIC_MAX_TOKEN_BUDGET", "status_current": "UNKNOWN", "status_base": null, "direction": null},
        {"symbol": "SHALLOW_MAX_TOKEN_BUDGET", "status_current": "UNKNOWN", "status_base": null, "direction": null},
        {"symbol": "INTAKE_TOKEN_BUDGET_CEILING_EXCEEDED", "status_current": "UNKNOWN", "status_base": null, "direction": null}
      ],
      "consumers": {
        "tests": [
          {"target": "PUBLIC_MAX_TOKEN_BUDGET", "hits": ["tests/test_intake_form.py:10", "tests/test_intake_form.py:57", "tests/test_intake_form.py:62", "tests/test_intake_form.py:63"]},
          {"target": "INTAKE_TOKEN_BUDGET_CEILING_EXCEEDED", "hits": ["tests/test_error_catalog.py:31", "tests/test_error_catalog.py:34", "tests/test_intake_form.py:7", "tests/test_intake_form.py:58"]}
        ],
        "map_checks": [
          {"target": "src/deepreason/preparation.py", "hits": ["docs/map/CON-authority.md:4", "docs/map/CON-authority.md:83", "docs/map/CON-authority.md:84", "docs/map/CON-run-identity.md:4", "docs/map/CON-run-identity.md:60", "docs/map/CON-run-identity.md:84", "docs/map/CON-seats.md:4", "docs/map/CON-seats.md:146", "docs/map/SEAM-manifest-x-schools.md:153", "docs/map/SEAM-manifest-x-schools.md:235", "docs/map/SEAM-manifest-x-schools.md:253", "docs/map/SUB-amendment.md:139"]},
          {"target": "src/deepreason/mcp_server.py", "hits": ["docs/map/SUB-amendment.md:139", "docs/map/SUB-periphery.md:4", "docs/map/SUB-periphery.md:119", "docs/map/SUB-periphery.md:162"]}
        ],
        "qualification_digest": [],
        "wheel_smoke_pins": []
      },
      "disclosure_summary": "This change touches none of the five frozen surfaces. 2 test file(s) and 2 map document(s) assert on the touched targets today. Reachability here means a syntactic call path exists from a known entry point; it does not prove the path is ever actually exercised at runtime -- a symbol can be syntactically reachable and still never fire because of a runtime precondition this gate does not evaluate.",
      "frozen_surface_verdict": "CLEAR"
    }

`frozen_surface_verdict: CLEAR`, both contact lists empty — no STOP
required by this gate. The three `reachability: UNKNOWN` entries are the
tool's honest limit for plain int/str CONSTANTS (not callables) rather
than a frozen-surface signal: `blast_radius.py`'s own docstring states
UNKNOWN is reported "for any symbol name the static walk cannot resolve
to a definition" in its call-graph BFS, which only walks function
call edges — a module-level constant is never a graph node, so every
constant target is UNKNOWN by construction, independent of any frozen-
surface question. None of the four target files or three symbols appear
in `frozen_surface_contacts`/`frozen_adjacent_contacts`, and (S12) none of
`harness.py`/`invariants.py`/`capabilities/state.py`/`run_manifest.py` is
a target file at all. Not a stop.

## Blast-radius census

Every hit from the tool's `consumers` field above, classified:

- `PUBLIC_MAX_TOKEN_BUDGET` → `tests/test_intake_form.py:10,57,62,63` —
  EXPECTED TO MOVE (S7 rewrites these two tests).
- `INTAKE_TOKEN_BUDGET_CEILING_EXCEEDED` →
  `tests/test_error_catalog.py:31,34`, `tests/test_intake_form.py:7,58` —
  EXPECTED TO MOVE (S7 rewrites both files).
- `preparation.py` → `docs/map/CON-authority.md`, `docs/map/CON-run-
  identity.md`, `docs/map/CON-seats.md`, `docs/map/SEAM-manifest-x-
  schools.md`, `docs/map/SUB-amendment.md` — MUST NOT MOVE. None of these
  hits reference `PUBLIC_MAX_TOKEN_BUDGET`, the removed validator, or
  `__all__`; they cite unrelated `preparation.py` symbols
  (`_request_digest`, seat-binding snapshot naming, etc.) — confirmed by
  reading each hit line, not just counting it. No edit expected or made.
- `mcp_server.py` → `docs/map/SUB-amendment.md`, `docs/map/SUB-
  periphery.md` — MUST NOT MOVE, same reasoning: these cite `mcp_server.py`
  as a file (its `Owns:` membership, its role as the closed MCP facade),
  never the `budget` schema's `maximum` key. No edit expected or made.
- `qualification_digest`, `wheel_smoke_pins` → both empty per the tool's
  symbol-name-based scan. Manual cross-check (required per dr-spec-change
  step 4, because the tool's wheel-smoke-pin detection is a textual/name
  scan and cannot see that `EXPECTED_MCP_SCHEMA_SHA256` is a DATA hash over
  the very schema `mcp_server.py` builds): traced by hand in S8/S8b above.
  `grep -rn "PUBLIC_MAX_TOKEN_BUDGET\|SHALLOW_MAX_TOKEN_BUDGET\|INTAKE_TOKEN_BUDGET_CEILING_EXCEEDED" scripts/ tests/test_mcp.py tests/test_mcp_help.py` → no hits (confirms the tool's empty census is correct AS A NAME SCAN; the sha-drift consequence is real anyway, established by reading `_check_mcp` in both wheel scripts, not by this grep).
- `docs/AGENT.md`, `docs/FORM_DR1_RUN_APPLICATION.md` — not covered by the
  tool (it only census-checks `tests/`/`docs/map/`); manually confirmed:
  `docs/AGENT.md` MUST MOVE (S5); `docs/FORM_DR1_RUN_APPLICATION.md` MUST
  NOT MOVE (S9 — generated only from `Field(description=...)` text, which
  S2 does not touch).

## Budget

    10  preparation.py (const+validator+__all__)      [S1]
    15  intake_form.py (const+validator+import)        [S2]
     8  shallow.py (const+enforcement+__all__)          [S3]
     3  mcp_server.py (schema key+import)                [S4]
     2  docs/AGENT.md (prose)                            [S5]
     7  error_catalog.py (entry removal)                 [S7]
    12  tests/test_intake_form.py                        [S7]
     4  tests/test_error_catalog.py                       [S7]
     4  tests/test_shallow_reason.py                       [S7]
     1  scripts/wheel_smoke.py (sha)                        [S8]
     1  scripts/wheel_operational_smoke.py (sha)             [S8]
     3  docs/map/SUB-application.md (Owns: addition)          [S14]
    ---
    70  TOTAL (python3 -c "print(sum([10,15,8,3,2,7,12,4,4,1,1,3]))" -> 70)

~70 lines, well under the ~300-line split threshold — one sub-tranche, no
split needed. Estimated 2 commits: (1) this SPEC.md + the coming
CHECKLIST.md, (2) one implementation commit carrying S1-S14 together (map
moves with code, wheel-smoke pins move with the schema change that forces
them — CLAUDE.md's same-commit rules for both). VALIDATION.md and
DELIVERY.md are further phase-boundary commits per R13.

Frozen surfaces touched: none (S12).

Rubric: 6/6 yes
- every R has a spec item with a machine-decidable accept: yes (S1-S14
  cover R1-R9; R10-R15 are process obligations enforced at CHECKLIST/commit
  checkpoints, explicitly listed rather than silently dropped)
- blast-radius census pasted and every hit classified: yes
- frozen-surface contact forecast recorded (tool-backed, pasted verbatim):
  yes
- every mechanism the request names traced to code it actually reaches:
  yes (S8b traces and resolves the "four pin locations" mechanism by
  inspection against its own cited precedent)
- nothing in the spec untraceable to an R/C number: yes
- Budget headline (70) equals the pasted itemization sum: yes
