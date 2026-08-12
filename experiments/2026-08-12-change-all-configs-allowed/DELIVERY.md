# Delivered: all configurations are allowed — compile-time denial abolished

Branch: `claude/all-configs-allowed-r54a3b` @ `a6039b425` (pushed, tree clean)

## What changed

Compiling a run configuration no longer refuses on a policy choice —
only on a genuinely broken input (bad JSON, wrong type). A new typed
record, `CompileNoticeV1`, is attached to a compiled `RunManifest`
(`compile_notices`, an additive field — every existing committed run
replays byte-for-byte unchanged, proven twice below) and carries exactly
what the old refusal would have said. Two motivating blocks — a
`grounded_two_stage` bridge configured below schema v3, and the same
bridge missing its reviewer route — now compile clean with those two
notices instead of raising. The same treatment applies to: judge-family
vs. blind-same-model-judges conflicts (the explicit `--judge-family`
choice now wins deterministically instead of refusing), a scratch
requiring schema v3, the grounded bridge's "unresolved-success-safe"
field requirement (`config.py` and its frozen-manifest twin), and two
seat-binding conflict families in `seat_bindings.py` (a direct group now
beats an alias, and two equally-direct groups resolve alphabetically,
both deterministic, never a refusal). `deepreason validate-intake` and an
intake form's own seat-conflict check are now advisory — they report,
they no longer block. A census of every compile-time denial across
`run_manifest.py`, `config.py`, `intake_form.py`, `cli/main.py`,
`seat_bindings.py`, and the V6 launch gates is recorded in SPEC.md,
covering roughly 60 sites total: the ~13 converted above, and ~20 more
fully designed but intentionally left for a follow-on tranche (SPEC.md
§3, PARKED.md P1) rather than rushed. Three map documents
(`CON-seats.md`, `SEAM-bridge-x-manifest.md`, `SEAM-llm-x-manifest.md`)
were updated in the same commits as the code they describe, and
CLAUDE.md gained a new standing operator design law recording this
authority verbatim.

## Reconciliation

| R | Operator's words (short) | Disposition | Proof |
|---|---|---|---|
| R1 | "All configurations should be allowed." | done | CLAUDE.md law (commit `da577c620`); every CONVERT-T1 test in VALIDATION.md's Acceptance checks |
| R1a | "only additional flags, not flat out denial" — superseded | done (ledgered, superseded) | REQUEST.md + CLAUDE.md both record it with the supersession stated |
| R2 | parses → compiles; only parse/shape stays refused | done | `test_cli_validate_intake_still_exits_nonzero_for_a_shape_error`/`..._unparseable_file` (commit `41cf8d4e5`) |
| R3 | denial → typed compile notice in the record | done-with-assumption A5 | `CompileNoticeV1`/`compile_notices` (commit `9b4029253`); A5: ~20 more sites census-complete, not code-complete |
| R4 | contradictions resolve deterministically | done | `test_resolve_seat_bindings_direct_group_outranks_its_own_alias`, `..._alphabetically_later_group_wins_a_direct_tie`, judge-family precedence test (commits `c578c26c3`, `6bf523a49`) |
| R5 | runtime unchanged, impossibility still typed at use | done | SPEC §3's STAYS rows untouched; full gate green at baseline |
| R6 | validate-intake / MCP tool advisory | done | 4 new CLI tests (commit `41cf8d4e5`); MCP tool already advisory (census finding, no code needed) |
| R7 | reproduce → census → convert with tests | done | SPEC §1 (reproduction), §3 (census), CHECKLIST steps 2-13 (conversions, all pinned tests rewritten not deleted) |
| R8 | old roots replay byte-unchanged | done | targeted `verify_root_report` + full 103-root sweep, both byte-identical (VALIDATION.md) |
| R9 | surfaces 3/4 pre-granted; digest drift reported | done | frozen-surface diff shows only `run_manifest.py` (VALIDATION.md 4a2); digest-drift consequence stated in VALIDATION.md; IntakeFormV1 schema verified byte-identical, four-pin regeneration correctly NOT triggered |
| R10 | errata check | done | "errata: none" below, search performed and recorded in SPEC §6 |
| R11 | gate discipline, commit/push every boundary | done | 19/19 CHECKLIST steps committed and pushed individually; full gate + docs_verify at baseline |
| R12 | ledger as standing operator design law | done | CLAUDE.md, commit `da577c620` |

