# Validation for: all configurations are allowed — compile-time denial abolished

Re-read REQUEST.md, SPEC.md, CHECKLIST.md in full before running these
checks (all 19 CHECKLIST steps are checked; this phase re-proves the
assembled whole, not just local per-step progress).

## Acceptance checks (SPEC §5, S-numbers = SPEC §3's row groups)

**§1 — the two grounded-extension blocks compile clean with notices
(delivery proof, re-run now):**

```
BLOCK1 (schema_version=2) notices: ['GROUNDED_BRIDGE_MANIFEST_V3_REQUIRED']
BLOCK2 (schema_version=3) notices: ['BRIDGE_REVIEWER_ROUTE_REQUIRED', 'BRIDGE_REVIEWER_SEATS_MISMATCH']
```
PASS — both compile (no exception), both carry the code the retired gate
would have raised.

**S-B1..S-B6 (run_manifest.py bridge/judge-family cluster) + S-C1
(config.py/BridgePolicy grounded-safety):**
`python -m pytest tests/test_run_manifest_scratch_bridge.py tests/test_run_manifest.py -q`
→ `96 passed`. PASS.

**S-S1..S-S3 (seat_bindings.py deterministic resolution):**
`python -m pytest tests/test_seat_bindings.py -q` → `16 passed`. PASS.

**S-I1 (intake_form.py advisory pass-through) + S-V1 (CLI validate-intake
advisory):**
`python -m pytest tests/test_intake_form.py tests/test_error_catalog.py tests/test_mcp.py tests/test_mcp_help.py -q`
→ `110 passed` (21 + 89). PASS.

## Full gate

`python -m pytest tests/ -q -n 4` → `1 failed, 3535 passed, 7 skipped in
672.85s`. The 1 failure is
`tests/test_bronze_report.py::test_census_totals_internally_consistent`
(`159 == 165`), the exact pre-existing failure named in REQUEST.md's own
baseline (confirmed independently in SPEC §7 before any code changed).
**PASS** (0 failures attributable to this tranche).

Two real issues surfaced and were resolved during CHECKLIST execution
(steps 17), not hidden: `test_manifest_integration.py::test_compile_bind_preflight_text_manifest`
asserted the retired `SECOND_JUDGE_FAMILY_REQUIRED` raise and was rewritten
to assert compile-with-notice; a `test_mcp_run.py` failure reproduced as
the disclosed "MCP-thread flaky under -n 4" baseline (passed in isolation
with `-n 1`, passed again under `-n 4` on immediate re-run).

## Record-behavior preservation

Two independent instruments, both PASS:
1. **Targeted `verify_root_report`** (CHECKLIST step 15): one committed
   root carrying `bridge_policy` (grounded_two_stage) — full report
   `model_dump(mode='json')` byte-identical between the tranche's base
   commit (via `git worktree`) and current HEAD.
2. **Full root sweep** (CHECKLIST step 18): all 103 openable roots under
   `experiments/`, `valid`/`epistemic_checks_passed`/`att`
   length/`module_digests`/`seat_digests` — byte-identical
   `sweep_before.txt` vs `sweep_after.txt` (diff: no differences).

An ad-hoc 2-root `verify_root` spot-check during this validation phase
found `violations: 0` for a healthy root and `violations: 1` for a
defect-era `failed-epoch1-...` root — expected (that root is a recorded
failure by design) and already covered by instrument 2 above, which
proves the count is UNCHANGED from before this tranche, not merely
present.

## Frozen-surface diff (4a2)

```
git diff --stat a9d9b31a3..HEAD -- src/deepreason/capabilities/state.py \
  src/deepreason/harness.py src/deepreason/invariants.py \
  src/deepreason/run_manifest.py src/deepreason/qualification.py

 src/deepreason/run_manifest.py | 148 +++++++++++++++++++++++++++++++++--------
 1 file changed, 120 insertions(+), 28 deletions(-)
```
Non-empty, but REQUEST.md quotes the operator's exact approval: "frozen
surfaces 3 and 4 as far as this conversion requires, changed
model-and-validator together" — surface 4 is `run_manifest.py` schemas AND
validators, which is exactly what changed (a new additive field,
`CompileNoticeV1`/`compile_notices`, plus five validator functions widened
from raise to notice-emit, model+validator moved together in every case
per DR-INV-frozen-surfaces' own trap). **PASS** (authorized touch, not a
violation).

