# Request: all configurations are allowed — compile-time denial is abolished

Captured: 2026-08-12 from the task-dispatch message (operator authority) and
the enclosing tranche instructions.

## Map preflight (recorded before any other artifact)

Resolved ids (`docs/map/INDEX.md` routing):

- `DR-SUB-manifest` — **frozen surface 4** (`run_manifest.py` schemas AND
  their validators). The census (R7) is expected to find most compile-time
  semantic denials here — the validator functions this document names
  (`_validate_v4_criticism_policy`, `_preflight_text_authority`,
  `preflight_payload`/`preflight_harness`, the role/ceiling checks, etc.).
- `DR-SUB-application` — owns `src/deepreason/cli/` (so `cli/main.py`) and
  `src/deepreason/intake_form.py` — both explicitly named in the census
  scope.
- `DR-CON-authority` — owns `src/deepreason/config.py`. Authority's own
  frozen rule ("the manifest vocabulary may never be widened... a per-run
  mode goes on `Config`") is a candidate site for a semantic denial
  (`TEXT_AUTHORITY_POLICY_MANIFEST_MISMATCH`) whose *shape as a refusal*
  this tranche may need to convert to a notice — read before touching.
- `DR-CON-seats` — owns `src/deepreason/seat_bindings.py`
  (`SEAT_BINDING_ROLE_CONFLICT` is exactly the kind of "two profiles claim
  one role" contradiction R4 asks to convert to deterministic resolution).
- `INV-frozen-surfaces.md` read in full before scoping. Surfaces 1
  (`capabilities/state.py`), 2 (`harness.py`), 3 (replay-validation
  formats), and 5 (qualification-subject digest inputs) are explicitly
  OUT of scope per the scope line (R8) below — this tranche touches only
  surface 4, and only in the direction the operator pre-granted (R9).
- No map document owns `src/deepreason/cli/main.py`'s "V6 gates" as a
  distinct concept — they are covered piecemeal by `DR-SUB-application`
  (`_admit_v6_root`, `require_v6_launch_allowed`) and `DR-CON-run-identity`
  (`runtime/launch_policy.py`). Treated as part of `DR-SUB-application`'s
  territory for this tranche; not a map gap worth a new document (the
  census, not a subsystem write-up, is the deliverable here).

## Verbatim

> Change tranche: ALL configurations are allowed — compile-time denial is
> abolished. Route through dr-change-orchestrator, all phases through
> dr-deliver-change WITHOUT stopping — the operator has pre-answered the
> design questions below. This SUPERSEDES the earlier "no dead-end denials /
> override flags" prompt if that window started: the rule is now stronger —
> no flags needed, nothing to override, compile never refuses.

> SETUP (fresh container): git fetch origin main && git checkout -B
> claude/all-configs-allowed-p4vn2q origin/main; git merge-base
> --is-ancestor 0a53008d9 HEAD || re-fetch. pip install -e .
> --break-system-packages -q; pip install pytest pytest-xdist jsonschema
> --break-system-packages -q. Use `python -m pytest`, never bare pytest.
> Read CLAUDE.md in full; load dr-explain-to-operator.

> AUTHORITY for REQUEST.md, operator verbatim (2026-08-12): "All
> configurations should be allowed." Context words from the same exchange:
> "There should only be additional flags, not flat out denial" — superseded
> by the final sentence: no flags, no denial. Ledger BOTH, with the
> supersession noted. Also ledger this as a new standing operator design law
> in CLAUDE.md's "Operator design laws" section, same commit as the code
> change, quoting the operator verbatim.

> BINDING DESIGN SHAPE:
> - Any input that PARSES into the configuration model COMPILES into a run.
>   The only remaining rejections are parse/shape errors (unreadable JSON,
>   a string where a number goes) — those are not configurations, they are
>   non-inputs, and their messages stay human-readable via the error
>   catalog.
> - Every current semantic denial (family requirements, role conflicts,
>   backend-identity gates, ceiling checks, combination restrictions)
>   becomes a TYPED COMPILE NOTICE recorded in the compiled manifest/run
>   record: the run proceeds, the record says what the old gate would have
>   said. Notices are disclosures, not gates.
> - Contradictory configurations get DETERMINISTIC RESOLUTION SEMANTICS,
>   not refusal: for each current conflict-denial (e.g. two profiles
>   claiming one role), SPEC.md defines a precedence rule (explicit-most
>   wins; document each rule), applies it, and records the resolution as a
>   typed notice. Same config in → same resolution out, always — run
>   identity stays deterministic.
> - Runtime is unchanged: a config naming an unreachable model, an
>   unsatisfiable ensemble, or a zero budget still FAILS TYPED at the point
>   of use (dispatch error, typed exhaustion, typed seat failure). Those
>   are recorded outcomes, not blocks, and they are the correct place for
>   impossibility to surface.
> - `deepseek validate-intake` and the MCP validate_intake tool become
>   ADVISORY: they report every notice the config will trigger (so a caller
>   can still pre-check), but nothing they report prevents compilation.

> PHASE ORDER: (1) reproduce the grounded-extension run's config compile and
> capture the two blocks it currently hits — both must compile clean (zero
> denials, notices allowed) by delivery; (2) census EVERY compile-time
> semantic denial in run_manifest.py, config.py, intake_form.py,
> cli/main.py, seat_bindings.py, and the V6 gates — SPEC.md tables each
> with its error string, site, pinned tests, and its conversion (notice /
> resolution rule); (3) convert, updating each denial's pinned tests in the
> same commit to assert the new behavior (compiles + emits the typed
> notice), per the census's predictions — never silently deleted.

> SCOPE LINE (definition, not a stop): replay/record validation of
> committed roots (verify_root, invariants.py, capabilities/state.py) is
> out of scope — it validates history, not configuration; how a past run
> verifies must not change, and old roots must replay byte-unchanged
> (prove with a targeted verify_root_report at validation).

> PRE-GRANTED (the operator's words above are the ledgered approval): frozen
> surfaces 3 and 4 as far as this conversion requires, changed
> model-and-validator together; qualification-subject digest drift is a
> consequence to REPORT in DELIVERY.md with its requalification cost, not a
> stop. If IntakeFormV1's schema changes: all FOUR pins in the SAME commit
> (wheel_smoke.py, wheel_operational_smoke.py, tests/test_mcp.py,
> tests/test_mcp_help.py) and regenerate FORM_DR1 (--check clean).

> ERRATA CHECK: any committed document claiming a denial was already
> removed, or describing validate-intake/compile gates as load-bearing
> guarantees that this change retires, gets a docs/ERRATA.md entry (next
> free number — check the ledger tail) same commit. Otherwise "errata:
> none".

> GATE: ring while iterating; full gate at the boundary (baselines: 1
> pre-existing test_bronze_report failure; 5 MCP-thread tests known-flaky
> under -n 4 — isolate before attributing). docs_verify full (baseline: 3
> pre-existing CON-run-identity.md shallow-clone failures). Map moves in
> the same commits as code. Commit and push every phase boundary (retry
> 2s/4s/8s/16s). Deliver with R-by-R reconciliation and the full
> before/after census: every former denial, its new notice or resolution
> rule, and the two motivating blocks shown compiling. No stops.

## Numbered requirements

- **R1.** All configurations are allowed: compile-time denial is abolished.
  (Operator verbatim: "All configurations should be allowed.")
- **R1a.** *Superseded record, not active* — an earlier context statement
  in the same exchange said "There should only be additional flags, not
  flat out denial." The operator's own final sentence supersedes this:
  no flags are needed, nothing to override, compile never refuses. R1a is
  ledgered for the record only; R1/R2/R3/R4 govern the actual design.
- **R2.** Anything that PARSES into the configuration model COMPILES into
  a run. Only parse/shape errors (non-inputs: unreadable JSON, wrong
  scalar type) may still be rejected, with human-readable messages via
  the existing error catalog.
- **R3.** Every current semantic denial (family requirements, role
  conflicts, backend-identity gates, ceiling checks, combination
  restrictions) becomes a typed COMPILE NOTICE recorded in the compiled
  manifest/run record. The run proceeds; the record states what the old
  gate would have said. Notices disclose, they do not gate.
- **R4.** Contradictory configurations resolve deterministically instead
  of refusing: each current conflict-denial gets a documented precedence
  rule (e.g. explicit-most-wins), applied and recorded as a typed notice.
  Same config in → same resolution out, always (run identity stays
  deterministic).
- **R5.** Runtime behavior is unchanged: an unreachable model, an
  unsatisfiable ensemble, or a zero budget still fails TYPED at point of
  use (dispatch error, typed exhaustion, typed seat failure) — these are
  recorded outcomes, not compile-time blocks, and are explicitly out of
  scope for conversion.
- **R6.** `deepreason validate-intake` (CLI) and the MCP `validate_intake`
  tool become advisory: they report every notice the config would
  trigger, but nothing they report prevents compilation.
- **R7.** Process/phase order: (a) reproduce the grounded-extension run's
  config-compile blocks and confirm both compile clean (zero denials,
  notices allowed) by delivery; (b) census EVERY compile-time semantic
  denial across `run_manifest.py`, `config.py`, `intake_form.py`,
  `cli/main.py`, `seat_bindings.py`, and the V6 gates, tabled with error
  string, site, pinned tests, and planned conversion; (c) convert each,
  updating its pinned tests in the same commit to assert new behavior
  (compiles + typed notice), per the census's predictions.
- **R8.** Scope line: replay/record validation of committed roots
  (`verify_root`, `invariants.py`, `capabilities/state.py`) is out of
  scope. How a past run verifies must not change; old roots must replay
  byte-unchanged, proven with a targeted `verify_root_report` at
  validation.
- **R9.** Pre-granted: touching frozen surfaces 3 and 4 as far as this
  conversion requires, changing model and validator together each time.
  Qualification-subject digest drift is a consequence to REPORT in
  DELIVERY.md with its requalification cost — not a stop. If
  `IntakeFormV1`'s schema changes: update all four pins
  (`wheel_smoke.py`, `wheel_operational_smoke.py`, `tests/test_mcp.py`,
  `tests/test_mcp_help.py`) in the same commit and regenerate FORM_DR1
  (`--check` clean).
- **R10.** Errata check: any committed document claiming a denial was
  already removed, or describing validate-intake/compile gates as
  load-bearing guarantees this change retires, gets a `docs/ERRATA.md`
  entry (next free number) in the same commit. Otherwise record
  "errata: none".
- **R11.** Gate discipline: affected-test ring while iterating, full gate
  at the boundary (baselines: 1 pre-existing `test_bronze_report`
  failure; 5 MCP-thread tests known-flaky under `-n 4`, isolate before
  attributing). `docs_verify` full (baseline: 3 pre-existing
  `CON-run-identity.md` shallow-clone failures). Map moves in the same
  commit as code. Commit and push at every phase boundary (retry
  2s/4s/8s/16s on network failure). Deliver with R-by-R reconciliation
  and the full before/after census: every former denial, its new notice
  or resolution rule, and the two motivating blocks shown compiling.
  No stops.
- **R12.** Ledger this tranche's authority as a new standing operator
  design law in `CLAUDE.md`'s "Operator design laws" section, quoting
  the operator verbatim, in the same commit as the code change.

## Assumptions recorded at capture (none yet — SPEC.md is where per-denial
assumptions get recorded, per the scope contract)

None at this stage; SPEC.md's per-requirement acceptance checks are where
ambiguity in an individual denial's conversion is resolved with a recorded
assumption, since the operator has pre-answered the design-level questions
above.