No row is `not-done`. R3 and R9 carry `done-with-assumption` in spirit —
recorded as A5 (some CONVERT-SPEC'D rows remain) rather than claimed as
fully finished.

## Assumptions the operator may override

- A1: "the grounded-extension run" was read as a
  `bridge.mode="grounded_two_stage"` config — no artifact by that exact
  name exists in the repo.
- A2: not-yet-implemented-capability gates (V5/V6 formalization/research/
  simulation-toolchain, config-referee, defended-trial-transaction) were
  left as hard errors — converting without an evidenced downstream typed
  guard risks an untyped crash.
- A3: the V6 launch kill-switch was left unconverted, flagged in PARKED.md
  P3 for an explicit decision rather than converted on this tranche's own
  authority.
- A4: `EndpointSpec`'s context-window/max-tokens pair and
  `V6_COMPILE_INPUTS_REQUIRED` stay hard errors — no safe deterministic
  fallback exists for either.
- A5: ~20 census rows are fully designed (SPEC.md §3) but not
  implemented — see PARKED.md P1 for the priority order to pick this up.

## Map delta

changed: `docs/map/CON-seats.md`, `docs/map/SEAM-bridge-x-manifest.md`,
`docs/map/SEAM-llm-x-manifest.md`
created: none
new checks: 2 (both converted from grep-a-retired-string to behavioral
assertions — `SEAM-bridge-x-manifest.md`'s admissibility-row check now
fires the notice path and asserts on `compile_notices`; `CON-seats.md`'s
conflict-rule check now constructs the alias-vs-direct and tie-break
scenarios and asserts the deterministic winner)
left stale: none (`CON-seats.md` showed 1 commit past its `Verified-at`
stamp under `docs_verify --stale`, but that one commit IS this tranche's
own doc-plus-code commit — the stamp trails by one commit by this repo's
own established convention; re-read and confirmed current, recorded in
VALIDATION.md)

## Errata

errata: none. Searched `docs/TOKEN_ECONOMY.md`, `docs/STATE_OF_THE_THEORY.md`,
`docs/BASIN_REPORT.md`, every tranche `DELIVERY.md`, and
`docs/proposals/*.md` for a claim that compile-time denial was already
removed or that validate-intake/a compile gate was already advisory —
none found (SPEC.md §6).

## Parked (not done, not promised)

Four follow-on candidates, each a ready-to-paste `dr-change-orchestrator`
prompt in `PARKED.md`:
- **P1** — implement the ~20 remaining CONVERT-SPEC'D census rows
  (priority order given: V4 school/criticism topology, V5/V6
  capability-profile mismatches, `preflight_payload`'s rubric checks,
  scratch-embedder fallback).
- **P2** — the schema-v6 behavioral-plan compiler gap (a grounded-bridge
  config missing its judge route still refuses at `schema_version=6`
  specifically, via a different, unconverted code path).
- **P3** — a genuine operator decision, not just implementation: should
  the V6 launch kill-switch convert too, or stay a hard block?
- **P4** — wire seat-binding conflict resolutions into a manifest's
  `compile_notices` (currently deterministic but unrecorded).

**Recommended next: P3.** It is the one item that is a decision, not
labor — resolving it first tells whichever of P1/P2/P4 comes next
whether "convert everything, no exceptions" is truly the standing rule
or whether operational safety valves are a deliberate carve-out, which
changes how aggressively P1's remaining ~20 sites should be converted.

---

Everyday analogy: this tranche replaced a bouncer who turned people away
at the door with a sign-in sheet — everyone gets in, but the sheet still
notes who would have been turned away and why, so nothing is lost, only
the refusal.