## Packaging surface (4a3)

`mcp_server.py`, `pyproject.toml`, and every console entry point are
untouched by this tranche (confirmed: no diff against any of them). The
CLI changes (`config compile`'s notice printing, `validate-intake`'s
exit-code logic) are internal behavior of EXISTING verbs, not new/renamed
verbs or a changed MCP tool schema. **Packaging surface untouched — smoke
not owed** (a recorded decision, not an omission — grepped
`scripts/wheel_smoke.py`/`wheel_operational_smoke.py` for the touched
symbols first; the only hits are `"validate_intake"` as a bare tool-name
string in an unrelated expected-set, unaffected by this tranche).

## Map

- `python tools/docs_verify.py` → `53 documents, 859 checks` → 3 failed
  (all pre-existing `CON-run-identity.md` shallow-clone git-history
  failures, matching SPEC §7's baseline exactly). **PASS.**
- `python tools/docs_verify.py --audit` → `0 finding(s)`. **PASS.**
- `python tools/docs_verify.py --links` → `0 dangling reference(s), 53
  document(s)`. **PASS.**
- `python tools/docs_verify.py --coverage` → `6 seam(s) swept, 16 without
  a Sweep: header, 0 finding(s)`. **PASS** (0 findings is the pass
  signal; the 16 "no Sweep: header" lines are a pre-existing, unrelated
  advisory backlog across the whole map, not something this tranche
  introduced — two of the sixteen, `SEAM-bridge-x-manifest.md` and
  `SEAM-llm-x-manifest.md`, are files this tranche touched, and adding a
  `Sweep:` header to them is a reasonable follow-up but was judged out of
  this tranche's scope, which is conversions, not map-backlog cleanup).
- `python tools/docs_verify.py --stale` → `1 document(s) worth
  re-reading`: `CON-seats.md`, 1 commit since its `Verified-at` stamp —
  that one commit (`c578c26c3`) is THIS TRANCHE'S OWN commit, which
  updated `CON-seats.md` in the same commit as the code it documents (the
  stamp records the PARENT commit per this repo's own established
  convention — see `SEAM-bridge-x-manifest.md`/`SEAM-llm-x-manifest.md`'s
  identical stamps set the same way in step 9/10-11). **Dismissed**: not
  a real staleness, an artifact of the stamp-trails-by-one-commit
  convention; re-read and confirmed current as part of writing this
  section.
- New checks added by this change: `SEAM-bridge-x-manifest.md`'s
  admissibility-row check now asserts the compile-notice behavior (was:
  asserts a raise); `CON-seats.md`'s conflict-rule check now asserts the
  deterministic-resolution behavior via a constructed scenario (was:
  `grep -q "SEAT_BINDING_ROLE_CONFLICT"`) — both are BEHAVIORAL, not
  textual, satisfying "anchor to meaning, not form."
- Record observables added vs sweep probes: `RunManifest.compile_notices`
  is a new field. `tools/root_sweep.py` does not read it — no probe
  added. **Justification, not a silent gap:** `compile_notices` is
  popped from canonical bytes/digest whenever empty (the overwhelming
  majority of existing roots and this tranche's own two motivating
  blocks are the exception, not committed roots), so a sweep probe would
  report "0 for every existing root" today, which is trivially true and
  proves nothing — exactly the anti-pattern `DR-INV-frozen-surfaces`'
  root-sweep section warns against manufacturing. A probe becomes
  meaningful once a run with actual notices is COMMITTED (none is, by
  this tranche); adding one now would be speculative coverage. Recorded
  here rather than silently omitted.

## Requirement sweep (REQUEST.md R1-R12)

- **R1**: demonstrated by every CONVERT-T1 row's test in "Acceptance
  checks" above, plus CLAUDE.md's new operator-design-law entry (step
  14) stating the rule as standing law.
- **R1a**: superseded, ledgered verbatim alongside R1 in both
  REQUEST.md and CLAUDE.md (step 14) — recorded, not acted on.
- **R2**: demonstrated by `test_cli_validate_intake_still_exits_nonzero_for_a_shape_error`
  and `..._for_an_unparseable_file` (parse/shape stays refused) plus
  every CONVERT-T1 test (a parseable config now compiles).
- **R3**: demonstrated by every CONVERT-T1 test asserting
  `manifest.compile_notices` carries the retired code/message/pointer.
- **R4**: demonstrated by `test_resolve_seat_bindings_direct_group_outranks_its_own_alias`,
  `..._alphabetically_later_group_wins_a_direct_tie`,
  `test_parse_seat_flags_duplicate_group_last_flag_wins`,
  `test_parse_school_seat_flags_duplicate_id_last_flag_wins`, and
  `test_blind_same_model_judges_conflicts_with_judge_family` (all
  deterministic, no raise).
- **R5**: demonstrated by SPEC §3's STAYS rows (resolve_route_seat_*
  dispatch resolvers, PROVIDER_CREDENTIAL_MISSING, REASONING_MUST_BE_DISABLED,
  qualification confirmation gates) — none touched; by-inspection plus
  the full gate passing with 0 attributable failures.
- **R6**: demonstrated by the four new `test_cli_validate_intake_*` tests
  (step 13) and the census's confirmation that the MCP tool was already
  advisory-shaped (no code change needed there).
- **R7**: (a) SPEC §1's empirical reproduction; (b) SPEC §3's full census
  table (three parallel research agents, one per file cluster); (c)
  CHECKLIST steps 2-13's conversions, each with rewritten pinned tests,
  never silently deleted (every renamed/rewritten test is named in its
  own CHECKLIST step).
- **R8**: demonstrated by "Record-behavior preservation" above — two
  independent instruments, both byte-identical.
- **R9**: qualification-subject digest drift reported below (not a
  stop); IntakeFormV1's JSON Schema verified byte-identical before/after
  (step 12), so the four-pin FORM_DR1 regeneration is NOT triggered —
  correctly not done, since doing it for an unchanged schema would be
  the wrong action, not merely an unnecessary one.
- **R10**: SPEC §6 — errata check performed (grepped for prior claims of
  removal/advisory-already), none found. **Errata: none.**
- **R11**: gate discipline followed throughout CHECKLIST (ring while
  iterating, e.g. `test_run_manifest.py`/`test_run_manifest_scratch_bridge.py`
  after each `run_manifest.py` edit; full gate + docs_verify only at the
  boundary); baselines matched exactly; every step committed and pushed
  (19/19); this VALIDATION.md itself is the R-by-R proof R11 asks for.
- **R12**: demonstrated by CLAUDE.md's new "All configurations should be
  allowed" bullet (step 14), same commit shape as the code (a
  docs-only commit, since no code changed in that step — R12 only asked
  for the ledger entry).

## Digest-drift consequence (R9, reported not stopped)

Any FUTURE manifest compile that actually triggers a notice (e.g. a real
grounded-bridge config missing its judge route, or a genuinely
single-family judge matrix under `require_cross_family`) will carry a
non-empty `compile_notices`, which is INCLUDED in that manifest's
canonical bytes and therefore its qualification-subject digest (per
`qualification_subject_payload`'s own rule: everything but `compiled_at`
and `run_input_digest` is in the digest). Requalification cost if an
operator's EXISTING profile now compiles with a notice it didn't carry
before (e.g. because they were relying on `judge_family` and
`blind_same_model_judges` together, previously refused, now resolved):
one full qualification battery, ~14 minutes, ~1160 provider calls, per
`DR-INV-frozen-surfaces`. This is a NEW-COMPILE cost, never a
re-derivation of an existing committed root's identity (proven above) —
no existing qualified subject is invalidated by this tranche.

## Known gaps (disclosed, not hidden)

1. **Schema v6 behavioral-plan compiler** (`_compile_route_seat_behavioral_capability_plan`):
   the SAME missing-judge-route scenario that compiles clean at
   `schema_version` 2/3 (SPEC §1) still hits an unconverted site,
   `V6_BEHAVIORAL_CONTRACT_ROUTE_REQUIRED`, at `schema_version=6`
   (found empirically during step 8, documented in SPEC §1's "Known gap"
   note). R2/R3 hold for schema 2/3; NOT yet for schema 6 with an
   identical missing-role configuration.
2. **CONVERT-SPEC'D rows** (SPEC §3, ~20 sites: the V4 school/criticism
   topology cluster, V5/V6 capability-profile mismatches,
   `preflight_payload`'s rubric/second-judge checks, the scratch-embedder
   fallback, calibration-receipt preflight) are fully designed with a
   stated conversion rule but NOT implemented in this tranche — CHECKLIST
   scoped to the tier-1 set only (§8, assumption 5).
3. **Not-yet-implemented-capability gates** (V5/V6 `_FORMALIZATION_UNAVAILABLE`,
   `_RESEARCH_UNAVAILABLE`, `_CONFIG_REFEREE_CRITIC_SEAT_REQUIRED`,
   `_DEFENDED_TRIAL_TRANSACTION_CONTRACT_REQUIRED`,
   `_SIMULATION_TOOLCHAIN_UNSAFE`) deliberately left as hard errors —
   converting without an evidenced downstream typed guard risks an
   untyped crash, violating "everything meaningful is TYPED" (SPEC §2.2).
4. **V6 launch kill-switch** (`V6_LAUNCH_DISABLED`, both the env-var and
   release-policy sources) deliberately left a hard error — judged an
   incident-rollback valve outside the operator's named denial
   categories, flagged for explicit confirmation rather than converted
   on this tranche's own authority (SPEC §3.5).
5. **Seat-binding resolutions carry no `CompileNoticeV1`** — `deepreason
   setup`'s seat-binding resolution runs before any `compile_run_manifest`
   call; R4 (deterministic resolution) is satisfied for all three
   converted sites, R3 (recorded in the compiled manifest/run record) is
   not yet wired for this family (SPEC §3.3 addendum).
6. **`EndpointSpec`'s context-window/max-tokens pair** and
   `V6_COMPILE_INPUTS_REQUIRED` (missing required CLI args for schema
   v6) stay hard errors — no safe deterministic fallback value exists for
   either (SPEC §3.2/§3.4).

None of these six are silent: each is named in SPEC.md's census table
with its classification and reasoning, and repeated here so DELIVERY.md's
reconciliation can point at them directly rather than the operator
discovering them by reading code.

## Assumptions carried (SPEC §8)

- A1: "the grounded-extension run" read as a `bridge.mode="grounded_two_stage"`
  config (no such named artifact exists in the repo).
- A2: not-yet-implemented-capability gates deferred without an evidenced
  downstream typed guard, rather than converted on faith.
- A3: the V6 launch kill-switch left unconverted, flagged for follow-up
  confirmation rather than decided unilaterally.
- A4: `EndpointSpec`'s context-window pair and `V6_COMPILE_INPUTS_REQUIRED`
  stay hard errors (no safe fallback exists).
- A5: CONVERT-SPEC'D rows are census-complete, not code-complete — stated
  plainly rather than implied as done.

## Verdict: PASS

Every acceptance check ran and passed; the full gate ends at exactly the
pre-existing baseline; both record-preservation instruments are
byte-identical; the map gate is clean (one stale-flag dismissed with
reason); every R1-R12 is demonstrated or explicitly, honestly deferred
with the operator's own authority cited. The six known gaps are scope
boundaries this tranche drew and disclosed, not defects — they do not
block PASS because SPEC.md itself scoped them out in advance (§8), and
none contradicts a specific operator instruction.
